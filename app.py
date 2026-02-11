from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

# Importa as configurações e a lógica do seu scanner original
from config import (
    DEFAULT_BANKROLL, DEFAULT_COMMISSION, DEFAULT_KELLY_FRACTION,
    DEFAULT_REGION_KEYS, DEFAULT_SHARP_BOOK, DEFAULT_SPORT_OPTIONS,
    KELLY_OPTIONS, MIN_EDGE_PERCENT, REGION_OPTIONS, SHARP_BOOKS,
)
from scanner import run_scan

load_dotenv()

app = Flask(__name__)
ENV_API_KEY = os.getenv("ODDS_API_KEY") or os.getenv("THEODDSAPI_API_KEY")

@app.route("/")
def index() -> str:
    # Renderiza o index.html que está dentro da pasta /templates/
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
def scan() -> tuple:
    payload = request.get_json(force=True, silent=True) or {}
    api_key = ENV_API_KEY or (payload.get("apiKey") or "").strip()
    
    # Executa o scanner original usando os parâmetros do seu site
    result = run_scan(
        api_key=api_key,
        sports=payload.get("sports"),
        all_sports=bool(payload.get("allSports")),
        stake_amount=float(payload.get("stake") or 100.0),
        regions=payload.get("regions") or DEFAULT_REGION_KEYS,
        commission_rate=float(payload.get("commission") or 5) / 100.0,
        sharp_book=payload.get("sharpBook") or DEFAULT_SHARP_BOOK,
        min_edge_percent=float(payload.get("minEdgePercent") or MIN_EDGE_PERCENT),
        bankroll=float(payload.get("bankroll") or DEFAULT_BANKROLL),
        kelly_fraction=float(payload.get("kellyFraction") or DEFAULT_KELLY_FRACTION)
    )
    
    return jsonify(result), (200 if result.get("success") else 400)

if __name__ == "__main__":
    # Garante que a pasta de dados exista
    Path("data").mkdir(exist_ok=True)
    # Porta dinâmica para o Railway
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
