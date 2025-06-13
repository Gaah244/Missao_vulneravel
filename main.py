from flask import Flask, request, render_template, redirect, url_for, render_template_string
import os
import sqlite3
import subprocess

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Criação do banco se não existir
def init_db():
    conn = sqlite3.connect('recrutados.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ranking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            flag TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL,
            senha TEXT NOT NULL
        )
    ''')
    # Inserir admin padrão se não existir
    cursor.execute("SELECT * FROM usuarios WHERE usuario = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES ('zetsu', 'theadmins')")
    conn.commit()
    conn.close()

init_db()

# Página principal SEM usar cache do Flask
@app.route('/')
def home():
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            html = f.read()
        return render_template_string(html)
    except Exception as e:
        return f"Erro ao carregar index.html: {str(e)}"

@app.route('/ver')
def ver_arquivo():
    nome_arquivo = request.args.get('arquivo', '')
    caminho = os.path.join("files", nome_arquivo)
    try:
        with open(caminho, 'r') as f:
            conteudo = f.read()
        return f"<pre>{conteudo}</pre>"
    except Exception as e:
        return f"Erro ao abrir o arquivo: {str(e)}"

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('arquivo')  # nome deve bater com o HTML
        if file:
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            caminho = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(caminho)
            return f"Arquivo <b>{file.filename}</b> enviado com sucesso para <b>{caminho}</b><br>" \
                   f"<a href='/executar?script={file.filename}'>Executar</a>"
        else:
            return "Nenhum arquivo selecionado."
    return render_template('upload.html')

@app.route('/executar')
def executar():
    script = request.args.get('script')
    arg = request.args.get('arg', '')
    caminho = os.path.join(app.config['UPLOAD_FOLDER'], script)

    if not os.path.isfile(caminho):
        return "Arquivo não encontrado."

    try:
        resultado = subprocess.check_output(
            ['python3', caminho, arg],
            stderr=subprocess.STDOUT,
            text=True
        )
        return f"<h3>Resultado:</h3><pre>{resultado}</pre>"
    except subprocess.CalledProcessError as e:
        return f"<h3>Erro:</h3><pre>{e.output}</pre>"

@app.route('/flag', methods=['GET', 'POST'])
def flag():
    if request.method == 'POST':
        nome = request.form['nome']
        flag = request.form['flag']

        conn = sqlite3.connect('recrutados.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO ranking (nome, flag) VALUES (?, ?)", (nome, flag))
            conn.commit()
            return render_template('sucesso.html', nome=nome)
        except Exception as e:
            return render_template('erro.html', erro=str(e))
        finally:
            conn.close()

    return render_template('flag.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']

        conn = sqlite3.connect('recrutados.db')
        cursor = conn.cursor()
        query = f"SELECT * FROM usuarios WHERE usuario = '{usuario}' AND senha = '{senha}'"
        try:
            cursor.execute(query)
            resultado = cursor.fetchone()
            if resultado:
                return "<h1>Login Realizado com Sucesso</h1><p>FLAG{login_falso_sucesso}</p>"
            else:
                return "<h1>Credenciais inválidas</h1><p>Tente novamente.</p>"
        except Exception as e:
            return f"Erro na consulta: {str(e)}"
        finally:
            conn.close()

    return render_template('login.html')

@app.route('/ranking')
def ranking():
    conn = sqlite3.connect('recrutados.db')
    cursor = conn.cursor()
    cursor.execute("SELECT nome, COUNT(*) as total_flags FROM ranking GROUP BY nome ORDER BY total_flags DESC")
    dados = cursor.fetchall()
    conn.close()
    return render_template('ranking.html', ranking=dados)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)

