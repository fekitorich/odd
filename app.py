from __future__ import annotations
import os
import sys
from pathlib import Path

# FORÇA O PYTHON A VER OS ARQUIVOS NA RAIZ (MAIN)
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from flask import Flask, render_template, jsonify, request
# Se o config.py está na raiz, este import agora VAI funcionar
try:
    import config
except ImportError:
    # Caso ele ainda engasgue, criamos um fallback
    config = None

app = Flask(__name__, 
            template_folder="templates", 
            static_folder="static")

@app.route("/")
def index():
    # Isso vai carregar o seu index.html azul bonito
    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
