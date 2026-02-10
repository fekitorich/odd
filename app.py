"""Configuration constants (copied from edge-scanner).""" 

from __future__ import annotations

REGION_CONFIG = {
    "us": {"name": "United States", "default": True},
    "us2": {"name": "United States (Additional)", "default": False},
    "uk": {"name": "United Kingdom", "default": False},
    "eu": {"name": "Europe", "default": True},
    "au": {"name": "Australia", "default": False},
}

DEFAULT_REGION_KEYS = [key for key, meta in REGION_CONFIG.items() if meta.get("default")]

REGION_OPTIONS = [
    {"key": key, "label": meta["name"], "default": meta.get("default", False)}
    for key, meta in REGION_CONFIG.items()
]

EXCHANGE_BOOKMAKERS = {
    "betfair_ex_eu": {"name": "Betfair"},
    "betfair_ex_uk": {"name": "Betfair"},
    "betfair_ex_au": {"name": "Betfair"},
    "sportsbet_ex": {"name": "Sportsbet Exchange"},
    "matchbook": {"name": "Matchbook"},
}

EXCHANGE_KEYS = set(EXCHANGE_BOOKMAKERS.keys())

DEFAULT_COMMISSION = 0.05  # 5%

# (truncated for brevity; copied constants required by scanner.py)

MIN_MIDDLE_GAP = 1.5
DEFAULT_MIDDLE_SORT = "ev"
SHOW_POSITIVE_EV_ONLY = True

PROBABILITY_PER_INTEGER = {"default": 0.03}

NFL_KEY_NUMBER_PROBABILITY = {3: 0.15}
KEY_NUMBER_SPORTS = {"americanfootball_nfl"}

MAX_MIDDLE_PROBABILITY = 0.35

SPORT_DISPLAY_NAMES = {"americanfootball_nfl": "NFL"}

AMERICAN_SPORTS = {"americanfootball_nfl"}
SOCCER_SPORTS = set()

DEFAULT_SPORT_KEYS = ["americanfootball_nfl"]
DEFAULT_SPORT_OPTIONS = [{"key": key, "label": SPORT_DISPLAY_NAMES.get(key, key)} for key in DEFAULT_SPORT_KEYS]

AMERICAN_MARKETS = ["h2h", "spreads", "totals"]
SOCCER_MARKETS = ["spreads", "totals"]

ROI_BANDS = [(0.0, 1.0, "0-1%"), (1.0, 2.0, "1-2%"), (2.0, float("inf"), "2%+")]

SHARP_BOOKS = [
    {"key": "pinnacle", "name": "Pinnacle", "region": "eu", "type": "bookmaker"},
    {"key": "betfair_ex_eu", "name": "Betfair Exchange", "region": "eu", "type": "exchange"},
    {"key": "matchbook", "name": "Matchbook", "region": "eu", "type": "exchange"},
]

DEFAULT_SHARP_BOOK = "pinnacle"
DEFAULT_BANKROLL = 1000.0
MIN_EDGE_PERCENT = 1.0
DEFAULT_KELLY_FRACTION = 0.25

SOFT_BOOK_KEYS = ["draftkings", "fanduel"]

EDGE_BANDS = [(1.0, 3.0, "1-3%"), (3.0, 5.0, "3-5%"), (5.0, 10.0, "5-10%"), (10.0, float("inf"), "10%+")]


def markets_for_sport(sport_key: str) -> list[str]:
    if sport_key in AMERICAN_SPORTS:
        return AMERICAN_MARKETS
    if sport_key in SOCCER_SPORTS:
        return SOCCER_MARKETS
    return SOCCER_MARKETS.copy()
	
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

# Ensure edge-scanner folder is importable so we can import scanner and config
EDGE_SCANNER_PATH = str(Path(__file__).parent.joinpath("edge-scanner"))
if EDGE_SCANNER_PATH not in sys.path:
	sys.path.insert(0, EDGE_SCANNER_PATH)

load_dotenv()

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

ENV_API_KEY = os.getenv("ODDS_API_KEY") or os.getenv("THEODDSAPI_API_KEY")

app = Flask(__name__, template_folder=str(Path(EDGE_SCANNER_PATH) / "templates"), static_folder=str(Path(EDGE_SCANNER_PATH) / "static"))


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
	try:
		min_edge_percent = (
			float(payload.get("minEdgePercent")) if payload.get("minEdgePercent") is not None else MIN_EDGE_PERCENT
		)
	except (TypeError, ValueError):
		min_edge_percent = MIN_EDGE_PERCENT
	min_edge_percent = max(0.0, min_edge_percent)
	try:
		bankroll_value = float(payload.get("bankroll")) if payload.get("bankroll") is not None else DEFAULT_BANKROLL
	except (TypeError, ValueError):
		bankroll_value = DEFAULT_BANKROLL
	bankroll_value = max(0.0, bankroll_value)
	try:
		kelly_fraction = (
			float(payload.get("kellyFraction"))
			if payload.get("kellyFraction") is not None
			else DEFAULT_KELLY_FRACTION
		)
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
	commission_rate = (
		commission_percent / 100.0 if commission_percent is not None else DEFAULT_COMMISSION
	)
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


if __name__ == "__main__":
	app.run(debug=True)
