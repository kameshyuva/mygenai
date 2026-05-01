from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from arq.jobs import Job

router = APIRouter()

class TaskRequest(BaseModel):
    query: str
    session_id: str

class TaskResponse(BaseModel):
    job_id: str
    status: str

@router.post("/execute", response_model=TaskResponse)
async def execute_agent_task(request: Request, payload: TaskRequest):
    redis = request.app.state.redis
    
    # Enqueue the job. 'run_agent_task' must match the function name registered in the worker.
    job = await redis.enqueue_job(
        'run_agent_task',
        query=payload.query,
        session_id=payload.session_id
    )
    
    if not job:
        raise HTTPException(status_code=500, detail="Failed to enqueue background job.")
        
    return TaskResponse(job_id=job.job_id, status="enqueued")

@router.get("/status/{job_id}")
async def get_task_status(request: Request, job_id: str):
    redis = request.app.state.redis
    job = Job(job_id, redis)
    
    status = await job.status()
    info = await job.info()
    
    response = {"job_id": job_id, "status": status.value}
    
    if status == status.complete:
        response["result"] = await job.result()
        
    return response
