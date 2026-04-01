"""
MOAT ETF Holdings Service

Provides structured access to VanEck Morningstar Wide Moat ETF (MOAT) holdings,
focused on the Technology sector. Parses the holdings Excel for per-holding
weight data (% of net assets) and computes sub-sector and total tech aggregates.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
DEFAULT_HOLDINGS_FILE = DATA_DIR / "MOAT_asof_20260327.xlsx"

# ============================================================================
# MOAT ETF Technology Sector Holdings (curated)
# ============================================================================

MOAT_TECH_SECTORS: dict[str, dict[str, str]] = {
    "Software & SaaS": {
        "MSFT": "Microsoft Corp",
        "ADBE": "Adobe Inc",
        "CRM": "Salesforce.com Inc",
        "ORCL": "Oracle Corp",
        "NOW": "ServiceNow Inc",
        "WDAY": "Workday Inc",
        "VEEV": "Veeva Systems Inc",
        "DDOG": "Datadog Inc",
        "TYL": "Tyler Technologies Inc",
        "FICO": "Fair Isaac Corp",
    },
    "Semiconductors & Hardware": {
        "NVDA": "Nvidia Corp",
        "NXPI": "NXP Semiconductors NV",
        "AMAT": "Applied Materials Inc",
        "AVGO": "Broadcom Inc",
        "ENTG": "Entegris Inc",
    },
    "Cybersecurity": {
        "FTNT": "Fortinet Inc",
        "PANW": "Palo Alto Networks Inc",
    },
    "Platforms & Data Infrastructure": {
        "META": "Meta Platforms Inc",
        "MSI": "Motorola Solutions Inc",
        "BR": "Broadridge Financial Solutions Inc",
        "TRU": "TransUnion",
        "CSGP": "CoStar Group Inc",
    },
}

ETF_AS_OF_DATE = "2026-03-27"


# ============================================================================
# Excel parser with column mapping
# ============================================================================

# Normalized column names we look for (case-insensitive partial match)
_COL_PATTERNS = {
    "ticker": ["ticker"],
    "holding_name": ["holding name", "name", "holding"],
    "pct_net_assets": ["% of net assets", "net assets", "weight"],
}


def _match_column(header: str, patterns: list[str]) -> bool:
    h = header.strip().lower()
    return any(p in h for p in patterns)


def _parse_pct(raw: Any) -> Optional[float]:
    """Parse a percentage value like '2.87%' or 0.0287 into 2.87."""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s == "--":
        return None
    try:
        if s.endswith("%"):
            return float(s[:-1])
        val = float(s)
        if 0 < val < 1:
            return round(val * 100, 4)
        return val
    except (ValueError, TypeError):
        return None


def parse_holdings_excel(
    filepath: Path | str | None = None,
) -> list[dict[str, Any]]:
    """
    Parse the MOAT ETF holdings Excel and return rows with normalized keys.

    Scans for the header row (the first row containing a 'ticker' column),
    then maps columns to: ticker, holding_name, pct_net_assets (float).
    """
    filepath = Path(filepath) if filepath else DEFAULT_HOLDINGS_FILE
    if not filepath.exists():
        logger.warning("Holdings Excel not found at %s", filepath)
        return []

    try:
        import openpyxl
    except ImportError:
        logger.warning("openpyxl not installed -- cannot parse Excel holdings")
        return []

    try:
        wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
        ws = wb.active
        if ws is None:
            return []

        rows = list(ws.iter_rows(values_only=True))
        wb.close()
    except Exception as e:
        logger.warning("Failed to read Excel %s: %s", filepath, e)
        return []

    if len(rows) < 2:
        return []

    # Scan for the header row (first row containing a 'ticker' column)
    header_idx: int | None = None
    raw_headers: list[str] = []
    for idx, row in enumerate(rows):
        cells = [str(c).strip() if c else "" for c in row]
        if any(_match_column(c, ["ticker"]) for c in cells):
            header_idx = idx
            raw_headers = cells
            break

    if header_idx is None:
        logger.warning("Could not find header row with 'ticker' in Excel")
        return []

    col_map: dict[str, int] = {}
    for norm_key, patterns in _COL_PATTERNS.items():
        for i, h in enumerate(raw_headers):
            if _match_column(h, patterns):
                col_map[norm_key] = i
                break

    if "ticker" not in col_map:
        logger.warning("Could not map 'ticker' column from headers: %s", raw_headers)
        return []

    holdings: list[dict[str, Any]] = []
    for row in rows[header_idx + 1:]:
        if not row or len(row) <= col_map["ticker"]:
            continue

        ticker_val = row[col_map["ticker"]]
        if not ticker_val or not str(ticker_val).strip():
            continue

        ticker = str(ticker_val).strip().upper()
        name = (
            str(row[col_map["holding_name"]]).strip()
            if "holding_name" in col_map and col_map["holding_name"] < len(row)
            else None
        )
        pct_raw = (
            row[col_map["pct_net_assets"]]
            if "pct_net_assets" in col_map and col_map["pct_net_assets"] < len(row)
            else None
        )
        pct = _parse_pct(pct_raw)

        holdings.append({
            "ticker": ticker,
            "holding_name": name,
            "pct_net_assets": pct,
        })

    return holdings


# ============================================================================
# Lazy-loaded weight cache (parsed once from Excel)
# ============================================================================

_excel_weights: dict[str, dict[str, Any]] | None = None


def _load_excel_weights() -> dict[str, dict[str, Any]]:
    """Parse the Excel once and return a dict keyed by ticker."""
    global _excel_weights
    if _excel_weights is not None:
        return _excel_weights

    rows = parse_holdings_excel()
    _excel_weights = {}
    for row in rows:
        t = row["ticker"]
        _excel_weights[t] = row

    if _excel_weights:
        logger.info("Loaded Excel weights for %d holdings", len(_excel_weights))
    else:
        logger.info("No Excel weight data available (file missing or empty)")

    return _excel_weights


def get_holding_weight(ticker: str) -> Optional[float]:
    """Return the % of net assets for a ticker, or None if unavailable."""
    weights = _load_excel_weights()
    entry = weights.get(ticker.upper())
    return entry["pct_net_assets"] if entry else None


# ============================================================================
# Public helpers
# ============================================================================

def get_all_tech_tickers() -> list[str]:
    """Return a flat sorted list of all MOAT ETF technology tickers."""
    tickers: set[str] = set()
    for sector_tickers in MOAT_TECH_SECTORS.values():
        tickers.update(sector_tickers.keys())
    return sorted(tickers)


def get_sector_for_ticker(ticker: str) -> Optional[str]:
    """Return the tech sub-sector name for a ticker, or None if not in MOAT tech."""
    ticker = ticker.upper()
    for sector, tickers in MOAT_TECH_SECTORS.items():
        if ticker in tickers:
            return sector
    return None


def is_moat_etf_holding(ticker: str) -> bool:
    """Check whether a ticker is part of the MOAT ETF technology sector."""
    return get_sector_for_ticker(ticker) is not None


def get_etf_tech_holdings(sub_sector: Optional[str] = None) -> dict[str, Any]:
    """
    Return structured MOAT ETF technology holdings grouped by sub-sector.

    Includes per-holding % of net assets (from Excel when available),
    per-sub-sector aggregate weight, and overall tech sector weight.
    """
    weights = _load_excel_weights()

    result: dict[str, Any] = {
        "etf": "VanEck Morningstar Wide Moat ETF (MOAT)",
        "as_of_date": ETF_AS_OF_DATE,
        "focus": "Technology Sector",
        "sub_sectors": {},
    }

    sectors_to_include = MOAT_TECH_SECTORS
    if sub_sector:
        matched = {k: v for k, v in MOAT_TECH_SECTORS.items()
                   if sub_sector.lower() in k.lower()}
        if matched:
            sectors_to_include = matched

    total_count = 0
    total_weight = 0.0
    has_weights = bool(weights)

    for sector, tickers in sectors_to_include.items():
        sector_weight = 0.0
        holdings_list = []

        for t, n in tickers.items():
            entry: dict[str, Any] = {"ticker": t, "name": n}
            w = weights.get(t)
            if w and w.get("pct_net_assets") is not None:
                pct = w["pct_net_assets"]
                entry["pct_net_assets"] = round(pct, 4)
                sector_weight += pct
                if w.get("holding_name"):
                    entry["name"] = w["holding_name"]
            holdings_list.append(entry)

        sector_data: dict[str, Any] = {
            "count": len(tickers),
            "holdings": holdings_list,
        }
        if has_weights:
            sector_data["sector_weight_pct"] = round(sector_weight, 4)

        result["sub_sectors"][sector] = sector_data
        total_count += len(tickers)
        total_weight += sector_weight

    result["total_tech_holdings"] = total_count
    if has_weights:
        result["total_tech_weight_pct"] = round(total_weight, 4)

    return result


def get_etf_summary() -> str:
    """Return a human-readable summary of MOAT ETF tech sector distribution."""
    weights = _load_excel_weights()
    has_weights = bool(weights)

    lines = [
        f"MOAT ETF Technology Holdings (as of {ETF_AS_OF_DATE})",
        f"Total tech companies: {len(get_all_tech_tickers())}",
    ]

    total_weight = 0.0
    for sector, tickers in MOAT_TECH_SECTORS.items():
        sector_weight = 0.0
        holding_lines = []
        for t, n in tickers.items():
            w = weights.get(t)
            pct = w["pct_net_assets"] if w and w.get("pct_net_assets") is not None else None
            if pct is not None:
                holding_lines.append(f"    - {n} ({t}): {pct:.2f}%")
                sector_weight += pct
            else:
                holding_lines.append(f"    - {n} ({t})")

        header = f"  {sector} ({len(tickers)})"
        if has_weights and sector_weight > 0:
            header += f" -- {sector_weight:.2f}% of ETF"
        lines.append("")
        lines.append(header + ":")
        lines.extend(holding_lines)
        total_weight += sector_weight

    if has_weights and total_weight > 0:
        lines.insert(2, f"Total tech sector weight: {total_weight:.2f}% of ETF net assets")

    lines.append("")
    return "\n".join(lines)
