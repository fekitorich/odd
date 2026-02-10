import os
from flask import Flask, render_template, request
from scanner import run_scan  # Importa a função REAL do arquivo acima

# Configuração para rodar na raiz sem pastas extras
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, template_folder=basedir, static_folder=basedir)

@app.route("/", methods=["GET"])
def index():
    # Renderiza a página inicial limpa
    return render_template("index.html", results=None)

@app.route("/scan", methods=["POST"])
def scan():
    # 1. Pega os dados que você digitou no site
    api_key = os.environ.get("ODDS_API_KEY") or request.form.get("apiKey")
    
    # Tratamento de erros para números
    try:
        bankroll = float(request.form.get("bankroll", 1000))
        commission = float(request.form.get("commission", 5))
    except ValueError:
        bankroll = 1000.0
        commission = 5.0
        
    sports = request.form.getlist("sports")
    regions = request.form.getlist("regions")

    # 2. CHAMA O SCANNER REAL
    # Isso vai demorar alguns segundos enquanto conecta na TheOddsAPI
    opportunities = []
    error_msg = None
    
    try:
        opportunities = run_scan(api_key, sports, regions, commission, bankroll)
    except Exception as e:
        error_msg = f"Erro no Scanner: {str(e)}"

    # 3. Devolve a página com a tabela preenchida (se houver dados)
    return render_template("index.html", results=opportunities, searched=True, error=error_msg)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
