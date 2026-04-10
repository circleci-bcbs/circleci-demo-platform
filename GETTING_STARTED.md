# Getting Started

Setup guide for onboarding the Platform Services project into CircleCI. Covers project configuration, pipeline definitions, triggers, and operational details.

## Prerequisites

- CircleCI account with the [GitHub App](https://circleci.com/docs/guides/integration/using-the-circleci-github-app-in-an-oauth-org/) installed
- The repository available in your GitHub org
- Organization admin access for URL orb allow-list configuration

---

## 1. Set Up the Project

1. In the [CircleCI web app](https://app.circleci.com), select your org
2. Go to **Projects** and find the repository
3. Click **Set Up Project**

> **Docs**: [Getting Started](https://circleci.com/docs/guides/getting-started/getting-started/)

---

## 2. Create Pipeline Definitions

Create five pipelines in **Project Settings > Project Setup > Add Pipeline**:

| Pipeline Name | Config File Path | Description |
|---|---|---|
| `dynamic-config` | `.circleci/config.yml` | Setup workflow with path-filtering |
| `api-pipeline` | `.circleci/api-pipeline.yml` | API service build, test, deploy |
| `worker-pipeline` | `.circleci/worker-pipeline.yml` | Worker service build, test, deploy |
| `web-pipeline` | `.circleci/web-pipeline.yml` | Web service build, test, deploy |
| `scale-demo` | `.circleci/scale-demo.yml` | CI infrastructure load test |

For all five, set both **Config Source** and **Checkout Source** to this repository.

> **Docs**: [Set Up a Pipeline](https://circleci.com/docs/guides/orchestrate/pipelines/#add-or-edit-a-pipeline)

---

## 3. Create Triggers

Only the `dynamic-config` pipeline needs an automatic trigger. It handles routing to the correct service pipeline based on which directories have changed files.

1. In the `dynamic-config` pipeline box, click **GitHub trigger +**
2. Set **Event** to **All pushes**
3. Click **Save**

The per-service pipelines and scale-demo have no automatic triggers. They run either through the dynamic config routing or via manual trigger from the UI/API.

> **Docs**: [Set Up Triggers](https://circleci.com/docs/guides/orchestrate/set-up-triggers/)

---

## 4. Configure URL Orb Allow-List

The API pipeline uses a shared [URL orb](https://circleci.com/docs/orbs/author/create-test-and-use-url-orbs/) for deploy markers and common commands.

1. Go to **Organization Settings > Orbs**
2. Add to the allow-list: `https://raw.githubusercontent.com/circleci-bcbs/shared-orbs/main/`

> **Docs**: [Managing URL Orb Allow Lists](https://circleci.com/docs/orbs/use/managing-url-orbs-allow-lists/)

---

## 5. Enable Dynamic Configuration

1. Go to **Project Settings > Advanced**
2. Enable **Setup Workflows**

This allows the setup workflow in `config.yml` to use the `path-filtering` orb and route to continuation configs.

> **Docs**: [Dynamic Config](https://circleci.com/docs/guides/orchestrate/dynamic-config/)

---

## How the Pipeline Works

### Path-filtered routing

When code is pushed, the `dynamic-config` pipeline runs a setup workflow that compares the changed files against a path mapping:

| Path | Routes to |
|---|---|
| `api/.*` | `api-pipeline.yml` |
| `worker/.*` | `worker-pipeline.yml` |
| `web/.*` | `web-pipeline.yml` |
| `shared/.*` | All three service pipelines (shared code affects every service) |
| No match | `no-updates.yml` (no-op job, consumes zero credits) |

Only the affected service's pipeline runs. A commit that touches only `worker/` will build and test the worker service — the API and web services are skipped. A commit that only changes `.circleci/` or `README.md` runs a no-op job that completes instantly.

### Test splitting

Each service pipeline splits its pytest suite across parallel containers using `circleci tests split --split-by=timings`. On the first run, tests are split by filename. After CircleCI collects timing data, subsequent runs balance test duration across containers for optimal speed.

The API service uses 4 containers (larger test suite), while worker and web use 2 each.

### Docker builds

Each service has a multi-stage Dockerfile. Docker Layer Caching (`docker_layer_caching: true`) ensures unchanged layers are reused between builds, significantly reducing build times after the first run.

### Deploy tracking

Deploy jobs use the shared URL orb's `deploy-marker-plan` and `deploy-marker-finalize` commands to track each deployment in the CircleCI [Deploys UI](https://circleci.com/docs/guides/deploy/deployment-overview/). This provides a timeline of what was deployed, when, and whether it succeeded.

### Handling intermittent test failures

The test suite includes tests that simulate intermittent conditions (network timeouts, connection pool exhaustion, retry convergence). These occasionally fail, which is expected. The pipeline handles this with `max_auto_reruns: 5` — failed workflows automatically retry up to 5 times.

CircleCI's [Insights](https://circleci.com/docs/guides/insights/flaky-tests/) dashboard detects these as flaky tests over time, giving visibility into test reliability without blocking the pipeline.

### CI infrastructure load testing

The `scale-demo` pipeline runs 50 parallel containers simultaneously. It's useful for validating that the CircleCI compute layer can handle burst workloads with zero queue time. Trigger it manually when needed — it has no automatic trigger.

---

## Operational Reference

### Manual triggers

Trigger any pipeline via the UI (**Trigger Pipeline** button) or CLI:

```bash
circleci pipeline run <org-slug> <project-id> \
  --pipeline-definition-id <pipeline-def-id> \
  --config-branch main \
  --checkout-branch main
```

### Pipeline definition IDs

| Pipeline | Definition ID |
|---|---|
| `dynamic-config` | `ffe78769-113d-45a8-bac5-f4a7c425db1c` |
| `api-pipeline` | `783b9f7e-2ba7-4f80-8459-ff63417e12ff` |
| `worker-pipeline` | `2d0f3450-4e83-44d5-ac65-18eb5136d1a0` |
| `web-pipeline` | `663c90b8-374b-468f-a4f0-e67caa7132f3` |
| `scale-demo` | `7da7c9e7-a130-42ac-884f-718352789f21` |

### Verifying path-filtering

To confirm routing works correctly, push a change to a single service directory and verify only that service's workflow runs:

```bash
echo "# update" >> worker/worker.py
git add worker/ && git commit -m "chore: worker update" && git push
# Expected: only worker-build-test-deploy workflow runs
```

### Viewing test insights

After several pipeline runs, test analytics are available at **Insights > Tests** in the CircleCI web app. The dashboard shows test durations, failure rates, and automatically flagged flaky tests.
