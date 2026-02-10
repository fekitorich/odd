import sys
import io
import os
from flask import Flask, render_template_string
from dotenv import load_dotenv

# Carrega variáveis
load_dotenv()

# Importa o scanner original
import scanner 

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Scanner: Modo Texto</title>
    <style>
        body { background: #0d1117; color: #c9d1d9; font-family: monospace; padding: 20px; }
        .box { background: #161b22; padding: 20px; border: 1px solid #30363d; border-radius: 6px; margin-top: 20px; white-space: pre-wrap; }
        button { background: #238636; color: white; padding: 15px; border: none; border-radius: 6px; cursor: pointer; font-size: 18px; font-weight: bold; width: 100%; }
        button:hover { background: #2ea043; }
        h1 { border-bottom: 1px solid #30363d; padding-bottom: 10px; }
        .status-ok { color: #00e676; }
        .status-err { color: #ff7b72; }
    </style>
</head>
<body>
    <h1>Scanner Original</h1>
    
    <div style="margin-bottom: 20px;">
        API Key: 
        {% if has_key %} <span class="status-ok">DETECTADA (Ambiente)</span>
        {% else %} <span class="status-err">NÃO ENCONTRADA (Configure ODDS_API_KEY)</span> {% endif %}
    </div>

    <form method="POST" action="/scan">
        <button type="submit">RODAR SCANNER E VER TEXTO</button>
    </form>

    {% if output %}
        <h2>Saída do Scanner:</h2>
        <div class="box" style="border-color: #00e676;">{{ output }}</div>
    {% endif %}

    {% if error %}
        <h2>Erro Técnico:</h2>
        <div class="box" style="border-color: #ff7b72;">{{ error }}</div>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    key = os.environ.get("ODDS_API_KEY") or os.environ.get("API_KEY")
    return render_template_string(HTML, has_key=(key is not None))

@app.route("/scan", methods=["POST"])
def scan():
    # Prepara para capturar o print()
    capture = io.StringIO()
    original_stdout = sys.stdout
    sys.stdout = capture
    
    error_msg = None
    
    # Prepara argumentos (caso o scanner precise)
    api_key = os.environ.get("ODDS_API_KEY") or os.environ.get("API_KEY")
    sports = ['basketball_nba', 'americanfootball_nfl']
    regions = ['us', 'eu', 'uk', 'au'] # Força todas as regiões
    
    try:
        # Tenta rodar de todas as formas possíveis
        if hasattr(scanner, 'run_scan'):
            # Tenta passar os argumentos. Se der erro, tenta sem.
            try:
                scanner.run_scan(api_key, sports, regions, 0.05, 1000)
            except TypeError:
                scanner.run_scan()
        elif hasattr(scanner, 'main'):
            scanner.main()
        else:
            error_msg = "Não achei função run_scan ou main."

    except Exception as e:
        error_msg = f"O scanner rodou mas deu erro interno: {str(e)}"
    
    # Restaura a saída e pega o texto
    sys.stdout = original_stdout
    output_text = capture.getvalue()

    if not output_text and not error_msg:
        output_text = "O scanner rodou com sucesso (retornou 0), mas não imprimiu nada na tela via print(). Isso geralmente significa que não encontrou oportunidades nos filtros atuais."

    return render_template_string(HTML, has_key=(api_key is not None), output=output_text, error=error_msg)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
