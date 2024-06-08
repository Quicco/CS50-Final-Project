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

        # Return dicts instead of tuples
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        try:
            query = """SELECT email, password FROM teacher WHERE email = (?);"""
            cur.execute(query, (email,))
            results = cur.fetchone()

            if results and ph.verify(results["password"], pw):
                cur.execute("SELECT * FROM class")
                results = cur.fetchall()
                classes = [dict(row) for row in results]
                return render_template("homepage.html", classes=classes)
            else:
                # TODO: CREATE ERROR USER INPUTS
                return "NO USER!! >:("
        except sqlite3.Error as e:
            return f"Database error: {e}"
        finally:
            con.close()
    return render_template("index.html")


@app.route("/select", methods=["GET", "POST"])
def select():
    if request.method == "POST":
        class_id = request.form["class_id"]

        # Return dicts instead of tuples
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        try:
            query = """SELECT * FROM student WHERE class_id = (?);"""
            cur.execute(query, (class_id,))
            results = cur.fetchall()
            students = [dict(row) for row in results]
            return render_template("select.html", students=students)

        except sqlite3.Error as e:
            return f"Database error: {e}"
        finally:
            con.close()

    return render_template("index.html")
