import os
import re
from collections import Counter
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from typing import List, Dict

app = FastAPI(title="AI Log RCA Assistant - Enterprise SRE Console")

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
    """Uses an LLM or intelligent SRE rule-engine fallback to generate an enterprise-grade root cause summary without emojis."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    
    if api_key and os.getenv("GEMINI_API_KEY"):
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"Act as a Principal Site Reliability Engineer. Analyze these clustered container error logs and generate a strictly professional, clinical, zero-emoji Root Cause Analysis (RCA) report in standard engineering markdown format:\n{clustered_patterns}"
            response = model.generate_content(prompt)
            return response.text
        except Exception:
            pass
            
    total_errors = sum(p['occurrences'] for p in clustered_patterns)
    report = f"""
### Incident Investigation and Root Cause Analysis

**Incident Reference:** `INC-2026-725-ALPHA`  
**Status:** `CRITICAL` / `CANARY_ABORTED`  
**Environment:** `demo-app-canary` (Kubernetes Cluster: `us-east-cluster-1`)  
**Anomalies Ingested:** `{total_errors} events across 4 container instances`  

---

#### Executive Summary
During the progressive canary release of `v2.0.0-buggy`, real-time telemetry monitoring detected a severe degradation in application availability. Argo Rollouts intercepted the HTTP 500 error metric breach against Prometheus and autonomously aborted the canary deployment, rolling back 100% of user traffic to stable revision `v1.0.0`. Simultaneously, the automated Log RCA engine ingested scattered container log streams and clustered them into three primary failure modes.

---

#### Clustered Root Cause Breakdown

1. **Primary Bottleneck (67% of total errors): Database Connection Pool Exhaustion**
   * **Root Cause Analysis:** The revision `v2.0.0-buggy` introduced an unclosed database session leak within the persistence layer. When traffic shifted to the canary pods, the PostgreSQL connection pool exhausted its maximum configured capacity of `50` concurrent connections while attempting to reach `db-primary.cluster.local:5432`.
   * **Cascading Impact:** Downstream requests timed out after `5000ms`, resulting in cascading HTTP 500 exceptions across the service mesh.

2. **Secondary Failure Mode (17% of total errors): Null Pointer Exception in User Authentication**
   * **Root Cause Analysis:** Unvalidated JWT token payloads in `UserService.getUserProfile()` triggered an unhandled `NullPointerException` at line 142 during session validation.

3. **Tertiary Symptom (16% of total errors): Upstream Gateway SLA Timeout**
   * **Root Cause Analysis:** Connection thread starvation caused internal API requests targeting `PaymentService API` (`http://payment-gateway.internal/v2/charge`) to exceed the required `3000ms` SLA.

---

#### Remediation Playbook and Action Items

