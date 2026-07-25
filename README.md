# Hackathon Playbook: The Risky Release (Zero-Downtime Pipeline)

This document is the master playbook for your 4-person team. It outlines the end-to-end process, what each member needs to do before the presentation, and the exact script for the live demo.

---

## 🛠️ Phase 1: Setup & Distribution (Before the Demo)

### Teammate 3: Security & CI/CD (The Repository Owner)
**Role:** Manages the Git repository and CI pipeline.
1. Create a new public GitHub repository.
2. Push all the files from this folder (`app/`, `k8s/`, `loadgen/`, `.github/`) to the repository.
3. Go to the GitHub repository **Settings > Secrets and variables > Actions**.
4. Add two Repository Secrets:
   - `DOCKERHUB_USERNAME`: Your Docker Hub username.
   - `DOCKERHUB_TOKEN`: A Docker Hub Personal Access Token.
5. Ensure the GitHub Action (`CI Pipeline`) runs successfully on the first push, building the image via **Docker Build Cloud**, scanning it with **Docker Scout**, and pushing it to Docker Hub.

### Teammate 1: Platform Engineer (The Docker Machine)
**Role:** Hosts the infrastructure since this is the only machine with Docker.
1. Open Docker Desktop and enable **Kubernetes** in the settings (or use `k3d`).
2. Open your terminal and install the core CNCF controllers:
   ```bash
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
3. Connect the cluster to Teammate 3's GitHub repository. Apply the initial manifests manually for the first time:
   ```bash
   kubectl apply -f k8s/argo-rollouts/service.yaml
   kubectl apply -f k8s/argo-rollouts/analysis.yaml
   kubectl apply -f k8s/monitoring/servicemonitor.yaml
   kubectl apply -f k8s/argo-rollouts/rollout.yaml
   ```
4. Start the Load Generator locally so there is continuous traffic:
   ```bash
   docker build -t loadgen:latest ./loadgen
   kubectl run loadgen --image=loadgen:latest --image-pull-policy=Never
   ```
5. Port-forward the Argo Rollouts Dashboard so it's ready for the presentation:
   ```bash
   kubectl argo rollouts dashboard -p 3100
   ```

### Teammate 2: Application Developer
**Role:** Application logic and testing.
1. Familiarize yourself with `app/main.py`.
2. Notice the `/metrics` endpoint which exposes RED (Rate, Error, Duration) metrics using the Prometheus client.
3. Notice the `SIMULATE_FAILURE` environment variable. When true, it causes 20% of requests to return an `HTTP 500` error and injects artificial latency. This is your "Risky Release" trigger.

### Teammate 4: SRE & Observability
**Role:** Explains the Progressive Delivery logic.
1. Review `k8s/argo-rollouts/rollout.yaml`. Understand that it sends 20% of traffic to the new version and pauses for 30 seconds.
2. Review `k8s/argo-rollouts/analysis.yaml`. Understand the PromQL query: it divides the rate of HTTP 500 errors by the total request rate. If this ratio exceeds `0.05` (5%), the deployment fails.

---

## 🎤 Phase 2: The Live Presentation (The Script)

During the judging phase, everyone has a speaking part to prove depth of knowledge.

### Part 1: The Architecture (Teammate 3 & 4)
*   **Teammate 3 (CI/Security):** Explain how you solved the "Lack of Local Docker" problem. "Since only one of us has Docker, we used GitOps. When we push code, **Docker Build Cloud** builds our images remotely. We then strictly enforce security using **Docker Scout** in our CI pipeline to block vulnerabilities before they ever hit the registry."
*   **Teammate 4 (SRE):** Explain the CNCF stack. "For deployment, we use **Kubernetes** and **Argo CD**. To solve the 'Risky Release' problem, we use **Argo Rollouts** for Canary deployments, pulling live telemetry from **Prometheus**."

### Part 2: Triggering the Risky Release (Teammate 2)
*   **Teammate 1** shares their screen, showing the **Argo Rollouts Dashboard** (`http://localhost:3100`) with the stable version running green.
*   **Teammate 2 (Dev):** "I'm going to simulate a developer pushing a bad feature." 
*   **Action:** Teammate 2 opens the GitHub repository in their browser, edits `k8s/argo-rollouts/rollout.yaml`, changes `SIMULATE_FAILURE` to `"true"`, changes the image tag (or just adds a dummy annotation to trigger a change), and commits the file directly to `main`.

### Part 3: The Autonomous Rollback (Teammate 1 & 4)
*   **Teammate 1 (Screen Sharer):** Refreshes/syncs Argo CD. The Argo Rollouts Dashboard immediately shows a new Canary revision spinning up, taking exactly 20% of the traffic.
*   **Teammate 4 (SRE Narration):** "Argo Rollouts has now routed 20% of live traffic to the new version. Behind the scenes, the Load Generator is hitting the pods, and the new pods are throwing HTTP 500 errors."
*   *(Wait about 10-20 seconds)*
*   **Teammate 4:** "Our `AnalysisTemplate` is querying Prometheus. It just detected the 5% error rate threshold was breached."
*   **Visual on Screen:** The Argo Rollouts Dashboard turns RED on the Canary, automatically scales the buggy pods down to 0, and restores 100% of the routing back to the original stable version.
*   **Teammate 1:** "As you can see, the system autonomously detected the anomaly and healed itself. Zero downtime, zero manual rollback required."

---

## 🏆 Hackathon Checklist Requirements Satisfied
- [x] **Docker Products:** Docker Desktop/Engine, Docker Build Cloud, Docker Scout, Docker Hub.
- [x] **CNCF Graduated/Incubating:** Kubernetes (Grad), Prometheus (Grad), Argo CD (Grad), Argo Rollouts (Incubating).
- [x] **Realistic Scope:** 2 small services (App + Loadgen) working flawlessly.
- [x] **Depth of Automation:** Full CI/CD + autonomous PromQL-driven rollback without human intervention.
