import os
import sys
from flask import Flask, jsonify, render_template, request
from scanner import run_scan

app = Flask(__name__)

# --- SUA CHAVE GRAVADA AQUI ---
FIXED_KEY = "b1691c0d7659b8bc527393de24731962"

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

# ... (mantenha todo o seu código de rotas e imports acima)

if __name__ == "__main__":
    # 1. Tenta pegar a porta que o Railway enviou
    # 2. Se não encontrar (rodando local), usa a 5000
    port = int(os.environ.get("PORT", 5000))
    
    # IMPORTANTE: host="0.0.0.0" é obrigatório para o Railway conseguir "enxergar" o app
    app.run(host="0.0.0.0", port=port)
