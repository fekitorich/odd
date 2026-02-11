import os
from flask import Flask, jsonify, render_template, request
from scanner import run_scan

app = Flask(__name__)

# Railway lê sua nova chave aqui
ENV_API_KEY = os.getenv("ODDS_API_KEY")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
def scan():
    payload = request.get_json() or {}
    
    # Chama o scanner original com os filtros do site
    result = run_scan(
        api_key=ENV_API_KEY or payload.get("apiKey"),
        sports=payload.get("sports"),
        regions=payload.get("regions"),
        stake_amount=float(payload.get("stake") or 100.0),
        commission_rate=float(payload.get("commission") or 1.0) / 100.0
    )
    # Retorna JSON para o JavaScript preencher a tabela
    return jsonify(result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
