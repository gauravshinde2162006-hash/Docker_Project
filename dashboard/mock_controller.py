from fastapi import FastAPI, BackgroundTasks
import asyncio
import random
import datetime

app = FastAPI()

# Mock State
class MockState:
    def __init__(self):
        self.stable_version = "v1"
        self.canary_version = "v2"
        self.canary_active = False
        self.stable_traffic = 100
        self.canary_traffic = 0
        self.canary_error_rate = 0.0
        self.canary_p95_latency_ms = 0.0
        self.decision = "STABLE"
        self.releases_log = []

state = MockState()

def log_audit(action, reason):
    version = state.canary_version if state.canary_active else state.stable_version
    state.releases_log.append({
        "version": version,
        "action": action,
        "reason": reason,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    })

@app.get("/api/status")
def get_status():
    return {
        "stable_version": state.stable_version,
        "canary_version": state.canary_version,
        "canary_active": state.canary_active,
        "stable_traffic": state.stable_traffic,
        "canary_traffic": state.canary_traffic,
        "canary_error_rate": state.canary_error_rate,
        "canary_p95_latency_ms": state.canary_p95_latency_ms,
        "decision": state.decision
    }

@app.get("/api/releases")
def get_releases():
    return state.releases_log

@app.post("/api/deploy")
async def deploy(req: dict):
    state.canary_version = req.get("version", "v2")
    state.canary_active = True
    state.canary_traffic = 10
    state.stable_traffic = 90
    state.decision = "MONITORING"
    log_audit("DEPLOY", f"Started canary deployment for {state.canary_version}")
    
    # Simulate metrics degradation if it's v2
    if state.canary_version == "v2":
        async def degrade():
            await asyncio.sleep(2)
            state.canary_error_rate = 35.5
            state.canary_p95_latency_ms = 950.0
            await asyncio.sleep(2)
            state.decision = "ROLLING_BACK"
            state.canary_traffic = 0
            state.stable_traffic = 100
            state.canary_active = False
            state.decision = "ROLLED_BACK"
            log_audit("ROLLBACK", "Error rate 35.5% exceeded 10%")
        asyncio.create_task(degrade())
    else:
        async def promote():
            await asyncio.sleep(2)
            state.canary_error_rate = 0.0
            state.canary_p95_latency_ms = 120.0
            state.canary_traffic = 100
            state.stable_traffic = 0
            state.decision = "PROMOTED"
            state.stable_version = state.canary_version
            state.canary_active = False
            log_audit("PROMOTED", f"{state.stable_version} is now stable")
        asyncio.create_task(promote())

    return {"status": "Deploying", "version": state.canary_version}

@app.post("/api/rollback")
def manual_rollback():
    state.decision = "ROLLING_BACK"
    state.canary_traffic = 0
    state.stable_traffic = 100
    state.canary_active = False
    state.decision = "ROLLED_BACK"
    log_audit("ROLLBACK", "Manual rollback requested")
    return {"status": "Rolled back"}

@app.post("/api/simulate-load")
def simulate_load():
    return {"status": "Load simulation started"}
