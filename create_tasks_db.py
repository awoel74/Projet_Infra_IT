import sqlite3

conn = sqlite3.connect("tasks.db")

with open("schema_tasks.sql") as f:
    conn.executescript(f.read())

conn.commit()
conn.close()

print("tasks.db créé")
