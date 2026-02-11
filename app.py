import os
from flask import Flask, jsonify, render_template, request
from scanner import run_scan

app = Flask(__name__)

# Pega a chave do Railway
ENV_API_KEY = os.getenv("ODDS_API_KEY")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
def scan():
    # Pega os dados do formulário
    data = request.get_json() or {}
    
    # Chama o SEU scanner original exatamente como ele foi criado para ser chamado.
    # Sem inventar moda, sem filtros extras.
    try:
        result = run_scan(
            api_key=ENV_API_KEY or data.get("apiKey"),
            sports=data.get("sports"),
            regions=data.get("regions"),
            stake_amount=float(data.get("stake") or 100),
            commission_rate=float(data.get("commission") or 1) / 100.0
        )
        return jsonify(result)
    except Exception as e:
        # Se der erro, mostra no log do Railway para sabermos o que é
        print(f"Erro no Scanner: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
