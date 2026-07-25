# Hackathon Playbook: The Risky Release (PS2) & AI Log RCA Assistant (PS7)

This document is the master playbook for your 4-person team. It outlines the end-to-end process for our **2-in-1 enterprise architecture**, combining **Problem Statement 2 (Zero-Downtime Pipeline)** with **Problem Statement 7 (AI Log RCA Assistant)**!

---

## 🌟 Why This 2-in-1 Combo Win Hackathons
When an incident hits in production:
1.  **PS2 (The Guard):** **Argo Rollouts** and **Prometheus** detect the HTTP 500 anomaly and automatically roll back the buggy release in seconds. **Customers are saved.**
2.  **PS7 (The Detective):** While the rollback saves the customers, *why* did the error happen? Our new **AI Log RCA Assistant** ingests the container logs, clusters scattered error patterns, and uses an LLM to generate a plain-English Root Cause Analysis (RCA) with a recommended remediation playbook. **Developers are saved.**

---

## 🛠️ Phase 1: Setup & Distribution (Before the Demo)

### Teammate 3: Security & CI/CD (The Repository Owner)
**Role:** Manages the Git repository and CI pipeline.
1. Ensure all project files (`app/`, `rca_assistant/`, `k8s/`, `loadgen/`) are pushed to your GitHub repo.
2. In GitHub **Settings > Secrets and variables > Actions**, verify your secrets:
   - `DOCKERHUB_USERNAME`: Your Docker Hub username.
   - `DOCKERHUB_TOKEN`: Your Docker Hub Access Token.

### Teammate 1: Platform Engineer (The Docker Machine)
**Role:** Hosts the infrastructure since this is the only machine with Docker.
1. Open Docker Desktop and enable **Kubernetes** in the settings (or use `k3d`).
2. Open your terminal and install the core CNCF controllers:
   ```powershell
   # 1. Install Prometheus (CNCF Graduated)
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm repo update
   helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace

   # 2. Install Argo CD (CNCF Graduated)
   kubectl create namespace argocd
   kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

   # 3. Install Argo Rollouts (CNCF Incubating)
   kubectl create namespace argo-rollouts
   kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
   ```
3. Build the Docker images locally for instant hackathon testing:
   ```powershell
   docker build -t demo-app:v1.0.0 ./app
   docker build -t demo-app:v2.0.0-buggy --build-arg APP_VERSION="v2.0.0 (Canary Bug)" ./app
   docker build -t rca-assistant:latest ./rca_assistant
   docker build -t loadgen:latest ./loadgen
   ```
4. Deploy the full suite into Kubernetes:
   ```powershell
   kubectl apply -f k8s/argo-rollouts/service.yaml
   kubectl apply -f k8s/argo-rollouts/analysis.yaml
   kubectl apply -f k8s/monitoring/servicemonitor.yaml
   kubectl apply -f k8s/argo-rollouts/rollout.yaml
   kubectl apply -f k8s/rca-assistant/deployment.yaml
   kubectl apply -f k8s/rca-assistant/service.yaml
   kubectl run loadgen --image=loadgen:latest --image-pull-policy=Never
   ```
5. Port-forward the dashboards so they are ready for the presentation:
   ```powershell
   # Open Terminal A: Argo Rollouts UI -> http://localhost:3100
   kubectl argo rollouts dashboard -p 3100

   # Open Terminal B: Microservice App -> http://localhost:8000
   kubectl port-forward svc/demo-app 8000:80

   # Open Terminal C: AI Log RCA Assistant (PS7) -> http://localhost:8001
   kubectl port-forward svc/rca-assistant 8001:80
   ```

---

## 🎤 Phase 2: The Live Presentation (The Script)

During the judging phase, everyone has a speaking part to prove depth of knowledge across BOTH problem statements.

