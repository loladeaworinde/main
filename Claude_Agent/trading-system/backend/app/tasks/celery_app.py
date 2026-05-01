from __future__ import annotations

from celery import Celery
from loguru import logger

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "trading_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/New_York",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,
    beat_schedule={
        # TODO: Uncomment tasks once task modules are implemented
        # "fetch-market-data": {
        #     "task": "app.tasks.market_data.fetch_market_data",
        #     "schedule": 60.0,
        # },
        # "run-strategies": {
        #     "task": "app.tasks.strategies.run_all_strategies",
        #     "schedule": 300.0,
        # },
        # "update-sentiment": {
        #     "task": "app.tasks.sentiment.update_sentiment_scores",
        #     "schedule": 1800.0,
        # },
    },
)

logger.info("Celery app '{}' initialised with broker: {}", celery_app.main, settings.REDIS_URL)
