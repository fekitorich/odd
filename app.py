from __future__ import annotations
import os
import sys
from flask import Flask, render_template, request, render_template_string

# --- TENTA IMPORTAR O SCANNER REAL ---
# Se o scanner.py estiver na pasta, ele usa. Se não, usa um modo de teste para não travar.
try:
    from scanner import run_scan
    SCANNER_AVAILABLE = True
except ImportError:
    SCANNER_AVAILABLE = False
    print("AVISO: scanner.py não encontrado. Usando modo de simulação.")

# --- CONFIGURAÇÕES VISUAIS (RESULTADOS) ---
# Esse HTML fica aqui dentro para você não precisar criar outro arquivo e arriscar erro 500
RESULTS_HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resultados do Scan</title>
    <style>
        body { background-color: #0f172a; color: #e2e8f0; font-family: sans-serif; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: white; border-bottom: 1px solid #334155; padding-bottom: 10px; }
        .btn-back { background: #3b82f6; color: white; text-decoration: none; padding: 10px 20px; border-radius: 5px; display: inline-block; margin-bottom: 20px; font-weight: bold; }
        .btn-back:hover { background: #2563eb; }
        
        /* Tabela de Resultados */
        .table-responsive { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; background: #1e293b; border-radius: 8px; overflow: hidden; }
        th { background: #334155; color: #94a3b8; text-align: left; padding: 15px; text-transform: uppercase; font-size: 12px; }
        td { padding: 15px; border-bottom: 1px solid #334155; font-size: 14px; }
        tr:hover { background: #2d3b4e; }
        
        .tag-edge { background: #064e3b; color: #34d399; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
        .tag-arb { background: #4c1d95; color: #a78bfa; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
        .book-soft { color: #60a5fa; font-weight: bold; }
        .book-sharp { color: #f472b6; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="btn-back">← Voltar para o Scanner</a>
        <h1>Oportunidades Encontradas</h1>
        
        {% if not scanner_active %}
            <div style="background: #7f1d1d; color: #fca5a5; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                ⚠️ <strong>Aviso:</strong> O arquivo 'scanner.py' não foi encontrado ou deu erro. Mostrando dados de exemplo.
            </div>
        {% endif %}

        {% if opportunities %}
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Evento</th>
                            <th>Mercado</th>
                            <th>Aposta (Soft)</th>
                            <th>Aposta (Sharp)</th>
                            <th>Edge / ROI</th>
                            <th>Kelly Stake</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for op in opportunities %}
                        <tr>
                            <td>{{ op.event }}<br><small style="color: #64748b">{{ op.sport }}</small></td>
                            <td>{{ op.market }}</td>
                            <td>
                                <span class="book-soft">{{ op.soft_book }}</span><br>
                                Odd: {{ op.soft_odd }}
                            </td>
                            <td>
                                <span class="book-sharp">{{ op.sharp_book }}</span><br>
                                Odd: {{ op.sharp_odd }}
                            </td>
                            <td><span class="tag-edge">{{ op.edge }}%</span></td>
                            <td>R$ {{ op.stake }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        {% else %}
            <div style="text-align: center; padding: 50px; color: #94a3b8;">
                Nenhuma oportunidade encontrada com os filtros atuais.
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

# Configuração para rodar na raiz
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, template_folder=basedir, static_folder=basedir)

@app.route("/")
def index():
    # Carrega seu index.html (o que você criou no passo anterior)
    try:
        return render_template("index.html", has_env_key=True)
    except Exception:
        return "ERRO: O arquivo index.html não foi encontrado na raiz."

@app.route("/scan", methods=["POST"])
def scan():
    # 1. Coleta os dados do Formulário HTML
    api_key = os.environ.get("ODDS_API_KEY") or request.form.get("apiKey")
    bankroll = float(request.form.get("bankroll", 1000))
    sports = request.form.getlist("sports") # Pega lista de checkboxes
    regions = request.form.getlist("regions")
    commission = float(request.form.get("commission", 5)) / 100.0
    
    opportunities = []

    # 2. Executa o Scan (Real ou Simulado)
    if SCANNER_AVAILABLE:
        try:
            # Tenta rodar a função real do seu scanner.py
            # Adaptamos os parâmetros para o formato que o scanner.py geralmente espera
            raw_results = run_scan(
                api_key=api_key,
                sports=sports,
                regions=regions,
                commission=commission,
                bankroll=bankroll
            )
            # Se o run_scan retornar JSON/Dict, processamos aqui. 
            # Se ele já retornar lista, ótimo. Assumindo que retorna um Dict com "data".
            if isinstance(raw_results, dict):
                opportunities = raw_results.get("data", [])
            else:
                opportunities = raw_results
                
        except Exception as e:
            print(f"Erro ao rodar scanner: {e}")
            # Em caso de erro, lista vazia ou simulação
            pass
    
    # 3. SE NÃO TIVER DADOS (ou scanner falhar), cria dados falsos para você ver a tela funcionando
    if not opportunities and not SCANNER_AVAILABLE:
        opportunities = [
            {
                "event": "Simulação: Lakers vs Warriors",
                "sport": "Basketball",
                "market": "Moneyline",
                "soft_book": "Bet365", "soft_odd": 2.10,
                "sharp_book": "Pinnacle", "sharp_odd": 1.90,
                "edge": 5.2,
                "stake": round(bankroll * 0.02, 2)
            },
            {
                "event": "Simulação: Nadal vs Federer",
                "sport": "Tennis",
                "market": "Winner",
                "soft_book": "DraftKings", "soft_odd": 1.95,
                "sharp_book": "Betfair", "sharp_odd": 1.85,
                "edge": 2.1,
                "stake": round(bankroll * 0.01, 2)
            }
        ]

    # 4. Renderiza a tabela bonita
    return render_template_string(RESULTS_HTML, opportunities=opportunities, scanner_active=SCANNER_AVAILABLE)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
