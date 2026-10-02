from celery import shared_task

from .services import run_question


@shared_task(name="adviser_v2.demo_question", ignore_result=True)
def demo_question(question_id: str):
    run_question(question_id)
