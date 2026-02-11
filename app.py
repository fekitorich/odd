import os
from flask import Flask, jsonify, render_template, request
from scanner import run_scan

app = Flask(__name__)

# Sua chave hardcoded para garantir que a API responda
FIXED_KEY = "b1691c0d7659b8bc527393de24731962"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json() or {}
    # Prioriza o que vem do site, depois a fixa, depois o .env
    api_key = (data.get("apiKey") or "").strip() or FIXED_KEY or os.getenv("ODDS_API_KEY")
    
    try:
        # Chama o seu scanner original
        result = run_scan(
            api_key=api_key,
            sports=data.get("sports") or ["soccer_brazil_campeonato"],
            regions=data.get("regions") or ["eu", "us", "uk"],
            stake_amount=float(data.get("stake") or 100),
            commission_rate=float(data.get("commission") or 0) / 100.0
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# O Gunicorn ignora o que está abaixo, mas mantemos para testes locais
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
