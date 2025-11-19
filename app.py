from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import qrcode
import io
# ... outros imports ...
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "chave_secreta_do_totem"
SENHA_ADMIN = "admin123"

# Configuração do Banco
import os

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'lava_rapido.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- CONFIGURAÇÃO DOS PACOTES E HARDWARE (Baseado no PPT) ---
PACOTES = {
    "1": {
        "nome": "BÁSICO (Lavar)",
        "desc": "Alta Pressão + Espuma",
        "itens": ["Lavadora", "Shampozeira"],  # [cite: 1]
        "hardware": {"lavadora": True, "shampoo": True, "aspirador": False, "ar": False},  # [cite: 22, 23]
        "precos": {
            10: 15.00,  # [cite: 4, 7]
            20: 22.50,  # [cite: 5, 13]
            30: 30.00  # [cite: 6, 9]
        }
    },
    "2": {
        "nome": "INTERMEDIÁRIO (Lavar + Aspirar)",
        "desc": "Alta Pressão + Espuma + Aspirador",
        "itens": ["Lavadora", "Shampozeira", "Aspirador"],  # [cite: 2]
        "hardware": {"lavadora": True, "shampoo": True, "aspirador": True, "ar": False},  # [cite: 24]
        "precos": {
            10: 25.00,  # [cite: 8]
            20: 31.25,  # [cite: 14]
            30: 37.50  # Proporcional
        }
    },
    "3": {
        "nome": "COMPLETO (Secar + Ar)",
        "desc": "Pressão + Espuma + Aspirador + Ar Comprimido",
        "itens": ["Lavadora", "Shampozeira", "Aspirador", "Ar Comprimido"],  # [cite: 3]
        "hardware": {"lavadora": True, "shampoo": True, "aspirador": True, "ar": True},  # [cite: 25]
        "precos": {
            10: 30.00,  # [cite: 9]
            20: 35.00,  # [cite: 15]
            30: 45.00
        }
    }
}


# Modelo de Venda
class Venda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    servico = db.Column(db.String(100))
    tempo = db.Column(db.Integer)
    valor = db.Column(db.Float)
    baia = db.Column(db.Integer)
    metodo_pagamento = db.Column(db.String(50))
    data_hora = db.Column(db.DateTime, default=datetime.now)


with app.app_context():
    db.create_all()


# --- FUNÇÃO DE CONTROLE DE HARDWARE (IoT) ---
def ativar_hardware(pacote_id, tempo_minutos):
    pacote = PACOTES.get(pacote_id)
    hw = pacote['hardware']

    print(f"\n--- INICIANDO HARDWARE (Tempo: {tempo_minutos} min) ---")

    if hw['lavadora']:
        print("⚡ RELÉ 1 LIGADO: Energiza Lavadora Alta Pressão")  # [cite: 22]
    if hw['shampoo']:
        print("⚡ RELÉ 2 LIGADO: Energiza Shampozeira")  # [cite: 23]
    if hw['aspirador']:
        print("⚡ RELÉ 3 LIGADO: Energiza Aspirador")  # [cite: 24]
    if hw['ar']:
        print("💨 VÁLVULA ABERTA: Libera Ar Comprimido")  # [cite: 25]

    print("----------------------------------------------------\n")
    # Aqui entraria o código da biblioteca RPi.GPIO para o Raspberry Pi real


# --- ROTAS ---

@app.route("/")
def welcome():
    session.clear()
    return render_template("1_welcome.html")


@app.route("/selecao")
def selection():
    # Envia os pacotes para o HTML desenhar a tela
    return render_template("2_selection.html", pacotes=PACOTES)


@app.route("/salvar_servico", methods=["POST"])
def salvar_servico():
    # Recebe qual pacote e qual tempo o cliente escolheu
    pacote_id = request.form.get("pacote_id")
    tempo_escolhido = int(request.form.get("tempo"))

    pacote = PACOTES[pacote_id]
    valor = pacote['precos'][tempo_escolhido]

    session['servico_id'] = pacote_id
    session['servico_nome'] = f"{pacote['nome']} ({tempo_escolhido} min)"
    session['servico_valor'] = valor
    session['servico_tempo'] = tempo_escolhido

    return redirect(url_for('bays'))


@app.route("/baias")
def bays():
    return render_template("3_bays.html", baias={1: False, 2: True, 3: False, 4: True})


