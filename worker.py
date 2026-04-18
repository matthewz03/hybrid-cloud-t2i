from celery import Celery, signals
from ImageGenerator import ImageGenerator
import boto3
import io
import os
from botocore.exceptions import ClientError
from botocore.client import Config
from dotenv import load_dotenv
load_dotenv() 

# 1. Grab the region from the environment
aws_region = os.environ.get('AWS_DEFAULT_REGION')
regional_endpoint = f"https://s3.{aws_region}.amazonaws.com"

s3_client = boto3.client(
    's3',
    region_name=aws_region,
    endpoint_url=regional_endpoint,
    config=Config(signature_version='s3v4')
)
app = Celery(
    'tasks', 
    broker='redis://18.188.188.54:6379/0', 
    backend='redis://18.188.188.54:6379/0'
)

# Create an empty global variable to hold our model
model = None 

# 2. The PyTorch Fix: Initialize the model INSIDE this signal
@signals.worker_process_init.connect
def setup_model(**kwargs):
    global model
    print("Worker cloned safely. Initializing PyTorch model...")
    # ---> INITIALIZE YOUR MODEL HERE <---
    model = ImageGenerator()

# 3. The Task Logic
@app.task(bind=True) # bind=True gives us access to 'self' (the task instance)
def generate_image(
        self, 
        prompt: str, 
        negative_prompt: str = '', 
        num_inference_steps: int = 50, 
        cfg_scale: float = 7.0, 
        seed: int = 42):
    
    # Grab the unique Job ID that Celery automatically created for this ticket
    job_id = self.request.id
    image = model.generate(
        prompt=prompt,
        negative_prompt=negative_prompt,
        steps=num_inference_steps,
        cfg_scale=cfg_scale,
        seed=seed
        )
    
    # Saving to IO buffer
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    save_path = f"outputs/{job_id}.png"
    try:
        s3_client.upload_fileobj(
            Fileobj=buffer,
            Bucket=os.environ.get('S3_BUCKET_NAME'),
            Key=save_path,
            ExtraArgs={'ContentType': 'image/png'}
        )
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': os.environ.get('S3_BUCKET_NAME'), 'Key': save_path},
        )
    except ClientError as e:
        print(f'AWS ClientError - {e}')
        raise
    except Exception as e:
        print(f"Unexpected Error during image generation: {type(e).__name__} - {e}")
        raise

    return presigned_url