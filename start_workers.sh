#!/bin/bash

# 1. Clear any old logs
echo "Cleaning up old logs..."
rm -f worker_gpu0.log worker_gpu1.log

# 2. Start Worker on GPU 0
echo "Starting Celery Worker on GPU 0..."
CUDA_VISIBLE_DEVICES=0 PYTHONPATH=. \
celery -A worker worker --loglevel=info --pool=solo -n worker0@%h > worker_gpu0.log 2>&1 &

# 3. Start Worker on GPU 1
echo "Starting Celery Worker on GPU 1..."
CUDA_VISIBLE_DEVICES=1 PYTHONPATH=. \
celery -A worker worker --loglevel=info --pool=solo -n worker1@%h > worker_gpu1.log 2>&1 &

echo "--------------------------------------------------"
echo "Both workers are launching in the background!"
echo "Check logs with: tail -f worker_gpu0.log"
echo "Check logs with: tail -f worker_gpu1.log"
echo "--------------------------------------------------"