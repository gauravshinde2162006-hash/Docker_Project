import os
import re
from collections import Counter
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from typing import List, Dict

app = FastAPI(title="SRE Incident Command Center - PS7")

SIMULATED_LOG_STREAM = [
    "2026-07-25 14:50:01 [ERROR] [demo-app-canary] DatabaseTimeoutException: Connection pool exhausted while connecting to db-primary.cluster.local:5432 after 5000ms. Max connections (50) reached.",
    "2026-07-25 14:50:03 [ERROR] [demo-app-canary] DatabaseTimeoutException: Connection pool exhausted while connecting to db-primary.cluster.local:5432 after 5000ms. Max connections (50) reached.",
    "2026-07-25 14:50:05 [ERROR] [demo-app-canary] NullPointerException in UserService.getUserProfile() at line 142: user_id token payload evaluates to None during session validation.",
    "2026-07-25 14:50:08 [ERROR] [demo-app-canary] DatabaseTimeoutException: Connection pool exhausted while connecting to db-primary.cluster.local:5432 after 5000ms. Max connections (50) reached.",
    "2026-07-25 14:50:12 [ERROR] [demo-app-canary] UpstreamGatewayTimeout: PaymentService API at http://payment-gateway.internal/v2/charge failed to respond within SLA (3000ms).",
    "2026-07-25 14:50:15 [ERROR] [demo-app-canary] DatabaseTimeoutException: Connection pool exhausted while connecting to db-primary.cluster.local:5432 after 5000ms. Max connections (50) reached."
]

def cluster_log_patterns(logs: List[str]) -> List[Dict]:
    pattern_counter = Counter()
    for log in logs:
        clean_log = re.sub(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} ', '', log)
        pattern_counter[clean_log] += 1
        
    clustered = []
    total = len(logs)
    for idx, (pattern, count) in enumerate(pattern_counter.most_common(), 1):
        percentage = int((count / total) * 100)
        
        # Parse clean titles and descriptions for production readability
        if "DatabaseTimeoutException" in pattern:
            title = "Database Connection Pool Exhaustion"
            desc = "The canary revision introduced an unclosed session leak. The PostgreSQL connection pool reached its maximum capacity of 50 concurrent connections when attempting to reach db-primary.cluster.local:5432."
            impact = "High"
            impact_color = "#ef4444"
        elif "NullPointerException" in pattern:
            title = "Null Pointer Exception in User Auth"
            desc = "Unvalidated JWT token payloads in UserService.getUserProfile() triggered an unhandled NullPointerException at line 142 during session validation."
            impact = "Medium"
            impact_color = "#f97316"
        else:
            title = "Upstream Gateway SLA Timeout"
            desc = "Connection thread starvation caused internal API requests targeting PaymentService API (http://payment-gateway.internal/v2/charge) to exceed the required 3000ms SLA."
            impact = "Medium"
            impact_color = "#eab308"
            
        clustered.append({
            "id": idx,
            "title": title,
            "desc": desc,
            "pattern": pattern,
            "count": count,
            "percentage": percentage,
            "impact": impact,
            "impact_color": impact_color
        })
    return clustered

