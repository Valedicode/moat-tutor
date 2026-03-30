"""
Data-Driven Moat Scorer

Calculates moat scores for companies using real historical data:
- Stock price data (yfinance): returns, volatility, drawdowns, trends
- News data (FNSPID): volume, sentiment indicators

This provides quantitative, data-backed moat scores instead of mock values.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from services.stock_data import StockDataService
from services.fnspid_retrieval import (
    is_fnspid_data_available,
    get_passage_count,
    get_date_range,
)
from services.roic_calculator import (
    check_roic_hurdle,
    extract_annual_financials,
    calculate_roic_time_series,
    DEFAULT_WACC,
)
from services.fundamentals_provider import get_fundamental_data

logger = logging.getLogger(__name__)

# Analysis period for moat scores (fixed)
MOAT_START_DATE = "2015-01-01"
MOAT_END_DATE = "2025-12-31"


class DataDrivenMoatScorer:
    """
    Calculate moat scores using real historical data.
    
    Scoring methodology:
    - Each factor scored 0-5 based on quantitative metrics
    - Base score of 2.5 (neutral) with bonuses/penalties
    - Uses 10-year historical data (2015-2025) for consistency
    """
    
    def __init__(self):
        self.stock_service = StockDataService()
    
    def calculate_moat_score(
        self,
        ticker: str,
        start_date: str = MOAT_START_DATE,
        end_date: str = MOAT_END_DATE
    ) -> dict:
        """
        Calculate comprehensive moat score for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Analysis start date (default: 2015-01-01)
            end_date: Analysis end date (default: 2025-12-31)
            
        Returns:
            Dict with overall_score, rating, confidence, factors, trend, summary
        """
        ticker = ticker.upper()
        logger.info(f"Calculating moat score for {ticker} ({start_date} to {end_date})")
        
        try:
            # Load price data
            df = self.stock_service.load_ticker_data(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date
            )
            
            if df.empty or len(df) < 30:
                logger.warning(f"Insufficient price data for {ticker}, using default score")
                return self._get_default_score(ticker)
            
            # Calculate price metrics
            price_metrics = self._calculate_price_metrics(df)
            
            # Check for news data
            has_news = is_fnspid_data_available(ticker)
            news_metrics = self._calculate_news_metrics(ticker) if has_news else {}
            
            # Try to get ROIC data
            roic_data = self._get_roic_data(ticker)
            has_roic = roic_data is not None
            
            # Calculate moat factors
            factors = {
                "network_effects": self._score_network_effects(price_metrics, news_metrics),
                "switching_costs": self._score_switching_costs(price_metrics, news_metrics),
                "intangible_assets": self._score_intangible_assets(price_metrics, news_metrics, roic_data),
                "cost_advantages": self._score_cost_advantages(price_metrics, news_metrics, roic_data),
                "efficient_scale": self._score_efficient_scale(price_metrics, news_metrics),
            }
            
            # Add financial performance factor if ROIC available
            if has_roic:
                factors["financial_performance"] = self._score_financial_performance(roic_data)
            
            # Calculate overall score and rating
            overall_score = np.mean(list(factors.values()))
            rating = self._determine_rating(overall_score, factors)
            confidence = self._determine_confidence(price_metrics, has_news, has_roic)
            trend = self._determine_trend(price_metrics, roic_data)
            summary = self._generate_summary(ticker, overall_score, rating, factors, trend, roic_data)
            
            return {
                "overall_score": round(overall_score, 2),
                "rating": rating,
                "confidence": confidence,
                "factors": factors,
                "trend": trend,
                "summary": summary,
                "time_range": f"{start_date} to {end_date}",
                "computed_at": datetime.utcnow().isoformat(),
                "from_cache": False,
            }
            
        except Exception as e:
            logger.error(f"Error calculating moat score for {ticker}: {e}")
            return self._get_default_score(ticker)
    
    def _calculate_price_metrics(self, df: pd.DataFrame) -> dict:
        """Calculate key price metrics for moat analysis."""
        metrics = {}
        
        # Returns
        df['returns'] = df['close'].pct_change()
        metrics['total_return'] = (df['close'].iloc[-1] / df['close'].iloc[0]) - 1
        metrics['cagr'] = ((df['close'].iloc[-1] / df['close'].iloc[0]) ** (252 / len(df)) - 1) * 100
        metrics['annual_return'] = df['returns'].mean() * 252 * 100
        
        # Volatility
        metrics['volatility'] = df['returns'].std() * np.sqrt(252) * 100
        metrics['downside_volatility'] = df['returns'][df['returns'] < 0].std() * np.sqrt(252) * 100
        
        # Risk metrics
        metrics['max_drawdown'] = self._calculate_max_drawdown(df['close'])
        metrics['sharpe_ratio'] = (metrics['annual_return'] - 2.0) / metrics['volatility'] if metrics['volatility'] > 0 else 0
        
        # Stability metrics
        monthly_returns = df['returns'].resample('ME').sum()
        metrics['positive_months_pct'] = (monthly_returns > 0).sum() / len(monthly_returns) * 100 if len(monthly_returns) > 0 else 50
        metrics['return_consistency'] = 1 / (1 + df['returns'].std()) if df['returns'].std() > 0 else 0.5
        
        # Recent trend (last 2 years)
        if len(df) >= 504:  # ~2 years of data
            recent_df = df.iloc[-504:]
            metrics['recent_return'] = (recent_df['close'].iloc[-1] / recent_df['close'].iloc[0]) - 1
        else:
            metrics['recent_return'] = metrics['total_return']
        
        return metrics
    
    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate maximum drawdown percentage."""
        cummax = prices.cummax()
        drawdown = (prices - cummax) / cummax
        return abs(drawdown.min()) * 100 if not drawdown.empty else 0
    
    def _calculate_news_metrics(self, ticker: str) -> dict:
        """Calculate news-based metrics for moat analysis."""
        metrics = {}
        
        try:
            # Get passage count (proxy for news volume)
            passage_count = get_passage_count(ticker)
            metrics['news_volume'] = passage_count
            
            # Get date range
            min_date, max_date = get_date_range(ticker)
            if min_date and max_date:
                metrics['news_coverage_years'] = (
                    datetime.fromisoformat(max_date).year - 
                    datetime.fromisoformat(min_date).year
                )
            else:
                metrics['news_coverage_years'] = 0
            
            # News volume per year (proxy for market attention)
            if metrics['news_coverage_years'] > 0:
                metrics['news_per_year'] = passage_count / max(metrics['news_coverage_years'], 1)
            else:
                metrics['news_per_year'] = 0
            
        except Exception as e:
            logger.warning(f"Could not calculate news metrics for {ticker}: {e}")
            metrics = {'news_volume': 0, 'news_coverage_years': 0, 'news_per_year': 0}
        
        return metrics
    
    def _get_roic_data(self, ticker: str) -> Optional[dict]:
        """
        Get ROIC data for a ticker.
        
        Returns None if ROIC data unavailable (e.g., fundamental data missing).
        """
        try:
            roic_result = check_roic_hurdle(ticker, years=10, use_cache=True)
            if "error" in roic_result:
                logger.warning(f"ROIC data not available for {ticker}: {roic_result.get('error')}")
                return None
            return roic_result
        except Exception as e:
            logger.warning(f"Could not calculate ROIC for {ticker}: {e}")
            return None
    
    # ========================================================================
    # Factor Scoring Methods
    # ========================================================================
    
    def _score_network_effects(self, price: dict, news: dict) -> float:
        """
        Score network effects based on consistent growth and market attention.
        
        Strong network effects show:
        - Consistent positive returns (more users = more value)
        - Growing news coverage (network expansion)
        - Above-average Sharpe ratio (quality growth)
        """
        score = 2.5  # Base neutral score
        
        # Bonus for strong consistent returns
        if price.get('annual_return', 0) > 15:
            score += 0.8
        elif price.get('annual_return', 0) > 8:
            score += 0.4
        
        # Bonus for high positive month ratio (consistent growth)
        if price.get('positive_months_pct', 50) > 60:
            score += 0.6
        elif price.get('positive_months_pct', 50) > 55:
            score += 0.3
        
        # Bonus for quality growth (high Sharpe)
        if price.get('sharpe_ratio', 0) > 1.5:
            score += 0.6
        elif price.get('sharpe_ratio', 0) > 1.0:
            score += 0.3
        
        # Bonus for news volume (market attention)
        news_per_year = news.get('news_per_year', 0)
        if news_per_year > 2000:
            score += 0.5
        elif news_per_year > 1000:
            score += 0.3
        
        return min(5.0, max(1.0, round(score, 1)))
    
    def _score_switching_costs(self, price: dict, news: dict) -> float:
        """
        Score switching costs based on revenue stability and low churn indicators.
        
        High switching costs show:
        - Low drawdowns (customers don't leave during tough times)
        - Low downside volatility (stable revenue base)
        - Consistent returns (predictable business)
        """
        score = 2.5
        
        # Bonus for shallow drawdowns (customer stickiness)
        max_dd = price.get('max_drawdown', 50)
        if max_dd < 20:
            score += 1.0
        elif max_dd < 30:
            score += 0.6
        elif max_dd < 40:
            score += 0.3
        
        # Bonus for low downside volatility
        downside_vol = price.get('downside_volatility', 50)
        if downside_vol < 20:
            score += 0.8
        elif downside_vol < 30:
            score += 0.4
        
        # Bonus for return consistency
        if price.get('return_consistency', 0) > 0.6:
            score += 0.7
        elif price.get('return_consistency', 0) > 0.5:
            score += 0.4
        
        return min(5.0, max(1.0, round(score, 1)))
    
    def _score_intangible_assets(self, price: dict, news: dict, roic: Optional[dict] = None) -> float:
        """
        Score intangible assets (brand, patents, IP) based on premium valuation.
        
        Strong intangibles show:
        - High long-term CAGR (premium pricing power)
        - Lower volatility (trust and brand loyalty)
        - Strong total returns (market recognizes value)
        """
        score = 2.5
        
        # Bonus for strong CAGR (pricing power)
        cagr = price.get('cagr', 0)
        if cagr > 20:
            score += 1.2
        elif cagr > 12:
            score += 0.7
        elif cagr > 8:
            score += 0.4
        
        # Bonus for total return (long-term value creation)
        total_return = price.get('total_return', 0)
        if total_return > 2.0:  # >200%
            score += 0.8
        elif total_return > 1.0:  # >100%
            score += 0.4
        
        # Bonus for lower volatility (brand stability)
        vol = price.get('volatility', 50)
        if vol < 25:
            score += 0.5
        elif vol < 35:
            score += 0.3
        
        # ROIC bonus (high ROIC suggests pricing power from brand/IP)
        if roic and roic.get('hurdle_passed'):
            avg_roic_pct = roic.get('avg_roic_pct', 0)
            if avg_roic_pct > 30:
                score += 0.7
            elif avg_roic_pct > 20:
                score += 0.4
        
        return min(5.0, max(1.0, round(score, 1)))
    
    def _score_cost_advantages(self, price: dict, news: dict, roic: Optional[dict] = None) -> float:
        """
        Score cost advantages based on margin proxies and performance.
        
        Cost advantages show:
        - Above-market returns (operating leverage)
        - Strong Sharpe ratio (efficient operations)
        - Positive recent trend (maintaining advantage)
        """
        score = 2.5
        
        # Bonus for strong annual returns (margin expansion)
        annual_return = price.get('annual_return', 0)
        if annual_return > 20:
            score += 1.0
        elif annual_return > 12:
            score += 0.6
        elif annual_return > 8:
            score += 0.3
        
        # Bonus for efficiency (high Sharpe)
        sharpe = price.get('sharpe_ratio', 0)
        if sharpe > 1.5:
            score += 0.8
        elif sharpe > 1.0:
            score += 0.4
        
        # Bonus for maintaining advantage (recent performance)
        recent_return = price.get('recent_return', 0)
        if recent_return > 0.5:  # >50% in 2 years
            score += 0.7
        elif recent_return > 0.2:  # >20%
            score += 0.4
        
        # ROIC bonus (high ROIC indicates cost efficiency)
        if roic and roic.get('hurdle_passed'):
            avg_roic_pct = roic.get('avg_roic_pct', 0)
            if avg_roic_pct > 25:
                score += 0.8
            elif avg_roic_pct > 15:
                score += 0.5
        
        return min(5.0, max(1.0, round(score, 1)))
    
    def _score_efficient_scale(self, price: dict, news: dict) -> float:
        """
        Score efficient scale based on market size constraints and natural oligopoly indicators.
        
        Efficient scale moats show:
        - Low volatility (stable market with limited competitors)
        - Shallow drawdowns (protected from new entrants)
        - Consistent returns (predictable cash flows in constrained market)
        """
        score = 2.5
        
        # Bonus for low overall volatility
        vol = price.get('volatility', 50)
        if vol < 20:
            score += 1.0
        elif vol < 30:
            score += 0.6
        elif vol < 40:
            score += 0.3
        
        # Bonus for shallow drawdowns (protection)
        max_dd = price.get('max_drawdown', 50)
        if max_dd < 25:
            score += 0.8
        elif max_dd < 35:
            score += 0.4
        
        # Bonus for return consistency
        consistency = price.get('return_consistency', 0)
        if consistency > 0.6:
            score += 0.7
        elif consistency > 0.5:
            score += 0.4
        
        return min(5.0, max(1.0, round(score, 1)))
    
    def _score_financial_performance(self, roic: dict) -> float:
        """
        Score based on ROIC > WACC over 10 years (quantitative moat proof).
        
        Strong moat:
        - ROIC > 15% consistently
        - ROIC > WACC for 8+ years (80%+)
        - Stable or improving ROIC trend
        """
        score = 2.5  # Base neutral score
        
        avg_roic_pct = roic.get('avg_roic_pct', 0)
        years_above_hurdle_pct = roic.get('years_above_hurdle_pct', 0)
        roic_trend = roic.get('roic_trend', 'stable')
        
        # Bonus for high average ROIC
        if avg_roic_pct > 30:
            score += 1.5
        elif avg_roic_pct > 20:
            score += 1.0
        elif avg_roic_pct > 15:
            score += 0.6
        elif avg_roic_pct > 10:
            score += 0.3
        
        # Bonus for consistency (years above WACC)
        if years_above_hurdle_pct >= 90:
            score += 1.0
        elif years_above_hurdle_pct >= 70:
            score += 0.6
        elif years_above_hurdle_pct >= 50:
            score += 0.3
        
        # Bonus for strengthening trend
        if roic_trend == "strengthening":
            score += 0.5
        elif roic_trend == "weakening":
            score -= 0.5
        
        return min(5.0, max(1.0, round(score, 1)))
    
    # ========================================================================
    # Rating and Summary Methods
    # ========================================================================
    
    def _determine_rating(self, overall_score: float, factors: dict) -> str:
        """Determine Wide/Narrow/None rating from scores."""
        strong_factors = sum(1 for score in factors.values() if score >= 4.0)
        
        if overall_score >= 4.0 and strong_factors >= 2:
            return "Wide"
        elif overall_score >= 3.5 and strong_factors >= 1:
            return "Wide"
        elif overall_score < 2.5:
            return "None"
        else:
            return "Narrow"
    
    def _determine_confidence(self, price: dict, has_news: bool, has_roic: bool = False) -> str:
        """Determine confidence level based on data availability and quality."""
        data_points = len([v for v in price.values() if v is not None])
        
        # High confidence: full data + news + ROIC
        if data_points >= 10 and has_news and has_roic:
            return "High"
        # Medium-high confidence: good price data + ROIC or news
        elif data_points >= 10 and (has_news or has_roic):
            return "High"
        # Medium confidence: good price data
        elif data_points >= 8:
            return "Medium"
        # Low confidence: limited data
        else:
            return "Low"
    
    def _determine_trend(self, price: dict, roic: Optional[dict] = None) -> str:
        """Determine moat trend from recent performance and ROIC."""
        # If ROIC data available, use it (more reliable for moat trend)
        if roic:
            roic_trend = roic.get('roic_trend', 'stable')
            if roic_trend in ['strengthening', 'weakening', 'stable']:
                return roic_trend
        
        # Fallback to price-based trend
        recent_return = price.get('recent_return', 0)
        total_return = price.get('total_return', 0)
        
        # Compare recent to overall performance
        if len([r for r in [recent_return, total_return] if r is not None]) < 2:
            return "stable"
        
        # Strengthening if recent outperforms historical
        if recent_return > total_return * 0.4:  # Recent is strong relative to total
            return "strengthening"
        # Weakening if recent underperforms
        elif recent_return < total_return * 0.1:
            return "weakening"
        else:
            return "stable"
    
    def _generate_summary(
        self,
        ticker: str,
        overall_score: float,
        rating: str,
        factors: dict,
        trend: str,
        roic: Optional[dict] = None
    ) -> str:
        """Generate human-readable summary of moat analysis."""
        # Find strongest factors
        sorted_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)
        top_factors = [name.replace('_', ' ').title() for name, score in sorted_factors[:2]]
        
        # Build summary
        if rating == "Wide":
            summary = f"{ticker} demonstrates a wide moat "
        elif rating == "Narrow":
            summary = f"{ticker} exhibits a narrow moat "
        else:
            summary = f"{ticker} shows limited moat characteristics "
        
        summary += f"with strengths in {top_factors[0]}"
        if len(top_factors) > 1:
            summary += f" and {top_factors[1]}"
        
        summary += ". "
        
        # Add ROIC context if available
        if roic and roic.get('hurdle_passed'):
            avg_roic = roic.get('avg_roic_pct', 0)
            summary += f"The company has sustained an average ROIC of {avg_roic:.1f}% over {roic.get('years_analyzed', 10)} years, significantly above its cost of capital ({roic.get('wacc_pct', 10):.1f}%), providing quantitative proof of durable competitive advantages. "
        
        # Add trend
        if trend == "strengthening":
            summary += "The competitive position has strengthened in recent years, "
        elif trend == "weakening":
            summary += "The competitive position has faced some erosion recently, "
        else:
            summary += "The competitive position has remained stable, "
        
        # Add score context
        summary += f"supported by comprehensive analysis of market and fundamental data (score: {overall_score:.1f}/5.0)."
        
        return summary
    
    def identify_moat_sources(self, ticker: str, use_cache: bool = True) -> dict:
        """
        Identify structural moat sources using financial metrics and news data.
        
        Replaces the hardcoded moat profiles by analyzing:
        - Gross margin level -> Intangible Assets / Pricing Power
        - Revenue growth consistency -> Network Effects
        - ROIC consistency + low volatility -> Cost Advantages
        - Revenue stability (low volatility) -> Switching Costs
        - Market concentration indicators -> Efficient Scale
        
        Args:
            ticker: Stock ticker symbol
            use_cache: Whether to use cached data
            
        Returns:
            Dict with identified moat sources, strength levels, and evidence
        """
        ticker = ticker.upper()
        logger.info(f"Identifying moat sources for {ticker}")
        
        sources = {}
        
        try:
            # Get financial data
            fundamental_data = get_fundamental_data(ticker, use_cache=use_cache)
            df = extract_annual_financials(fundamental_data)
            
            if df.empty or len(df) < 3:
                return {
                    "ticker": ticker,
                    "sources": {},
                    "primary_moat": "Insufficient data",
                    "summary": f"Insufficient financial history to identify moat sources for {ticker}.",
                }
            
            df = df.sort_values("year", ascending=True)
            
            # Get ROIC data
            roic_data = self._get_roic_data(ticker)
            
            # === 1. Gross Margin Analysis -> Intangible Assets / Pricing Power ===
            revenues = df["revenue"].values
            op_incomes = df["operating_income"].values
            
            if len(revenues) >= 3:
                # Calculate gross margin proxy (operating margin as we don't have COGS)
                op_margins = op_incomes / (revenues + 1e-9)
                avg_op_margin = float(np.mean(op_margins[op_margins > -1]))  # Filter outliers
                
                if avg_op_margin > 0.35:
                    sources["intangible_assets"] = {
                        "strength": "Strong",
                        "evidence": f"High average operating margin ({avg_op_margin*100:.1f}%) indicates pricing power from brand, patents, or proprietary technology.",
                        "metric": f"Avg operating margin: {avg_op_margin*100:.1f}%",
                    }
                elif avg_op_margin > 0.20:
                    sources["intangible_assets"] = {
                        "strength": "Moderate",
                        "evidence": f"Moderate operating margin ({avg_op_margin*100:.1f}%) suggests some pricing power from intangible assets.",
                        "metric": f"Avg operating margin: {avg_op_margin*100:.1f}%",
                    }
                
                # === 2. Revenue Growth Consistency -> Network Effects ===
                if len(revenues) >= 4:
                    rev_growth = np.diff(revenues) / (np.abs(revenues[:-1]) + 1e-9)
                    positive_growth_pct = float((rev_growth > 0).sum() / len(rev_growth)) * 100
                    avg_growth = float(np.mean(rev_growth))
                    
                    if avg_growth > 0.10 and positive_growth_pct > 70:
                        sources["network_effects"] = {
                            "strength": "Strong",
                            "evidence": (
                                f"Consistent revenue growth (avg {avg_growth*100:.1f}%, "
                                f"positive in {positive_growth_pct:.0f}% of years) suggests "
                                f"compounding network effects or platform dynamics."
                            ),
                            "metric": f"Avg revenue growth: {avg_growth*100:.1f}%, positive {positive_growth_pct:.0f}% of years",
                        }
                    elif avg_growth > 0.05 and positive_growth_pct > 60:
                        sources["network_effects"] = {
                            "strength": "Moderate",
                            "evidence": (
                                f"Moderate revenue growth (avg {avg_growth*100:.1f}%) with "
                                f"some consistency suggests potential network effects."
                            ),
                            "metric": f"Avg revenue growth: {avg_growth*100:.1f}%",
                        }
                    
                    # === 3. Revenue Stability -> Switching Costs ===
                    rev_volatility = float(np.std(rev_growth))
                    
                    if rev_volatility < 0.15 and avg_growth > 0:
                        sources["switching_costs"] = {
                            "strength": "Strong",
                            "evidence": (
                                f"Low revenue volatility ({rev_volatility*100:.1f}%) combined with "
                                f"positive growth suggests high customer retention and switching costs."
                            ),
                            "metric": f"Revenue growth volatility: {rev_volatility*100:.1f}%",
                        }
                    elif rev_volatility < 0.25:
                        sources["switching_costs"] = {
                            "strength": "Moderate",
                            "evidence": (
                                f"Moderate revenue stability ({rev_volatility*100:.1f}% volatility) "
                                f"suggests some degree of customer lock-in."
                            ),
                            "metric": f"Revenue growth volatility: {rev_volatility*100:.1f}%",
                        }
            
            # === 4. ROIC-Based Analysis -> Cost Advantages ===
            if roic_data and roic_data.get("hurdle_passed"):
                avg_roic_pct = roic_data.get("avg_roic_pct", 0)
                roic_trend = roic_data.get("roic_trend", "stable")
                
                if avg_roic_pct > 25:
                    sources["cost_advantages"] = {
                        "strength": "Strong",
                        "evidence": (
                            f"Sustained high ROIC ({avg_roic_pct:.1f}%) well above cost of capital "
                            f"indicates structural cost advantages from scale, technology, or unique resources."
                        ),
                        "metric": f"Avg ROIC: {avg_roic_pct:.1f}% vs WACC: {DEFAULT_WACC*100:.0f}%",
                    }
                elif avg_roic_pct > 15:
                    sources["cost_advantages"] = {
                        "strength": "Moderate",
                        "evidence": (
                            f"ROIC ({avg_roic_pct:.1f}%) exceeds cost of capital, "
                            f"suggesting some operational cost advantages."
                        ),
                        "metric": f"Avg ROIC: {avg_roic_pct:.1f}%",
                    }
                
                # === 5. Efficient Scale ===
                # High ROIC + stable trend + low revenue volatility suggests
                # market only supports limited competitors profitably
                if (
                    avg_roic_pct > 20 
                    and roic_trend in ["strengthening", "stable"]
                    and "switching_costs" in sources
                ):
                    sources["efficient_scale"] = {
                        "strength": "Strong" if avg_roic_pct > 30 else "Moderate",
                        "evidence": (
                            f"Combination of high ROIC ({avg_roic_pct:.1f}%), {roic_trend} trend, "
                            f"and revenue stability suggests limited market size supports only a few profitable competitors."
                        ),
                        "metric": f"ROIC: {avg_roic_pct:.1f}%, Trend: {roic_trend}",
                    }
            
            # === 6. Efficient Scale (heuristic fallback) ===
            # Low volatility + consistent returns in capital-intensive industries
            if len(revenues) >= 5:
                rev_growth = np.diff(revenues) / (np.abs(revenues[:-1]) + 1e-9)
                rev_vol = float(np.std(rev_growth))
                if rev_vol < 0.10 and avg_op_margin > 0.15:
                    if "efficient_scale" not in sources:
                        sources["efficient_scale"] = {
                            "strength": "Potential",
                            "evidence": (
                                f"Very stable revenue ({rev_vol*100:.1f}% volatility) with decent margins "
                                f"may indicate efficient scale where limited market size deters new entrants."
                            ),
                            "metric": f"Revenue volatility: {rev_vol*100:.1f}%",
                        }
            
            # Determine primary moat source
            strength_order = {"Strong": 3, "Moderate": 2, "Potential": 1}
            if sources:
                primary = max(sources.items(), key=lambda x: strength_order.get(x[1]["strength"], 0))
                primary_moat = primary[0].replace("_", " ").title()
            else:
                primary_moat = "None identified"
            
            # Build summary
            strong_sources = [k.replace("_", " ").title() for k, v in sources.items() if v["strength"] == "Strong"]
            moderate_sources = [k.replace("_", " ").title() for k, v in sources.items() if v["strength"] == "Moderate"]
            
            summary_parts = []
            if strong_sources:
                summary_parts.append(f"Strong: {', '.join(strong_sources)}")
            if moderate_sources:
                summary_parts.append(f"Moderate: {', '.join(moderate_sources)}")
            
            summary = f"{ticker} moat sources: " + "; ".join(summary_parts) if summary_parts else f"{ticker}: No clear moat sources identified from financial data."
            
            return {
                "ticker": ticker,
                "sources": sources,
                "primary_moat": primary_moat,
                "summary": summary,
                "source_count": len(sources),
                "strong_count": len(strong_sources),
            }
            
        except Exception as e:
            logger.error(f"Error identifying moat sources for {ticker}: {e}")
            return {
                "ticker": ticker,
                "sources": {},
                "primary_moat": "Error",
                "summary": f"Could not analyze moat sources for {ticker}: {str(e)}",
            }
    
    def _get_default_score(self, ticker: str) -> dict:
        """Return default/fallback score when data is insufficient."""
        return {
            "overall_score": 3.0,
            "rating": "Narrow",
            "confidence": "Low",
            "factors": {
                "network_effects": 3.0,
                "switching_costs": 3.0,
                "intangible_assets": 3.0,
                "cost_advantages": 3.0,
                "efficient_scale": 3.0,
            },
            "trend": "stable",
            "summary": f"{ticker} analysis limited by insufficient historical data. Default neutral scores applied pending more comprehensive data coverage.",
            "time_range": f"{MOAT_START_DATE} to {MOAT_END_DATE}",
            "computed_at": datetime.utcnow().isoformat(),
            "from_cache": False,
        }
