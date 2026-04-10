# Getting Started

Step-by-step guide to setting up the CircleCI Demo Platform project. This covers project onboarding, pipeline definitions, triggers, and how to demo each feature.

## Prerequisites

- A CircleCI account with the [GitHub App](https://circleci.com/docs/guides/integration/using-the-circleci-github-app-in-an-oauth-org/) installed
- The [circleci-demo-platform](https://github.com/circleci-bcbs/circleci-demo-platform) repo in your GitHub org
- The URL orb allow-list configured (see Step 4)

---

## 1. Set Up the Project

1. In the [CircleCI web app](https://app.circleci.com), select your org
2. Go to **Projects** and find `circleci-demo-platform`
3. Click **Set Up Project** (or use the CLI: `circleci project create circleci <org-slug> --name circleci-demo-platform`)

---

## 2. Create Pipeline Definitions

Create five pipeline definitions in **Project Settings > Project Setup > Add Pipeline**:

| Pipeline Name | Config Source | Config File Path | Checkout Source |
|---|---|---|---|
| `dynamic-config` | `circleci-demo-platform` | `.circleci/config.yml` | `circleci-demo-platform` |
| `api-pipeline` | `circleci-demo-platform` | `.circleci/api-pipeline.yml` | `circleci-demo-platform` |
| `worker-pipeline` | `circleci-demo-platform` | `.circleci/worker-pipeline.yml` | `circleci-demo-platform` |
| `web-pipeline` | `circleci-demo-platform` | `.circleci/web-pipeline.yml` | `circleci-demo-platform` |
| `scale-demo` | `circleci-demo-platform` | `.circleci/scale-demo.yml` | `circleci-demo-platform` |

> **Docs**: [Set Up a Pipeline](https://circleci.com/docs/guides/orchestrate/pipelines/#add-or-edit-a-pipeline)

---

## 3. Create Triggers

Only the `dynamic-config` pipeline needs an automatic trigger. The others are triggered manually or via the dynamic config routing.

### Dynamic Config Trigger (all pushes)

1. In the `dynamic-config` pipeline box, click **GitHub trigger +**
2. Configure:

| Field | Value |
|---|---|
| **Trigger Name** | `all-pushes` |
| **Event** | **All pushes** |
| **Event Source** | `circleci-demo-platform` |

3. Click **Save**

### Per-Service Pipelines (manual only)

No triggers needed — they are either routed to by the dynamic config pipeline or triggered manually via the **Trigger Pipeline** button or API.

### Scale Demo (manual only)

No trigger. Fire manually from the UI or API to demo 50 parallel containers.

> **Docs**: [Set Up Triggers](https://circleci.com/docs/guides/orchestrate/set-up-triggers/) | [GitHub Trigger Event Options](https://circleci.com/docs/guides/orchestrate/github-trigger-event-options/)

---

## 4. Configure URL Orb Allow-List

The API pipeline uses a shared [URL orb](https://circleci.com/docs/orbs/author/create-test-and-use-url-orbs/) from `circleci-bcbs/shared-orbs`.

1. Go to **Organization Settings > Orbs**
2. Add to the allow-list: `https://raw.githubusercontent.com/circleci-bcbs/shared-orbs/main/`

> **Docs**: [Managing URL Orb Allow Lists](https://circleci.com/docs/orbs/use/managing-url-orbs-allow-lists/)

---

## 5. Enable Dynamic Config

Dynamic configuration must be enabled for the project.

1. Go to **Project Settings > Advanced**
2. Enable **Setup Workflows**

This allows the `config.yml` setup workflow to use the `setup: true` directive and the `path-filtering` orb to route to continuation configs.

> **Docs**: [Dynamic Config](https://circleci.com/docs/guides/orchestrate/dynamic-config/)

---

## How to Demo Each Feature

### Dynamic Configuration (path-filtering)

**What to show:** Push a change to only one service directory. Only that service's pipeline runs.

```bash
# Change only the worker
echo "# bump" >> worker/worker.py
git add worker/ && git commit -m "chore: worker update" && git push

# Result: dynamic-config detects worker/ changed -> runs worker-pipeline.yml only
```

Point out in the UI: the setup workflow runs first, detects what changed, then routes to the correct continuation config.

### Test Splitting

**What to show:** The API test job runs with `parallelism: 4`, splitting 22 tests across 4 containers.

1. Trigger the `api-pipeline` manually
2. Click into the **API Tests (split)** job
3. Show the 4 parallel containers in the job view
4. Each container runs a subset of tests

On subsequent runs, CircleCI uses timing data to balance test durations across containers.

### Flaky Test Detection

**What to show:** Navigate to **Insights > Tests** for the project. After multiple runs, CircleCI flags the 5 intentionally flaky tests.

The flaky tests have realistic names:
- `test_intermittent_network_timeout`
- `test_race_condition_on_write`
- `test_connection_pool_recovery`
- `test_queue_drain_under_memory_pressure`
- `test_retry_backoff_jitter_convergence`

`max_auto_reruns: 5` means failed workflows automatically retry, so flaky tests don't block the pipeline permanently.

### Docker Layer Caching

**What to show:** Compare two consecutive runs of a Docker build job.

1. First run: full Docker build (all layers pulled/built)
2. Second run: cached layers reused, significantly faster

Look at the **Docker Build** job timing — the second run should be noticeably faster.

### Scale Demo (parallelism: 50)

**What to show:** Trigger the `scale-demo` pipeline manually.

1. In CircleCI UI, click **Trigger Pipeline** on the `scale-demo` pipeline
2. Watch 50 containers spin up simultaneously
3. All containers start with zero queue time

This demonstrates CircleCI's ability to scale compute on demand without capacity planning.

### Deploy Markers

**What to show:** After a deploy job completes, go to **Deploys** in the sidebar.

The timeline shows each deployment with environment, component, version, and status. The API pipeline uses the shared URL orb for deploy markers.

### URL Orbs (cross-project config reuse)

**What to show:** Open the `api-pipeline.yml` and point to the orb import:

```yaml
orbs:
  platform: https://raw.githubusercontent.com/circleci-bcbs/shared-orbs/main/bcbsm-platform-tools.yml
```

Then show the orb being used:
```yaml
- platform/deploy-marker-plan:
    deploy-name: "api-deploy"
    ...
- platform/deploy-marker-finalize:
    deploy-name: "api-deploy"
```

The same orb is shared across multiple projects. Changes to the orb propagate automatically (5-minute cache).

### Auto-Reruns

**What to show:** Find a pipeline where a flaky test caused a failure. The workflow view shows multiple attempts — failed runs followed by a successful rerun.

The `max_auto_reruns: 5` setting in the workflow config handles this automatically.

---

## Manual Triggers

### Trigger a specific service pipeline

```bash
# Via CircleCI UI: Trigger Pipeline button > select the pipeline

# Via CLI:
circleci pipeline run <org-slug> <project-id> \
  --pipeline-definition-id <api-pipeline-def-id> \
  --config-branch main \
  --checkout-branch main
```

### Trigger the scale demo

```bash
circleci pipeline run <org-slug> <project-id> \
  --pipeline-definition-id <scale-demo-def-id> \
  --config-branch main \
  --checkout-branch main
```

---

## Pipeline Definition IDs

For reference when using the CLI or API:

| Pipeline | Definition ID |
|---|---|
| `dynamic-config` | `ffe78769-113d-45a8-bac5-f4a7c425db1c` |
| `api-pipeline` | `783b9f7e-2ba7-4f80-8459-ff63417e12ff` |
| `worker-pipeline` | `2d0f3450-4e83-44d5-ac65-18eb5136d1a0` |
| `web-pipeline` | `663c90b8-374b-468f-a4f0-e67caa7132f3` |
| `scale-demo` | `7da7c9e7-a130-42ac-884f-718352789f21` |
