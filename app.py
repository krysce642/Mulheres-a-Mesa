import sqlite3
from flask import Flask, request, render_template_string, url_for
from datetime import datetime
import uuid
import qrcode
import os
from flask import Flask, render_template


app = Flask(__name__)

# 🔹 suas outras rotas (cadastro, pagamento, etc)
@app.route("/")
def home():
    return "Home"

# 🔥 COLOQUE AQUI (FINAL DO ARQUIVO)
@app.route("/ingresso")
def ingresso():
    return render_template(
        "ingresso.html",
        evento_nome="Mulheres à mesa - curando minha alma",
        data_evento="08/08/2026",
        local_evento="Maricá - RJ",
        nome_usuario="Cristiane",
        codigo_ingresso="ABC123",
        qr_code="/static/qrcode.png"
    )

if __name__ == "__main__":
    app.run(debug=True)

# ==========================
# CONFIGURAÇÕES
# ==========================
CHAVE_PIX = "21990831887"
VALOR_INSCRICAO = 35.00


# ==========================
# QR CODE PIX
# ==========================
def gerar_qrcode_pix(chave_pix, valor, nome_arquivo):

    payload = f"pix:{chave_pix}?amount={valor}"

    qr = qrcode.make(payload)

    caminho = os.path.join("static", "qrcodes")
    os.makedirs(caminho, exist_ok=True)

    caminho_arquivo = os.path.join(caminho, nome_arquivo)
    qr.save(caminho_arquivo)

    return caminho_arquivo


# ==========================
# BANCO
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
# HTML PRINCIPAL
# ==========================
HTML = """
<!DOCTYPE html>
<html>
<div style="text-align:center; margin-bottom:20px;">
    <img src="/static/convite.jpg"
         style="width:100%;max-width:500px;border-radius:15px;">
</div>
<head>
    <title>Mulheres à Mesa</title>
</head>
<body style="font-family:Arial;max-width:800px;margin:auto;padding:20px;">
<div style="background:#faf7f5;padding:20px;border-radius:10px;margin-bottom:20px;">
    <h2>Mulheres à Mesa</h2>
    <p>Curando Minha Alma</p>
    <p><b>Data:</b> 08/08</p>
    <p><b>Horário:</b> 18h</p>
    <p><b>Valor:</b> R$ 35,00</p>
</div>
<h1>Faça sua inscrição</h1>

<form method="POST">

    <input name="nome" placeholder="Nome" required><br><br>
    <input name="email" placeholder="Email" required><br><br>
    <input name="telefone" placeholder="Telefone"><br><br>
    <input name="igreja" placeholder="Igreja"><br><br>
    <input name="cidade" placeholder="Cidade"><br><br>
    <textarea name="observacoes" placeholder="Observações"></textarea><br><br>

    <button type="submit">Inscrever</button>

</form>

<hr>

<h2>Inscritas</h2>

<table border="1" width="100%">
<tr>
<th>ID</th><th>Nome</th><th>Email</th><th>Telefone</th>
</tr>

{% for p in inscritos %}
<tr>
<td>{{ p[0] }}</td>
<td>{{ p[1] }}</td>
<td>{{ p[2] }}</td>
<td>{{ p[3] }}</td>
</tr>
{% endfor %}

</table>

</body>
</html>
"""


# ==========================
# ROTA PRINCIPAL
# ==========================
@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        protocolo = "MM-" + datetime.now().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:4].upper()

        status = "PENDENTE"
        data = datetime.now().strftime("%d/%m/%Y %H:%M")

        # 🔥 QR CODE PIX
        gerar_qrcode_pix(CHAVE_PIX, VALOR_INSCRICAO, f"{protocolo}.png")

        conn = sqlite3.connect("evento.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO inscritos (
                nome, email, telefone, igreja, cidade,
                observacoes, protocolo, status_pagamento, data_inscricao
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form["nome"],
            request.form["email"],
            request.form["telefone"],
            request.form["igreja"],
            request.form["cidade"],
            request.form["observacoes"],
            protocolo,
            status,
            data
        ))
        return render_template(
    "ingresso.html",
    evento_nome="Mulheres à Mesa - Curando Minha Alma",
    data_evento="08/08/2026",
    local_evento="Maricá - RJ",
    nome_usuario="Cristiane",
    codigo_ingresso="ABC123",
    qr_code=url_qr 
    # caminho do QR gerado
)
        conn.commit()
        conn.close()

        # ==========================
        # 🔥 TELA DE CONFIRMAÇÃO (PASSO 5 FINAL)
        # ==========================
        return render_template_string("""
        <html>
        <body style="font-family:Arial;text-align:center;background:#f5f5f5;padding:30px;">

        <div style="background:white;padding:30px;border-radius:12px;max-width:500px;margin:auto;">

            <h1>🎉 Inscrição Confirmada</h1>

            <h2 style="color:#6f4ca1;">{{ protocolo }}</h2>

            <p><b>Status:</b> {{ status }}</p>

            <hr>

            <h3>💳 Pagamento PIX</h3>

            <p><b>Valor:</b> R$ {{ valor }}</p>

            <p><b>Chave PIX:</b> {{ pix }}</p>

            <!-- 🔥 QR CODE -->
            <img src="{{ url_for('static', filename='qrcodes/' + protocolo + '.png') }}"
                 width="220">

            <br><br>

            <!-- 🔥 BOTÃO COPIAR PIX -->
            <button onclick="copiarPix()"
                    style="padding:10px;background:#6f4ca1;color:white;border:none;border-radius:6px;">
                Copiar PIX
            </button>

            <script>
            function copiarPix(){
                navigator.clipboard.writeText("{{ pix }}");
                alert("PIX copiado!");
            }
            </script>

            <br><br>

            <a href="/">Nova inscrição</a>

        </div>

        </body>
        </html>
        """,
        protocolo=protocolo,
        status=status,
        pix=CHAVE_PIX,
        valor=VALOR_INSCRICAO)

    # LISTAGEM
    conn = sqlite3.connect("evento.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, nome, email, telefone FROM inscritos ORDER BY id DESC")
    inscritos = cursor.fetchall()

    conn.close()

    return render_template_string(HTML, inscritos=inscritos)


# ==========================
# START
# ==========================
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)