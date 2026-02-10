import os
import requests
from flask import Flask, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>DIAGNÓSTICO DA API</title>
    <style>
        body { background: #000; color: #fff; font-family: monospace; padding: 20px; text-align: center; }
        .box { border: 2px solid #fff; padding: 20px; margin: 20px auto; max-width: 600px; border-radius: 10px; }
        h1 { color: yellow; }
        .big-number { font-size: 48px; font-weight: bold; }
        .red { color: #ff5252; border-color: #ff5252; }
        .green { color: #00e676; border-color: #00e676; }
        button { font-size: 20px; padding: 15px 30px; cursor: pointer; background: yellow; border: none; font-weight: bold; }
    </style>
</head>
<body>
    <h1>🕵️ DIAGNÓSTICO DE SAÚDE DA API</h1>
    
    <form method="POST" action="/check">
        <button type="submit">CHECAR MINHA CONTA AGORA</button>
    </form>

    {% if checked %}
        <div class="box {{ 'green' if success else 'red' }}">
            <h2>Status da API Key:</h2>
            <p style="font-size: 24px;">{{ status_msg }}</p>
            
            <hr style="border-color: #333;">
            
            <p>Requisições Restantes:</p>
            <div class="big-number">{{ remaining }}</div>
            
            <p>Requisições Usadas:</p>
            <div class="big-number">{{ used }}</div>
        </div>

        {% if raw_error %}
            <div style="color: red; text-align: left; background: #220000; padding: 10px;">
                <strong>RESPOSTA BRUTA DA API (ERRO):</strong><br>
                {{ raw_error }}
            </div>
        {% endif %}
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML)

@app.route("/check", methods=["POST"])
def check():
    api_key = os.environ.get("ODDS_API_KEY") or os.environ.get("API_KEY")
    
    if not api_key:
        return render_template_string(HTML, checked=True, success=False, status_msg="ERRO: Nenhuma API KEY encontrada no Railway Variables.", remaining="---", used="---")

    # Faz uma requisição leve para testar a chave
    # Usamos 'upcoming' para qualquer esporte só pra pegar os headers
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {
        "apiKey": api_key,
        "regions": "us",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }

    try:
        response = requests.get(url, params=params)
        
        # A TheOddsAPI manda essas informações no Cabeçalho (Headers) da resposta
        remaining = response.headers.get("x-requests-remaining", "Desconhecido")
        used = response.headers.get("x-requests-used", "Desconhecido")
        
        if response.status_code == 200:
            return render_template_string(HTML, checked=True, success=True, 
                                          status_msg="✅ CHAVE ATIVA E FUNCIONANDO", 
                                          remaining=remaining, used=used)
        elif response.status_code == 401:
            return render_template_string(HTML, checked=True, success=False, 
                                          status_msg="❌ CHAVE INVÁLIDA OU EXPIRADA", 
                                          remaining="0", used=used, raw_error=response.text)
        elif response.status_code == 422 or "quota" in response.text.lower():
             return render_template_string(HTML, checked=True, success=False, 
                                          status_msg="💀 QUOTA EXCEDIDA (Acabou o limite)", 
                                          remaining="0", used=used, raw_error=response.text)
        else:
            return render_template_string(HTML, checked=True, success=False, 
                                          status_msg=f"⚠️ ERRO DE CONEXÃO: {response.status_code}", 
                                          remaining=remaining, used=used, raw_error=response.text)

    except Exception as e:
        return render_template_string(HTML, checked=True, success=False, status_msg="ERRO INTERNO NO PYTHON", remaining="---", used="---", raw_error=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
