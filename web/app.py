"""Simple Flask frontend that renders HTML templates and proxies to the API."""

import sys
import os
import requests
from flask import Flask, jsonify, render_template_string

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.config import get_config
from shared.health import health_check

app = Flask(__name__)
config = get_config("web")

API_URL = config["api_url"]

# ---------------------------------------------------------------------------
# HTML Templates (inline for simplicity)
# ---------------------------------------------------------------------------

HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>CircleCI Demo Platform</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               max-width: 800px; margin: 40px auto; padding: 0 20px; color: #1a1a1a; }
        h1 { color: #161e2e; }
        .badge { display: inline-block; padding: 4px 12px; border-radius: 12px;
                 font-size: 0.85em; font-weight: 600; }
        .badge-ok { background: #d1fae5; color: #065f46; }
        .card { border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px;
                margin: 16px 0; }
        a { color: #3b82f6; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>CircleCI Demo Platform</h1>
    <p>A multi-service application for demonstrating CircleCI capabilities.</p>

    <div class="card">
        <h2>Services</h2>
        <ul>
            <li><strong>API</strong> &mdash; REST backend for item management</li>
            <li><strong>Worker</strong> &mdash; Background task processor</li>
            <li><strong>Web</strong> &mdash; This frontend <span class="badge badge-ok">running</span></li>
        </ul>
    </div>

    <div class="card">
        <h2>Links</h2>
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/health">Health Check</a></li>
        </ul>
    </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Dashboard - CircleCI Demo Platform</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               max-width: 800px; margin: 40px auto; padding: 0 20px; color: #1a1a1a; }
        h1 { color: #161e2e; }
        table { width: 100%%; border-collapse: collapse; margin: 16px 0; }
        th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid #e5e7eb; }
        th { background: #f9fafb; font-weight: 600; }
        .status { padding: 2px 10px; border-radius: 10px; font-size: 0.85em; }
        .status-ok { background: #d1fae5; color: #065f46; }
        .status-error { background: #fee2e2; color: #991b1b; }
        a { color: #3b82f6; text-decoration: none; }
    </style>
</head>
<body>
    <h1>Dashboard</h1>
    <p><a href="/">&larr; Home</a></p>

    <h2>Items ({{ item_count }})</h2>
    <table>
        <thead>
            <tr><th>ID</th><th>Name</th><th>Category</th><th>Price</th></tr>
        </thead>
        <tbody>
        {% for item in items %}
            <tr>
                <td>{{ item.id }}</td>
                <td>{{ item.name }}</td>
                <td>{{ item.category }}</td>
                <td>${{ "%.2f"|format(item.price) }}</td>
            </tr>
        {% endfor %}
        </tbody>
    </table>

    <h2>API Status</h2>
    <p>
        {% if api_healthy %}
            <span class="status status-ok">Connected</span>
        {% else %}
            <span class="status status-error">Unreachable</span>
        {% endif %}
    </p>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    """Render the home page."""
    return render_template_string(HOME_TEMPLATE)


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify(health_check("web"))


@app.route("/dashboard")
def dashboard():
    """Render dashboard with items from the API (falls back to mock data)."""
    items, api_healthy = _fetch_items()
    return render_template_string(
        DASHBOARD_TEMPLATE,
        items=items,
        item_count=len(items),
        api_healthy=api_healthy,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _fetch_items() -> tuple[list[dict], bool]:
    """Try to fetch items from the API service; return mock data on failure."""
    try:
        resp = requests.get(f"{API_URL}/items", timeout=3)
        resp.raise_for_status()
        data = resp.json()
        return data.get("items", []), True
    except Exception:
        # Fallback mock data so the dashboard always renders.
        return [
            {"id": "mock-1", "name": "Widget A", "category": "hardware", "price": 29.99},
            {"id": "mock-2", "name": "Widget B", "category": "software", "price": 49.99},
            {"id": "mock-3", "name": "Gadget C", "category": "hardware", "price": 14.50},
        ], False


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host=config["host"], port=int(os.environ.get("WEB_PORT", 5002)), debug=config["debug"])
