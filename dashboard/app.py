import os
import re
import json
import requests
import pandas as pd
import streamlit as st
import google.generativeai as genai
from datetime import datetime
from kubernetes import client, config

st.set_page_config(page_title="SafeShip AI Control Center", layout="wide")

# Configuration
K8S_NAMESPACE = os.getenv("K8S_NAMESPACE", "default")
ROLLOUT_NAME = os.getenv("ROLLOUT_NAME", "demo-app")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus-server.monitoring.svc.cluster.local:9090")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SAFESHIP_MODE = os.getenv("SAFESHIP_MODE", "k8s") # 'mock' or 'k8s'

st.sidebar.title("Configuration")
gemini_api_key_input = st.sidebar.text_input("Gemini API Key", type="password", value=GEMINI_API_KEY)
if gemini_api_key_input:
    genai.configure(api_key=gemini_api_key_input)

st.title("🚢 SafeShip AI Control Center")

# Initialize session state variables
if "narrator_feed" not in st.session_state:
    st.session_state.narrator_feed = []
if "last_state" not in st.session_state:
    st.session_state.last_state = None
if "history_error" not in st.session_state:
    st.session_state.history_error = []
if "history_latency" not in st.session_state:
    st.session_state.history_latency = []
if "k8s_client_initialized" not in st.session_state:
    st.session_state.k8s_client_initialized = False

def init_k8s():
    if not st.session_state.k8s_client_initialized and SAFESHIP_MODE != "mock":
        try:
            try:
                config.load_incluster_config()
            except config.ConfigException:
                config.load_kubeconfig()
            st.session_state.k8s_client_initialized = True
        except Exception as e:
            pass
    return st.session_state.k8s_client_initialized

def get_rollout():
    if SAFESHIP_MODE == "mock":
        return {"phase": "Healthy", "stable": "abc1234", "canary": "N/A", "weight": 0, "step": 0}
    try:
        api = client.CustomObjectsApi()
        rollout = api.get_namespaced_custom_object(
            group="argoproj.io",
            version="v1alpha1",
            namespace=K8S_NAMESPACE,
            plural="rollouts",
            name=ROLLOUT_NAME,
        )
        status = rollout.get("status", {})
        
        phase = status.get("phase", "Unknown")
        stable = status.get("stableRS", "Unknown")
        canary = status.get("currentPodHash", "Unknown")
        weight = status.get("canary", {}).get("weight", 0) if "canary" in status else 0
        if status.get("promoteFull"):
            phase = "Promoted"
        elif status.get("abort"):
            phase = "Aborted"
            
        return {
            "phase": phase,
            "stable": stable,
            "canary": canary if canary != stable else "N/A",
            "weight": weight,
            "step": status.get("currentStepIndex", 0),
        }
    except Exception as e:
        return None

def get_analysis_runs():
    if SAFESHIP_MODE == "mock":
        return []
    try:
        api = client.CustomObjectsApi()
        runs = api.list_namespaced_custom_object(
            group="argoproj.io",
            version="v1alpha1",
            namespace=K8S_NAMESPACE,
            plural="analysisruns",
        )
        return runs.get("items", [])
    except:
        return []

def get_prometheus_metrics():
    if SAFESHIP_MODE == "mock":
        return {"error_rate": 0.0, "latency": 50.0}
    try:
        query_err = f'sum(rate(http_requests_total{{status="500", job="{ROLLOUT_NAME}"}}[1m])) / sum(rate(http_requests_total{{job="{ROLLOUT_NAME}"}}[1m]))'
        res = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query_err}, timeout=1)
        res.raise_for_status()
        data = res.json()
        err_rate = 0.0
        if data["data"]["result"]:
            val = data["data"]["result"][0]["value"][1]
            if val != "NaN":
                err_rate = float(val) * 100.0
                
        # Fake latency for demonstration 
        query_lat = f'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{{job="{ROLLOUT_NAME}"}}[1m])) by (le))'
        res_lat = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query_lat}, timeout=1)
        lat = 50.0
        if res_lat.status_code == 200:
            data_lat = res_lat.json()
            if data_lat["data"]["result"]:
                val = data_lat["data"]["result"][0]["value"][1]
                if val != "NaN":
                    lat = float(val) * 1000.0
        
        return {"error_rate": err_rate, "latency": lat}
    except Exception as e:
        return None

