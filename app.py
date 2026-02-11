from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

# Importa configurações e scanner originais
from config import (
    DEFAULT_BANKROLL,
    DEFAULT_COMMISSION,
    DEFAULT_KELLY_FRACTION,
    DEFAULT_REGION_KEYS,
    DEFAULT_SHARP_BOOK,
    DEFAULT_SPORT_OPTIONS,
    KELLY_OPTIONS,
    MIN_EDGE_PERCENT,
    REGION_OPTIONS,
    SHARP_BOOKS,
)
from scanner import run_scan

load_dotenv()

app = Flask(__name__)
ENV_API_KEY = os.getenv("ODDS_API_KEY") or os.getenv("THEODDSAPI_API_KEY")

@app.route("/")
def index() -> str:
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
    sports = payload.get("sports") or []
    all_sports = bool(payload.get("allSports"))
    stake = payload.get("stake")
    regions = payload.get("regions")
    commission = payload.get("commission")
    sharp_book = (payload.get("sharpBook") or DEFAULT_SHARP_BOOK).strip().lower()

    # Tratamento de erros de conversão (mantendo lógica original)
    try:
        min_edge_percent = float(payload.get("minEdgePercent")) if payload.get("minEdgePercent") is not None else MIN_EDGE_PERCENT
    except (TypeError, ValueError):
        min_edge_percent = MIN_EDGE_PERCENT
    min_edge_percent = max(0.0, min_edge_percent)

    try:
        bankroll_value = float(payload.get("bankroll")) if payload.get("bankroll") is not None else DEFAULT_BANKROLL
    except (TypeError, ValueError):
        bankroll_value = DEFAULT_BANKROLL
    bankroll_value = max(0.0, bankroll_value)

    try:
        kelly_fraction = float(payload.get("kellyFraction")) if payload.get("kellyFraction") is not None else DEFAULT_KELLY_FRACTION
    except (TypeError, ValueError):
        kelly_fraction = DEFAULT_KELLY_FRACTION
    kelly_fraction = max(0.0, min(kelly_fraction, 1.0))

    try:
        stake_value = float(stake) if stake is not None else 100.0
    except (TypeError, ValueError):
        stake_value = 100.0

    if isinstance(regions, list):
        regions_value = [str(region) for region in regions if isinstance(region, str)]
    else:
        regions_value = None

    try:
        commission_percent = float(commission) if commission is not None else None
    except (TypeError, ValueError):
        commission_percent = None
    commission_rate = (commission_percent / 100.0 if commission_percent is not None else DEFAULT_COMMISSION)

    # Chama o scanner original
    result = run_scan(
        api_key,
        sports,
        all_sports,
        stake_value,
        regions_value or DEFAULT_REGION_KEYS,
        commission_rate,
        sharp_book=sharp_book,
        min_edge_percent=min_edge_percent,
        bankroll=bankroll_value,
        kelly_fraction=kelly_fraction,
    )
    status = 200 if result.get("success") else result.get("error_code", 500)
    return jsonify(result), status

def ensure_data_dir() -> None:
    Path("data").mkdir(exist_ok=True)

if __name__ == "__main__":
    ensure_data_dir()
    # Esta parte só roda se você testar no PC.
    # No Railway, quem manda é o Procfile + Gunicorn.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
