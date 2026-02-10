web: gunicorn app:app --bind 0.0.0.0:$PORT
import os

if __name__ == "__main__":
    # O Railway diz ao seu código em qual porta ele deve rodar
    port = int(os.environ.get("PORT", 8080)) 
    app.run(host='0.0.0.0', port=port)
