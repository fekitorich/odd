"""Core arbitrage scanning logic (copied from edge-scanner).
"""

from __future__ import annotations

import datetime as dt
import itertools
import math
import uuid
from typing import Dict, List, Optional, Sequence, Tuple

import requests

from config import (
    DEFAULT_BANKROLL,
    DEFAULT_COMMISSION,
    DEFAULT_KELLY_FRACTION,
    DEFAULT_MIDDLE_SORT,
    DEFAULT_REGION_KEYS,
    DEFAULT_SHARP_BOOK,
    DEFAULT_SPORT_KEYS,
    EDGE_BANDS,
    EXCHANGE_BOOKMAKERS,
    EXCHANGE_KEYS,
    KEY_NUMBER_SPORTS,
    MAX_MIDDLE_PROBABILITY,
    MIN_EDGE_PERCENT,
    MIN_MIDDLE_GAP,
    NFL_KEY_NUMBER_PROBABILITY,
    PROBABILITY_PER_INTEGER,
    REGION_CONFIG,
    ROI_BANDS,
    SHARP_BOOKS,
    SHOW_POSITIVE_EV_ONLY,
    SOFT_BOOK_KEYS,
    SPORT_DISPLAY_NAMES,
    markets_for_sport,
)

BASE_URL = "https://api.the-odds-api.com/v4"
MIDDLE_MARKETS = {"spreads", "totals"}
ALLOWED_PLUS_EV_MARKETS = {"h2h", "spreads", "totals"}
SOFT_BOOK_KEY_SET = set(SOFT_BOOK_KEYS)
SHARP_BOOK_MAP = {book["key"]: book for book in SHARP_BOOKS}


class ScannerError(Exception):
    """Raised for recoverable scanner issues."""


def _iso_now() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _clamp_commission(rate: float) -> float:
    if rate is None:
        return DEFAULT_COMMISSION
    return max(0.0, min(rate, 0.2))


def _normalize_regions(regions: Optional[Sequence[str]]) -> List[str]:
    if not regions:
        return list(DEFAULT_REGION_KEYS)
    valid = [region for region in regions if region in REGION_CONFIG]
    return valid or list(DEFAULT_REGION_KEYS)


def _ensure_sharp_region(regions: List[str], sharp_key: str) -> List[str]:
    required_region = SHARP_BOOK_MAP.get(sharp_key, {}).get("region", "eu")
    normalized = []
    seen = set()
    for region in regions:
        if region not in seen:
            normalized.append(region)
            seen.add(region)
    if required_region and required_region not in seen and required_region in REGION_CONFIG:
        normalized.append(required_region)
    return normalized


def _apply_commission(price: float, commission_rate: float, is_exchange: bool) -> float:
    if not is_exchange:
        return price
    edge = price - 1.0
    if edge <= 0:
        return price
    return 1.0 + edge * (1.0 - commission_rate)


def _sharp_priority(selected_key: str) -> List[dict]:
    priority = []
    seen = set()
    if selected_key in SHARP_BOOK_MAP:
        priority.append(SHARP_BOOK_MAP[selected_key])
        seen.add(selected_key)
    for book in SHARP_BOOKS:
        key = book.get("key")
        if key and key not in seen:
            priority.append(book)
            seen.add(key)
    return priority


def _points_match(point_a, point_b, tolerance: float = 1e-6) -> bool:
    if point_a is None and point_b is None:
        return True
    if point_a is None or point_b is None:
        return False
    try:
        return abs(float(point_a) - float(point_b)) <= tolerance
    except (TypeError, ValueError):
        return False


def _spread_gap_info(favorite_line: float, underdog_line: float) -> Optional[dict]:
    if favorite_line is None or underdog_line is None:
        return None
    if favorite_line >= 0 or underdog_line <= 0:
        return None
    fav_abs = abs(favorite_line)
    if fav_abs >= underdog_line:
        return None
    gap = round(underdog_line - fav_abs, 2)
    start = math.floor(fav_abs) + 1
    end = math.ceil(underdog_line) - 1
    if end < start:
        return None
    middle_integers = list(range(start, end + 1))
    if not middle_integers:
        return None
    return {
        "gap_points": round(gap, 2),
        "middle_integers": middle_integers,
        "integer_count": len(middle_integers),
    }


def _total_gap_info(over_line: float, under_line: float) -> Optional[dict]:
    if over_line is None or under_line is None:
        return None
    if over_line >= under_line:
        return None
    gap = under_line - over_line
    lower = math.floor(over_line) + 1
    upper = math.ceil(under_line) - 1
    if upper < lower:
        return None
    middle_integers = list(range(lower, upper + 1))
    if not middle_integers:
        return None
    return {
        "gap_points": round(gap, 2),
        "middle_integers": middle_integers,
        "integer_count": len(middle_integers),
    }


# Note: This file is a trimmed copy; for full functionality use the original repo.