def generate_narration(template_msg):
    if gemini_api_key_input:
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            prompt = f"Rewrite this SRE alert in a natural, concise sentence suitable for a live dashboard feed. Keep all facts and numbers exactly as they are. Do not invent details. The alert: '{template_msg}'"
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception:
            pass
    return template_msg

def update_kubernetes_rollout(action):
    if SAFESHIP_MODE == "mock":
        return True
    try:
        api = client.CustomObjectsApi()
        patch = {}
        if action == "promote":
            # For Argo Rollouts, unpause the rollout
            patch = {"spec": {"paused": False}}
        elif action == "abort":
            patch = {"status": {"abort": True}}
        elif action == "retry":
            patch = {"status": {"abort": False}}
            
        api.patch_namespaced_custom_object(
            group="argoproj.io",
            version="v1alpha1",
            namespace=K8S_NAMESPACE,
            plural="rollouts",
            name=ROLLOUT_NAME,
            body=patch
        )
        return True
    except Exception as e:
        st.error(f"Failed to update K8s: {e}")
        return False

@st.fragment(run_every="2s")
def live_dashboard():
    init_k8s()
    
    rollout = get_rollout()
    metrics = get_prometheus_metrics()
    
    if not rollout:
        st.error("⚠️ Cluster unavailable (Could not read Argo Rollout)")
        # Graceful degradation, don't return early if we want to show other elements
        rollout = {"phase": "Unknown", "stable": "N/A", "canary": "N/A", "weight": 0, "step": 0}
        
    if not metrics:
        st.warning("⚠️ Prometheus unavailable (Metrics not loading)")
        metrics = {"error_rate": 0.0, "latency": 0.0}

    # Update history for predictions
    st.session_state.history_error.append(metrics["error_rate"])
    st.session_state.history_latency.append(metrics["latency"])
    if len(st.session_state.history_error) > 5:
        st.session_state.history_error.pop(0)
        st.session_state.history_latency.pop(0)

    # Predictive Rollback Signal (Advisory Only)
    prediction_msg = None
    if len(st.session_state.history_error) == 5 and rollout["phase"] in ["Progressing", "Paused"]:
        err_slope = (st.session_state.history_error[-1] - st.session_state.history_error[0]) / 4
        proj_err = metrics["error_rate"] + (err_slope * 3)
        if proj_err > 5.0 and err_slope > 0:  # Threshold from AnalysisTemplate is 5% (0.05)
            prediction_msg = f"⚠️ SafeShip AI predicts the failure threshold may be crossed in approximately 6 seconds (projected error rate {proj_err:.1f}% > 5.0%)."

    # State Rendering
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Stable Hash", rollout["stable"][:8] if rollout["stable"] != "N/A" else "N/A")
    col2.metric("Canary Hash", rollout["canary"][:8] if rollout["canary"] != "N/A" else "N/A")
    col3.metric("Phase", rollout["phase"])
    col4.metric("Canary Weight", f"{rollout['weight']}%")

    m1, m2 = st.columns(2)
    m1.metric("Live Error Rate", f"{metrics['error_rate']:.2f}%")
    m2.metric("Live P95 Latency", f"{metrics['latency']:.0f}ms")

    if prediction_msg:
        st.warning(prediction_msg)

    # Narrator Logic
    last_state = st.session_state.last_state
    now = datetime.now().strftime("%H:%M:%S")
    
    if last_state:
        if last_state["phase"] != rollout["phase"]:
            if rollout["phase"] == "Aborted":
                msg = generate_narration("Argo Rollouts aborted the canary. Traffic returned to the stable revision.")
                st.session_state.narrator_feed.insert(0, f"🔴 [{now}] {msg}")
            elif rollout["phase"] == "Progressing":
                msg = generate_narration(f"Canary revision {rollout['canary'][:8]} started.")
                st.session_state.narrator_feed.insert(0, f"🔵 [{now}] {msg}")
            elif rollout["phase"] == "Healthy":
                msg = generate_narration("Canary revision is healthy and fully promoted.")
                st.session_state.narrator_feed.insert(0, f"🟢 [{now}] {msg}")
            elif rollout["phase"] == "Paused":
                msg = generate_narration("Rollout is paused, waiting for analysis or manual promotion.")
                st.session_state.narrator_feed.insert(0, f"🟡 [{now}] {msg}")

        if last_state["weight"] != rollout["weight"] and rollout["weight"] > 0:
            msg = generate_narration(f"Traffic shifted to {rollout['weight']}% canary.")
            st.session_state.narrator_feed.insert(0, f"🟡 [{now}] {msg}")
            
        # Detect metric spikes
        if metrics["error_rate"] >= 5.0 and last_state.get("error_rate", 0) < 5.0:
            msg = generate_narration(f"Error rate increased from {last_state.get('error_rate', 0):.1f}% to {metrics['error_rate']:.1f}%.")
            st.session_state.narrator_feed.insert(0, f"🟠 [{now}] {msg}")

    st.session_state.last_state = {
        "phase": rollout["phase"],
        "weight": rollout["weight"],
        "error_rate": metrics["error_rate"]
    }

    st.subheader("Autonomous SRE Narrator Feed")
    feed_container = st.container(height=200)
    for item in st.session_state.narrator_feed:
        # Simple color rendering
        color = item.split(" ")[0]
        text = " ".join(item.split(" ")[1:])
        feed_container.markdown(f"**{color}** {text}")

