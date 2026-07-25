# Hackathon Playbook: The Risky Release (PS2) & AI Log RCA Assistant (PS7)

This document is the master playbook for your 4-person team. It outlines the end-to-end process for our **2-in-1 enterprise architecture**, combining **Problem Statement 2 (Zero-Downtime Pipeline)** with **Problem Statement 7 (AI Log RCA Assistant)**!

---

## 🌟 Why This 2-in-1 Combo Win Hackathons
When an incident hits in production:
1.  **PS2 (The Guard):** **Argo Rollouts** and **Prometheus** detect the HTTP 500 anomaly and automatically roll back the buggy release in seconds. **Customers are saved.**
2.  **PS7 (The Detective):** While the rollback saves the customers, *why* did the error happen? Our new **AI Log RCA Assistant** ingests container logs, clusters error patterns, and synthesizes an executive Root Cause Analysis (RCA) with a structured remediation playbook. **Developers are saved.**

---

## 🛠️ Phase 1: Setup & Distribution (Before the Demo)

### Teammate 3: Security & CI/CD (The Repository Owner)
**Role:** Manages the Git repository and CI pipeline.
1. Ensure all project files are pushed to your GitHub repo.
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

## 🎤 Phase 2: The Live Presentation (Both Sides of the Coin!)

During the judging phase, we demonstrate **both sides of the coin**: a clean upgrade that promotes automatically, and a buggy release that rolls back automatically!

### Part 1: The Architecture & Hardware Solution (Teammate 3 & 4)
*   **Teammate 3 (CI/Security):** "Hello Judges! We built an integrated SRE platform solving **BOTH Problem Statement 2 (The Risky Release) and Problem Statement 7 (The Log RCA Assistant)**. To make our solution realistic, we embraced a hardware constraint: only 1 of our 4 laptops has Docker installed. We solved this by building a **GitOps** pipeline where **Docker Build Cloud** builds our images remotely, and **Docker Scout** scans them for CVEs in CI to block insecure code."
*   **Teammate 4 (SRE):** "For our deployment engine, we used 4 official **CNCF tools**: **Kubernetes**, **Argo CD**, **Prometheus**, and **Argo Rollouts** (Incubating). Instead of an 'all-at-once' release, Argo Rollouts performs a **Canary Deployment**, releasing new code to only 20% of users while Prometheus acts as an automated doctor."

### Part 2: Starting State — Stable Version 1.0 (Teammate 1)
*   **Action:** Teammate 1 runs:
    ```powershell
    kubectl apply -f k8s/demo-scenarios/1-stable-v1.yaml
    ```
*   **Teammate 1 (pointing to screen):** "Right now, our cluster is running Stable Version 1.0. As you can see on our application dashboard (`http://localhost:8000`), traffic is 100% healthy with our **Neon Blue UI**."

### Part 3: Side A (The Happy Path) — Clean Upgrade to Version 2.0 (Teammate 2)
*   **Teammate 2 (Dev):** "First, we will demonstrate the happy path: a developer deploying a clean, bug-free upgrade."
*   **Action:** Teammate 1 applies Scenario 2:
    ```powershell
    kubectl apply -f k8s/demo-scenarios/2-canary-success-v2.yaml
    ```
*   **Teammate 4 (SRE Narration):** "Argo Rollouts routes 20% of traffic to Version 2.0. Prometheus scrapes our metrics for 25 seconds... error rate is 0%! Because the health checks pass, Argo Rollouts automatically **promotes** the release to 100% without human intervention!"
*   **Visual on Screen:** Notice how the application dashboard (`http://localhost:8000`) dynamically changes from Neon Blue to **Neon Green (v2.0 Clean)**!

### Part 4: Side B (The Risky Release) — Automated Rollback of Version 3.0 (Teammate 4)
*   **Teammate 2 (Dev):** "Now, let's look at the other side of the coin: what happens when a developer accidentally deploys a critical bug that causes HTTP 500 errors and DB pool leaks."
*   **Action:** Teammate 1 applies Scenario 3:
    ```powershell
    kubectl apply -f k8s/demo-scenarios/3-canary-rollback-v3.yaml
    ```
*   **Teammate 4 (SRE Narration):** "Argo Rollouts routes 20% of live traffic to the buggy Version 3.0. When we refresh our application tab, notice that 1 in 5 users hit our bright red `⚠️ HTTP 500` error screen."
*   *(Wait about 15 seconds)*
*   **Teammate 4:** "Our CNCF Prometheus query just detected that the error rate breached our 5% safety threshold. In 3, 2, 1..."
*   **Visual on Screen:** The Canary turns RED on Argo Rollouts, automatically terminates, and routing snaps 100% back to the safe **Neon Green Version 2.0**!
*   **Teammate 1:** "The system detected the anomaly and autonomously healed itself. Zero customer outages and zero manual intervention required."

### Part 5: The AI Log RCA Detective (PS7 Demo - Teammate 3)
*   **Teammate 3:** "While Argo Rollouts saved our customers by rolling back, as developers, we still need to know *why* that release failed. That is where our **Problem Statement 7 AI Log RCA Command Center** comes in."
*   **Teammate 1:** Opens Tab 3 in browser: `http://localhost:8001` (The SRE Command Center UI).
*   **Teammate 3:** "Our RCA service ingested the scattered container logs from the failed Canary pods, stripped timestamps, and clustered the errors into recurring failure modes. Notice our KPI cards and structured failure analysis: we isolated the primary bottleneck (67% DB pool leak) and generated a structured SRE Remediation Playbook with exact config and code line fixes!"

---

## 🏆 Hackathon Checklist Requirements Satisfied (Double Score!)
- [x] **Docker Products:** Docker Desktop/Engine, Docker Build Cloud, Docker Scout, Docker Hub.
- [x] **CNCF Graduated/Incubating:** Kubernetes (Grad), Prometheus (Grad), Argo CD (Grad), Argo Rollouts (Incubating).
- [x] **AI Agent Framework:** Log RCA engine clustering failure modes and synthesizing plain-English root cause summaries (PS7).
- [x] **Realistic Scope:** 3 microservices (App, Loadgen, AI RCA Command Center) working flawlessly together.
