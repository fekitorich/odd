import os
from flask import Flask, jsonify, render_template_string, request
from dotenv import load_dotenv

# Importa a sua lógica original
from config import *
from scanner import run_scan

load_dotenv()
app = Flask(__name__)
ENV_API_KEY = os.getenv("ODDS_API_KEY")

# HTML e CSS ORIGINAIS INTEGRADOS (Ignora as pastas templates e static)
HTML_INTEGRADO = """
<!doctype html>
<html lang="en" data-theme="light">
<head>
  <meta charset="utf-8" />
  <title>Edge Scanner</title>
  <style>
    /* CSS ORIGINAL INTEGRADO */
    :root { --bg: #f8fafc; --card: #ffffff; --card-border: #e2e8f0; --text: #1e293b; --accent: #3b82f6; }
    [data-theme="dark"] { --bg: #0f172a; --card: #1e293b; --card-border: #334155; --text: #e2e8f0; }
    body { margin: 0; font-family: sans-serif; background: var(--bg); color: var(--text); padding: 20px; }
    .card { background: var(--card); border: 1px solid var(--card-border); border-radius: 12px; padding: 20px; margin-bottom: 20px; }
    button { background: var(--accent); color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { text-align: left; padding: 12px; border-bottom: 1px solid var(--card-border); }
    .hidden { display: none; }
    /* Adicione aqui o restante do seu style.css se quiser o visual 100% igual */
  </style>
</head>
<body>
  <h1>Edge Scanner (Versão Single-File)</h1>
  <div class="card">
    <form id="scan-form">
      <p>API Key detectada: <strong>{{ "SIM" if has_env_key else "NÃO" }}</strong></p>
      <button type="submit" id="scan-btn">Scan Now</button>
    </form>
  </div>
  <div id="results-area" class="card">
    <h3>Resultados</h3>
    <table id="results-table">
      <thead><tr><th>Sport</th><th>Event</th><th>ROI</th></tr></thead>
      <tbody></tbody>
    </table>
  </div>

  <script>
    const form = document.getElementById('scan-form');
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      document.getElementById('scan-btn').innerText = 'Scanning...';
      const resp = await fetch('/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sports: ['basketball_nba'], regions: ['us','eu'] })
      });
      const data = await resp.json();
      const tbody = document.querySelector('#results-table tbody');
      tbody.innerHTML = '';
      if (data.arbitrage && data.arbitrage.opportunities) {
        data.arbitrage.opportunities.forEach(opp => {
          const row = `<tr><td>${opp.sport}</td><td>${opp.event}</td><td>${opp.roi_percent}%</td></tr>`;
          tbody.innerHTML += row;
        });
      }
      document.getElementById('scan-btn').innerText = 'Scan Now';
    });
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_INTEGRADO, has_env_key=bool(ENV_API_KEY))

@app.route("/scan", methods=["POST"])
def scan():
    payload = request.get_json(force=True, silent=True) or {}
    api_key = ENV_API_KEY or payload.get("apiKey")
    
    # Chama a função original do seu scanner.py
    result = run_scan(
        api_key=api_key,
        sports=payload.get("sports", ["basketball_nba"]),
        all_sports=payload.get("allSports", False),
        stake_amount=float(payload.get("stake", 100.0)),
        regions=payload.get("regions", ["us", "eu"]),
        commission_rate=0.05
    )
    return jsonify(result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
