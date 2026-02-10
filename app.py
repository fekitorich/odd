import os
from flask import Flask, render_template, jsonify

# --- DADOS DE CONFIGURAÇÃO (Para o HTML não quebrar) ---
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

# --- CORREÇÃO DO ERRO ---
# Pega o caminho exato onde este arquivo app.py está
basedir = os.path.abspath(os.path.dirname(__file__))

# template_folder=basedir -> Diz pro Flask: "O HTML está AQUI COMIGO, não procure pasta templates"
# static_folder=basedir   -> Diz pro Flask: "O CSS está AQUI COMIGO, não procure pasta static"
app = Flask(__name__, template_folder=basedir, static_folder=basedir)

@app.route("/")
def index():
    try:
        # Tenta carregar o arquivo que está na raiz
        return render_template("index.html", **CONFIG_DATA)
    except Exception as e:
        return f"ERRO CRÍTICO: Não encontrei 'index.html' na pasta {basedir}. Erro: {e}", 500

@app.route("/scan", methods=["POST"])
def scan():
    return jsonify({"success": True, "message": "Scan simulado com sucesso"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
