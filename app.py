import sys
import io
import os
from flask import Flask, render_template_string
from dotenv import load_dotenv

# Carrega as chaves do Railway
load_dotenv()

# Tenta importar o scanner e o config
try:
    import config
except ImportError:
    config = None

import scanner 

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Scanner: Modo Texto Real</title>
    <style>
        body { background: #0d1117; color: #c9d1d9; font-family: monospace; padding: 20px; }
        .console { 
            background: #161b22; 
            padding: 20px; 
            border: 1px solid #30363d; 
            border-radius: 6px; 
            margin-top: 20px; 
            white-space: pre-wrap; /* Mantém a formatação do texto original */
            font-size: 14px; 
            line-height: 1.5; 
            min-height: 100px;
        }
        button { background: #238636; color: white; padding: 15px; border: none; border-radius: 6px; cursor: pointer; font-size: 18px; font-weight: bold; width: 100%; }
        button:hover { background: #2ea043; }
        .status-ok { color: #00e676; font-weight: bold; }
        .status-err { color: #ff7b72; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Scanner Original</h1>
    
    <div>
        API Key: 
        {% if has_key %} <span class="status-ok">DETECTADA ({{ key_start }}...)</span>
        {% else %} <span class="status-err">NÃO ENCONTRADA</span> {% endif %}
    </div>

    <form method="POST" action="/scan">
        <button type="submit">RODAR SCANNER</button>
    </form>

    {% if output %}
        <h2>Resultado do Terminal:</h2>
        <div class="console" style="border-color: #00e676;">{{ output }}</div>
    {% endif %}

    {% if error %}
        <h2>Erro de Execução:</h2>
        <div class="console" style="border-color: #ff7b72;">{{ error }}</div>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    key = os.environ.get("ODDS_API_KEY") or os.environ.get("API_KEY")
    key_start = key[:4] if key else ""
    return render_template_string(HTML, has_key=(key is not None), key_start=key_start)

@app.route("/scan", methods=["POST"])
def scan():
    # 1. Configura a API Key no módulo config (se existir)
    # Isso garante que o scanner leia a chave mesmo se ele esperar ela hardcoded
    key = os.environ.get("ODDS_API_KEY") or os.environ.get("API_KEY")
    if config and key:
        # Injeta a chave em todas as variáveis possíveis que o config original possa ter
        config.API_KEY = key
        config.ODDS_API_KEY = key
        config.api_key = key

    # 2. Captura o print() (STDOUT)
    capture = io.StringIO()
    original_stdout = sys.stdout
    sys.stdout = capture
    
    error_msg = None
    
    try:
        # 3. Executa o scanner
        # Não guardamos o retorno em variável para não dar erro de iterable
        if hasattr(scanner, 'run_scan'):
            # Tenta passar parâmetros completos
            try:
                scanner.run_scan(key, ['basketball_nba', 'americanfootball_nfl'], ['us', 'eu', 'uk', 'au'], 0.05, 1000)
            except TypeError:
                # Se falhar, tenta sem parâmetros (lendo do config)
                scanner.run_scan()
        elif hasattr(scanner, 'main'):
            scanner.main()
        elif hasattr(scanner, 'scan'):
            scanner.scan()
        else:
            # Se não tiver função, roda o arquivo bruto
            with open("scanner.py") as f:
                exec(f.read())

    except Exception as e:
        error_msg = f"Erro ao rodar script: {str(e)}"
    
    # 4. Recupera o texto e restaura o print normal
    sys.stdout = original_stdout
    output_text = capture.getvalue()

    if not output_text and not error_msg:
        output_text = "O scanner finalizou mas não imprimiu nada na tela. (Verifique se há 'print' no código original)."

    return render_template_string(HTML, has_key=(key is not None), key_start=key[:4] if key else "", output=output_text, error=error_msg)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
