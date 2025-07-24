from pydantic import BaseModel
from typing import Optional

class AnalysisRequest(BaseModel):
    country: str
    city: str
    job_role: str
    include_skills: bool = True
    include_salaries: bool = True
    include_companies: bool = True
    include_trends: bool = True

class AnalysisResponse(BaseModel):
    task_id: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None