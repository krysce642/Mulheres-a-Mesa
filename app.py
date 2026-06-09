import sqlite3
from flask import Flask, request, render_template
from datetime import datetime
from flask import Flask, request, render_template, url_for
import uuid
import qrcode
import os

app = Flask(__name__)

os.makedirs("static/qrcodes", exist_ok=True)

# ==========================
# CONFIGURAÇÕES
# ==========================
CHAVE_PIX = "21990831887"
VALOR_INSCRICAO = 35.00

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
            data_inscricao TEXT
        )
    """)

    conn.commit()
    conn.close()

criar_banco()

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
            pix=CHAVE_PIX,
            valor=VALOR_INSCRICAO,
            qr_code=f"/static/qrcodes/{protocolo}.png",
            pix_copia_cola=CHAVE_PIX
        )

   

    return render_template("index.html")
    

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

    conn.commit()
    conn.close()

    return """
    <html>
    <body style='font-family:Arial;text-align:center;padding:40px'>
        <h2>✅ Pagamento confirmado</h2>

        <a href='/admin'>Voltar ao Admin</a>
    </body>
    </html>
    """
    
if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=8080
    )

