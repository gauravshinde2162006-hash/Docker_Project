import os
import random
import time
from fastapi import FastAPI, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="Demo Microservice")

# Prometheus Metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"]
)

# Configuration from Environment Variables
# In a real scenario, this might be a bug introduced in a new version.
# For the hackathon, we use an env var to toggle the "bad release" behavior.
SIMULATE_FAILURE = os.getenv("SIMULATE_FAILURE", "false").lower() == "true"
VERSION = os.getenv("APP_VERSION", "v1.0.0")

@app.middleware("http")
async def monitor_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # Don't record metrics for the metrics endpoint itself
    if request.url.path != "/metrics":
        REQUEST_COUNT.labels(
            method=request.method, 
            endpoint=request.url.path, 
            status=response.status_code
        ).inc()
        REQUEST_LATENCY.labels(
            method=request.method, 
            endpoint=request.url.path
        ).observe(duration)
        
    return response

@app.get("/")
def read_root():
    if SIMULATE_FAILURE:
        # Simulate a bug: 20% of requests fail, and there's a latency spike
        if random.random() < 0.20:
            return Response(content="Internal Server Error (Simulated Bug)", status_code=500)
        time.sleep(random.uniform(0.1, 0.5)) # Simulate high latency
    
    return {"message": "Hello World", "version": VERSION, "status": "ok"}

@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/healthz")
def health():
    return {"status": "healthy"}
