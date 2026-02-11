import os
import sys
from flask import Flask, jsonify, render_template, request
from scanner import run_scan

app = Flask(__name__)

# Configuração de Porta para o Railway
# Lemos a porta logo no início do arquivo
PORT = int(os.environ.get("PORT", 5000))

# Sua chave hardcoded
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
            regions=data.get("regions") or ["us", "uk", "eu"],
            stake_amount=float(data.get("stake") or 100),
            commission_rate=float(data.get("commission") or 0) / 100.0
        )
        return jsonify(result)
    except Exception as e:
        print(f"ERRO NO SCANNER: {e}")
        return jsonify({"error": str(e), "success": False}), 500

if __name__ == "__main__":
    # Rodando com host 0.0.0.0 para ser visível externamente
    app.run(host="0.0.0.0", port=PORT)
