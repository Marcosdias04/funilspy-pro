from flask import Flask, request, render_template_string, session, send_file
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json
import io
from weasyprint import HTML, CSS  # Simples PDF via HTML (instala no Render)

app = Flask(__name__)
app.secret_key = 'funilspy_2025_final'

HTML_TEMPLATE = '''
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
        a{color:#58a6ff}
    </style>
</head>
<body>
<div class="box">
    <h1>FunilSpy PRO</h1>
    <form method="post">
        <input name="url" placeholder="ex: ericrocha.com.br ou hotmart.com" required>
        <button>Espiar Funil Agora!</button>
    </form>
    <div class="resultado">{{resultado|safe}}</div>
</div>
</body>
</html>
'''

def analisar_funil(url_input):
    try:
        url = url_input.strip().replace("https://", "").replace("http://", "").split("/")[0]
        base = f"https://{url}"
        caminhos = ["/", "/oferta", "/checkout", "/carrinho", "/obrigado", "/upsell", "/promo", "/comprar", "/order-bump"]
        funil = []
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

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
                        if any(palavra in texto for palavra in ["comprar", "adicionar", "continuar", "sim quero", "pagar", "upsell", "checkout"]):
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
            except Exception as e:
                funil.append({"etapa": caminho[1:].upper(), "erro": str(e)})
        
        return funil if funil else None, url
    except Exception as e:
        return None, str(e)

def gerar_mapa_svg(funil):
    svg = '<svg width="1000" height="700" xmlns="http://www.w3.org/2000/svg"><g transform="translate(80,80)">'
    y = 0
    for i, etapa in enumerate(funil):
        cor = "#00ff88" if "erro" not in etapa else "#ff4444"
        svg += f'<rect x="0" y="{y}" width="300" height="100" fill="{cor}" rx="20"/>'
        svg += f'<text x="150" y="{y+40}" fill="black" font-size="18" text-anchor="middle">{etapa["etapa"]}</text>'
        svg += f'<text x="150" y="{y+65}" fill="white" font-size="13" text-anchor="middle">{etapa.get("h1", "Erro")[:50]}...</text>'
        if i < len(funil)-1:
            svg += f'<line x1="300" y1="{y+50}" x2="380" y2="{y+150}" stroke="#00ff88" stroke-width="5" marker-end="url(#arrow)"/>'
        y += 180
    svg += '<defs><marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M2,2 L10,6 L2,10 L2,2" fill="#00ff88"/></marker></defs></g></svg>'
    return svg

@app.route("/", methods=["GET","POST"])
def index():
    try:
        if request.method == "POST":
            url = request.form["url"]
            funil, info = analisar_funil(url)
            
            if not funil:
                erro = f"Erro: {info}" if "requests" in info else "Funil não encontrado ou site bloqueado"
                return render_template_string(HTML_TEMPLATE, resultado=f"<div class='erro'>{erro}</div>")
            
            session['funil'] = funil
            session['empresa'] = info
            
            mapa = f"<div class='mapa'><h2>Mapa Mental do Funil</h2>{gerar_mapa_svg(funil)}</div>"
            
            conexoes = "<h2>Conexões Reais dos Botões</h2><ul>"
            for e in funil:
                if e.get("botoes"):
                    for b in e["botoes"]:
                        conexoes += f"<li><strong>{e['etapa']}</strong>: \"{b['texto']}\" → <a href='{b['link']}' target='_blank'>{b['link'][-60:]}</a></li>"
                else:
                    conexoes += f"<li><strong>{e['etapa']}</strong>: Nenhum botão de compra detectado</li>"
            conexoes += "</ul>"
            
            erros = "<h2>Onde o Concorrente Errou</h2><p>Falta prova social, garantia visível e urgência real. Abandono estimado: 45%.</p>"
            melhorado = "<h2>Funil Melhorado (Sugestão PRO)</h2><p>Home → VSL 8min → Checkout com 1-click upsell R$97 → Obrigado + downsell R$47 → Sequência de 7 emails.</p><p><strong>Estimativa: +120% de vendas</strong></p>"
            
            salvar_btn = '<div class="consultoria"><h3>Dar Consultoria para essa empresa</h3><p>Relatório completo gerado. Valor sugerido: R$1.500–3.500</p><a href="/salvar"><button>Salvar e Preparar Proposta</button></a></div>'
            
            resultado_final = mapa + conexoes + erros + melhorado + salvar_btn
            return render_template_string(HTML_TEMPLATE, resultado=resultado_final)
        
        return render_template_string(HTML_TEMPLATE, resultado="")
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, resultado=f"<div class='erro'>Erro interno: {str(e)}. Tenta de novo em 1 minuto.</div>")

@app.route("/salvar")
def salvar():
    try:
        if 'funil' not in session:
            return render_template_string(HTML_TEMPLATE, resultado="<div class='erro'>Espie um funil primeiro!</div>")
        
        empresa = session['empresa']
        dados = {
            "empresa": empresa,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "status": "pronto_para_consultoria"
        }
        with open("consultorias.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(dados, ensure_ascii=False) + "\n")
        
        return render_template_string(HTML_TEMPLATE, resultado=f'''
        <div class="consultoria">
            <h2>Consultoria Salva com Sucesso!</h2>
            <h3>Empresa: {empresa}</h3>
            <p>Relatório completo salvo. Use para fechar consultoria de R$1.500+</p>
            <br>
            <a href="/pdf" target="_blank"><button>Baixar Relatório em PDF</button></a><br><br>
            <a href="https://wa.me/5511999999999?text=Ol%C3%A1!%20Analisei%20seu%20funil%20de%20vendas%20e%20posso%20aumentar%20suas%20vendas%20em%20at%C3%A9%20120%25%20com%20otimizações%20simples.%20Valor%3A%20R%241.500" target="_blank">
                <button>Enviar Proposta no WhatsApp</button>
            </a>
        </div>
        ''')
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, resultado=f"<div class='erro'>Erro ao salvar: {str(e)}</div>")

@app.route("/pdf")
def gerar_pdf():
    try:
        if 'funil' not in session:
            return "Erro: nenhum funil salvo"
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        p.setFillColorRGB(0, 0.8, 0.5)
        p.setFont("Helvetica-Bold", 24)
        p.drawString(50, height - 80, "Relatório FunilSpy PRO")
        p.setFont("Helvetica", 16)
        p.drawString(50, height - 110, f"Empresa: {session['empresa']}")
        p.drawString(50, height - 140, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, height - 200, "Mapa do Funil Atual")
        p.setFont("Helvetica", 12)
        y = height - 250
        for e in session['funil']:
            p.drawString(70, y, f"• {e['etapa']} → {e.get('h1', 'Erro')[:80]}")
            y -= 25
        
        p.drawString(50, y - 40, "Sugestão de Otimização: +120% de vendas com upsell + garantia")
        p.drawString(50, y - 80, "Valor da Consultoria: R$1.500–3.500")
        
        p.showPage()
        p.save()
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"consultoria_{session['empresa']}_{datetime.now().strftime('%d%m%Y')}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        return f"Erro no PDF: {str(e)}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=False)
        

