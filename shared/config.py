"""Shared configuration helpers for all services."""

import os


def get_config(service_name: str) -> dict:
    """Build a configuration dict from environment variables.

    Each service can override defaults via env vars prefixed with the
    uppercased service name (e.g. API_PORT, WORKER_LOG_LEVEL).
    """
    prefix = service_name.upper()
    return {
        "service": service_name,
        "host": os.getenv(f"{prefix}_HOST", "0.0.0.0"),
        "port": int(os.getenv(f"{prefix}_PORT", "5000")),
        "debug": os.getenv(f"{prefix}_DEBUG", "false").lower() == "true",
        "log_level": os.getenv(f"{prefix}_LOG_LEVEL", "INFO"),
        "api_url": os.getenv("API_URL", "http://localhost:5000"),
    }


def get_version() -> str:
    """Return the current application version."""
    return os.getenv("APP_VERSION", "0.1.0")
