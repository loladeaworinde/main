from __future__ import annotations
import asyncio
import time
from loguru import logger

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False


POSITIVE_WORDS = {"buy", "bull", "bullish", "moon", "rocket", "calls", "long", "breakout", "upside", "strong", "beat", "rally"}
NEGATIVE_WORDS = {"sell", "bear", "bearish", "crash", "dump", "short", "puts", "downside", "weak", "miss", "correction", "collapse"}


class SentimentAggregator:

    def __init__(self, news_provider, anthropic_api_key: str = "", reddit_client_id: str = "", reddit_client_secret: str = "", reddit_user_agent: str = "TradingBot/1.0"):
        self.news_provider = news_provider
        self.anthropic_api_key = anthropic_api_key
        self.reddit_client_id = reddit_client_id
        self.reddit_client_secret = reddit_client_secret
        self.reddit_user_agent = reddit_user_agent
        self._cache: dict[str, tuple[dict, float]] = {}

    async def analyze_symbol(self, symbol: str) -> dict:
        cache_key = symbol.upper()
        if cache_key in self._cache:
            result, ts = self._cache[cache_key]
            if time.time() - ts < 1800:
                return result

        news_score, reddit_score, ai_score = await asyncio.gather(
            self._get_news_sentiment(symbol),
            self._get_reddit_sentiment(symbol),
            self._get_ai_sentiment(symbol),
            return_exceptions=True,
        )
        news_score = float(news_score) if isinstance(news_score, (int, float)) else 0.0
        reddit_score = float(reddit_score) if isinstance(reddit_score, (int, float)) else 0.0
        ai_score = float(ai_score) if isinstance(ai_score, (int, float)) else 0.0

        score, confidence = self._aggregate_scores(news_score, reddit_score, ai_score)
        block_trade, reduce_size = self._determine_action(score, confidence)

        if score > 0.3:
            signal = "bullish"
        elif score < -0.3:
            signal = "bearish"
        else:
            signal = "neutral"

        result = {
            "score": round(score, 3),
            "confidence": round(confidence, 3),
            "breakdown": {"news": round(news_score, 3), "reddit": round(reddit_score, 3), "ai": round(ai_score, 3)},
            "signal": signal,
            "block_trade": block_trade,
            "reduce_size": reduce_size,
            "reasoning": f"Composite sentiment: news={news_score:.2f}, reddit={reddit_score:.2f}, ai={ai_score:.2f}. Signal: {signal}.",
        }
        self._cache[cache_key] = (result, time.time())
        return result

    async def _get_news_sentiment(self, symbol: str) -> float:
        try:
            articles = await asyncio.to_thread(self.news_provider.get_news_articles, [symbol], 24)
            if not articles:
                return 0.0
            headlines = [a.get("title", "") + " " + a.get("description", "") for a in articles[:10]]
            if self.anthropic_api_key and ANTHROPIC_AVAILABLE:
                return await self._score_with_claude(headlines, symbol)
            return self._simple_word_score(headlines)
        except Exception as e:
            logger.warning(f"News sentiment error for {symbol}: {e}")
            return 0.0

    async def _get_reddit_sentiment(self, symbol: str) -> float:
        if not PRAW_AVAILABLE or not self.reddit_client_id:
            return 0.0
        try:
            reddit = praw.Reddit(
                client_id=self.reddit_client_id,
                client_secret=self.reddit_client_secret,
                user_agent=self.reddit_user_agent,
            )
            texts = []
            for sub in ["stocks", "wallstreetbets", "investing"]:
                results = await asyncio.to_thread(
                    lambda: list(reddit.subreddit(sub).search(symbol, time_filter="day", limit=15))
                )
                for post in results:
                    texts.append(post.title + " " + (post.selftext[:200] if post.selftext else ""))
            if not texts:
                return 0.0
            return self._simple_word_score(texts)
        except Exception as e:
            logger.warning(f"Reddit sentiment error for {symbol}: {e}")
            return 0.0

    async def _get_ai_sentiment(self, symbol: str) -> float:
        if not self.anthropic_api_key or not ANTHROPIC_AVAILABLE:
            return 0.0
        try:
            articles = await asyncio.to_thread(self.news_provider.get_news_articles, [symbol], 48)
            headlines = [a.get("title", "") for a in articles[:8] if a.get("title")]
            if not headlines:
                return 0.0
            return await self._score_with_claude(headlines, symbol)
        except Exception as e:
            logger.warning(f"AI sentiment error for {symbol}: {e}")
            return 0.0

    async def _score_with_claude(self, headlines: list[str], symbol: str) -> float:
        client = anthropic.AsyncAnthropic(api_key=self.anthropic_api_key)
        prompt = f"""Analyze the sentiment of these headlines about {symbol} and return a JSON object with a single key "score" (float from -1.0 to 1.0, where -1 is very bearish and 1 is very bullish):

Headlines:
{chr(10).join(f"- {h}" for h in headlines)}

Respond with only valid JSON: {{"score": <float>}}"""
        message = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=64,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
        text = message.content[0].text.strip()
        data = json.loads(text)
        return float(max(-1.0, min(1.0, data.get("score", 0.0))))

    @staticmethod
    def _simple_word_score(texts: list[str]) -> float:
        if not texts:
            return 0.0
        pos = sum(1 for text in texts for word in POSITIVE_WORDS if word in text.lower())
        neg = sum(1 for text in texts for word in NEGATIVE_WORDS if word in text.lower())
        total = pos + neg
        if total == 0:
            return 0.0
        return round((pos - neg) / total, 3)

    @staticmethod
    def _aggregate_scores(news: float, reddit: float, ai: float) -> tuple[float, float]:
        score = news * 0.4 + reddit * 0.2 + ai * 0.4
        non_zero = sum(1 for s in [news, reddit, ai] if s != 0.0)
        confidence = min(0.9, 0.3 * non_zero + 0.1 * min(abs(score) * 2, 1.0))
        return round(score, 3), round(confidence, 3)

    @staticmethod
    def _determine_action(score: float, confidence: float) -> tuple[bool, bool]:
        block_trade = score < -0.7 and confidence > 0.6
        reduce_size = score < -0.4
        return block_trade, reduce_size
