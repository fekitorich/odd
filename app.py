import os
import sys
from flask import Flask, jsonify, render_template, request
from scanner import run_scan

app = Flask(__name__)

# Sua API Key gravada
FIXED_KEY = "ac611e223968599cffdcd6c1944f9958"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json() or {}
    final_key = (data.get("apiKey") or "").strip() or FIXED_KEY
    
    try:
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

# --- A SOLUÇÃO ESTÁ AQUI ---
# Movemos a definição da porta para fora do __main__
# Isso força o Gunicorn a ver a porta certa do Railway
if os.environ.get("PORT"):
    port = int(os.environ.get("PORT"))
else:
    port = 5000

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
