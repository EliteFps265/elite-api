from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import uuid
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")


# ---------- UTILIDADES ----------
def load_users():
    if not os.path.exists(USERS_FILE):
        return {"users": [], "licenses": []}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ---------- ROTAS ----------
@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "service": "Elite API",
        "time": datetime.utcnow().isoformat()
    })


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    db = load_users()

    for user in db["users"]:
        if user["username"] == username and user["password"] == password:
            return jsonify({
                "success": True,
                "message": "Login realizado com sucesso"
            })

    return jsonify({
        "success": False,
        "message": "Usuário ou senha inválidos"
    }), 401


@app.route("/license/create", methods=["POST"])
def create_license():
    data = request.json
    username = data.get("username")
    days = int(data.get("days", 30))

    license_key = str(uuid.uuid4()).upper()
    expires_at = (datetime.utcnow() + timedelta(days=days)).isoformat()

    db = load_users()

    db["licenses"].append({
        "username": username,
        "license": license_key,
        "expires_at": expires_at
    })

    save_users(db)

    return jsonify({
        "success": True,
        "license": license_key,
        "expires_at": expires_at
    })


@app.route("/license/validate", methods=["POST"])
def validate_license():
    data = request.json
    license_key = data.get("license")

    db = load_users()

    for lic in db["licenses"]:
        if lic["license"] == license_key:
            if datetime.fromisoformat(lic["expires_at"]) > datetime.utcnow():
                return jsonify({
                    "valid": True,
                    "username": lic["username"]
                })
            else:
                return jsonify({
                    "valid": False,
                    "reason": "Licença expirada"
                })

    return jsonify({
        "valid": False,
        "reason": "Licença não encontrada"
    }), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)