import os
import sys
from flask import Flask, render_template_string, request

# Tenta importar o scanner original e suas configurações
try:
    import config  # Se o original tem config.py, isso garante que ele seja lido
    import scanner # O arquivo original
except ImportError as e:
    print(f"ERRO CRÍTICO: Faltam arquivos originais. {e}")

app = Flask(__name__)

# HTML Básico (Apenas para exibir o resultado do scanner original)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Scanner Original</title>
    <style>
        body { background: #111; color: #eee; font-family: sans-serif; padding: 20px; }
        button { background: #007bff; color: white; padding: 15px 30px; border: none; font-size: 18px; cursor: pointer; }
        button:hover { background: #0056b3; }
        pre { background: #222; padding: 15px; overflow-x: auto; border: 1px solid #444; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #444; padding: 10px; text-align: left; }
        th { background: #333; }
    </style>
</head>
<body>
    <h1>Scanner de Arbitragem (Original)</h1>
    <form method="POST" action="/scan">
        <label>API Key (Opcional se já estiver no Config):</label><br>
        <input type="text" name="apiKey" style="width: 300px; padding: 10px; margin-bottom: 10px;" placeholder="Sua Key aqui...">
        <br>
        <button type="submit">RODAR SCANNER AGORA</button>
    </form>
    
    {% if result %}
        <h2>Resultados:</h2>
        {% if result is iterable and result is not string %}
            <table>
                <thead>
                    <tr>
                        {% for key in result[0].keys() %}
                        <th>{{ key }}</th>
                        {% endfor %}
                    </tr>
                </thead>
                <tbody>
                    {% for item in result %}
                    <tr>
                        {% for value in item.values() %}
                        <td>{{ value }}</td>
                        {% endfor %}
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        {% else %}
            <pre>{{ result }}</pre>
        {% endif %}
    {% endif %}
    
    {% if error %}
        <div style="color: red; margin-top: 20px;">
            <h3>Erro:</h3>
            <pre>{{ error }}</pre>
        </div>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/scan", methods=["POST"])
def scan_route():
    api_key = request.form.get("apiKey")
    # Se o usuário der API Key, tenta injetar no config
    if api_key and hasattr(config, 'API_KEY'):
        config.API_KEY = api_key

    try:
        # TENTA RODAR A FUNÇÃO DO ARQUIVO ORIGINAL
        # Verifica qual nome de função o original usa
        if hasattr(scanner, 'run_scan'):
            # Tenta passar argumentos padrão
            data = scanner.run_scan(api_key, [], [], 5, 1000)
        elif hasattr(scanner, 'main'):
            data = scanner.main()
        elif hasattr(scanner, 'scan'):
            data = scanner.scan()
        else:
            return render_template_string(HTML_TEMPLATE, error="Não encontrei a função principal no scanner.py original.")
            
        return render_template_string(HTML_TEMPLATE, result=data)

    except Exception as e:
        return render_template_string(HTML_TEMPLATE, error=f"O código original quebrou com erro: {str(e)}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
