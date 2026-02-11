import os
from flask import Flask, jsonify, render_template, request
from scanner import run_scan

app = Flask(__name__)

# O Railway já está lendo sua chave aqui
ENV_API_KEY = os.getenv("ODDS_API_KEY")

@app.route("/")
def index():
    # Apenas abre o site. Os nomes (NFL, NBA) agora estão fixos no HTML para não sumirem.
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
def scan():
    # Captura o clique do botão Scan
    payload = request.get_json() or {}
    
    # Manda os dados para o seu scanner.py original
    result = run_scan(
        api_key=ENV_API_KEY or payload.get("apiKey"),
        sports=payload.get("sports"),
        regions=payload.get("regions"),
        stake_amount=float(payload.get("stake") or 100.0),
        commission_rate=float(payload.get("commission") or 1.0) / 100.0
    )
    # Retorna os jogos como DADOS para a tabela (JSON)
    return jsonify(result)

if __name__ == "__main__":
    # Mantém a porta que o Railway já está usando
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
