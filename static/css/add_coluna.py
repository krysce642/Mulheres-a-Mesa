import sqlite3

conn = sqlite3.connect("evento.db")
cursor = conn.cursor()

cursor.execute("ALTER TABLE inscritos ADD COLUMN convite_id TEXT")

conn.commit()
conn.close()

print("Coluna adicionada")