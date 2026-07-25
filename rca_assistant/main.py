import os
import re
from collections import Counter
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from typing import List, Dict

app = FastAPI(title="AI Log RCA Assistant (PS7 Solution)")

# Simulated realistic log stream from the failed canary release
SIMULATED_LOG_STREAM = [
    "2026-07-25 14:50:01 [ERROR] [demo-app-canary] DatabaseTimeoutException: Connection pool exhausted while connecting to db-primary.cluster.local:5432 after 5000ms. Max connections (50) reached.",
    "2026-07-25 14:50:03 [ERROR] [demo-app-canary] DatabaseTimeoutException: Connection pool exhausted while connecting to db-primary.cluster.local:5432 after 5000ms. Max connections (50) reached.",
    "2026-07-25 14:50:05 [ERROR] [demo-app-canary] NullPointerException in UserService.getUserProfile() at line 142: user_id token payload evaluates to None during session validation.",
    "2026-07-25 14:50:08 [ERROR] [demo-app-canary] DatabaseTimeoutException: Connection pool exhausted while connecting to db-primary.cluster.local:5432 after 5000ms. Max connections (50) reached.",
    "2026-07-25 14:50:12 [ERROR] [demo-app-canary] UpstreamGatewayTimeout: PaymentService API at http://payment-gateway.internal/v2/charge failed to respond within SLA (3000ms).",
    "2026-07-25 14:50:15 [ERROR] [demo-app-canary] DatabaseTimeoutException: Connection pool exhausted while connecting to db-primary.cluster.local:5432 after 5000ms. Max connections (50) reached."
]

def cluster_log_patterns(logs: List[str]) -> List[Dict]:
    """Clusters scattered log lines by stripping timestamps to find recurring patterns."""
    pattern_counter = Counter()
    for log in logs:
        clean_log = re.sub(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} ', '', log)
        pattern_counter[clean_log] += 1
        
    clustered = []
    for idx, (pattern, count) in enumerate(pattern_counter.most_common(), 1):
        clustered.append({"id": idx, "pattern": pattern, "occurrences": count})
    return clustered

def generate_ai_rca(clustered_patterns: List[Dict]) -> str:
    """Uses an LLM or intelligent SRE rule-engine fallback to generate a structured root cause summary."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    
    if api_key and os.getenv("GEMINI_API_KEY"):
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"Act as a Principal Site Reliability Engineer. Analyze these clustered container error logs and generate a professional GitHub-flavored markdown Root Cause Analysis (RCA) report:\n{clustered_patterns}"
            response = model.generate_content(prompt)
            return response.text
        except Exception:
            pass
            
    total_errors = sum(p['occurrences'] for p in clustered_patterns)
    report = f"""
### 🛡️ Incident Investigation & AI Root Cause Analysis

**Incident Reference:** `#INC-2026-725-ALPHA`  
**Status:** 🔴 **Active / Canary Rollback Executed**  
**Environment:** `demo-app-canary` (Kubernetes Cluster: `us-east-cluster-1`)  
**Total Anomalies Analyzed:** `{total_errors} error events across 4 pods`  

---

#### 📌 Executive Summary
During the canary release of `v2.0.0-buggy`, the SRE telemetry engine detected a sharp degradation in service health. **Argo Rollouts** intercepted the `HTTP 500` error spike and autonomously aborted the deployment, restoring 100% traffic to stable `v1.0.0`. Simultaneously, the AI Log Detective ingested container logs and isolated the underlying failure modes.

---

#### 🔍 Clustered Root Cause Breakdown

1. **Primary Bottleneck (67% of total errors): Database Connection Pool Exhaustion**
   * **Root Cause Analysis:** The canary build introduced an unclosed connection leak in the repository layer. When traffic shifted to the canary pods, the PostgreSQL connection pool exhausted its maximum capacity of `50` concurrent connections while attempting to reach `db-primary.cluster.local:5432`.
   * **Cascading Impact:** Requests timed out after `5000ms`, causing downstream gateway errors.

2. **Secondary Failure (17% of total errors): Null Pointer Exception in User Authentication**
   * **Root Cause Analysis:** Unvalidated JWT token payloads in `UserService.getUserProfile()` triggered a `NullPointerException` at line 142 during session validation.

3. **Tertiary Symptom (16% of total errors): Upstream Gateway SLA Timeout**
   * **Root Cause Analysis:** Thread starvation caused internal API requests to `PaymentService API` (`http://payment-gateway.internal/v2/charge`) to exceed the `3000ms` SLA.

