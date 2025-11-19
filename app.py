from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import qrcode
import io
import threading
import time
# ... outros imports ...
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ... (Imports do GPIO e Classe Falsa continuam iguais) ...
try:
    from gpiozero import OutputDevice

    RPI_REAL = True
except ImportError:
    RPI_REAL = False


    class OutputDevice:
        def __init__(self, pin, active_high=True): pass

        def on(self): pass

        def off(self): pass

app = Flask(__name__)
app.secret_key = "chave_secreta_do_totem"
SENHA_ADMIN = "admin123"

# Configuração do Banco
import os

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'lava_rapido.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- ESTADO GLOBAL (Para sincronizar as duas telas) ---
# Guarda quando a lavagem vai acabar.
ESTADO_ATUAL = {
    "em_uso": False,
    "fim_em": None,  # Vai guardar o datetime do fim
    "pacote_nome": ""
}

# --- CONFIGURAÇÃO PACOTES E HARDWARE (MANTIDO IGUAL) ---
PACOTES = {
    "1": {"nome": "BÁSICO", "desc": "Alta Pressão + Espuma", "itens": ["Lavadora", "Shampozeira"],
          "hardware": {"lavadora": True, "shampoo": True, "aspirador": False, "ar": False},
          "precos": {10: 15.00, 20: 22.50, 30: 30.00}},
    "2": {"nome": "INTERMEDIÁRIO", "desc": "Alta Pressão + Espuma + Aspirador",
          "itens": ["Lavadora", "Shampozeira", "Aspirador"],
          "hardware": {"lavadora": True, "shampoo": True, "aspirador": True, "ar": False},
          "precos": {10: 25.00, 20: 31.25, 30: 37.50}},
    "3": {"nome": "COMPLETO", "desc": "Pressão + Espuma + Aspirador + Ar",
          "itens": ["Lavadora", "Shampozeira", "Aspirador", "Ar Comprimido"],
          "hardware": {"lavadora": True, "shampoo": True, "aspirador": True, "ar": True},
          "precos": {10: 30.00, 20: 35.00, 30: 45.00}}
}

# ... (Definição de Pinos GPIO continua igual) ...
rele_lavadora = OutputDevice(17, active_high=False)
rele_shampoo = OutputDevice(27, active_high=False)
rele_aspirador = OutputDevice(22, active_high=False)
rele_ar = OutputDevice(23, active_high=False)


# ... (Classe Venda continua igual) ...
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


# --- THREAD DE HARDWARE (ATUALIZADA PARA CONTROLAR O ESTADO) ---
def ciclo_lavagem_thread(hw, tempo_segundos, nome_pacote):
    global ESTADO_ATUAL

    # Atualiza o estado para "EM USO"
    ESTADO_ATUAL["em_uso"] = True
    ESTADO_ATUAL["pacote_nome"] = nome_pacote
    # Define a hora exata que vai acabar
    ESTADO_ATUAL["fim_em"] = datetime.now() + timedelta(seconds=tempo_segundos)

    print(f"--- LIGANDO MÁQUINAS ({tempo_segundos}s) ---")
    if hw['lavadora'] and RPI_REAL: rele_lavadora.on()
    if hw['shampoo'] and RPI_REAL: rele_shampoo.on()
    if hw['aspirador'] and RPI_REAL: rele_aspirador.on()
    if hw['ar'] and RPI_REAL: rele_ar.on()

    time.sleep(tempo_segundos)

    print("--- DESLIGANDO TUDO ---")
    if RPI_REAL:
        rele_lavadora.off()
        rele_shampoo.off()
        rele_aspirador.off()
        rele_ar.off()

    # Libera o estado
    ESTADO_ATUAL["em_uso"] = False
    ESTADO_ATUAL["fim_em"] = None


def ativar_hardware(pacote_id, tempo_minutos):
    pacote = PACOTES.get(pacote_id)
    hw = pacote['hardware']
    tempo_segundos = tempo_minutos * 60  # (Para teste use * 5)

    t = threading.Thread(target=ciclo_lavagem_thread, args=(hw, tempo_segundos, pacote['nome']))
    t.start()


# --- NOVAS ROTAS PARA A TELA 2 ---

@app.route("/timer")
def timer_screen():
    """Renderiza a tela do cronômetro (Tela 2)"""
    return render_template("timer.html")


@app.route("/api/status")
def api_status():
    """O JavaScript da Tela 2 chama isso a cada 1 segundo"""
    agora = datetime.now()

    if ESTADO_ATUAL["em_uso"] and ESTADO_ATUAL["fim_em"]:
        segundos_restantes = (ESTADO_ATUAL["fim_em"] - agora).total_seconds()
        if segundos_restantes < 0: segundos_restantes = 0

        return jsonify({
            "ativo": True,
            "servico": ESTADO_ATUAL["pacote_nome"],
            "segundos": int(segundos_restantes)
        })
    else:
        return jsonify({
            "ativo": False,
            "servico": "LIVRE",
            "segundos": 0
        })


# --- ROTAS PADRÃO (MANTIDAS) ---
# (Copie as rotas /, /selecao, /salvar_servico, /baias, /salvar_baia, /pagamento, /gerar_qrcode iguais ao anterior)
# Apenas atualize o processar_pagamento para chamar o novo ativar_hardware

@app.route("/")
def welcome():
    session.clear()
    return render_template("1_welcome.html")


@app.route("/selecao")
def selection():
    return render_template("2_selection.html", pacotes=PACOTES)


@app.route("/salvar_servico", methods=["POST"])
def salvar_servico():
    # ... (Mesmo código de antes) ...
    session['servico_id'] = request.form.get("pacote_id")
    session['servico_tempo'] = int(request.form.get("tempo"))

    # Recalcula valor e nome só pra garantir
    pct = PACOTES[session['servico_id']]
    session['servico_valor'] = pct['precos'][session['servico_tempo']]
    session['servico_nome'] = f"{pct['nome']} ({session['servico_tempo']} min)"

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
    # ... (Mesmo código de antes) ...
    img = qrcode.make("PIX-TESTE")
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


@app.route("/processar_pagamento", methods=["POST"])
def processar_pagamento():
    metodo = request.form.get("metodo")

    # Salva Banco
    nova_venda = Venda(
        servico=session.get('servico_nome'),
        tempo=session.get('servico_tempo'),
        valor=session.get('servico_valor'),
        baia=session.get('baia_escolhida'),
        metodo_pagamento=metodo
    )
    db.session.add(nova_venda)
    db.session.commit()

    # LIGA O HARDWARE
    ativar_hardware(session.get('servico_id'), session.get('servico_tempo'))

    return redirect(url_for('confirmation'))


@app.route("/confirmacao")
def confirmation():
    return render_template("5_confirm.html", baia=session.get('baia_escolhida'))


@app.route("/recibo")
def receipt():
    return render_template("6_receipt.html")


# ... (Rotas de Admin e Login mantidas iguais) ...
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
    app.run(host='0.0.0.0', port=5000, debug=True)