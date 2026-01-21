import sqlite3

connection = sqlite3.connect('database.db')

with open('schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

# Utilisateurs
cur.execute("INSERT INTO users (username, role) VALUES (?, ?)", ('admin', 'admin'))
cur.execute("INSERT INTO users (username, role) VALUES (?, ?)", ('user', 'user'))

# Livres (données de test)
cur.execute(
    "INSERT INTO books (title, author, stock_total, stock_available) VALUES (?, ?, ?, ?)",
    ('1984', 'George Orwell', 5, 5)
)
cur.execute(
    "INSERT INTO books (title, author, stock_total, stock_available) VALUES (?, ?, ?, ?)",
    ('Le Petit Prince', 'Antoine de Saint-Exupéry', 3, 3)
)
cur.execute(
    "INSERT INTO books (title, author, stock_total, stock_available) VALUES (?, ?, ?, ?)",
    ('L’Étranger', 'Albert Camus', 4, 4)
)

connection.commit()
connection.close()

print("Base bibliothèque créée")
