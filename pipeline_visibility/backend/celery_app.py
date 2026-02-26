from celery import Celery

from .config import settings

celery_app = Celery("pipeline_visibility", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(task_serializer="json", result_serializer="json", timezone="UTC")


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def run_connector_sync(self, org_id: str, source: str) -> dict[str, str]:
    return {"org_id": org_id, "source": source, "status": "queued"}
