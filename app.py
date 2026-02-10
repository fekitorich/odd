import sys
import os
from flask import Flask, render_template_string, request

# Importa o scanner original (que você já subiu)
import scanner

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Scanner Original - Interface</title>
    <style>
        body { background: #121212; color: #e0e0e0; font-family: sans-serif; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        input, select { width: 100%; padding: 10px; margin: 10px 0; background: #333; border: 1px solid #555; color: white; }
        button { background: #00e676; color: black; padding: 15px; width: 100%; border: none; font-weight: bold; cursor: pointer; }
        button:hover { background: #00c853; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; border: 1px solid #333; }
        th, td { padding: 10px; border: 1px solid #444; text-align: left; }
        th { background: #1f1f1f; color: #00e676; }
        tr:nth-child(even) { background: #1a1a1a; }
        .error { color: #ff5252; background: rgba(255, 82, 82, 0.1); padding: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Scanner de Arbitragem (Original)</h1>
        
        <form method="POST" action="/scan">
            <label>Sua API Key (TheOddsAPI):</label>
            <input type="text" name="apiKey" placeholder="Cole a chave aqui..." required>
            
            <label>Esportes (Separados por vírgula):</label>
            <input type="text" name="sports" value="basketball_nba" placeholder="Ex: basketball_nba,americanfootball_nfl">
            
            <button type="submit">RODAR SCANNER</button>
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
                <p>O scanner rodou com sucesso, mas não encontrou oportunidades com os filtros atuais.</p>
            {% endif %}
        {% endif %}

        {% if error %}
            <div class="error">
                <strong>Erro:</strong> {{ error }}
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML)

@app.route("/scan", methods=["POST"])
def scan():
    # 1. Pega os dados do formulário
    api_key = request.form.get("apiKey")
    sports_input = request.form.get("sports")
    
    # Transforma 'basketball_nba, soccer_epl' em lista ['basketball_nba', 'soccer_epl']
    sports_list = [s.strip() for s in sports_input.split(',')] if sports_input else ['basketball_nba']
    
    # 2. Configurações padrão (já que não temos inputs pra tudo)
    regions = ['us', 'eu', 'uk'] 
    commission = 0.05
    bankroll = 1000

    results = []
    error_msg = None

    try:
        # 3. CHAMA A FUNÇÃO DO SCANNER ORIGINAL PASSANDO OS DADOS
        # Isso garante que a API Key chegue lá dentro
        if hasattr(scanner, 'run_scan'):
            results = scanner.run_scan(api_key, sports_list, regions, commission, bankroll)
        elif hasattr(scanner, 'main'):
            # Se for main(), ele pode não aceitar argumentos, aí dependemos do config.py
            results = scanner.main()
        else:
            error_msg = "Não encontrei a função 'run_scan' no seu arquivo scanner.py."

    except Exception as e:
        error_msg = f"O scanner original deu erro: {str(e)}"

    return render_template_string(HTML, searched=True, results=results, error=error_msg)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
