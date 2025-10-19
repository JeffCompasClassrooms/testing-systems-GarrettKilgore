import sqlite3

conn = sqlite3.connect("template_squirrel_db.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE squirrels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    size TEXT NOT NULL
)
""")

conn.commit()
conn.close()

print("✅ template_squirrel_db.db created successfully.")