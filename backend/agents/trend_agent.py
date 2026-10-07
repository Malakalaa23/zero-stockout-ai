"""
Advanced Trend Agent — multi-source real-time trend detection.

Aggregates signals from:
  - Google Trends (search interest)
  - Reddit (community discussion volume)
  - Twitter/X (social media buzz — requires auth)
  - Yahoo Finance (market sentiment)
  - News sentiment (VADER)

Computes a weighted trend score and returns a forecast multiplier.

Author: Malak (System Architect)
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


# ============================================================
# TREND AGENT
# ============================================================

class TrendAgent:
    """Multi-source trend detection for inventory forecasting."""

    # Source weights (sum to 1.0)
    WEIGHTS = {
        "google_trends": 0.40,
        "reddit": 0.20,
        "twitter": 0.10,
        "finance": 0.10,
        "news_sentiment": 0.20,
    }

    # Cache TTL in seconds (10 minutes)
    CACHE_TTL = 600

    def __init__(
        self,
        enabled: bool = True,
        reddit_client_id: Optional[str] = None,
        reddit_client_secret: Optional[str] = None,
        reddit_user_agent: Optional[str] = None,
    ) -> None:
        self.enabled = enabled
        self._cache: dict[str, tuple[dict, float]] = {}

        # Source availability flags
        self._pytrends_available = False
        self._reddit_available = False
        self._reddit_client = None
        self._twitter_available = False
        self._yfinance_available = False
        self._vader_available = False
        self._vader = None

        if not enabled:
            logger.info("Trend Agent disabled")
            return

        self._init_sources(reddit_client_id, reddit_client_secret, reddit_user_agent)

    def _init_sources(
        self,
        reddit_client_id: Optional[str],
        reddit_client_secret: Optional[str],
        reddit_user_agent: Optional[str],
    ) -> None:
        """Initialize all trend data sources."""
        # Google Trends
        try:
            from pytrends.request import TrendReq  # noqa: F401
            self._pytrends_available = True
            logger.info("  ✓ Google Trends ready")
        except ImportError:
            logger.warning("  ✗ pytrends not installed")

        # Reddit
        if reddit_client_id and reddit_client_secret:
            try:
                import praw
                self._reddit_client = praw.Reddit(
                    client_id=reddit_client_id,
                    client_secret=reddit_client_secret,
                    user_agent=reddit_user_agent or "zero-stockout-trend-agent/1.0",
                )
                self._reddit_available = True
                logger.info("  ✓ Reddit ready")
            except Exception as exc:
                logger.warning(f"  ✗ Reddit init failed: {exc}")
        else:
            logger.info("  ✗ Reddit credentials not provided")

        # Twitter
        try:
            from twikit import Client  # noqa: F401
            self._twitter_available = True
            logger.info("  ✓ Twitter/X installed (requires auth at runtime)")
        except ImportError:
            logger.warning("  ✗ twikit not installed")

        # Yahoo Finance
        try:
            import yfinance  # noqa: F401
            self._yfinance_available = True
            logger.info("  ✓ Yahoo Finance ready")
        except ImportError:
            logger.warning("  ✗ yfinance not installed")

        # VADER Sentiment
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self._vader = SentimentIntensityAnalyzer()
            self._vader_available = True
            logger.info("  ✓ VADER sentiment ready")
        except ImportError:
            logger.warning("  ✗ vaderSentiment not installed")

    # ============================================================
    # PUBLIC API
    # ============================================================

    def get_trend_score(self, query: str, product_name: Optional[str] = None) -> dict:
        """Get a multi-source trend score for the given query.

        Args:
            query: SKU ID or search term
            product_name: Optional human-readable product name for better search results

        Returns:
            {
                "trend_score": float (0.0 – 2.0),
                "multiplier": float (0.7 – 1.5),
                "direction": "rising" | "stable" | "declining",
                "confidence": float (0.0 – 1.0),
                "sources": {source_name: {...}},
                "sources_available": int,
                "query_used": str,
            }
        """
        # Cache check
        cache_key = f"{query}|{product_name or ''}"
        cached = self._cache.get(cache_key)
        if cached and (time.time() - cached[1]) < self.CACHE_TTL:
            return cached[0]

        search_term = product_name or query

        # Collect signals from each source
        signals = {}

        if self._pytrends_available:
            signals["google_trends"] = self._google_trends(search_term)

        if self._reddit_available:
            signals["reddit"] = self._reddit_trend(search_term)

        if self._twitter_available:
            signals["twitter"] = self._twitter_trend(search_term)

        if self._yfinance_available:
            signals["finance"] = self._finance_trend(search_term)

        if self._vader_available:
            signals["news_sentiment"] = self._news_sentiment(search_term)

        # Aggregate
        result = self._aggregate(signals, search_term)

        # Cache
        self._cache[cache_key] = (result, time.time())
        return result

    # ============================================================
    # SOURCE: GOOGLE TRENDS
    # ============================================================

    def _google_trends(self, term: str) -> dict:
        """Fetch 90-day search interest from Google Trends."""
        try:
            from pytrends.request import TrendReq

            pytrends = TrendReq(hl="en-US", tz=0, timeout=(10, 25))
            pytrends.build_payload([term], timeframe="today 3-m")

            df = pytrends.interest_over_time()
            if df is None or df.empty or term not in df.columns:
                return {"ok": False, "reason": "no_data"}

            values = df[term].astype(float).tolist()
            if len(values) < 7:
                return {"ok": False, "reason": "insufficient_samples"}

            recent = float(np.mean(values[-7:]))
            baseline = float(np.mean(values[-37:-7])) if len(values) >= 37 else float(np.mean(values[:-7]))
            if baseline <= 0:
                baseline = 1.0

            ratio = recent / baseline

            # Growth: last 7 days vs first 7 days
            first_week = float(np.mean(values[:7]))
            growth = (recent - first_week) / max(first_week, 1.0)

            return {
                "ok": True,
                "ratio": round(ratio, 3),
                "growth": round(growth, 3),
                "samples": len(values),
                "recent_avg": round(recent, 2),
                "baseline_avg": round(baseline, 2),
            }
        except Exception as exc:
            logger.warning(f"Google Trends failed: {exc}")
            return {"ok": False, "reason": str(exc)}

    # ============================================================
    # SOURCE: REDDIT
    # ============================================================

    def _reddit_trend(self, term: str) -> dict:
        """Measure discussion volume on Reddit over the last 30 days."""
        try:
            if self._reddit_client is None:
                return {"ok": False, "reason": "not_configured"}

            # Search across all of Reddit
            results = list(self._reddit_client.subreddit("all").search(
                term, limit=50, time_filter="month", sort="relevance"
            ))
            if not results:
                return {"ok": False, "reason": "no_results"}

            # Count posts per week (rough proxy for trend direction)
            now = datetime.utcnow()
            this_week = 0
            prev_week = 0
            for post in results:
                age_days = (now - datetime.utcfromtimestamp(post.created_utc)).days
                if age_days <= 7:
                    this_week += 1
                elif age_days <= 14:
                    prev_week += 1

            if prev_week == 0:
                ratio = 1.5 if this_week > 0 else 1.0
            else:
                ratio = this_week / prev_week

            return {
                "ok": True,
                "ratio": round(min(ratio, 3.0), 3),
                "this_week": this_week,
                "prev_week": prev_week,
                "total_posts": len(results),
            }
        except Exception as exc:
            logger.warning(f"Reddit failed: {exc}")
            return {"ok": False, "reason": str(exc)}

    # ============================================================
    # SOURCE: TWITTER / X (requires authentication)
    # ============================================================

    def _twitter_trend(self, term: str) -> dict:
        """Twitter/X search — requires authentication. Skipped if not logged in."""
        # twikit requires an authenticated session. Without stored cookies or
        # credentials, we can't search. Return graceful "requires_authentication"
        # so the aggregator skips this source.
        return {"ok": False, "reason": "requires_authentication"}

    # ============================================================
    # SOURCE: YAHOO FINANCE (market sentiment)
    # ============================================================

    def _finance_trend(self, term: str) -> dict:
        """Check if there's a publicly traded company closely matching the term."""
        try:
            import yfinance as yf

            # Try common ticker patterns — only short, uppercase, alpha symbols
            cleaned = "".join(c for c in term if c.isalpha()).upper()
            if len(cleaned) < 2 or len(cleaned) > 5:
                return {"ok": False, "reason": "no_ticker_match"}

            tickers = [cleaned]
            for ticker in tickers:
                try:
                    t = yf.Ticker(ticker)
                    hist = t.history(period="1mo")
                    if hist.empty or len(hist) < 10:
                        continue

                    prices = hist["Close"].tolist()
                    recent = float(np.mean(prices[-5:]))
                    baseline = float(np.mean(prices[:-5]))
                    if baseline <= 0:
                        continue

                    ratio = recent / baseline
                    return {
                        "ok": True,
                        "ticker": ticker,
                        "ratio": round(ratio, 3),
                        "recent_price": round(recent, 2),
                        "baseline_price": round(baseline, 2),
                    }
                except Exception:
                    continue

            return {"ok": False, "reason": "no_ticker_match"}
        except Exception as exc:
            logger.warning(f"Yahoo Finance failed: {exc}")
            return {"ok": False, "reason": str(exc)}

    # ============================================================
    # SOURCE: NEWS SENTIMENT (VADER)
    # ============================================================

    def _news_sentiment(self, term: str) -> dict:
        """Fetch recent news headlines and score sentiment with VADER."""
        try:
            import re
            import requests

            # Google News RSS is free, no auth, real-time
            url = f"https://news.google.com/rss/search?q={term}&hl=en-US&gl=US&ceid=US:en"
            headers = {"User-Agent": "Mozilla/5.0 (compatible; ZeroStockout/1.0)"}
            resp = requests.get(url, timeout=10, headers=headers)
            if resp.status_code != 200:
                return {"ok": False, "reason": f"HTTP {resp.status_code}"}

            # Extract titles from <item> blocks
            item_blocks = re.findall(r"<item>(.*?)</item>", resp.text, re.DOTALL)
            titles = []
            for block in item_blocks:
                title_match = re.search(
                    r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>",
                    block,
                    re.DOTALL,
                )
                if title_match:
                    title = title_match.group(1).strip()
                    if title and title.lower() != term.lower():
                        titles.append(title)
            titles = titles[:20]

            # Fallback: direct title extraction if item blocks failed
            if not titles:
                raw_titles = re.findall(
                    r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>",
                    resp.text,
                    re.DOTALL,
                )
                titles = [
                    t.strip() for t in raw_titles
                    if t and t.strip().lower() != term.lower()
                ][:20]

            if not titles:
                return {"ok": False, "reason": "no_headlines"}

            # Score each headline
            scores = [self._vader.polarity_scores(t)["compound"] for t in titles]
            avg_sentiment = float(np.mean(scores))

            # Map sentiment to a ratio-like signal
            # -1.0 -> 0.7 (declining), 0.0 -> 1.0 (stable), +1.0 -> 1.3 (rising)
            ratio = 1.0 + (avg_sentiment * 0.3)

            return {
                "ok": True,
                "ratio": round(max(0.7, min(ratio, 1.3)), 3),
                "sentiment": round(avg_sentiment, 3),
                "headlines": len(titles),
                "top_headline": titles[0][:100],
            }
        except Exception as exc:
            logger.warning(f"News sentiment failed: {exc}")
            return {"ok": False, "reason": str(exc)}

    # ============================================================
    # AGGREGATION
    # ============================================================

    def _aggregate(self, signals: dict, search_term: str) -> dict:
        """Weight and combine all source signals into a single trend score."""
        weighted_ratios = []
        weights_used = []
        sources_report = {}

        for source, weight in self.WEIGHTS.items():
            sig = signals.get(source)
            if sig and sig.get("ok"):
                ratio = float(sig.get("ratio", 1.0))
                weighted_ratios.append(ratio * weight)
                weights_used.append(weight)
                sources_report[source] = sig
            else:
                sources_report[source] = sig or {"ok": False, "reason": "not_run"}

        # No sources available → neutral
        if not weighted_ratios:
            return self._neutral_result(search_term, sources_report)

        # Weighted average (renormalize if some sources failed)
        total_weight = sum(weights_used)
        combined_ratio = sum(weighted_ratios) / total_weight

        # If only one source contributed, dampen the multiplier toward 1.0
        # (single-source trends are less reliable than multi-source confirmation)
        if len(weights_used) == 1:
            combined_ratio = 1.0 + (combined_ratio - 1.0) * 0.5

        # Clamp to [0.7, 1.5] for the multiplier
        multiplier = float(np.clip(combined_ratio, 0.7, 1.5))

        # Trend score normalized to [0, 2]
        trend_score = float(np.clip(combined_ratio, 0.0, 2.0))

        # Direction
        if combined_ratio >= 1.15:
            direction = "rising"
        elif combined_ratio <= 0.85:
            direction = "declining"
        else:
            direction = "stable"

        # Confidence = coverage across sources
        confidence = round(len(weights_used) / len(self.WEIGHTS), 2)

        logger.info(
            f"Trend '{search_term}': ratio={combined_ratio:.2f} "
            f"direction={direction} multiplier={multiplier:.2f} "
            f"confidence={confidence} sources={len(weights_used)}"
        )

        return {
            "trend_score": round(trend_score, 3),
            "multiplier": round(multiplier, 3),
            "direction": direction,
            "confidence": confidence,
            "sources": sources_report,
            "sources_available": len(weights_used),
            "query_used": search_term,
            "fetched_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def _neutral_result(search_term: str, sources_report: dict) -> dict:
        """Neutral fallback when no source returns data."""
        return {
            "trend_score": 1.0,
            "multiplier": 1.0,
            "direction": "stable",
            "confidence": 0.0,
            "sources": sources_report,
            "sources_available": 0,
            "query_used": search_term,
            "fetched_at": datetime.utcnow().isoformat(),
        }