from flask import Flask, render_template, request, session
from argon2 import PasswordHasher
import sqlite3

app = Flask(__name__)
db_path = "flaskr/database.db"
ph = PasswordHasher()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        pw = request.form["password"]

        if not email or not pw:
            error = "Please fill in your email and password."
            return render_template("index.html", error=error)

        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        try:
            query = """SELECT email, password FROM teacher WHERE email = (?);"""
            cur.execute(query, (email,))
            results = cur.fetchone()

            if results and ph.verify(results["password"], pw):
                return "USER!! :)"
            else:
                return "NO USER!! >:("
        except sqlite3.Error as e:
            return f"Database error: {e}"
        finally:
            con.close()
    return render_template("index.html")
