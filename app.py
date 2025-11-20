from flask import Flask, request, render_template_string, session, send_file
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import os

app = Flask(__name__)
app.secret_key = 'funilspy_pro_2025_marcos'

# HTML principal
HTML = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <title>FunilSpy PRO</title>
    <style>
        body{font-family:Arial;background:#0d1117;color:white;padding:20px;text-align:center}
        .box{max-width:1100px;margin:auto;background:#161b22;padding:40px;border-radius:20px}
        input,button{padding:16px;font-size:18px;border:none;border-radius:12px;margin:10px}
        input{width:70%} button{background:#00ff88;color:black;font-weight:bold;cursor:pointer}
        .resultado{background:#1e1e2e;padding:30px;margin-top:30px;border-radius:15px;text-align:left;line-height:2}
        .mapa{background:#000;padding:20px;border-radius:10px;overflow-x:auto;margin:20px 0}
        .consultoria{background:#4a90e2;padding:25px;border-radius:15px;margin-top:30px}
        .erro{background:#ff4444;padding:15px;border-radius:10px;color:white}
        a{color:#58a6ff;text-decoration:none}
    </style>
</head>
<body>
<div class="box">
    <h1>FunilSpy PRO</h1>
    <form method="post">
        <input name="url" placeholder="ex: ericrocha.com.br, hotmart.com, seu site..." required>
        <button>Espiar Funil Agora!</button>
    </form>
    <div class="resultado">{{resultado|safe}}</div>
</div>
</body>
</html>
'''

def analisar_funil(url_input):
    try:
        url = url_input.strip().replace("https://","").replace("http://","").split("/")[0]
        base = f"https://{url}"
        caminhos = ["/", "/oferta", "/checkout", "/carrinho", "/obrigado", "/upsell", "/promo", "/comprar", "/order-bump"]
        funil = []
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        for caminho in caminhos:
            try:
                r = requests.get(base + caminho, headers=headers, timeout=10)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    titulo = soup.title.string.strip() if soup.title else "Sem título"
                    h1 = soup.find("h1")
                    h1_text = h1.get_text(strip=True) if h1 else "Sem H1"
                    
                    botoes = []
                    for a in soup.find_all("a", href=True):
                        texto = a.get_text(strip=True).lower()
                        if any(p in texto for p in ["comprar","adicionar","continuar","sim quero","pagar","upsell","checkout"]):
                            destino = a['href']
                            if destino.startswith("/"):
                                destino = base + destino
                            elif not destino.startswith("http"):
                                destino = base + "/" + destino
                            botoes.append({"texto": a.get_text(strip=True), "link": destino})
                    
                    funil.append({
                        "etapa": "HOME" if caminho == "/" else caminho[1:].upper(),
                        "url": r.url,
                        "titulo": titulo,
                        "h1": h1_text,
                        "botoes": botoes[:4]
                    })
            except:
                continue
        
        return funil if funil else None, url
    except Exception as e:
        return None, str(e)

def gerar_mapa_svg(funil):
    svg = '<svg width="1000" height="700" xmlns="http://www.w3.org/2000/svg"><g transform="translate(80,80)">'
    y = 0
    for i, etapa in enumerate(funil):
        svg += f'<rect x="0" y="{y}" width="300" height="100" fill="#00ff88" rx="20"/>'
        svg += f'<text x="150" y="{y+40}" fill="black" font-size="18" text-anchor="middle">{etapa["etapa"]}</text>'
        svg += f'<text x="150" y="{y+65}" fill="white" font-size="13" text-anchor="middle">{etapa["h1"][:50]}...</text>'
        if i < len(funil)-1:
            svg += f'<line x1="300" y1="{y+50}" x2="380" y2="{y+150}" stroke="#00ff88" stroke-width="5" marker-end="url(#arrow)"/>'
        y += 180
    svg += '<defs><marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M2,2 L10,6 L2,10 L2,2" fill="#00ff88"/></marker></defs></g></svg>'
    return svg

@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "POST":
        url = request.form["url"]
        funil, info = analisar_funil(url)
        

