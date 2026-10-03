import os
import json
import uuid
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

DATA_DIR = os.environ.get("DATA_DIR", "/app/data")
NODE_ID = os.environ.get("NODE_ID", "app")
PEERS = [p for p in os.environ.get("PEERS", "").split(",") if p]
FILE = os.path.join(DATA_DIR, f"{NODE_ID}.jsonl")
os.makedirs(DATA_DIR, exist_ok=True)


def load():
    if not os.path.exists(FILE):
        return []
    with open(FILE) as f:
        return [json.loads(line) for line in f if line.strip()]


def save(msg):
    with open(FILE, "a") as f:
        f.write(json.dumps(msg) + "\n")


@app.route("/send", methods=["POST"])
def send():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON inválido"}), 400

    msg = {"id": str(uuid.uuid4()), "origin": NODE_ID, "data": data}
    save(msg)

    replicated = {}
    for peer in PEERS:
        try:
            r = requests.post(f"http://{peer}:5000/replicate", json=msg, timeout=3)
            r.raise_for_status()
            replicated[peer] = "ok"
        except requests.RequestException as e:
            replicated[peer] = f"falhou: {e}"

    return jsonify({"status": "ok", "id": msg["id"], "replicated": replicated}), 201


@app.route("/replicate", methods=["POST"])
def replicate():
    msg = request.get_json(silent=True)
    if not msg or "id" not in msg:
        return jsonify({"error": "mensagem inválida"}), 400
    if msg["id"] not in {m["id"] for m in load()}:
        save(msg)
    return jsonify({"status": "ok"}), 201


@app.route("/messages", methods=["GET"])
def messages():
    return jsonify(load())


@app.route("/verify", methods=["GET"])
def verify():
    mine = {m["id"] for m in load()}
    result = {}
    for peer in PEERS:
        try:
            r = requests.get(f"http://{peer}:5000/messages", timeout=3)
            r.raise_for_status()
            theirs = {m["id"] for m in r.json()}
            result[peer] = {
                "ok": mine == theirs,
                "faltando_no_peer": sorted(mine - theirs),
                "faltando_aqui": sorted(theirs - mine),
            }
        except requests.RequestException as e:
            result[peer] = {"ok": False, "erro": str(e)}
    return jsonify({"node": NODE_ID, "total": len(mine), "peers": result})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)