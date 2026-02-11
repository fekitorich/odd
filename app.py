import os
from flask import Flask, jsonify, render_template, request
from scanner import run_scan

app = Flask(__name__)

# CHAVE HARDCODED (Para garantir que funcione mesmo sem .env)
FIXED_KEY = "ac611e223968599cffdcd6c1944f9958"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json() or {}
    # Prioridade: 1. Chave digitada no site | 2. Chave fixa | 3. Variável de ambiente
    final_key = (data.get("apiKey") or "").strip() or FIXED_KEY or os.getenv("ODDS_API_KEY")
    
    try:
        # Chama o seu scanner original exatamente como ele é
        result = run_scan(
            api_key=final_key,
            sports=data.get("sports") or [],
            regions=data.get("regions") or ["us", "uk", "eu"],
            stake_amount=float(data.get("stake") or 100),
            commission_rate=float(data.get("commission") or 0) / 100.0
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

# FORÇA O FLASK A ESCUTAR A PORTA DO RAILWAY
if __name__ == "__main__":
    # O Railway injeta a porta na variável PORT. Se não houver, usa 8080.
    port = int(os.environ.get("PORT", 8080))
    # host="0.0.0.0" é OBRIGATÓRIO para o Railway enxergar o app
    app.run(host="0.0.0.0", port=port)
