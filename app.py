from flask import Flask, request, render_template, url_for
from datetime import datetime
from flask import send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import sqlite3
import uuid
import qrcode
import os

app = Flask(__name__)

os.makedirs("static/qrcodes", exist_ok=True)

# ==========================
# CONFIGURAÇÕES
# ==========================
CHAVE_PIX = "21990831887"
NOME_RECEBEDOR = "TATIANE_S_NASCIMENTO"
VALOR_INSCRICAO = 35

# ==========================
# BANCO DE DADOS
# ==========================
def criar_banco():
    conn = sqlite3.connect("evento.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inscritos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            email TEXT,
            telefone TEXT,
            igreja TEXT,
            cidade TEXT,
            observacoes TEXT,
            protocolo TEXT,
            status_pagamento TEXT,
            data_inscricao TEXT,
            convite_id TEXT
        )
    """)

    conn.commit()
    conn.close()
criar_banco()
print("BANCO CRIADO COM SUCESSO")
# ==========================
# GERAR QR CODE
# ==========================
def gerar_qrcode_pix(chave_pix, valor, nome_arquivo):

    payload = f"pix:{chave_pix}?amount={valor}"

    qr = qrcode.make(payload)

    caminho = os.path.join("static", "qrcodes")
    os.makedirs(caminho, exist_ok=True)

    arquivo = os.path.join(caminho, nome_arquivo)

    qr.save(arquivo)

    return arquivo
def gerar_qr_convite(convite_id):

    link = f"http://127.0.0.1:8080/convite/{convite_id}"

    qr = qrcode.make(link)

    caminho = os.path.join("static", "qrcodes")

    arquivo = os.path.join(caminho, f"convite_{convite_id}.png")

    qr.save(arquivo)

    return arquivo
# ==========================
# PÁGINA PRINCIPAL
# ==========================
@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        protocolo = (
            "MM-"
            + datetime.now().strftime("%Y%m%d")
            + "-"
            + uuid.uuid4().hex[:4].upper()
        )

        status = "PENDENTE"

        data = datetime.now().strftime("%d/%m/%Y %H:%M")

        gerar_qrcode_pix(
            CHAVE_PIX,
            VALOR_INSCRICAO,
            f"{protocolo}.png"
        )

        conn = sqlite3.connect("evento.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO inscritos (
                nome,
                email,
                telefone,
                igreja,
                cidade,
                observacoes,
                protocolo,
                status_pagamento,
                data_inscricao
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form["nome"],
            request.form["email"],
            request.form.get("telefone", ""),
            request.form.get("igreja", ""),
            request.form.get("cidade", ""),
            request.form.get("observacoes", ""),
            protocolo,
            status,
            data
        ))

        conn.commit()
        conn.close()

        return render_template(
            "pagamento.html",
            protocolo=protocolo,
            status=status,
            recebedor=NOME_RECEBEDOR,
            valor=VALOR_INSCRICAO,
            pix=CHAVE_PIX,
            qr_code=f"/static/qrcodes/{protocolo}.png",
            pix_copia_cola=CHAVE_PIX,
        )

   

    return render_template("index.html")
#=========================#
# INSCRIÇÃO
# ==========================#

@app.route("/inscricao")
def inscricao():
    return render_template("inscricao.html")   

# ==========================
# INGRESSO
# ==========================
@app.route("/ingresso/<protocolo>")
def ingresso(protocolo):

    conn = sqlite3.connect("evento.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nome, status_pagamento
        FROM inscritos
        WHERE protocolo = ?
    """, (protocolo,))

    user = cursor.fetchone()

    conn.close()

    if not user:
        return "Ingresso não encontrado"

    nome, status = user
    if status != "PAGO":
        return """
        <html>
        <body style='font-family:Arial;text-align:center;padding:40px'>
            <h1>⏳ Pagamento Pendente</h1>

            <p>Seu ingresso estará disponível após a confirmação do pagamento.</p>

            <p>Entre em contato com a organização caso já tenha efetuado o PIX.</p>
        </body>
        </html>
        """

    return render_template(
        "ingresso.html",
        nome=nome,
        status=status,
        protocolo=protocolo,
        qr=f"/static/qrcodes/{protocolo}.png"
    )

# ==========================
# ADMIN
# ==========================
@app.route("/admin")
def admin():

    conn = sqlite3.connect("evento.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            nome,
            email,
            telefone,
            cidade,
            protocolo,
            status_pagamento
        FROM inscritos
        ORDER BY id DESC
    """)

    dados = cursor.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        dados=dados
    )

# ==========================
# START
# ==========================
@app.route("/pagar/<protocolo>")
def pagar(protocolo):

    conn = sqlite3.connect("evento.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE inscritos
        SET status_pagamento = 'PAGO'
        WHERE protocolo = ?
    """, (protocolo,))

    # 👉 criar convite ID
    convite_id = uuid.uuid4().hex[:10].upper()

    cursor.execute("""
        UPDATE inscritos
        SET convite_id = ?
        WHERE protocolo = ?
    """, (convite_id, protocolo))

    conn.commit()
    conn.close()

    # 👉 gerar QR do convite
    gerar_qr_convite(convite_id)

    return f"""
    <html>
    <body style='font-family:Arial;text-align:center;padding:40px;background:#111;color:#fff'>

        <h2>✅ Pagamento confirmado</h2>

        <p>Seu ingresso VIP está pronto!</p>

        <a href='/convite/{convite_id}'
           style='padding:10px 20px;background:gold;color:#000;text-decoration:none;border-radius:8px'>
           🎟️ VER CONVITE VIP
        </a>

    </body>
    </html>
    """

    
@app.route("/convite/<convite_id>")
def convite(convite_id):

    conn = sqlite3.connect("evento.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nome, protocolo
        FROM inscritos
        WHERE convite_id = ?
    """, (convite_id,))

    user = cursor.fetchone()
    conn.close()

    if not user:
        return "Convite não encontrado"

    nome, protocolo = user

    return render_template(
        "convite.html",
        nome=nome,
        convite_id=convite_id,
        qr=f"/static/qrcodes/convite_{convite_id}.png"
    )
    
@app.route("/pdf/<convite_id>")
def gerar_pdf(convite_id):

    conn = sqlite3.connect("evento.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nome, protocolo
        FROM inscritos
        WHERE convite_id = ?
    """, (convite_id,))

    user = cursor.fetchone()

    conn.close()

    if not user:
        return "Convite não encontrado"

    nome, protocolo = user

    os.makedirs("pdfs", exist_ok=True)

    arquivo_pdf = f"pdfs/{convite_id}.pdf"

    doc = SimpleDocTemplate(arquivo_pdf)

    styles = getSampleStyleSheet()

    elementos = []

    elementos.append(
        Paragraph("CONVITE VIP", styles["Title"])
    )

    elementos.append(Spacer(1, 20))

    elementos.append(
        Paragraph(f"Nome: {nome}", styles["Normal"])
    )

    elementos.append(
        Paragraph(f"Protocolo: {protocolo}", styles["Normal"])
    )

    elementos.append(
        Paragraph(f"ID Convite: {convite_id}", styles["Normal"])
    )

    elementos.append(Spacer(1, 20))

    elementos.append(
        Paragraph("Entrada autorizada.", styles["Normal"])
    )

    doc.build(elementos)

    return send_file(
        arquivo_pdf,
        as_attachment=True
    )
if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=8080
    )

