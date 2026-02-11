import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

# Importa a lógica do seu scanner e configurações originais
from config import (
    DEFAULT_BANKROLL, DEFAULT_COMMISSION, DEFAULT_KELLY_FRACTION,
    DEFAULT_REGION_KEYS, DEFAULT_SHARP_BOOK, DEFAULT_SPORT_OPTIONS,
    KELLY_OPTIONS, MIN_EDGE_PERCENT, REGION_OPTIONS, SHARP_BOOKS
)
from scanner import run_scan

load_dotenv()

app = Flask(__name__)
# Railway usa variáveis de ambiente para a chave da API
ENV_API_KEY = os.getenv("ODDS_API_KEY") or os.getenv("THEODDSAPI_API_KEY")

@app.route("/")
def index():
    # Renderiza o seu index.html original (dentro da pasta /templates)
    return render_template(
        "index.html",
        default_sports=DEFAULT_SPORT_OPTIONS,
        region_options=REGION_OPTIONS,
        default_commission_percent=int(DEFAULT_COMMISSION * 100),
        has_env_key=bool(ENV_API_KEY),
        sharp_books=SHARP_BOOKS,
        default_sharp_book=DEFAULT_SHARP_BOOK,
        default_min_edge_percent=MIN_EDGE_PERCENT,
        default_bankroll=DEFAULT_BANKROLL,
        default_kelly_fraction=DEFAULT_KELLY_FRACTION,
        kelly_options=KELLY_OPTIONS,
    )

@app.route("/scan", methods=["POST"])
def scan():
    payload = request.get_json(force=True, silent=True) or {}
    api_key = ENV_API_KEY or (payload.get("apiKey") or "").strip()
    
    # Coleta os dados que o seu index.html envia quando você aperta "Scan Now"
    sports = payload.get("sports")
    all_sports = bool(payload.get("allSports"))
    stake = payload.get("stake")
    regions = payload.get("regions")
    commission = payload.get("commission")
    sharp_book = (payload.get("sharpBook") or DEFAULT_SHARP_BOOK).strip().lower()

    # Converte os valores para os formatos que o seu scanner.py exige
    try:
        min_edge = float(payload.get("minEdgePercent") or MIN_EDGE_PERCENT)
        bankroll = float(payload.get("bankroll") or DEFAULT_BANKROLL)
        kelly = float(payload.get("kellyFraction") or DEFAULT_KELLY_FRACTION)
        stake_val = float(stake or 100.0)
    except:
        min_edge, bankroll, kelly, stake_val = MIN_EDGE_PERCENT, DEFAULT_BANKROLL, DEFAULT_KELLY_FRACTION, 100.0

    comm_rate = (float(commission) / 100.0) if commission is not None else DEFAULT_COMMISSION

    # CHAMA O SCANNER ORIGINAL (Matemática pura do seu scanner.py)
    result = run_scan(
        api_key=api_key,
        sports=sports,
        all_sports=all_sports,
        stake_amount=stake_val,
        regions=regions or DEFAULT_REGION_KEYS,
        commission_rate=comm_rate,
        sharp_book=sharp_book,
        min_edge_percent=min_edge,
        bankroll=bankroll,
        kelly_fraction=kelly
    )
    
    # Retorna JSON (Dados) para o JavaScript do seu index.html preencher a tabela
    return jsonify(result)

if __name__ == "__main__":
    Path("data").mkdir(exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