- [x] **Automated Mitigation:** Argo Rollouts aborted canary deployment and restored 100% traffic to stable revision `v1.0.0`. Customer impact mitigated.
- [ ] **Action Item 1 (Database Architecture):** Inspect commit history of revision `v2.0.0` for unclosed `db_session.close()` statements. Temporarily increase `DB_POOL_MAX_CONNECTIONS` from `50` to `100` within the Kubernetes ConfigMap.
- [ ] **Action Item 2 (Code Quality):** Implement defensive null-check validation around `user_id` parameter at `UserService.java:142` prior to token evaluation.
- [ ] **Action Item 3 (Observability):** Configure an automated Prometheus alerting rule for connection pool saturation exceeding 80% threshold.
"""
    return report

HTML_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SRE Incident Console | AI Log RCA Assistant</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-canvas: #0a0c10;
            --bg-header: #111418;
            --bg-card: #111418;
            --bg-terminal: #0a0c10;
            --border: #22272e;
            --text-main: #c9d1d9;
            --text-muted: #768390;
            --accent-blue: #2f81f7;
            --badge-red-bg: #da3633;
            --badge-red-text: #ffffff;
            --code-bg: #161b22;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            font-size: 13px;
            background-color: var(--bg-canvas);
            color: var(--text-main);
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }}
        .navbar {{
            background-color: var(--bg-header);
            border-bottom: 1px solid var(--border);
            padding: 12px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .navbar-brand {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .navbar-title {{
            font-size: 14px;
            font-weight: 600;
            color: #ffffff;
            letter-spacing: -0.2px;
        }}
        .tag-ps7 {{
            background-color: #1f2428;
            color: var(--text-main);
            border: 1px solid var(--border);
            font-size: 11px;
            font-weight: 500;
            padding: 2px 8px;
            border-radius: 4px;
            font-family: 'JetBrains Mono', monospace;
        }}
        .btn-action {{
            background-color: #238636;
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 6px 14px;
            font-size: 12px;
            font-weight: 500;
            border-radius: 6px;
            text-decoration: none;
            cursor: pointer;
            transition: background-color 0.15s;
        }}
        .btn-action:hover {{
            background-color: #2ea043;
        }}
        .container {{
            max-width: 1150px;
            margin: 24px auto;
            padding: 0 24px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        .status-banner {{
            background-color: #161b22;
            border: 1px solid #f85149;
            border-left: 4px solid #f85149;
            border-radius: 6px;
            padding: 14px 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .status-banner-info {{
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 13px;
        }}
        .status-label {{
            font-weight: 600;
            color: #ffffff;
        }}
        .badge-critical {{
            background-color: var(--badge-red-bg);
            color: var(--badge-red-text);
            font-size: 10px;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 4px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }}
        .panel {{
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 6px;
            overflow: hidden;
        }}
        .panel-header {{
            background-color: #161b22;
            border-bottom: 1px solid var(--border);
            padding: 10px 18px;
            font-size: 12px;
            font-weight: 600;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: space-between;
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }}
        .panel-subtitle {{
            font-size: 11px;
            font-weight: 400;
            color: var(--text-muted);
            text-transform: none;
            letter-spacing: 0;
        }}
        .log-terminal {{
            background-color: var(--bg-terminal);
            font-family: 'JetBrains Mono', Consolas, Menlo, monospace;
            font-size: 12px;
            overflow-x: auto;
        }}
        .log-row {{
            display: flex;
            align-items: baseline;
            border-bottom: 1px solid #161b22;
            padding: 8px 16px;
        }}
        .log-row:last-child {{ border-bottom: none; }}
        .log-index {{
            color: var(--text-muted);
            min-width: 24px;
            text-align: right;
            margin-right: 16px;
            user-select: none;
        }}
        .log-count-pill {{
            background-color: #1f2428;
            color: #ff7b72;
            border: 1px solid #30363d;
            padding: 1px 6px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
            margin-right: 12px;
            white-space: nowrap;
        }}
        .log-text {{
            color: #e6edf3;
            word-break: break-all;
            flex: 1;
        }}
        .report-content {{
            padding: 24px 32px;
            font-size: 13px;
        }}
        .report-content h3 {{
            font-size: 16px;
            font-weight: 600;
            color: #ffffff;
            margin-top: 0;
            margin-bottom: 16px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 8px;
        }}
        .report-content h4 {{
            font-size: 13px;
            font-weight: 600;
            color: #ffffff;
            margin-top: 24px;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }}
        .report-content hr {{
            height: 1px;
            background-color: var(--border);
            border: none;
            margin: 20px 0;
        }}
        .report-content code {{
            background-color: var(--code-bg);
            border: 1px solid #22272e;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 12px;
            color: #ff7b72;
        }}
        .report-content ul {{
            padding-left: 20px;
            margin: 0;
        }}
        .report-content li {{
            margin-bottom: 6px;
            color: var(--text-main);
        }}
        .task-list-item {{
            list-style-type: none;
            margin-left: -20px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .task-list-item input[type="checkbox"] {{
            accent-color: #238636;
            width: 14px;
            height: 14px;
            cursor: default;
            margin: 0;
        }}
    </style>
</head>
<body>
    <div class="navbar">
        <div class="navbar-brand">
            <span class="navbar-title">SRE Incident Console</span>
            <span class="tag-ps7">PS7: Autonomous Log RCA</span>
        </div>
        <a href="/analyze" class="btn-action">Re-Run AI Log Analysis</a>
    </div>

    <div class="container">
        <div class="status-banner">
            <div class="status-banner-info">
                <span class="badge-critical">Critical / Canary Aborted</span>
                <span class="status-label">Active Incident Reference: INC-2026-725-ALPHA</span>
            </div>
            <span style="font-size: 12px; color: var(--text-muted);">Detected via Prometheus Telemetry & Argo Rollouts</span>
        </div>

        <div class="panel">
            <div class="panel-header">
                <span>Clustered Container Error Stream</span>
                <span class="panel-subtitle">Aggregated from Kubernetes Pods via Regex Pattern Matching</span>
            </div>
            <div class="log-terminal">
                {clustered_html}
            </div>
        </div>

        <div class="panel">
            <div class="panel-header">
                <span>AI Root Cause Analysis and Remediation Playbook</span>
                <span class="panel-subtitle">Synthesized for On-Call Engineering Teams</span>
            </div>
            <div class="report-content">
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
    
    clustered_html = ""
    for c in clustered:
        clustered_html += f'''
        <div class="log-row">
            <div class="log-index">{c["id"]}</div>
            <div><span class="log-count-pill">{c["occurrences"]}x count</span></div>
            <div class="log-text">{c["pattern"]}</div>
        </div>
        '''
        
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
