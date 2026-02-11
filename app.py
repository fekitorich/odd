import os
from pathlib import Path
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

# Importa as suas configurações e o seu scanner original
from config import (
    DEFAULT_BANKROLL, DEFAULT_COMMISSION, DEFAULT_KELLY_FRACTION,
    DEFAULT_REGION_KEYS, DEFAULT_SHARP_BOOK, DEFAULT_SPORT_OPTIONS,
    KELLY_OPTIONS, MIN_EDGE_PERCENT, REGION_OPTIONS, SHARP_BOOKS
)
from scanner import run_scan

load_dotenv()
app = Flask(__name__)

# Pega a chave das variáveis de ambiente do Railway
ENV_API_KEY = os.getenv("ODDS_API_KEY") or os.getenv("THEODDSAPI_API_KEY")

@app.route("/")
def index():
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
    
    # Parâmetros vindos do formulário (Lógica original)
    sports = payload.get("sports") or []
    all_sports = bool(payload.get("allSports"))
    stake = payload.get("stake")
    regions = payload.get("regions")
    commission = payload.get("commission")
    sharp_book = (payload.get("sharpBook") or DEFAULT_SHARP_BOOK).strip().lower()

    try:
        stake_val = float(stake) if stake is not None else 100.0
        min_edge = float(payload.get("minEdgePercent")) if payload.get("minEdgePercent") is not None else MIN_EDGE_PERCENT
        bankroll = float(payload.get("bankroll")) if payload.get("bankroll") is not None else DEFAULT_BANKROLL
        kelly = float(payload.get("kellyFraction")) if payload.get("kellyFraction") is not None else DEFAULT_KELLY_FRACTION
    except:
        stake_val, min_edge, bankroll, kelly = 100.0, MIN_EDGE_PERCENT, DEFAULT_BANKROLL, DEFAULT_KELLY_FRACTION

    comm_rate = (float(commission) / 100.0) if commission is not None else DEFAULT_COMMISSION

    # CHAMA O SEU SCANNER ORIGINAL
    result = run_scan(
        api_key, sports, all_sports, stake_val,
        regions or DEFAULT_REGION_KEYS, comm_rate,
        sharp_book=sharp_book, min_edge_percent=min_edge,
        bankroll=bankroll, kelly_fraction=kelly
    )
    
    return jsonify(result), (200 if result.get("success") else 500)

if __name__ == "__main__":
    Path("data").mkdir(exist_ok=True)
    # Porta dinâmica do Railway
    port = int(os.environ.get("PORT", 5000))
    # Host 0.0.0.0 é obrigatório para o site ficar visível online
    app.run(host="0.0.0.0", port=port)
