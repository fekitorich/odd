import os
import sys
import subprocess
from flask import Flask, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Scanner Terminal</title>
    <style>
        body { background: #0d1117; color: #c9d1d9; font-family: monospace; padding: 20px; }
        .box { background: #161b22; padding: 20px; border: 1px solid #30363d; border-radius: 6px; margin-top: 20px; white-space: pre-wrap; }
        button { background: #238636; color: white; padding: 15px 30px; border: none; border-radius: 6px; cursor: pointer; font-size: 18px; font-weight: bold; width: 100%; }
        button:hover { background: #2ea043; }
        h1 { border-bottom: 1px solid #30363d; padding-bottom: 10px; }
        .error { color: #ff7b72; border-color: #ff7b72; }
        .success { color: #7ee787; border-color: #7ee787; }
    </style>
    <script>
        function showLoading() {
            document.getElementById('btn').innerText = "RODANDO... AGUARDE (Pode demorar 10-20seg)...";
            document.getElementById('btn').style.background = "#9e6a03";
        }
    </script>
</head>
<body>
    <h1>Scanner: Execução Direta</h1>
    <p>Isso roda o comando <code>python scanner.py</code> no servidor.</p>
    
    <form method="POST" action="/run" onsubmit="showLoading()">
        <button type="submit" id="btn">RODAR AGORA</button>
    </form>

    {% if output %}
        <h2>Saída (STDOUT):</h2>
        <div class="box success">{{ output }}</div>
    {% endif %}

    {% if error %}
        <h2>Erros (STDERR):</h2>
        <div class="box error">{{ error }}</div>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML)

@app.route("/run", methods=["POST"])
def run_script():
    try:
        # COMANDO MÁGICO: Executa o arquivo como se fosse no terminal
        # sys.executable garante que usamos o mesmo python do ambiente
        result = subprocess.run(
            [sys.executable, "scanner.py"], 
            capture_output=True, 
            text=True,
            timeout=60 # Espera até 60 segundos antes de desistir
        )
        
        output_text = result.stdout
        error_text = result.stderr

        # Se não saiu nada, avisa
        if not output_text and not error_text:
            output_text = "O script rodou mas não imprimiu nada. Verifique se ele tem 'print()' no final."

        return render_template_string(HTML, output=output_text, error=error_text)

    except subprocess.TimeoutExpired:
        return render_template_string(HTML, error="O scanner demorou mais de 60 segundos e foi cancelado.")
    except Exception as e:
        return render_template_string(HTML, error=f"Erro ao tentar executar: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
