"""Flask REST API service — items CRUD with health checks."""

import sys
import os
import uuid
from flask import Flask, jsonify, request

# Allow imports from the project root so shared/ is reachable.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.config import get_config
from shared.health import health_check

app = Flask(__name__)
config = get_config("api")

# In-memory data store (demo purposes only).
ITEMS: dict[str, dict] = {
    "1": {"id": "1", "name": "Widget A", "category": "hardware", "price": 29.99},
    "2": {"id": "2", "name": "Widget B", "category": "software", "price": 49.99},
    "3": {"id": "3", "name": "Gadget C", "category": "hardware", "price": 14.50},
}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/health")
def health():
    """Liveness / health endpoint."""
    return jsonify(health_check("api"))


@app.route("/items", methods=["GET"])
def list_items():
    """Return all items, with optional category filter."""
    category = request.args.get("category")
    items = list(ITEMS.values())
    if category:
        items = [i for i in items if i["category"] == category]
    return jsonify({"items": items, "count": len(items)})


@app.route("/items", methods=["POST"])
def create_item():
    """Create a new item. Requires 'name' and 'price' in JSON body."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    errors = _validate_item(data)
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 422

    item_id = str(uuid.uuid4())[:8]
    item = {
        "id": item_id,
        "name": data["name"],
        "category": data.get("category", "general"),
        "price": float(data["price"]),
    }
    ITEMS[item_id] = item
    return jsonify(item), 201


@app.route("/items/<item_id>", methods=["GET"])
def get_item(item_id: str):
    """Retrieve a single item by ID."""
    item = ITEMS.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    return jsonify(item)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _validate_item(data: dict) -> list[str]:
    """Return a list of validation error strings (empty means valid)."""
    errors = []
    if "name" not in data or not str(data["name"]).strip():
        errors.append("'name' is required and must be non-empty")
    if "price" not in data:
        errors.append("'price' is required")
    else:
        try:
            price = float(data["price"])
            if price < 0:
                errors.append("'price' must be non-negative")
        except (TypeError, ValueError):
            errors.append("'price' must be a number")
    return errors


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host=config["host"], port=config["port"], debug=config["debug"])

# api v0.1.1