@app.route("/salvar_baia/<int:numero_baia>")
def salvar_baia(numero_baia):
    session['baia_escolhida'] = numero_baia
    return redirect(url_for('payment'))


@app.route("/pagamento")
def payment():
    return render_template("4_payment.html",
                           servico=session.get('servico_nome'),
                           valor=session.get('servico_valor'),
                           baia=session.get('baia_escolhida'))


@app.route("/gerar_qrcode")
def gerar_qrcode():
    valor = session.get('servico_valor', 0.00)
    servico = session.get('servico_nome', 'Serviço')
    dados_pix = f"LAVA-RAPIDO-PAGAMENTO-{servico}-R${valor}"
    img = qrcode.make(dados_pix)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


@app.route("/processar_pagamento", methods=["POST"])
def processar_pagamento():
    metodo = request.form.get("metodo")

    # 1. Salva no Banco
    nova_venda = Venda(
        servico=session.get('servico_nome'),
        tempo=session.get('servico_tempo'),
        valor=session.get('servico_valor'),
        baia=session.get('baia_escolhida'),
        metodo_pagamento=metodo
    )
    db.session.add(nova_venda)
    db.session.commit()

    # 2. Ativa o Hardware (Simulação)
    pacote_id = session.get('servico_id')
    tempo = session.get('servico_tempo')
    ativar_hardware(pacote_id, tempo)

    return redirect(url_for('confirmation'))


@app.route("/confirmacao")
def confirmation():
    return render_template("5_confirm.html", baia=session.get('baia_escolhida'))


@app.route("/recibo")
def receipt():
    return render_template("6_receipt.html")


# --- ADMIN E LOGIN (Mantidos iguais) ---
@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    if request.method == "POST":
        if request.form.get("senha") == SENHA_ADMIN:
            session['usuario_logado'] = True
            return redirect(url_for('admin'))
        else:
            erro = "Senha incorreta!"
    return render_template("login.html", erro=erro)


@app.route("/logout")
def logout():
    session.pop('usuario_logado', None)
    return redirect(url_for('welcome'))


@app.route("/admin")
def admin():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    todas_vendas = Venda.query.order_by(Venda.data_hora.desc()).all()
    total_faturado = sum(v.valor for v in todas_vendas)

    dados_grafico = {}
    for v in todas_vendas:
        dados_grafico[v.servico] = dados_grafico.get(v.servico, 0) + 1

    return render_template("admin.html",
                           vendas=todas_vendas,
                           total=total_faturado,
                           nomes_servicos=list(dados_grafico.keys()),
                           contagem_vendas=list(dados_grafico.values()))

# --- NOVA ROTA: GERAR PDF ---
@app.route("/baixar_recibo")
def baixar_recibo():
    # 1. Cria um arquivo na memória (não no disco)
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    # 2. Dados da Venda (da sessão)
    servico = session.get('servico_nome', 'Serviço Avulso')
    valor = session.get('servico_valor', 0.0)
    baia = session.get('baia_escolhida', 0)
    data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")

    # 3. Desenhando o PDF (Coordenadas X, Y - O Y=0 é o fundo da página)
    p.setTitle(f"Recibo - {servico}")

    # Cabeçalho
    p.setFont("Helvetica-Bold", 20)
    p.drawString(200, 800, "LAVA RÁPIDO SELF-SERVICE")

    p.setFont("Helvetica", 12)
    p.drawString(200, 780, "Comprovante de Pagamento")
    p.line(100, 770, 500, 770) # Linha divisória

    # Detalhes
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, 730, f"SERVIÇO: {servico}")

    p.setFont("Helvetica", 12)
    p.drawString(100, 700, f"DATA: {data_hoje}")
    p.drawString(100, 680, f"LOCAL: Baia {baia}")
    p.drawString(100, 660, "MÉTODO: Pagamento Digital / Totem")

    # Total
    p.line(100, 630, 500, 630)
    p.setFont("Helvetica-Bold", 25)
    p.drawString(100, 590, f"TOTAL: R$ {valor:.2f}")

    # Rodapé
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(100, 500, "Obrigado pela preferência!")
    p.drawString(100, 485, "Visite: lorcanaru.pythonanywhere.com")

    # 4. Finaliza o PDF
    p.showPage()
    p.save()

    # 5. Envia para o navegador baixar
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"Recibo_LavaRapido_{datetime.now().strftime('%Y%m%d')}.pdf", mimetype='application/pdf')
if __name__ == "__main__":
    app.run(debug=True)