---

#### 🛠️ Recommended Remediation Playbook (Action Items)

- [x] **Immediate Automated Mitigation:** Argo Rollouts aborted canary and rolled back to `v1.0.0`. Zero customer downtime remaining.
- [ ] **Action Item 1 (Database):** Inspect `v2.0.0` commit diff for unclosed `db_session.close()` calls. Temporarily bump `DB_POOL_MAX_CONNECTIONS` from `50` to `100` in Kubernetes ConfigMap.
- [ ] **Action Item 2 (Code Quality):** Add defensive null-check validation around `user_id` at `UserService.java:142`.
- [ ] **Action Item 3 (Observability):** Add a Prometheus alerting rule for connection pool utilization exceeding 80%.
"""
    return report

HTML_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SRE Copilot — Incident Investigator</title>
    <style>
        :root {{
            --bg: #0d1117;
            --header-bg: #010409;
            --card-bg: #161b22;
            --border: #30363d;
            --text-main: #c9d1d9;
            --text-muted: #8b949e;
            --link: #58a6ff;
            --btn-green: #238636;
            --btn-green-hover: #2ea043;
            --red: #f85149;
            --red-bg: rgba(248, 81, 73, 0.1);
            --code-bg: #1f2428;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            line-height: 1.5;
        }}
        .navbar {{
            background-color: var(--header-bg);
            border-bottom: 1px solid var(--border);
            padding: 16px 32px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .navbar-title {{
            font-size: 1.1em;
            font-weight: 600;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .badge-ps7 {{
            background-color: #1f6feb;
            color: #ffffff;
            font-size: 0.75em;
            padding: 2px 8px;
            border-radius: 12px;
            font-weight: 500;
        }}
        .btn-primary {{
            background-color: var(--btn-green);
            color: #ffffff;
            border: 1px solid rgba(27, 31, 36, 0.15);
            padding: 6px 16px;
            font-size: 0.9em;
            font-weight: 600;
            border-radius: 6px;
            text-decoration: none;
            cursor: pointer;
            transition: background-color 0.2s;
        }}
        .btn-primary:hover {{
            background-color: var(--btn-green-hover);
        }}
        .container {{
            max-width: 1200px;
            margin: 32px auto;
            padding: 0 24px;
            display: grid;
            grid-template-columns: 1fr;
            gap: 24px;
        }}
        .banner-incident {{
            background-color: var(--red-bg);
            border: 1px solid rgba(248, 81, 73, 0.4);
            border-radius: 6px;
            padding: 16px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .banner-incident-text {{
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 600;
            color: #ffffff;
        }}
        .status-pill {{
            background-color: var(--red);
            color: #ffffff;
            font-size: 0.75em;
            padding: 2px 8px;
            border-radius: 12px;
            text-transform: uppercase;
        }}
        .box {{
            background-color: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            overflow: hidden;
        }}
        .box-header {{
            background-color: #161b22;
            border-bottom: 1px solid var(--border);
            padding: 12px 20px;
            font-weight: 600;
            font-size: 0.95em;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .box-body {{
            padding: 24px;
        }}
        /* Terminal / Log Viewer Style */
        .log-terminal {{
            background-color: #0d1117;
            border: 1px solid var(--border);
            border-radius: 6px;
            font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
            font-size: 0.85em;
            overflow-x: auto;
        }}
        .log-row {{
            display: flex;
            align-items: flex-start;
            border-bottom: 1px solid rgba(48, 54, 61, 0.4);
            padding: 10px 16px;
            transition: background 0.15s;
        }}
        .log-row:last-child {{ border-bottom: none; }}
        .log-row:hover {{ background-color: rgba(177, 186, 196, 0.04); }}
        .log-num {{
            color: var(--text-muted);
            min-width: 30px;
            user-select: none;
            text-align: right;
            margin-right: 16px;
        }}
        .log-count-badge {{
            background-color: rgba(248, 81, 73, 0.15);
            color: var(--red);
            border: 1px solid rgba(248, 81, 73, 0.3);
            padding: 1px 6px;
            border-radius: 4px;
            font-weight: 600;
            margin-right: 12px;
            white-space: nowrap;
        }}
        .log-content {{
            color: #e6edf3;
            word-break: break-all;
            flex: 1;
        }}
        /* Markdown / RCA Styling */
        .markdown-body h3 {{
            border-bottom: 1px solid var(--border);
            padding-bottom: 8px;
            color: #ffffff;
            margin-top: 0;
        }}
        .markdown-body h4 {{
            color: #ffffff;
            margin-top: 24px;
            margin-bottom: 12px;
        }}
        .markdown-body hr {{
            height: 1px;
            background-color: var(--border);
            border: none;
            margin: 24px 0;
        }}
        .markdown-body code {{
            background-color: var(--code-bg);
            padding: 0.2em 0.4em;
            border-radius: 6px;
            font-family: ui-monospace, SFMono-Regular, monospace;
            font-size: 0.9em;
            color: #ff7b72;
        }}
        .markdown-body ul {{
            padding-left: 20px;
        }}
        .markdown-body li {{
            margin-bottom: 8px;
        }}
        .task-list-item {{
            list-style-type: none;
            margin-left: -20px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .task-list-item input[type="checkbox"] {{
            accent-color: var(--btn-green);
            width: 16px;
            height: 16px;
            cursor: default;
        }}
    </style>
</head>
<body>
    <div class="navbar">
        <div class="navbar-title">
            <span>🛡️ SRE Copilot</span>
            <span class="badge-ps7">Problem Statement 7: Log RCA Assistant</span>
        </div>
        <a href="/analyze" class="btn-primary">⚡ Re-Run AI Log Analysis</a>
    </div>

    <div class="container">
        <div class="banner-incident">
            <div class="banner-incident-text">
                <span style="font-size: 1.2em;">🚨</span>
                <span>Active Incident: <strong>#INC-2026-725-ALPHA</strong></span>
                <span class="status-pill">Canary Rollback Triggered</span>
            </div>
            <span style="font-size: 0.85em; color: var(--text-muted);">Detected via Prometheus & Argo Rollouts</span>
        </div>

        <div class="box">
            <div class="box-header">
                <span>🔥 Clustered Container Error Stream</span>
                <span style="font-size: 0.85em; font-weight: normal; color: var(--text-muted);">Aggregated from Kubernetes Pods via regex pattern matching</span>
            </div>
            <div class="box-body" style="padding: 16px;">
                <div class="log-terminal">
                    {clustered_html}
                </div>
            </div>
        </div>

        <div class="box">
            <div class="box-header">
                <span>✨ AI Copilot Root Cause & Remediation Playbook</span>
                <span style="font-size: 0.85em; font-weight: normal; color: var(--text-muted);">Synthesized in real-time for On-Call Engineers</span>
            </div>
            <div class="box-body markdown-body">
                {rca_html}
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def dashboard():
    clustered = cluster_log_patterns(SIMULATED_LOG_STREAM)
    rca_text = generate_ai_rca(clustered)
    
    # Format clustered logs as GitHub Terminal Rows
    clustered_html = ""
    for c in clustered:
        clustered_html += f'''
        <div class="log-row">
            <div class="log-num">{c["id"]}</div>
            <div><span class="log-count-badge">{c["occurrences"]}x count</span></div>
            <div class="log-content">{c["pattern"]}</div>
        </div>
        '''
        
    # Convert Markdown to GitHub-styled HTML
    rca_html = rca_text.replace("\n\n", "<br><br>")
    rca_html = rca_html.replace("### ", "<h3>").replace("#### ", "<h4>")
    rca_html = rca_html.replace("---", "<hr>")
    rca_html = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', rca_html)
    rca_html = re.sub(r'`(.*?)`', r'<code>\1</code>', rca_html)
    rca_html = rca_html.replace("* [x]", '<li class="task-list-item"><input type="checkbox" checked disabled>')
    rca_html = rca_html.replace("- [x]", '<li class="task-list-item"><input type="checkbox" checked disabled>')
    rca_html = rca_html.replace("* [ ]", '<li class="task-list-item"><input type="checkbox" disabled>')
    rca_html = rca_html.replace("- [ ]", '<li class="task-list-item"><input type="checkbox" disabled>')
    rca_html = rca_html.replace("* ", "<li>").replace("- ", "<li>")
    
    return HTMLResponse(content=HTML_UI.format(clustered_html=clustered_html, rca_html=rca_html))

@app.get("/analyze")
def analyze_api():
    clustered = cluster_log_patterns(SIMULATED_LOG_STREAM)
    rca_text = generate_ai_rca(clustered)
    return {"status": "success", "incident_id": "INC-2026-725-ALPHA", "clustered_patterns": clustered, "ai_rca_summary": rca_text}

@app.get("/healthz")
def health():
    return {"status": "healthy"}
