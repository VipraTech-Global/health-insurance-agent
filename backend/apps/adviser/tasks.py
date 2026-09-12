from celery import shared_task
from django.core.cache import cache

from .services import reconcile_expired_attempts


@shared_task(ignore_result=True)  # type: ignore[misc]
def reconcile_abandoned_turns() -> int:
    reconciled = reconcile_expired_attempts()
    cache.set("adviser:turn-reconciler-health", "ok", timeout=90)
    return reconciled
