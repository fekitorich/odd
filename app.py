import sys
import io
import os
from flask import Flask, render_template_string

# Tenta importar o scanner original
try:
    import scanner
except ImportError as e:
    scanner = None
    import_error = str(e)

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Scanner: Forçar Execução</title>
    <style>
        body { background: #111; color: #ddd; font-family: sans-serif; padding: 20px; }
        .box { background: #222; padding: 15px; border: 1px solid #444; margin-top: 20px; white-space: pre-wrap; }
        button { background: #007bff; color: white; padding: 15px; border: none; font-size: 18px; cursor: pointer; width: 100%; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #555; padding: 8px; text-align: left; }
        th { color: #00e676; }
    </style>
</head>
<body>
    <h1>Scanner Original</h1>
    <p>Status do arquivo scanner.py: 
       {% if scanner_ok %} <span style="color: #00e676">CARREGADO</span> 
       {% else %} <span style="color: red">ERRO: {{ import_error }}</span> {% endif %}
    </p>

    <form method="POST" action="/run">
        <button type="submit">FORÇAR EXECUÇÃO (Scan)</button>
    </form>

    {% if output %}
        <h2>Resultado (Texto):</h2>
        <div class="box" style="border-color: #00e676;">{{ output }}</div>
    {% endif %}

    {% if data_list %}
        <h2>Resultado (Tabela de Dados):</h2>
        <table>
            <thead>
                <tr>
                    {% for key in data_list[0].keys() %}
                    <th>{{ key }}</th>
                    {% endfor %}
                </tr>
            </thead>
            <tbody>
                {% for item in data_list %}
                <tr>
                    {% for val in item.values() %}
                    <td>{{ val }}</td>
                    {% endfor %}
                </tr>
                {% endfor %}
            </tbody>
        </table>
    {% endif %}

    {% if error %}
        <h2 style="color: red">Erro:</h2>
        <div class="box" style="border-color: red;">{{ error }}</div>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML, scanner_ok=(scanner is not None), import_error=locals().get('import_error', ''))

@app.route("/run", methods=["POST"])
def run_scan():
    if not scanner:
        return render_template_string(HTML, error="O arquivo scanner.py não pôde ser importado.")

    # Captura prints (caso o scanner apenas imprima na tela)
    capture = io.StringIO()
    sys.stdout = capture
    
    result_data = None
    execution_error = None

    try:
        # TENTA ACHAR A FUNÇÃO CERTA E RODAR
        # Verifica as funções mais comuns usadas em scripts
        if hasattr(scanner, 'main'):
            result_data = scanner.main()
        elif hasattr(scanner, 'run_scan'):
            # Tenta rodar sem argumentos (pegando do config)
            try:
                result_data = scanner.run_scan()
            except TypeError:
                # Se pedir argumentos, tenta passar listas vazias
                result_data = scanner.run_scan(None, [], [], None, 1000)
        elif hasattr(scanner, 'scan'):
            result_data = scanner.scan()
        else:
            execution_error = "Não achei uma função conhecida (main, run_scan, scan) no arquivo original."
            
    except Exception as e:
        execution_error = f"Ocorreu um erro ao rodar a função interna: {str(e)}"
    
    sys.stdout = sys.__stdout__ # Devolve o print pro lugar certo
    printed_output = capture.getvalue()

    # Se o resultado for uma lista (dados), passamos para a tabela
    is_list = isinstance(result_data, list) and len(result_data) > 0
    
    if not printed_output and not is_list and not execution_error:
        printed_output = "A função rodou mas não retornou dados nem imprimiu texto. O scanner pode não ter encontrado oportunidades hoje."

    return render_template_string(HTML, 
                                  scanner_ok=True, 
                                  output=printed_output, 
                                  data_list=result_data if is_list else None, 
                                  error=execution_error)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
