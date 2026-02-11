import os
from flask import Flask, jsonify, render_template, request
from scanner import run_scan

app = Flask(__name__)

# Chave de backup do servidor
ENV_API_KEY = os.getenv("ODDS_API_KEY")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json() or {}
    
    # MUDANÇA CRÍTICA:
    # 1. Tenta pegar a chave que você digitou no site.
    # 2. Se você deixar em branco, tenta usar a do servidor.
    final_key = data.get("apiKey") or ENV_API_KEY
    
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
        print(f"Erro no Scanner: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
