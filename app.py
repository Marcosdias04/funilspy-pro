from flask import Flask, request, render_template_string, jsonify
import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <title>FunilSpy PRO</title>
    <style>
        body {font-family: Arial; background: #0d1117; color: white; padding: 20px; text-align: center;}
        .box {max-width: 1100px; margin: auto; background: #161b22; padding: 40px; border-radius: 20px;}
        input, button {padding: 16px; font-size: 18px; border: none; border-radius: 12px; margin: 10px;}
        input {width: 70%;}
        button {background: #00ff88; color: black; font-weight: bold; cursor: pointer;}
        .resultado {background: #1e1e2e; padding: 30px; margin-top: 30px; border-radius: 15px; text-align: left; line-height: 2;}
        .mapa {background: #000; padding: 20px; border-radius: 10px; margin: 20px 0;}
        .consultoria {background: #4a90e2; padding: 20px; border-radius: 15px; margin-top: 30px;}
        a {color: #58a6ff;}
    </style>
</head>
<body>
<div class="box">
    <h1>FunilSpy PRO</h1>
    <form method="post">
        <input name="url" placeholder="ex: ericrocha.com.br ou hotmart.com" required>
        <button type="submit">Espiar Funil Agora</button>
    </form>
    <div class="resultado">{{resultado|safe}}</div>
</div>
</body>
</html>
'''

def analisar(url):
    urls = ["", "/oferta", "/checkout", "/carrinho", "/obrigado", "/upsell", "/order-bump", "/promo"]
    funil = []
    for p in urls:
        try:
            r = requests.get("https://"+url+p, timeout=8, headers={"User-Agent":"Mozilla/5.0"})
            if r.status_code == 200:
                s = BeautifulSoup(r.text, 'html.parser')
                titulo = s.title.string.strip() if s.title else "Sem título"
                h1 = s.find("h1")
                h1_text = h1.get_text(strip=True) if h1 else ""
                botoes = [a.get('href') for a in s.find_all('a', href=True) if any(x in a.get_text().lower() for x in ["comprar","adicionar","continuar","sim quero"])]
                funil.append({"etapa": p or "Home", "url": r.url, "titulo": titulo, "h1": h1_text, "botoes": botoes[:5]})
        except:
            pass
    return funil

def gerar_mapa(funil):
    svg = '<svg width="100%" height="500" xmlns="http://www.w3.org/2000/svg"><g transform="translate(100,50)">'
    y = 0
    for i, etapa in enumerate(funil):
        svg += f'<rect x="0" y="{y}" width="300" height="80" fill="#238636" rx="15"/><text x="150" y="{y+45}" fill="white" font-size="18" text-anchor="middle">{etapa["etapa"].upper()}</text>'
        if i < len(funil)-1:
            svg += f'<line x1="300" y1="{y+40}" x2="380" y2="{y+100}" stroke="#00ff88" stroke-width="4" marker-end="url(#arrow)"/>'
        y += 120
    svg += '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#00ff88"/></marker></defs></g></svg>'
    return svg

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        url = request.form["url"].lower().replace("https://","").replace("http://","").split("/")[0]
        funil = analisar(url)
        if not funil:
            return render_template_string(HTML, resultado="<h3 style='color:#ff4444'>Funil não encontrado ou bloqueado</h3>")

        mapa = gerar_mapa(funil)
        lista = "<h2>Mapa do Funil</h2>" + mapa
        lista += "<h2>Análise de Copy & Conexões</h2><ul>"
        for e in funil:
            lista += f"<li><strong>{e['etapa'].upper()}</strong> → {e['url']}<br>H1: {e['h1']}<br>Botões levam para: {', '.join(e['botoes']) or 'Nenhum detectado'}</li>"
        lista += "</ul>"

        lista += "<h2>Onde ele errou</h2><p>Falta prova social, garantia visível e urgência real.</p>"
        lista += "<h2>Funil Melhorado (Sugestão Minha)</h2><p>Home → Vídeo VSL → Checkout com 1-click upsell R$97 → Obrigado com downsell R$47 → Email sequência 7 dias.</p>"
        lista += '<div class="consultoria"><h3>Dar Consultoria para essa empresa</h3><p>Relatório completo pronto. Preço sugerido: R$1.500–3.000</p><a href="https://wa.me/5511999999999?text=Ol%C3%A1!%20Analisei%20seu%20funil%20e%20posso%20aumentar%20suas%20vendas%20em%2030-50%25" target="_blank"><button>Enviar Proposta no WhatsApp</button></a></div>'

        return render_template_string(HTML, resultado=lista)
    return render_template_string(HTML, resultado="")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
