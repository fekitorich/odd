import sys
import io
import os
from flask import Flask, render_template_string, request

# Importa o seu scanner original
import scanner

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Scanner Original (Output Real)</title>
    <style>
        body { background: #0d1117; color: #c9d1d9; font-family: monospace; padding: 20px; }
        .console { background: #161b22; padding: 20px; border: 1px solid #30363d; border-radius: 6px; white-space: pre-wrap; word-wrap: break-word; }
        button { background: #238636; color: white; padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; }
        button:hover { background: #2ea043; }
        h1 { border-bottom: 1px solid #30363d; padding-bottom: 10px; }
    </style>
</head>
<body>
    <h1>Scanner Original</h1>
    <p>Este botão roda o scanner usando EXATAMENTE o seu config.py</p>
    
    <form method="POST" action="/run">
        <button type="submit">RODAR SCANNER</button>
    </form>

    {% if output %}
        <h2>Resultado do Terminal:</h2>
        <div class="console">{{ output }}</div>
    {% endif %}
    
    {% if error %}
        <h2 style="color: #ff7b72">Erro:</h2>
        <div class="console" style="border-color: #ff7b72;">{{ error }}</div>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML)

@app.route("/run", methods=["POST"])
def run_scanner():
    # 1. Cria um "bloco de notas" na memória para capturar o que o scanner imprimir
    capture_output = io.StringIO()
    original_stdout = sys.stdout # Guarda a saída original
    sys.stdout = capture_output  # Desvia os prints para nossa memória

    output_text = ""
    error_text = None

    try:
        # 2. Tenta rodar a função principal do scanner original
        # A maioria dos scripts tem run_scan ou main
        if hasattr(scanner, 'main'):
            scanner.main()
        elif hasattr(scanner, 'run_scan'):
            # Chama SEM ARGUMENTOS para forçar o uso do config.py
            try:
                scanner.run_scan()
            except TypeError:
                # Se ele exigir argumentos, passamos None para ele tentar usar defaults
                # Mas o ideal é que ele leia do config
                scanner.run_scan(None, None, None, None, None)
        else:
            print("AVISO: Não achei função 'main' ou 'run_scan'. Tentando executar o arquivo...")
            # Último recurso: executa o script inteiro
            exec(open("scanner.py").read())

    except Exception as e:
        error_text = str(e)
        import traceback
        error_text += "\n" + traceback.format_exc()
    
    finally:
        # 3. Restaura a saída original e pega o texto
        sys.stdout = original_stdout
        output_text = capture_output.getvalue()

    return render_template_string(HTML, output=output_text, error=error_text)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
