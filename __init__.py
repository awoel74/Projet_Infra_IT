from flask import Flask, render_template, jsonify, request, redirect, url_for, session, Response
from functools import wraps
import sqlite3

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # Clé secrète pour les sessions


# =========================
# AUTHENTIFICATION ADMIN
# =========================

def est_authentifie():
    return session.get('authentifie')


# =========================
# AUTHENTIFICATION USER (Basic Auth)
# login : user
# password : 12345
# =========================

def user_auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != "user" or auth.password != "12345":
            return Response(
                "Accès refusé", 401,
                {"WWW-Authenticate": 'Basic realm="User Area"'}
            )
        return f(*args, **kwargs)
    return decorated


# =========================
# ROUTES EXISTANTES
# =========================

@app.route('/')
def hello_world():
    return render_template('hello.html')


@app.route('/lecture')
def lecture():
    if not est_authentifie():
        return redirect(url_for('authentification'))

    return "<h2>Bravo, vous êtes authentifié</h2>"


@app.route('/authentification', methods=['GET', 'POST'])
def authentification():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'password':
            session['authentifie'] = True
            return redirect(url_for('lecture'))
        else:
            return render_template('formulaire_authentification.html', error=True)

    return render_template('formulaire_authentification.html', error=False)


@app.route('/fiche_client/<int:post_id>')
def Readfiche(post_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients WHERE id = ?', (post_id,))
    data = cursor.fetchall()
    conn.close()
    return render_template('read_data.html', data=data)


@app.route('/consultation/')
def ReadBDD():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients;')
    data = cursor.fetchall()
    conn.close()
    return render_template('read_data.html', data=data)


@app.route('/enregistrer_client', methods=['GET'])
def formulaire_client():
    return render_template('formulaire.html')


@app.route('/enregistrer_client', methods=['POST'])
def enregistrer_client():
    nom = request.form['nom']
    prenom = request.form['prenom']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO clients (created, nom, prenom, adresse) VALUES (?, ?, ?, ?)',
        (1002938, nom, prenom, "ICI")
    )
    conn.commit()
    conn.close()

    return redirect('/consultation/')



@app.route('/fiche_nom/')
@user_auth_required
def fiche_nom():
    nom = request.args.get('nom', '').strip()

    if nom == "":
        return jsonify({
            "error": "Paramètre 'nom' manquant. Exemple : /fiche_nom/?nom=Dupont"
        }), 400

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM clients WHERE nom LIKE ?",
        (f"%{nom}%",)
    )
    data = cursor.fetchall()
    conn.close()

    return render_template('read_data.html', data=data)


if __name__ == "__main__":
    app.run(debug=True)
