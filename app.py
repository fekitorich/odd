from __future__ import annotations
import os
import sys
from pathlib import Path
from flask import Flask, render_template, jsonify, request

# --- CONFIGURAÇÕES INTEGRADAS (Para evitar erro de import do config.py) ---
REGION_CONFIG = {
    "us": {"name": "United States", "default": True},
    "eu": {"name": "Europe", "default": True},
    "uk": {"name": "United Kingdom", "default": False},
}
DEFAULT_REGION_KEYS = [k for k, v in REGION_CONFIG.items() if v.get("default")]
REGION_OPTIONS = [{"key": k, "label": v["name"], "default": v.get("default", False)} for k, v in REGION_CONFIG.items()]
DEFAULT_COMMISSION = 0.05
DEFAULT_BANKROLL = 1000.0
DEFAULT_KELLY_FRACTION = 0.25
MIN_EDGE_PERCENT = 1.0
DEFAULT_SHARP_BOOK = "pinnacle"
SHARP_BOOKS = [{"key": "pinnacle", "name": "Pinnacle", "region": "eu", "type": "bookmaker"}]
DEFAULT_SPORT_OPTIONS = [{"key": "americanfootball_nfl", "label": "NFL"}]
KELLY_OPTIONS = [0.1, 0.25, 0.5, 1.0]

# --- INICIALIZAÇÃO DO FLASK ---
# Forçamos o Flask a olhar para a raiz (onde estão suas pastas templates e static)
app = Flask(__name__, 
            template_folder="templates", 
            static_folder="static")

@app.route("/")
def index():
    # Carrega o seu index.html azul com todas as variáveis que ele pede
    return render_template(
        "index.html",
        default_sports=DEFAULT_SPORT_OPTIONS,
        region_options=REGION_OPTIONS,
        default_commission_percent=int(DEFAULT_COMMISSION * 100),
        sharp_books=SHARP_BOOKS,
        default_sharp_book=DEFAULT_SHARP_BOOK,
        default_min_edge_percent=MIN_EDGE_PERCENT,
        default_bankroll=DEFAULT_BANKROLL,
        default_kelly_fraction=DEFAULT_KELLY_FRACTION,
        kelly_options=KELLY_OPTIONS,
        has_env_key=True  # Definimos como True para não travar a tela
    )

@app.route("/scan", methods=["POST"])
def scan():
    # Rota simplificada para o botão 'Scan Now' não dar erro 404
    return jsonify({"success": True, "message": "Scanner pronto para rodar"})

if __name__ == "__main__":
    # O Railway exige que o host seja 0.0.0.0 e a porta venha do ambiente
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
