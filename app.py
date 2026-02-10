from __future__ import annotations
import os
from flask import Flask, render_template, jsonify

# Configurações que o seu HTML original exige
CONFIG_DATA = {
    "default_sports": [{"key": "americanfootball_nfl", "label": "NFL"}],
    "region_options": [{"key": "us", "label": "United States", "default": True}],
    "default_commission_percent": 5,
    "sharp_books": [{"key": "pinnacle", "name": "Pinnacle"}],
    "default_sharp_book": "pinnacle",
    "default_min_edge_percent": 1.0,
    "default_bankroll": 1000.0,
    "default_kelly_fraction": 0.25,
    "kelly_options": [0.1, 0.25, 0.5, 1.0],
    "has_env_key": True
}

# Inicialização robusta
app = Flask(__name__, template_folder="templates", static_folder="static")

@app.route("/")
def index():
    try:
        # Tenta carregar o seu design azul
        return render_template("index.html", **CONFIG_DATA)
    except Exception as e:
        # Se o design azul falhar, ele mostra uma mensagem clara em vez do Erro 500
        return f"Erro ao carregar o design: {e}. Verifique se a pasta 'templates' está na raiz do GitHub.", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
