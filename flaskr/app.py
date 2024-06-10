from flask import Flask, render_template, request, session, redirect
from argon2 import PasswordHasher
import sqlite3

app = Flask(__name__)
db_path = "flaskr/database.db"
ph = PasswordHasher()


@app.route("/")
def index():
    return render_template("index.html")


# --- Database related functions---


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


# ---Class Related Routes---
@app.route("/class_view", methods=["GET", "POST"])
def select():
    if request.method == "POST":
        class_id = request.form.get("class_id")

        if not class_id:
            # TODO Error message
            return

        # Return dicts instead of tuples
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        try:
            query = """SELECT * FROM student WHERE class_id = (?);"""
            cur.execute(query, (class_id,))
            results = cur.fetchall()
            students = [dict(row) for row in results]
            return render_template(
                "classview.html", students=students, class_id=class_id
            )

        except sqlite3.Error as e:
            return f"Database error: {e}"
        finally:
            con.close()

    return


# ---Student Related Routes---
@app.route("/edit_student", methods=["GET", "POST"])
def editstudent():
    if request.method == "POST":
        student_id = request.form.get("student_id")

        if not student_id:
            error = "Sorry, an error has occurred."
            return render_template("select.html", error=error)

        # Return dicts instead of tuples
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        try:
            query = "SELECT * FROM student WHERE student_id = (?)"
            cur.execute(
                query,
                (student_id,),
            )
            student = cur.fetchone()

            locations = ["Lisbon", "Sintra", "Porto"]
            class_types = ["PowerUp", "Bootcamp"]

            return render_template(
                "editstudent.html",
                student=student,
                locations=locations,
                class_types=class_types,
            )

        except sqlite3.Error as e:
            return f"Database error: {e}"
        finally:
            con.close()
    return render_template("")


@app.route("/confirm_edit", methods=["GET", "POST"])
def confirm_edit():
    if request.method == "POST":
        student_id = request.form.get("student_id")
        class_id = request.form.get("class_id")
        upd_name = request.form.get("name")
        upd_email = request.form.get("email")
        upd_phone = request.form.get("phone")
        upd_location = request.form.get("location")
        upd_class_type = request.form.get("class_type")

        # Return dicts instead of tuples
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        cur.execute(
            """UPDATE student SET name = (?), email = (?), phone = (?), location = (?), class_type = (?) WHERE student_id = (?)""",
            (
                upd_name,
                upd_email,
                upd_phone,
                upd_location,
                upd_class_type,
                student_id,
            ),
        )
        con.commit()
        query = """SELECT * FROM student WHERE class_id = (?);"""
        cur.execute(query, (class_id,))

        results = cur.fetchall()
        students = [dict(row) for row in results]

        return render_template("classview.html", students=students)


@app.route("/delete_student", methods=["GET", "POST"])
def delete_student():
    if request.method == "POST":
        student_id = request.form.get("student_id")
        class_id = request.form.get("class_id")

        if student_id:
            try:
                # Return dicts instead of tuples
                con = sqlite3.connect(db_path)
                con.row_factory = sqlite3.Row
                cur = con.cursor()

                cur.execute("DELETE FROM student WHERE student_id = (?)", (student_id,))
                con.commit()

                cur.execute("SELECT * FROM student WHERE class_id = (?)", (class_id,))
                results = cur.fetchall()
                students = [dict(row) for row in results]
                return render_template("classview.html", students=students)
            finally:
                con.close()
