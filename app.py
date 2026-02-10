import sys
import os
from flask import Flask, render_template_string, request
from dotenv import load_dotenv

# Carrega variáveis de ambiente (.env ou Railway Variables)
load_dotenv()

# Importa seu scanner original
import scanner 

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Scanner Automático</title>
    <style>
        body { background: #121212; color: #e0e0e0; font-family: sans-serif; padding: 20px; }
        .container { max-width: 900px; margin: 0 auto; }
        .status { padding: 15px; background: #333; margin-bottom: 20px; border-left: 5px solid #00e676; }
        button { background: #00e676; color: black; padding: 15px 30px; border: none; font-size: 18px; font-weight: bold; cursor: pointer; width: 100%; }
        button:hover { background: #00c853; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; border: 1px solid #333; }
        th, td { padding: 12px; border: 1px solid #444; text-align: left; }
        th { background: #1f1f1f; color: #00e676; }
        tr:nth-child(even) { background: #1a1a1a; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Scanner de Arbitragem</h1>
        
        <div class="status">
            Status da Chave: 
            {% if has_key %} 
                <strong style="color: #00e676">DETECTADA ({{ key_source }})</strong>
            {% else %}
                <strong style="color: #ff5252">NÃO ENCONTRADA</strong> <br>
                <small>Configure ODDS_API_KEY nas variáveis do Railway.</small>
            {% endif %}
        </div>

        <form method="POST" action="/scan">
            <button type="submit">RODAR SCANNER AGORA</button>
        </form>

        {% if searched %}
            <h2>Resultados</h2>
            {% if results %}
                <table>
                    <thead>
                        <tr>
                            {% for key in results[0].keys() %}
                            <th>{{ key }}</th>
                            {% endfor %}
                        </tr>
                    </thead>
                    <tbody>
                        {% for row in results %}
                        <tr>
                            {% for cell in row.values() %}
                            <td>{{ cell }}</td>
                            {% endfor %}
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            {% else %}
                <p>Scanner rodou mas não retornou oportunidades no momento.</p>
            {% endif %}
        {% endif %}

        {% if error %}
            <div style="color: #ff5252; margin-top: 20px;">
                <h3>Erro:</h3>
                <pre>{{ error }}</pre>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    # Verifica se a chave existe no ambiente
    api_key = os.environ.get("ODDS_API_KEY") or os.environ.get("API_KEY")
    return render_template_string(HTML, has_key=(api_key is not None), key_source="Ambiente/.env")

@app.route("/scan", methods=["POST"])
def scan():
    # 1. Tenta pegar a chave do ambiente
    api_key = os.environ.get("ODDS_API_KEY") or os.environ.get("API_KEY")
    
    if not api_key:
        return render_template_string(HTML, error="ERRO: API Key não encontrada nas variáveis de ambiente.")

    # Configurações fixas ou pegas do ambiente também
    sports = ['basketball_nba', 'americanfootball_nfl'] # Pode adicionar mais
    regions = ['us', 'eu', 'uk', 'au'] # Pega tudo para garantir
    commission = 0.05
    bankroll = 1000

    results = []
    error_msg = None

    try:
        # 2. Chama o scanner original
        # Passamos a API Key direto para garantir que ele use a certa
        if hasattr(scanner, 'run_scan'):
            results = scanner.run_scan(api_key, sports, regions, commission, bankroll)
        elif hasattr(scanner, 'main'):
            # Se for main(), torcemos para ele ler do os.environ internamente
            results = scanner.main()
        else:
            error_msg = "Função 'run_scan' não encontrada no scanner.py."

    except Exception as e:
        error_msg = f"Erro na execução: {str(e)}"

    return render_template_string(HTML, has_key=True, searched=True, results=results, error=error_msg)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
