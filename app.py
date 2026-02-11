import os
import sys
import json
from flask import Flask, jsonify, render_template, request
from scanner import run_scan

app = Flask(__name__)

ENV_API_KEY = os.getenv("ODDS_API_KEY")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json() or {}
    
    # 1. Pega a chave manual OU do ambiente
    raw_key = data.get("apiKey") or ENV_API_KEY or ""
    
    # 2. LIMPEZA DE SEGURANÇA: Remove espaços invisíveis antes e depois
    final_key = raw_key.strip()

    # LOG: Vamos ver se a chave limpa está correta
    print(f"--- DEBUG CHAVE ---", file=sys.stdout)
    print(f"Chave recebida (limpa): {final_key[:5]}... (tamanho: {len(final_key)})", file=sys.stdout)

    try:
        result = run_scan(
            api_key=final_key,
            sports=data.get("sports"),
            regions=data.get("regions"),
            stake_amount=float(data.get("stake") or 100),
            commission_rate=float(data.get("commission") or 1) / 100.0
        )
        return jsonify(result)

    except Exception as e:
        print(f"ERRO CRÍTICO: {e}", file=sys.stdout)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
