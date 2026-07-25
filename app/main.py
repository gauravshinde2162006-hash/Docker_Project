import os
import random
import time
from fastapi import FastAPI, Response, Request
from fastapi.responses import HTMLResponse
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
SIMULATE_FAILURE = os.getenv("SIMULATE_FAILURE", "false").lower() == "true"
VERSION = os.getenv("APP_VERSION", "v1.0.0 (Stable)")
COLOR_THEME = os.getenv("COLOR_THEME", "#00f0ff") # Neon blue for stable, orange/red for canary

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cloud Native Hackathon - Demo Service</title>
    <style>
        :root {{
            --primary: {color_theme};
            --bg: #0d1117;
            --card: #161b22;
            --text: #c9d1d9;
        }}
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}
        .card {{
            background-color: var(--card);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 40px;
            width: 90%;
            max-width: 500px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        .card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--primary);
            box-shadow: 0 0 15px var(--primary);
        }}
        .badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--primary);
            color: var(--primary);
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        h1 {{
            font-size: 1.8em;
            margin: 10px 0;
            color: #ffffff;
        }}
        .status {{
            font-size: 1.2em;
            margin: 20px 0;
            padding: 15px;
            border-radius: 8px;
            background: {status_bg};
            color: {status_color};
            border: 1px solid {status_border};
            font-weight: bold;
        }}
        .details {{
            font-size: 0.9em;
            color: #8b949e;
            margin-top: 30px;
            border-top: 1px solid rgba(255,255,255,0.05);
            padding-top: 20px;
        }}
        .pulse {{
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--primary);
            margin-right: 8px;
            box-shadow: 0 0 10px var(--primary);
            animation: pulse 1.5s infinite;
        }}
        @keyframes pulse {{
            0% {{ transform: scale(0.95); opacity: 0.8; }}
            50% {{ transform: scale(1.2); opacity: 1; }}
            100% {{ transform: scale(0.95); opacity: 0.8; }}
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="badge"><span class="pulse"></span>Live Telemetry</div>
        <h1>Microservice Instance</h1>
        <div class="status">
            {status_text}
        </div>
        <div class="details">
            <p><strong>Version:</strong> {version}</p>
            <p><strong>Failure Simulation:</strong> {bug_status}</p>
            <p><strong>Metrics Endpoint:</strong> /metrics</p>
        </div>
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    if SIMULATE_FAILURE:
        # Simulate a bug: 20% of requests fail with HTTP 500
        if random.random() < 0.20:
            html_content = HTML_TEMPLATE.format(
                color_theme="#ff3333",
                status_bg="rgba(255, 51, 51, 0.1)",
                status_color="#ff3333",
                status_border="rgba(255, 51, 51, 0.3)",
                status_text="⚠️ HTTP 500 - INTERNAL SERVER ERROR",
                version=VERSION,
                bug_status="ACTIVE (20% Failure Rate)"
            )
            return HTMLResponse(content=html_content, status_code=500)
        time.sleep(random.uniform(0.1, 0.3)) # Simulate latency spike
        
    html_content = HTML_TEMPLATE.format(
        color_theme=COLOR_THEME,
        status_bg="rgba(0, 240, 255, 0.1)",
        status_color="#00f0ff",
        status_border="rgba(0, 240, 255, 0.3)",
        status_text="✨ OPERATIONAL & HEALTHY ✨",
        version=VERSION,
        bug_status="INACTIVE (Normal Mode)"
    )
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/healthz")
def health():
    return {"status": "healthy"}
