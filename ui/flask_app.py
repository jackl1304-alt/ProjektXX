from __future__ import annotations

from flask import Flask, jsonify, request

from .settings_manager import load_settings, save_settings


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/settings")
    def get_settings():
        return jsonify(load_settings())

    @app.post("/settings")
    def update_settings():
        payload = request.get_json(force=True)
        if not isinstance(payload, dict):
            return jsonify({"error": "Ungültige Payload"}), 400
        save_settings(payload)
        return jsonify({"status": "ok"})

    return app


if __name__ == "__main__":
    create_app().run(debug=True)

