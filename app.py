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
    
    # 1. Define a chave (Manual ganha do Servidor)
    final_key = data.get("apiKey")
    if not final_key or final_key.strip() == "":
        final_key = ENV_API_KEY

    # LOG: Mostra no Railway o que estamos enviando
    print(f"--- INICIANDO DEBUG ---", file=sys.stdout)
    print(f"Chave usada (primeiros 5 digitos): {final_key[:5] if final_key else 'SEM CHAVE'}", file=sys.stdout)
    print(f"Filtros recebidos: {data.get('sports')}", file=sys.stdout)

    try:
        # Chama o SEU scanner original
        result = run_scan(
            api_key=final_key,
            sports=data.get("sports"),
            regions=data.get("regions"),
            stake_amount=float(data.get("stake") or 100),
            commission_rate=float(data.get("commission") or 1) / 100.0
        )
        
        # LOG: Mostra EXATAMENTE o que o scanner devolveu
        # Se aqui aparecer "opportunities": [], o scanner original não achou nada.
        # Se aqui aparecer dados, o erro é no HTML.
        print(f"--- RESULTADO DO SCANNER ---", file=sys.stdout)
        print(json.dumps(result, indent=2), file=sys.stdout)
        print(f"--- FIM DO DEBUG ---", file=sys.stdout)
        
        return jsonify(result)

    except Exception as e:
        print(f"ERRO CRÍTICO NO SCANNER: {e}", file=sys.stdout)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
