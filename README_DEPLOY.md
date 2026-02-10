Deploy rápido no Render

Passos resumidos para ter um URL estável (Render):

1. Faça push deste repositório para o GitHub (se ainda não estiver):

```bash
git add .
git commit -m "Prepare app for Render"
git push origin main
```

2. No Render (https://render.com) crie um novo **Web Service** e conecte seu repositório GitHub.
   - Build Command: `pip install -r requirements.txt`
   - Start Command: use o `Procfile` (Render detecta automaticamente) ou `gunicorn app:app --bind 0.0.0.0:$PORT`
   - Ambiente: informe a variável `ODDS_API_KEY` nas Environment Settings.

3. Deploy: o Render fará build e exporá uma URL permanente (ex: `https://my-app.onrender.com`).

Observações:
- Se preferir não usar GitHub, você pode empacotar a app como uma imagem Docker e fazer deploy em qualquer provedor que aceite contêineres.
- Certifique-se de configurar `ODDS_API_KEY` nas variáveis de ambiente da instância Render para que a rota `/scan` funcione com dados reais.
