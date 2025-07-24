from celery import Celery
from app.config import settings
from app.core.task_manager import TaskManager

celery = Celery(
    __name__,
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

@celery.task(bind=True)
def run_analysis_task(self, user_id: str, params: dict):
    """Celery task to run CrewAI analysis"""
    task_id = self.request.id
    
    manager = TaskManager(task_id, user_id, params)
    return manager.run_crew()