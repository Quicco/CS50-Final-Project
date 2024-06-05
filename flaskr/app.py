from flask import Flask, render_template, request, session
from argon2 import PasswordHasher
import sqlite3

app = Flask(__name__)
db_path = "flaskr/database.db"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        con = sqlite3.connect(db_path)
        cur = con.cursor()

        email = request.form.get("email")
        pw = request.form.get("password")

        if email and pw:
            query = """SELECT email, password FROM teacher WHERE email = ? AND password = ?;"""
            cur.execute(query, (email, pw))

            results = cur.fetchall()
            print("RESULTSSSSS->", results)
            # Validate whether the user is in the db
            if len(results) != 0:
                return "USER!! :)"
            else:
                return "NO USER!! >:("
    con.close()
    return "ASDOJASODJAOSDJOAJSDOAJSDOAJDOJA"
