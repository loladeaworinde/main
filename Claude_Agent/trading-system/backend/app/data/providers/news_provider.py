import time
from datetime import datetime, timezone, timedelta

import httpx
from loguru import logger

try:
    from app.core.config import settings
except ImportError:
    class _FallbackSettings:
        NEWS_API_KEY: str = ""
    settings = _FallbackSettings()  # type: ignore[assignment]


NEWS_API_BASE_URL = "https://newsapi.org/v2"

# Cache entry format: {"data": list[dict], "fetched_at": float}
_CACHE_TTL_SECONDS = 300  # 5 minutes


class NewsProvider:

    def __init__(self) -> None:
        self._api_key: str = getattr(settings, "NEWS_API_KEY", "")
        if not self._api_key:
            logger.warning("NEWS_API_KEY is not set; news requests will return empty results")

        # symbol → {"data": list[dict], "fetched_at": float}
        self._cache: dict[str, dict] = {}

    def _is_cache_valid(self, cache_key: str) -> bool:
        entry = self._cache.get(cache_key)
        if entry is None:
            return False
        return (time.monotonic() - entry["fetched_at"]) < _CACHE_TTL_SECONDS

    def _get_cached(self, cache_key: str) -> list[dict] | None:
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]["data"]
        return None

    def _set_cache(self, cache_key: str, data: list[dict]) -> None:
        self._cache[cache_key] = {"data": data, "fetched_at": time.monotonic()}

    async def get_news_articles(
        self,
        symbols: list[str],
        hours_back: int = 24,
    ) -> list[dict]:
        if not self._api_key:
            return []

        results: list[dict] = []

        for symbol in symbols:
            cache_key = f"articles:{symbol}:{hours_back}"
            cached = self._get_cached(cache_key)
            if cached is not None:
                logger.debug("News cache hit | symbol={}", symbol)
                results.extend(cached)
                continue

            from_dt = (datetime.now(tz=timezone.utc) - timedelta(hours=hours_back)).strftime("%Y-%m-%dT%H:%M:%SZ")

            params = {
                "q":         symbol,
                "language":  "en",
                "sortBy":    "publishedAt",
                "from":      from_dt,
                "apiKey":    self._api_key,
            }

            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    response = await client.get(f"{NEWS_API_BASE_URL}/everything", params=params)
                    response.raise_for_status()
                    payload = response.json()
            except httpx.HTTPError as exc:
                logger.error("NewsAPI request failed | symbol={} error={}", symbol, exc)
                continue

            articles = self._parse_articles(payload.get("articles", []))
            self._set_cache(cache_key, articles)
            results.extend(articles)

        return results

    async def get_market_news(self, category: str = "general") -> list[dict]:
        if not self._api_key:
            return []

        cache_key = f"market_news:{category}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            logger.debug("Market news cache hit | category={}", category)
            return cached

        # NewsAPI top-headlines maps "general" → business for financial context.
        params = {
            "category": "business",
            "language": "en",
            "apiKey":   self._api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(f"{NEWS_API_BASE_URL}/top-headlines", params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            logger.error("NewsAPI market news request failed | category={} error={}", category, exc)
            return []

        articles = self._parse_articles(payload.get("articles", []))
        self._set_cache(cache_key, articles)
        return articles

    @staticmethod
    def _parse_articles(raw_articles: list[dict]) -> list[dict]:
        parsed: list[dict] = []
        for article in raw_articles:
            parsed.append({
                "title":          article.get("title"),
                "description":    article.get("description"),
                "source":         article.get("source", {}).get("name"),
                "published_at":   article.get("publishedAt"),
                "url":            article.get("url"),
                "sentiment_hint": None,
            })
        return parsed
