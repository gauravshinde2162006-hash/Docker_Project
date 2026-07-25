# SafeShip AI Control Center

The SafeShip AI Dashboard acts as an advanced observability and operations pane for the **Argo Rollouts** progressive delivery pipeline. It provides a natural language interface for commanding rollouts and uses an Autonomous SRE Narrator to summarize live cluster events.

## Architecture
The SafeShip AI Dashboard runs on Streamlit and integrates directly with the Kubernetes cluster and Prometheus:

```
SafeShip AI Dashboard
|
+---- Kubernetes API ----> Reads Argo Rollouts & AnalysisRuns (Source of Truth)
|
+---- Prometheus --------> Reads live canary metrics
|
+---- Gemini (Optional) -> Explains events & parses NL commands
```

**Note:** Argo Rollouts remains the sole authority for deterministic deployment decisions. The AI Dashboard provides observation, prediction, explanation, and human-approved command dispatching.

## Configuration & Environment Variables

You must configure the dashboard to connect to your Kubernetes cluster and Prometheus instance. By default, it will use your active `kubeconfig` if run locally, or an in-cluster service account if deployed within the cluster.

| Variable | Description | Default |
|----------|-------------|---------|
| `K8S_NAMESPACE` | The Kubernetes namespace where Argo Rollouts is running. | `default` |
| `ROLLOUT_NAME` | The name of the Rollout custom resource to monitor. | `demo-app` |
| `PROMETHEUS_URL` | The URL to query for Prometheus metrics. | `http://prometheus-server.monitoring.svc.cluster.local:9090` |
| `GEMINI_API_KEY` | Optional. If provided, activates the AI Narrator and AI command parsing. | `""` |
| `SAFESHIP_MODE` | Set to `mock` ONLY for local development without a K8s cluster. | `k8s` |

## How to Launch the Dashboard

### Prerequisites
1. Ensure you have Python 3.9+ installed.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure your local `kubeconfig` is pointing to the cluster where Argo Rollouts is installed (e.g., `kubectl get rollouts` works).
4. Set the `PROMETHEUS_URL` if you are port-forwarding Prometheus locally:
   ```bash
   export PROMETHEUS_URL=http://localhost:9090
   ```

### Running the App
Start the Streamlit application:
```bash
streamlit run app.py
```

## Features

### 1. Autonomous SRE Narrator
The dashboard continuously polls the Kubernetes `Rollout` resource and the Prometheus metrics. When it detects meaningful state changes (e.g., phase changes, traffic splits, or error rate spikes), it logs an event.
- **AI Mode (Gemini)**: Rewrites raw cluster events into natural, human-readable SRE narrative updates.
- **Offline Mode**: Operates deterministically, showing template alerts directly.

### 2. Predictive Rollback Signal
By observing a rolling window of Prometheus metrics, the dashboard calculates a trend line. If the trend predicts that the Argo Rollouts `AnalysisTemplate` failure threshold will be breached soon, it displays a warning banner. *This is advisory only; the dashboard never executes an automatic rollback itself.*

### 3. Natural-Language Release Commands
Operators can type natural language commands such as:
- *"promote the canary"*
- *"abort the rollout"*
- *"retry the rollout"*

In **AI Mode**, Gemini parses these commands into actionable JSON. In **Offline Mode**, keyword/regex parsing is used. 
**Safety First:** Any interpreted command that changes the Kubernetes deployment requires explicit human confirmation via a UI button before execution.

### Local Mock Development Mode
If you need to test the UI without a Kubernetes cluster or Prometheus instance, you can run the dashboard in Mock Mode:
```bash
export SAFESHIP_MODE=mock
streamlit run app.py
```
*Note: Mock mode is purely for development and should not be used as the primary hackathon demonstration.*
