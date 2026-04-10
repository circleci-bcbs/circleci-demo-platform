"""Shared health check logic for all services."""

import time

_start_time = time.time()


def health_check(service_name: str) -> dict:
    """Return a standardized health check response.

    Includes service identity, status, and uptime in seconds.
    """
    return {
        "status": "ok",
        "service": service_name,
        "uptime_seconds": round(time.time() - _start_time, 2),
    }


def readiness_check(dependencies: list[dict]) -> dict:
    """Check readiness by verifying all listed dependencies.

    Each dependency dict should have 'name' and 'healthy' keys.
    Returns overall status and per-dependency breakdown.
    """
    all_healthy = all(dep.get("healthy", False) for dep in dependencies)
    return {
        "ready": all_healthy,
        "dependencies": dependencies,
    }
