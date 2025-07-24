from celery.result import AsyncResult
from fastapi import APIRouter
from app.schemas.analysis import AnalysisRequest, AnalysisResponse, TaskStatusResponse
from app.tasks.analysis import run_analysis_task
from app.tasks.analysis import celery
import uuid

router = APIRouter()

@router.post("/start", response_model=AnalysisResponse)
async def start_analysis(request: AnalysisRequest):
    try:
        task_id = str(uuid.uuid4())
        run_analysis_task.apply_async(
            args=["anonymous", request.dict()],
            task_id=task_id
        )
        return {"task_id": task_id}
    except Exception as e:
        return {"task_id": None}

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    result = AsyncResult(task_id, app=celery)
    
    response = {
        "task_id": task_id,
        "status": result.status,
        "result": None,
        "error": None
    }

    if result.failed():
        response["error"] = str(result.result)
    elif result.successful():
        response["result"] = result.result

    return response