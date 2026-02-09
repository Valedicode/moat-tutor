"""
Moat News Classifier

Classifies news passages into moat source categories using semantic search,
detects price-anchored moat events, and identifies moat milestones.

Three-layer approach:
- Layer 1: Price-anchored events (find big price moves, search surrounding news)
- Layer 2: Moat-themed scans (curated queries per moat source)
- Layer 3: ROIC overlay (connect events to ROIC inflection points)
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np

from services.fnspid_news_pipeline import (
    CACHE_DIR,
    EMBEDDINGS_DIR,
    EMBEDDING_MODEL,
    load_passages_jsonl,
    load_embeddings,
    cosine_similarity,
    generate_embeddings,
)
from services.fnspid_retrieval import is_fnspid_data_available
from services.stock_data import StockDataService, get_stock_data_service
from services.roic_calculator import check_roic_hurdle

logger = logging.getLogger(__name__)


# ============================================================================
# Moat Source Query Bank
# ============================================================================

MOAT_SOURCE_QUERIES = {
    "network_effects": [
        "platform user growth ecosystem expansion developer adoption",
        "marketplace growth partner integrations network value increasing",
        "customer base expanding viral adoption platform dominance",
    ],
    "switching_costs": [
        "enterprise adoption long-term contracts customer retention",
        "platform migration difficulty integration depth lock-in",
        "recurring revenue subscription growth customer loyalty",
    ],
    "intangible_assets": [
        "patent granted intellectual property innovation breakthrough",
        "brand strength premium pricing market leadership recognition",
        "proprietary technology trade secret research advancement",
    ],
    "cost_advantages": [
        "economies of scale manufacturing efficiency cost reduction",
        "operational leverage margin expansion supply chain optimization",
        "cost leadership competitive pricing process improvement",
    ],
    "regulatory_barriers": [
        "regulatory approval government contract compliance certification",
        "antitrust investigation regulatory scrutiny market regulation",
        "licensing requirement entry barrier regulatory protection",
    ],
    "ecosystem_lockin": [
        "platform ecosystem integration multi-product bundle strategy",
        "developer tools API adoption third-party integration",
        "cross-product synergy platform standard proprietary format",
    ],
}

# Classification thresholds
CLASSIFICATION_THRESHOLD = 0.35  # Minimum similarity to assign a moat source
HIGH_CONFIDENCE_THRESHOLD = 0.50  # High-confidence classification

# Milestone scoring weights
PRICE_IMPACT_WEIGHT = 0.4
SIMILARITY_WEIGHT = 0.6

# Cache for moat query embeddings
_moat_query_embeddings_cache: Optional[dict[str, np.ndarray]] = None


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class MoatEvent:
    """A news event classified to a moat source."""
    date: str
    ticker: str
    moat_source: str
    strength: str  # "Strong", "Moderate", "Weak"
    similarity: float
    headline: str
    passage_text: str
    url: str
    passage_id: str
    price_change_pct: Optional[float] = None  # If price-anchored


@dataclass
class MoatMilestone:
    """A significant moat event combining news, price, and ROIC signals."""
    date: str
    ticker: str
    moat_source: str
    headline: str
    passage_text: str
    milestone_score: float
    price_impact_pct: Optional[float]
    similarity: float
    roic_context: Optional[str]  # e.g., "ROIC increased from 20% to 25% in this year"
    url: str


# ============================================================================
# Moat Query Embedding Cache
# ============================================================================

def _get_moat_query_embeddings() -> dict[str, np.ndarray]:
    """
    Get or compute embeddings for the moat query bank.

    These are computed once and cached in memory. Each moat source
    gets a matrix of query embeddings (n_queries x dimensions).
    """
    global _moat_query_embeddings_cache

    if _moat_query_embeddings_cache is not None:
        return _moat_query_embeddings_cache

    # Check disk cache first
    cache_path = EMBEDDINGS_DIR / "_moat_queries.npz"
    meta_path = EMBEDDINGS_DIR / "_moat_queries.json"

    if cache_path.exists() and meta_path.exists():
        try:
            data = np.load(cache_path)
            with open(meta_path, "r") as f:
                meta = json.load(f)

            embeddings = {}
            for source in MOAT_SOURCE_QUERIES:
                key = f"source_{source}"
                if key in data:
                    embeddings[source] = data[key]

            if len(embeddings) == len(MOAT_SOURCE_QUERIES):
                _moat_query_embeddings_cache = embeddings
                logger.info("Loaded moat query embeddings from disk cache")
                return embeddings
        except Exception as e:
            logger.warning(f"Failed to load cached moat embeddings: {e}")

    # Generate embeddings for all queries
    logger.info("Generating moat query embeddings (one-time cost)...")
    embeddings = {}

    for source, queries in MOAT_SOURCE_QUERIES.items():
        emb = generate_embeddings(queries)
        embeddings[source] = emb

    # Save to disk
    try:
        EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
        np.savez(
            cache_path,
            **{f"source_{k}": v for k, v in embeddings.items()},
        )
        with open(meta_path, "w") as f:
            json.dump(
                {
                    "sources": list(embeddings.keys()),
                    "model": EMBEDDING_MODEL,
                    "generated_at": datetime.now().isoformat(),
                },
                f,
            )
        logger.info(f"Saved moat query embeddings to {cache_path}")
    except Exception as e:
        logger.warning(f"Failed to cache moat embeddings: {e}")

    _moat_query_embeddings_cache = embeddings
    return embeddings


# ============================================================================
# Layer 2: Moat-Themed News Classification
# ============================================================================

def classify_passages_by_moat_source(
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    top_k_per_source: int = 10,
) -> dict:
    """
    Classify news passages into moat source categories using the query bank.

    For each moat source, finds the passages most semantically similar
    to the curated queries. Uses pre-computed passage embeddings (no API
    calls for passages, only for query bank on first run).

    Args:
        ticker: Stock ticker symbol
        start_date: Optional start date filter
        end_date: Optional end date filter
        top_k_per_source: Number of top passages per moat source

    Returns:
        Dict with classified passages grouped by moat source
    """
    ticker = ticker.upper()

    if not is_fnspid_data_available(ticker):
        return {
            "ticker": ticker,
            "error": f"No FNSPID data available for {ticker}.",
        }

    # Load passages and embeddings
    passages = load_passages_jsonl(ticker)
    embeddings, passage_ids = load_embeddings(ticker)

    if not passages or len(embeddings) == 0:
        return {"ticker": ticker, "error": "No passage data."}

    # Build passage lookup and filter by date
    passage_map = {p.passage_id: p for p in passages}
    valid_indices = []
    for i, pid in enumerate(passage_ids):
        if pid not in passage_map:
            continue
        p = passage_map[pid]
        if start_date and p.date < start_date:
            continue
        if end_date and p.date > end_date:
            continue
        valid_indices.append(i)

    if not valid_indices:
        return {"ticker": ticker, "error": "No passages in date range."}

    filtered_embeddings = embeddings[valid_indices]
    filtered_ids = [passage_ids[i] for i in valid_indices]

    # Get moat query embeddings
    moat_embeddings = _get_moat_query_embeddings()

    # Classify passages
    classified: dict[str, list[MoatEvent]] = defaultdict(list)

    for source, query_embs in moat_embeddings.items():
        # Average the query embeddings for this source to create a centroid
        centroid = query_embs.mean(axis=0)

        # Compute similarity of all passages to this centroid
        similarities = cosine_similarity(centroid, filtered_embeddings)

        # Get top-k above threshold
        top_indices = np.argsort(similarities)[::-1][:top_k_per_source]

        for idx in top_indices:
            sim = float(similarities[idx])
            if sim < CLASSIFICATION_THRESHOLD:
                continue

            pid = filtered_ids[idx]
            p = passage_map.get(pid)
            if not p:
                continue

            strength = (
                "Strong" if sim >= HIGH_CONFIDENCE_THRESHOLD
                else "Moderate" if sim >= 0.40
                else "Weak"
            )

            event = MoatEvent(
                date=p.date,
                ticker=ticker,
                moat_source=source,
                strength=strength,
                similarity=round(sim, 4),
                headline=p.headline,
                passage_text=p.passage_text[:300],
                url=p.url,
                passage_id=p.passage_id,
            )
            classified[source].append(event)

    # Sort each source by similarity descending
    for source in classified:
        classified[source].sort(key=lambda e: e.similarity, reverse=True)

    # Build summary
    source_counts = {s: len(evts) for s, evts in classified.items()}
    primary_source = max(source_counts, key=source_counts.get) if source_counts else None

    return {
        "ticker": ticker,
        "date_range": f"{start_date or 'all'} to {end_date or 'all'}",
        "sources": {
            s: [asdict(e) for e in evts]
            for s, evts in classified.items()
        },
        "source_counts": source_counts,
        "primary_source": primary_source,
        "total_classified": sum(source_counts.values()),
        "calculated_at": datetime.now().isoformat(),
    }


# ============================================================================
# Layer 1: Price-Anchored Event Detection
# ============================================================================

def detect_price_anchored_events(
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    price_threshold_pct: float = 5.0,
    news_window_days: int = 3,
    max_events: int = 50,
) -> list[MoatEvent]:
    """
    Find notable price movements and search for moat-relevant news around them.

    1. Find all daily price moves >= threshold
    2. For each move, find passages within +/- news_window_days
    3. Classify each passage to a moat source
    4. Return events combining price signal + news classification

    Args:
        ticker: Stock ticker symbol
        start_date: Optional start date
        end_date: Optional end date
        price_threshold_pct: Minimum daily price change (%)
        news_window_days: Days before/after price move to search for news
        max_events: Maximum events to return

    Returns:
        List of MoatEvent objects with price_change_pct populated
    """
    ticker = ticker.upper()
    service = get_stock_data_service()

    # Get notable price movements
    movements = service.find_notable_movements(
        ticker,
        start_date=start_date,
        end_date=end_date,
        threshold_pct=price_threshold_pct,
    )

    if not movements:
        return []

    # Check if FNSPID data is available
    if not is_fnspid_data_available(ticker):
        # Return price-only events
        return [
            MoatEvent(
                date=m["date"],
                ticker=ticker,
                moat_source="unknown",
                strength="Price-only",
                similarity=0.0,
                headline=f"{m['direction'].title()} {abs(m['pct_change']):.1f}%",
                passage_text="No news data available for classification.",
                url="",
                passage_id="",
                price_change_pct=m["pct_change"],
            )
            for m in movements[:max_events]
        ]

    # Load passages and embeddings
    passages = load_passages_jsonl(ticker)
    embeddings_arr, passage_ids = load_embeddings(ticker)

    if not passages or len(embeddings_arr) == 0:
        return []

    passage_map = {p.passage_id: p for p in passages}
    moat_embeddings = _get_moat_query_embeddings()

    events: list[MoatEvent] = []

    for movement in movements:
        move_date = movement["date"]
        move_pct = movement["pct_change"]

        # Define news window
        d = datetime.strptime(move_date, "%Y-%m-%d")
        window_start = (d - timedelta(days=news_window_days)).strftime("%Y-%m-%d")
        window_end = (d + timedelta(days=news_window_days)).strftime("%Y-%m-%d")

        # Find passages in the window
        window_indices = []
        for i, pid in enumerate(passage_ids):
            p = passage_map.get(pid)
            if not p:
                continue
            if p.date >= window_start and p.date <= window_end:
                window_indices.append(i)

        if not window_indices:
            continue

        window_embs = embeddings_arr[window_indices]
        window_pids = [passage_ids[i] for i in window_indices]

        # Classify each passage against moat sources
        best_source = None
        best_sim = 0.0
        best_pid = None

        for source, query_embs in moat_embeddings.items():
            centroid = query_embs.mean(axis=0)
            sims = cosine_similarity(centroid, window_embs)
            max_idx = int(np.argmax(sims))
            max_sim = float(sims[max_idx])

            if max_sim > best_sim:
                best_sim = max_sim
                best_source = source
                best_pid = window_pids[max_idx]

        if best_source and best_sim >= CLASSIFICATION_THRESHOLD and best_pid:
            p = passage_map[best_pid]
            strength = (
                "Strong" if best_sim >= HIGH_CONFIDENCE_THRESHOLD
                else "Moderate" if best_sim >= 0.40
                else "Weak"
            )

            events.append(MoatEvent(
                date=move_date,
                ticker=ticker,
                moat_source=best_source,
                strength=strength,
                similarity=round(best_sim, 4),
                headline=p.headline,
                passage_text=p.passage_text[:300],
                url=p.url,
                passage_id=p.passage_id,
                price_change_pct=move_pct,
            ))

    # Sort by absolute price impact descending
    events.sort(key=lambda e: abs(e.price_change_pct or 0), reverse=True)
    return events[:max_events]


# ============================================================================
# Layer 3: Milestone Detection (combines all layers + ROIC)
# ============================================================================

def detect_moat_milestones(
    ticker: str,
    top_n: int = 15,
) -> dict:
    """
    Identify the most significant moat milestones for a ticker by combining:
    - Price-anchored events (Layer 1)
    - Moat-themed scan results (Layer 2)
    - ROIC year-over-year context (Layer 3)

    A milestone is scored by:
      score = PRICE_IMPACT_WEIGHT * normalized_price_impact
            + SIMILARITY_WEIGHT * similarity

    Args:
        ticker: Stock ticker symbol
        top_n: Number of top milestones to return

    Returns:
        Dict with ranked milestones and timeline
    """
    ticker = ticker.upper()

    # --- Layer 1: Price-anchored events ---
    price_events = detect_price_anchored_events(
        ticker, price_threshold_pct=5.0, max_events=100
    )

    # --- Layer 2: Moat-themed scan (top passages per source) ---
    classification = classify_passages_by_moat_source(
        ticker, top_k_per_source=15
    )
    themed_events: list[MoatEvent] = []
    for source, events_list in classification.get("sources", {}).items():
        for e_dict in events_list:
            themed_events.append(MoatEvent(**e_dict))

    # --- Layer 3: ROIC context ---
    roic_by_year = _build_roic_context(ticker)

    # --- Merge and score ---
    # Deduplicate by passage_id, preferring price-anchored version
    seen_pids = set()
    all_candidates: list[MoatEvent] = []

    for e in price_events:
        if e.passage_id and e.passage_id not in seen_pids:
            seen_pids.add(e.passage_id)
            all_candidates.append(e)

    for e in themed_events:
        if e.passage_id and e.passage_id not in seen_pids:
            seen_pids.add(e.passage_id)
            all_candidates.append(e)

    if not all_candidates:
        return {
            "ticker": ticker,
            "milestones": [],
            "error": "No moat events found. Ensure FNSPID data is available.",
        }

    # Normalize price impacts for scoring
    price_impacts = [abs(e.price_change_pct or 0) for e in all_candidates]
    max_impact = max(price_impacts) if price_impacts else 1.0

    # Score and rank
    milestones: list[MoatMilestone] = []
    for e in all_candidates:
        norm_impact = abs(e.price_change_pct or 0) / max(max_impact, 0.01)
        score = (
            PRICE_IMPACT_WEIGHT * norm_impact
            + SIMILARITY_WEIGHT * e.similarity
        )

        # ROIC context for the year of the event
        event_year = int(e.date[:4]) if e.date and len(e.date) >= 4 else None
        roic_ctx = roic_by_year.get(event_year) if event_year else None

        milestones.append(MoatMilestone(
            date=e.date,
            ticker=ticker,
            moat_source=e.moat_source,
            headline=e.headline,
            passage_text=e.passage_text,
            milestone_score=round(score, 4),
            price_impact_pct=e.price_change_pct,
            similarity=e.similarity,
            roic_context=roic_ctx,
            url=e.url,
        ))

    # Sort by milestone score descending
    milestones.sort(key=lambda m: m.milestone_score, reverse=True)
    top_milestones = milestones[:top_n]

    # Build timeline (chronological)
    timeline = sorted(top_milestones, key=lambda m: m.date)

    return {
        "ticker": ticker,
        "milestones": [asdict(m) for m in top_milestones],
        "timeline": [asdict(m) for m in timeline],
        "total_candidates": len(all_candidates),
        "moat_source_distribution": _count_sources(top_milestones),
        "calculated_at": datetime.now().isoformat(),
    }


def _build_roic_context(ticker: str) -> dict[int, str]:
    """Build year-to-ROIC-context mapping for milestone annotation."""
    try:
        result = check_roic_hurdle(ticker, years=20, use_cache=True)
        if "error" in result:
            return {}

        annual = result.get("annual_data", [])
        roic_map = {}

        for entry in annual:
            year = entry["year"]
            roic_pct = entry["roic_pct"]
            spread = entry.get("roic_wacc_spread_pct", roic_pct - 10.0)
            roic_map[year] = (
                f"ROIC: {roic_pct:.1f}% (spread: {spread:+.1f}pp vs WACC)"
            )

        return roic_map

    except Exception as e:
        logger.warning(f"Could not build ROIC context for {ticker}: {e}")
        return {}


def _count_sources(milestones: list[MoatMilestone]) -> dict[str, int]:
    """Count moat sources among milestones."""
    counts: dict[str, int] = defaultdict(int)
    for m in milestones:
        counts[m.moat_source] += 1
    return dict(counts)
