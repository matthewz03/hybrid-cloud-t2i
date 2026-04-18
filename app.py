import streamlit as st
import requests
import time

# Point this to your local FastAPI server
API_URL = "http://127.0.0.1:8000"

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Async T2I Engine", layout="wide")
st.title("🎨 Distributed Stable Diffusion Engine")
st.markdown("Powered by FastAPI, Celery, Redis, PyTorch, and AWS S3.")

# --- SIDEBAR: HYPERPARAMETERS ---
with st.sidebar:
    st.header("Engine Settings")
    steps = st.slider("Inference Steps", min_value=10, max_value=100, value=50, step=5)
    cfg = st.slider("CFG Scale", min_value=1.0, max_value=15.0, value=7.0, step=0.5)
    seed = st.number_input("Seed", value=42, step=1)
    negative_prompt = st.text_area("Negative Prompt", value="blurry, ugly, bad anatomy, low quality")

# --- MAIN WORKSPACE ---
prompt = st.text_input("Enter your prompt:", "A cyberpunk street market at night, neon signs, highly detailed")

# The Generate Button
if st.button("Generate Image", type="primary"):
    
    # 1. Send the POST request to FastAPI
    with st.spinner("Submitting job to the Redis queue..."):
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "num_inference_steps": steps,
            "cfg_scale": cfg,
            "seed": seed
        }
        
        try:
            response = requests.post(f"{API_URL}/generate", json=payload)
            response.raise_for_status() # Throw an error if the API crashes
            job_id = response.json().get("job_id")
            st.success(f"Job queued successfully! Ticket ID: `{job_id}`")
        except Exception as e:
            st.error(f"Failed to connect to the backend API: {e}")
            st.stop() # Halt execution if the server is unreachable

    # 2. The Asynchronous Polling Loop
    status_container = st.empty()
    progress_bar = st.progress(0)
    
    while True:
        try:
            res = requests.get(f"{API_URL}/status/{job_id}").json()
            status = res.get("status")
            
            if status == "PENDING":
                status_container.info("Status: Waiting in queue or initializing GPU...")
                progress_bar.progress(10)
                
            elif status == "STARTED" or status == "PROCESSING":
                status_container.warning("Status: GPU is currently rendering the image...")
                progress_bar.progress(50)
                
            elif status == "SUCCESS":
                status_container.success("Status: Generation Complete! Fetching secure link from AWS S3...")
                progress_bar.progress(100)
                
                # Render the image using the AWS Presigned URL
                s3_url = res.get("result")
                st.image(s3_url, caption=f"Prompt: {prompt}", use_container_width=True)
                break # Exit the loop, the job is done!
                
            elif status == "FAILURE":
                status_container.error("Job failed on the Celery worker node. Check your cluster terminal logs.")
                progress_bar.empty()
                break
                
            # Sleep for 2 seconds before asking again so we don't spam FastAPI
            time.sleep(2) 
            
        except Exception as e:
            status_container.error("Lost connection to the polling server.")
            break