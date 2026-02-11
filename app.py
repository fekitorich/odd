import os
import sys
from flask import Flask, jsonify, render_template, request
from scanner import run_scan

app = Flask(__name__)

# Sua chave hardcoded para não haver erro de leitura
FIXED_KEY = "ac611e223968599cffdcd6c1944f9958"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json() or {}
    final_key = (data.get("apiKey") or "").strip() or FIXED_KEY

    try:
        # Chama o seu scanner original
        result = run_scan(
            api_key=final_key,
            sports=data.get("sports") or [],
            regions=data.get("regions") or ["us"],
            stake_amount=float(data.get("stake") or 100),
            commission_rate=float(data.get("commission") or 0) / 100.0
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

# Força a porta no ambiente do Railway
port = int(os.environ.get("PORT", 8080))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