### Part 1: The Architecture & Hardware Solution (Teammate 3 & 4)
*   **Teammate 3 (CI/Security):** "Hello Judges! We built an integrated SRE platform solving **BOTH Problem Statement 2 (The Risky Release) and Problem Statement 7 (The Log RCA Assistant)**. To make our solution realistic, we embraced a hardware constraint: only 1 of our 4 laptops has Docker installed. We solved this by building a **GitOps** pipeline where **Docker Build Cloud** builds our images remotely, and **Docker Scout** scans them for CVEs in CI to block insecure code."
*   **Teammate 4 (SRE):** "For our deployment engine, we used 4 official **CNCF tools**: **Kubernetes**, **Argo CD**, **Prometheus**, and **Argo Rollouts** (Incubating). Instead of an 'all-at-once' release, Argo Rollouts performs a **Canary Deployment**, releasing new code to only 20% of users while Prometheus acts as an automated doctor."

### Part 2: Triggering the Risky Release (Teammate 2)
*   **Teammate 1** shares their screen, showing the **Argo Rollouts Dashboard** (`http://localhost:3100`) with the stable version running green, and the **Microservice UI** (`http://localhost:8000`) showing Neon Blue operational status.
*   **Teammate 2 (Dev):** "I'm going to simulate a developer pushing a buggy release that causes HTTP 500 errors, database connection leaks, and latency spikes." 
*   **Action:** In `k8s/argo-rollouts/rollout.yaml`, change line 37 to `image: demo-app:v2.0.0-buggy` and line 44 to `value: "true"`, then apply!

### Part 3: The Autonomous Rollback (PS2 Demo - Teammate 1 & 4)
*   **Teammate 1 (Screen Sharer):** The Argo Rollouts Dashboard immediately shows a new Canary revision spinning up, taking exactly 20% of the traffic.
*   **Teammate 4 (SRE Narration):** "Argo Rollouts has now routed 20% of live traffic to the new version. On our application tab (`http://localhost:8000`), when we refresh, notice that 1 in 5 users hit our bright red `⚠️ HTTP 500` error screen."
*   *(Wait about 15 seconds)*
*   **Teammate 4:** "Our CNCF Prometheus query just detected that the error rate breached our 5% safety threshold. In 3, 2, 1..."
*   **Visual on Screen:** The Canary turns RED on Argo Rollouts, automatically terminates, and routing snaps 100% back to the Green Stable version!
*   **Teammate 1:** "The system detected the anomaly and autonomously healed itself. Zero customer outages and zero manual intervention required."

### Part 4: The AI Log RCA Detective (PS7 Demo - Teammate 2 & 3)
*   **Teammate 2 (Dev):** "While Argo Rollouts saved our customers by rolling back, as developers, we still need to know *why* that release failed. That is where our **Problem Statement 7 AI Log RCA Assistant** comes in."
*   **Teammate 1:** Opens Tab 3 in browser: `http://localhost:8001` (The AI Log RCA Assistant UI).
*   **Teammate 3 (Security/CI):** "Our RCA service ingested the scattered container logs from the failed Canary pods, stripped timestamps and variable IDs, and clustered the errors into recurring failure modes. By clicking **'Run Live AI RCA'**, our LLM engine synthesizes a plain-English executive summary for on-call engineers."
*   **Visual on Screen:** Show the clustered patterns (67% Database Pool Exhaustion, 17% NullPointer, 16% Gateway Timeout) and the generated **Plain-English SRE Playbook** recommending exact config changes and code line fixes!

---

## 🏆 Hackathon Checklist Requirements Satisfied (Double Score!)
- [x] **Docker Products:** Docker Desktop/Engine, Docker Build Cloud, Docker Scout, Docker Hub.
- [x] **CNCF Graduated/Incubating:** Kubernetes (Grad), Prometheus (Grad), Argo CD (Grad), Argo Rollouts (Incubating).
- [x] **AI Agent Framework:** LLM-powered Log RCA Assistant synthesizing plain-English root cause summaries (PS7).
- [x] **Realistic Scope:** 3 microservices (App, Loadgen, AI RCA Assistant) working flawlessly together.
