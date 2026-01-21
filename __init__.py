from flask import Flask, render_template, jsonify, request, redirect, url_for, session, Response
from functools import wraps
import sqlite3

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


# =========================
# AUTH ADMIN (session)
# =========================
def est_authentifie():
    return session.get('authentifie')


@app.route('/authentification', methods=['GET', 'POST'])
def authentification():
    if request.method == 'POST':
        if request.form.get('username') == 'admin' and request.form.get('password') == 'password':
            session['authentifie'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('formulaire_authentification.html', error=True)

    return render_template('formulaire_authentification.html', error=False)


# =========================
# AUTH USER (Basic Auth)
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
# HOME
# =========================
@app.route('/')
def home():
    return render_template('hello.html')


# =========================
# API BOOKS (public)
# =========================
@app.route('/books')
def list_books():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books")
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)


@app.route('/books/available')
def available_books():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE stock_available > 0")
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)


# =========================
# USER FLOW (loan / return)
# =========================
@app.route('/loan/<int:book_id>')
@user_auth_required
def loan_book(book_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT stock_available FROM books WHERE id = ?", (book_id,))
    stock = cursor.fetchone()

    if not stock or stock[0] <= 0:
        conn.close()
        return "Livre indisponible", 400

    # user_id = 1 (simple pour le TP)
    cursor.execute(
        "INSERT INTO loans (user_id, book_id, loan_date) VALUES (?, ?, DATE('now'))",
        (1, book_id)
    )
    cursor.execute(
        "UPDATE books SET stock_available = stock_available - 1 WHERE id = ?",
        (book_id,)
    )

    conn.commit()
    conn.close()
    return "Livre emprunté"


@app.route('/return/<int:loan_id>')
@user_auth_required
def return_book(loan_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT book_id FROM loans WHERE id = ? AND return_date IS NULL",
        (loan_id,)
    )
    book = cursor.fetchone()

    if not book:
        conn.close()
        return "Emprunt invalide", 400

    cursor.execute(
        "UPDATE loans SET return_date = DATE('now') WHERE id = ?",
        (loan_id,)
    )
    cursor.execute(
        "UPDATE books SET stock_available = stock_available + 1 WHERE id = ?",
        (book[0],)
    )

    conn.commit()
    conn.close()
    return "Livre retourné"


# =========================
# ADMIN FLOW (dashboard + books)
# =========================
@app.route('/admin')
def admin_dashboard():
    if not est_authentifie():
        return redirect(url_for('authentification'))
    return render_template('admin_dashboard.html')


@app.route('/admin/books')
def admin_books():
    if not est_authentifie():
        return redirect(url_for('authentification'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    conn.close()

    return render_template('admin_books.html', books=books)


@app.route('/admin/books/add', methods=['GET', 'POST'])
def admin_add_book():
    if not est_authentifie():
        return redirect(url_for('authentification'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        stock_str = request.form.get('stock', '').strip()

        if title == "" or author == "" or stock_str == "":
            return "Champs manquants", 400

        try:
            stock = int(stock_str)
            if stock <= 0:
                return "Stock invalide", 400
        except ValueError:
            return "Stock invalide", 400

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO books (title, author, stock_total, stock_available) VALUES (?, ?, ?, ?)",
            (title, author, stock, stock)
        )
        conn.commit()
        conn.close()

        return redirect('/admin/books')

    # GET
    return render_template('admin_add_book.html')


@app.route('/admin/books/delete/<int:book_id>')
def admin_delete_book(book_id):
    if not est_authentifie():
        return redirect(url_for('authentification'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()

    return redirect('/admin/books')


@app.route('/admin/loans')
def admin_loans():
    if not est_authentifie():
        return redirect(url_for('authentification'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT loans.id, users.username, books.title, loans.loan_date, loans.return_date
        FROM loans
        JOIN users ON loans.user_id = users.id
        JOIN books ON loans.book_id = books.id
        ORDER BY loans.id DESC
    """)
    data = cursor.fetchall()
    conn.close()

    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True)


@app.route('/loan_many/<int:book_id>')
@user_auth_required
def loan_many(book_id):
    q = request.args.get('q', '1').strip()
    try:
        q = int(q)
        if q <= 0:
            return "Quantité invalide", 400
    except ValueError:
        return "Quantité invalide", 400

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT stock_available FROM books WHERE id = ?", (book_id,))
    stock = cursor.fetchone()

    if not stock:
        conn.close()
        return "Livre introuvable", 404

    stock_available = stock[0]
    if stock_available < q:
        conn.close()
        return f"Stock insuffisant (disponible: {stock_available})", 400

    # user_id = 1 (simple TP)
    for _ in range(q):
        cursor.execute(
            "INSERT INTO loans (user_id, book_id, loan_date) VALUES (?, ?, DATE('now'))",
            (1, book_id)
        )

    cursor.execute(
        "UPDATE books SET stock_available = stock_available - ? WHERE id = ?",
        (q, book_id)
    )

    conn.commit()
    conn.close()

    return f"{q} emprunt(s) effectué(s)"

@app.route('/user')
@user_auth_required
def user_page():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, author, stock_available FROM books ORDER BY id")
    books = cursor.fetchall()
    conn.close()

    return render_template('user_books.html', books=books)

@app.route('/user/loan', methods=['POST'])
@user_auth_required
def user_loan_post():
    book_id = request.form.get('book_id', '').strip()
    qty = request.form.get('qty', '1').strip()

    try:
        book_id = int(book_id)
        qty = int(qty)
        if qty <= 0:
            return "Quantité invalide", 400
    except ValueError:
        return "Données invalides", 400

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT stock_available FROM books WHERE id = ?", (book_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return "Livre introuvable", 404

    stock_available = row[0]
    if stock_available < qty:
        conn.close()
        return f"Stock insuffisant (disponible: {stock_available})", 400

    # user_id = 1 (simplifié pour le TP)
    for _ in range(qty):
        cursor.execute(
            "INSERT INTO loans (user_id, book_id, loan_date) VALUES (?, ?, DATE('now'))",
            (1, book_id)
        )

    cursor.execute(
        "UPDATE books SET stock_available = stock_available - ? WHERE id = ?",
        (qty, book_id)
    )

    conn.commit()
    conn.close()

    return redirect('/user')
