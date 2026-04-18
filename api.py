from fastapi import FastAPI
from pydantic import BaseModel
from celery.result import AsyncResult
from celery import Celery

class PromptRequest(BaseModel):
    prompt: str
    negative_prompt: str = ''
    num_inference_steps: int = 50
    cfg_scale: float = 7.0
    seed: int = 42

app = FastAPI()
celery_app = Celery(
    'web_client',
    broker='redis://localhost:6379/0', 
    backend='redis://localhost:6379/0'
)

@app.post('/generate')
def generate(request: PromptRequest):
    task = celery_app.send_task(
        'worker.generate_image',
        kwargs={
            'prompt': request.prompt,
            'negative_prompt': request.negative_prompt,
            'num_inference_steps': request.num_inference_steps,
            'cfg_scale': request.cfg_scale,
            'seed': request.seed
        }
    )
    result = {
        "job_id": task.id
    }
    return result

@app.get('/status/{job_id}')
def status(job_id: str):
    result = AsyncResult(job_id, app=celery_app)
    if result.status == 'SUCCESS':
        return {"status": result.status, "result": result.result}
    else:
        return {"status": result.status}