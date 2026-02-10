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