# --- End Fragment ---
live_dashboard()

st.markdown("---")
# Feature: Natural Language Commands
st.subheader("Natural-Language Release Commands")
nl_command = st.text_input("Type a command (e.g., 'promote the canary', 'abort the rollout')")

if nl_command:
    parsed_action = None
    
    if gemini_api_key_input:
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            prompt = f"""
            Parse the following natural language command into a JSON object.
            Allowed actions: "promote", "abort", "retry".
            If the user is asking for status, ignore. We only care about actionable mutations.
            Command: "{nl_command}"
            Return ONLY raw valid JSON, no markdown formatting.
            Example: {{"action": "promote"}}
            """
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```json"): text = text[7:-3].strip()
            elif text.startswith("```"): text = text[3:-3].strip()
            parsed_action = json.loads(text)
        except:
            pass
            
    if not parsed_action:
        # Fallback Regex
        cmd = nl_command.lower()
        if re.search(r"\bpromote\b|\badvance\b", cmd):
            parsed_action = {"action": "promote"}
        elif re.search(r"\babort\b|\brollback\b", cmd):
            parsed_action = {"action": "abort"}
        elif re.search(r"\bretry\b", cmd):
            parsed_action = {"action": "retry"}

    if parsed_action and "action" in parsed_action:
        action = parsed_action['action']
        st.info(f"Interpreted action: **{action.upper()}**")
        
        # Require explicit user confirmation
        if action in ["promote", "abort", "retry"]:
            if st.button(f"Confirm {action.capitalize()}"):
                success = update_kubernetes_rollout(action)
                if success:
                    st.success(f"Action '{action}' dispatched to Kubernetes successfully.")
    else:
        st.warning("Command not recognized as a supported action (promote, abort, retry).")

st.markdown("---")
st.subheader("Argo AnalysisRuns History")
if st.button("Refresh Analysis History"):
    runs = get_analysis_runs()
    if runs:
        history = []
        for r in runs:
            # Parse metrics results if available
            metrics_results = r.get("status", {}).get("metricResults", [{}])
            successful = metrics_results[0].get("successful", 0) if metrics_results else 0
            failed = metrics_results[0].get("failed", 0) if metrics_results else 0
            
            history.append({
                "Name": r.get("metadata", {}).get("name"),
                "Phase": r.get("status", {}).get("phase", "Unknown"),
                "Successful Measurements": successful,
                "Failed Measurements": failed,
            })
        st.dataframe(pd.DataFrame(history), use_container_width=True)
    else:
        st.write("No AnalysisRuns found.")
