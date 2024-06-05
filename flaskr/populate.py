import sqlite3
from argon2 import PasswordHasher

con = sqlite3.connect("flaskr/database.db")
cur = con.cursor()
ph = PasswordHasher()


def initialize_db():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS teacher(id INTEGER PRIMARY KEY, email TEXT, password TEXT);"
    )
    DEV_MAIL = "admin@dev.com"
    DEV_PW = ph.hash("123")
    cur.execute(
        "INSERT INTO teacher (email, password) VALUES (?, ?)",
        (
            DEV_MAIL,
            DEV_PW,
        ),
    )
    con.commit()


initialize_db()
con.close()
