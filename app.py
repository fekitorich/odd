import os
import sys
from flask import Flask, jsonify, render_template, request
from scanner import run_scan

app = Flask(__name__)

# --- SUA CHAVE GRAVADA AQUI ---
FIXED_KEY = "ac611e223968599cffdcd6c1944f9958"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json() or {}
    
    # Lógica Blindada:
    # 1. Tenta pegar o que estiver na caixa do site.
    # 2. Se a caixa estiver vazia, USA A CHAVE FIXA AUTOMATICAMENTE.
    user_input = data.get("apiKey") or ""
    final_key = user_input.strip()
    
    if not final_key:
        final_key = FIXED_KEY

    # Filtros padrão
    sports = data.get("sports") or []
    regions = data.get("regions") or ["us"]
    stake = float(data.get("stake") or 100)
    commission = float(data.get("commission") or 1) / 100.0

    try:
        # Chama o scanner original
        result = run_scan(
            api_key=final_key,
            sports=sports,
            regions=regions,
            stake_amount=stake,
            commission_rate=commission
        )
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