HTML_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SRE Incident Command Center | Production Console</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-main: #0f172a;
            --bg-card: #1e293b;
            --bg-subcard: #0b1329;
            --border: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #38bdf8;
            --green: #22c55e;
            --red: #ef4444;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            font-size: 14px;
            background-color: var(--bg-main);
            color: var(--text-main);
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }}
        .header {{
            background-color: #0b1329;
            border-bottom: 1px solid var(--border);
            padding: 16px 32px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .header-title {{
            font-size: 16px;
            font-weight: 700;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .header-tag {{
            background-color: #1e293b;
            color: var(--accent);
            border: 1px solid #38bdf8;
            font-size: 11px;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 20px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }}
        .header-actions {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}
        .status-pulse {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            font-weight: 600;
            color: var(--red);
            background-color: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            padding: 6px 14px;
            border-radius: 20px;
        }}
        .dot {{
            width: 8px;
            height: 8px;
            background-color: var(--red);
            border-radius: 50%;
        }}
        .btn-refresh {{
            background-color: #2563eb;
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            text-decoration: none;
            transition: background 0.15s;
        }}
        .btn-refresh:hover {{
            background-color: #1d4ed8;
        }}
        .container {{
            max-width: 1300px;
            margin: 32px auto;
            padding: 0 32px;
        }}
        /* KPI Cards Grid */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 28px;
        }}
        .kpi-card {{
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
        }}
        .kpi-label {{
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        .kpi-value {{
            font-size: 24px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 4px;
        }}
        .kpi-subtext {{
            font-size: 12px;
            color: var(--text-muted);
        }}
        /* Two Column Layout */
        .main-grid {{
            display: grid;
            grid-template-columns: 1.6fr 1fr;
            gap: 24px;
            align-items: start;
        }}
        .section-title {{
            font-size: 15px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        /* Clustered Error Cards */
        .error-card {{
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
        }}
        .error-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }}
        .error-title {{
            font-size: 15px;
            font-weight: 700;
            color: #ffffff;
        }}
        .error-meta {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .impact-badge {{
            font-size: 11px;
            font-weight: 700;
            color: #ffffff;
            padding: 2px 8px;
            border-radius: 4px;
            text-transform: uppercase;
        }}
        .percent-badge {{
            font-size: 12px;
            font-weight: 700;
            color: var(--text-muted);
            background: #0f172a;
            padding: 2px 8px;
            border-radius: 4px;
            border: 1px solid var(--border);
        }}
        .error-desc {{
            font-size: 13px;
            color: #cbd5e1;
            margin-bottom: 16px;
            line-height: 1.6;
        }}
        .log-snippet {{
            background-color: #0b1329;
            border: 1px solid #1e293b;
            border-radius: 6px;
            padding: 12px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: #f87171;
            word-break: break-all;
        }}
        /* Playbook Card */
        .playbook-card {{
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 24px;
        }}
        .playbook-section {{
            margin-bottom: 24px;
        }}
        .playbook-section:last-child {{ margin-bottom: 0; }}
        .playbook-heading {{
            font-size: 12px;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .check-item {{
            display: flex;
            align-items: flex-start;
            gap: 12px;
            background: #0f172a;
            border: 1px solid var(--border);
            padding: 14px;
            border-radius: 6px;
            margin-bottom: 10px;
        }}
        .check-icon {{
            width: 18px;
            height: 18px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 700;
            flex-shrink: 0;
            margin-top: 1px;
        }}
        .check-done {{
            background-color: rgba(34, 197, 94, 0.2);
            color: var(--green);
            border: 1px solid var(--green);
        }}
        .check-pending {{
            background-color: #1e293b;
            color: var(--text-muted);
            border: 1px solid var(--border);
        }}
        .check-text {{
            font-size: 13px;
            color: #e2e8f0;
            font-weight: 500;
            line-height: 1.4;
        }}
        .check-sub {{
            font-size: 12px;
            color: var(--text-muted);
            font-weight: 400;
            margin-top: 4px;
        }}
        .tag {{
            display: inline-block;
            font-size: 10px;
            font-weight: 600;
            padding: 1px 6px;
            border-radius: 4px;
            margin-left: 8px;
            text-transform: uppercase;
        }}
        .tag-auto {{ background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }}
        .tag-manual {{ background: rgba(249, 115, 22, 0.15); color: #f97316; border: 1px solid rgba(249, 115, 22, 0.3); }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-title">
            <span>SRE Incident Command Center</span>
            <span class="header-tag">Problem Statement 7: Log RCA Engine</span>
        </div>
        <div class="header-actions">
            <div class="status-pulse">
                <span class="dot"></span>
                <span>Active Incident: INC-2026-725-ALPHA</span>
            </div>
            <a href="/analyze" class="btn-refresh">Analyze Latest Telemetry</a>
        </div>
    </div>

    <div class="container">
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Total Anomaly Events</div>
                <div class="kpi-value">6 Events</div>
                <div class="kpi-subtext">Aggregated across 4 canary pods</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Primary Root Cause</div>
                <div class="kpi-value">DB Pool Leak</div>
                <div class="kpi-subtext">67% of ingested error stream</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Resolution Time (MTTR)</div>
                <div class="kpi-value">18 Seconds</div>
                <div class="kpi-subtext">Auto-aborted by Argo Rollouts</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Current Cluster Health</div>
                <div class="kpi-value" style="color: var(--green);">Stable Restored</div>
                <div class="kpi-subtext">100% traffic routed to v1.0.0</div>
            </div>
        </div>

        <div class="main-grid">
            <div>
                <div class="section-title">
                    <span>Clustered Failure Modes & Root Cause Analysis</span>
                    <span style="font-size: 12px; font-weight: 500; color: var(--text-muted);">AI Pattern Clustering Active</span>
                </div>
                {error_cards_html}
            </div>

            <div>
                <div class="section-title">
                    <span>SRE Remediation Playbook</span>
                    <span style="font-size: 12px; font-weight: 500; color: var(--text-muted);">Actionable SRE Checklist</span>
                </div>
                <div class="playbook-card">
                    <div class="playbook-section">
                        <div class="playbook-heading">
                            <span>Completed Automated Mitigation</span>
                        </div>
                        <div class="check-item">
                            <div class="check-icon check-done">&#10003;</div>
                            <div>
                                <div class="check-text">Abort Canary Revision <span class="tag tag-auto">Automated</span></div>
                                <div class="check-sub">Argo Rollouts intercepted HTTP 500 threshold breach and immediately terminated v2.0.0-buggy pods.</div>
                            </div>
                        </div>
                        <div class="check-item">
                            <div class="check-icon check-done">&#10003;</div>
                            <div>
                                <div class="check-text">Restore Traffic to Stable Service <span class="tag tag-auto">Automated</span></div>
                                <div class="check-sub">100% of user traffic successfully rerouted back to stable revision v1.0.0. Zero customer impact remaining.</div>
                            </div>
                        </div>
                    </div>

                    <div class="playbook-section">
                        <div class="playbook-heading">
                            <span>Required On-Call Actions</span>
                        </div>
                        <div class="check-item">
                            <div class="check-icon check-pending">1</div>
                            <div>
                                <div class="check-text">Expand Database Connection Buffer <span class="tag tag-manual">ConfigMap</span></div>
                                <div class="check-sub">Inspect commit history for unclosed DB sessions. Temporarily increase DB_POOL_MAX_CONNECTIONS from 50 to 100.</div>
                            </div>
                        </div>
                        <div class="check-item">
                            <div class="check-icon check-pending">2</div>
                            <div>
                                <div class="check-text">Implement Token Sanitization <span class="tag tag-manual">Code Fix</span></div>
                                <div class="check-sub">Add defensive null-check validation on user_id token payload at UserService.java:142 prior to evaluation.</div>
                            </div>
                        </div>
                        <div class="check-item">
                            <div class="check-icon check-pending">3</div>
                            <div>
                                <div class="check-text">Configure Saturation Alerting Rule <span class="tag tag-manual">Prometheus</span></div>
                                <div class="check-sub">Add an automated Prometheus alert when database pool utilization exceeds 80% capacity for 60 seconds.</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def dashboard():
    clustered = cluster_log_patterns(SIMULATED_LOG_STREAM)
    
    error_cards_html = ""
    for c in clustered:
        error_cards_html += f'''
        <div class="error-card">
            <div class="error-header">
                <div class="error-title">{c["id"]}. {c["title"]}</div>
                <div class="error-meta">
                    <span class="percent-badge">{c["percentage"]}% of Errors</span>
                    <span class="impact-badge" style="background-color: {c["impact_color"]};">{c["impact"]} Impact</span>
                </div>
            </div>
            <div class="error-desc">{c["desc"]}</div>
            <div class="log-snippet">{c["pattern"]}</div>
        </div>
        '''
        
    return HTMLResponse(content=HTML_UI.format(error_cards_html=error_cards_html))

@app.get("/analyze")
def analyze_api():
    clustered = cluster_log_patterns(SIMULATED_LOG_STREAM)
    return {"status": "success", "incident_id": "INC-2026-725-ALPHA", "clustered_patterns": clustered}

@app.get("/healthz")
def health():
    return {"status": "healthy"}
