# CircleCI Demo Platform

A multi-service demo application designed to showcase CircleCI platform capabilities including dynamic configuration, test splitting, parallelism, Docker layer caching, and workflow orchestration.

> **Note:** This is a demo/sandbox application for CircleCI feature demonstrations. It is not production code and should not be used as a reference for production architecture.

## Architecture

The platform consists of three services and a shared library:

```
circleci-demo-platform/
├── api/       Flask REST API (backend)
├── worker/    Background task processor (middleware)
├── web/       Flask frontend (UI)
└── shared/    Shared utilities (config, health checks)
```

### API Service

Flask-based REST API providing CRUD operations for items.

| Endpoint          | Method | Description              |
|-------------------|--------|--------------------------|
| `/health`         | GET    | Liveness check           |
| `/items`          | GET    | List all items           |
| `/items`          | POST   | Create a new item        |
| `/items/<id>`     | GET    | Get a single item by ID  |

Items are stored in-memory. Query parameter `?category=` filters the list.

### Worker Service

Background task processor with retry logic and exponential backoff. Processes tasks from an in-memory queue with configurable retry count and delay.

### Web Frontend

Flask app that renders HTML pages and proxies data from the API service. Falls back to mock data when the API is unreachable.

| Route        | Description                          |
|-------------|---------------------------------------|
| `/`          | Home page with service overview      |
| `/health`    | Health check                         |
| `/dashboard` | Dashboard showing items from the API |

### Shared Library

Common utilities consumed by all services:

- **`config.py`** — Environment-based configuration with per-service prefixes
- **`health.py`** — Standardized health check and readiness check responses

## Running Locally

### Individual Services

```bash
# Install dependencies
pip install -r api/requirements.txt

# Run the API
python api/app.py

# Run the worker
python worker/worker.py

# Run the web frontend (set API_URL to point at the API)
API_URL=http://localhost:5000 python web/app.py
```

### With Docker

```bash
# Build and run the API
docker build -t demo-api ./api
docker run -p 5000:5000 demo-api

# Build and run the web frontend
docker build -t demo-web ./web
docker run -p 5002:5002 -e API_URL=http://host.docker.internal:5000 demo-web
```

## Running Tests

Each service has its own test suite using pytest. Run them from the project root:

```bash
# All API tests
python -m pytest api/tests/ -v

# All worker tests
python -m pytest worker/tests/ -v

# All web tests
python -m pytest web/tests/ -v

# Everything
python -m pytest api/tests/ worker/tests/ web/tests/ -v
```

### Test Structure

Each service contains:

- **Unit tests** — Core functionality (health checks, CRUD, retry logic)
- **Validation tests** — Input validation and error handling
- **Flaky tests** — Intentionally intermittent tests that simulate real-world conditions (network timeouts, race conditions, memory pressure). These are useful for demonstrating CircleCI's flaky test detection and rerun capabilities.

### Test Counts

| Service | Tests | Includes Flaky |
|---------|-------|----------------|
| API     | ~19   | 3              |
| Worker  | ~16   | 2              |
| Web     | ~16   | 0              |
| **Total** | **~51** | **5**       |

The test suite is designed to work well with CircleCI's test splitting and parallelism features (target: `parallelism: 4`).

## Configuration

Services are configured via environment variables:

| Variable            | Default              | Description                  |
|---------------------|----------------------|------------------------------|
| `API_HOST`          | `0.0.0.0`           | API bind host                |
| `API_PORT`          | `5000`               | API bind port                |
| `API_DEBUG`         | `false`              | Enable Flask debug mode      |
| `API_URL`           | `http://localhost:5000` | URL the web frontend uses to reach the API |
| `WEB_PORT`          | `5002`               | Web frontend bind port       |
| `WORKER_LOG_LEVEL`  | `INFO`               | Worker log verbosity         |
| `APP_VERSION`       | `0.1.0`              | Application version string   |

## CircleCI Configuration

CircleCI pipeline configuration is coming soon. The planned setup will demonstrate:

- Dynamic configuration with `setup` workflows and `path-filtering`
- Per-service Docker image builds with layer caching
- Test splitting across parallel containers
- Flaky test detection and automatic reruns
- Workspace and artifact management
- Approval gates for deployments

## License

This project is a demo application and is provided as-is for demonstration purposes.
