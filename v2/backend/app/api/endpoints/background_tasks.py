from fastapi import APIRouter
from app.services.background_task_status_service import BackgroundTaskStatusService

router = APIRouter()

status_service = BackgroundTaskStatusService()

@router.get("/background-tasks/status", tags=["background-tasks"])
def get_background_tasks_status():
    return [task.dict() for task in status_service.get_all_statuses()]
