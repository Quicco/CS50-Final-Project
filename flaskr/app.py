from flask import Flask, render_template, request, session, redirect
from argon2 import PasswordHasher
from dotenv import load_dotenv
import os
from utils import validate_phone_num, LOCATIONS, CLASS_TYPES
import sqlite3

load_dotenv()

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = os.getenv("SESSION_PERMANENT", "False") == "True"
app.config["SESSION_TYPE"] = os.getenv("SESSION_TYPE", "filesystem")
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")

db_path = "database.db"
ph = PasswordHasher()


@app.route("/")
def index():
    return render_template("login-form.html")


# --- Login Related Routes ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        # Store the form data to the session object
        session["email"] = request.form.get("email")

        email = request.form["email"]
        pw = request.form["password"]

        if not email or not pw:
            error = "Please fill in your email and password."
            return render_template("login.html", error=error)

        # Return dicts instead of tuples
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        try:
            query = """SELECT email, password FROM teacher WHERE email = (?);"""
            cur.execute(query, (email,))
            results = cur.fetchone()

            if results and ph.verify(results["password"], pw):
                classes = cur.execute("SELECT * FROM class")
                return render_template("course_class/homepage.html", classes=classes)
            else:
                # TODO: CREATE ERROR USER INPUTS
                return "NO USER!! >:("
        except sqlite3.Error as e:
            return f"Database error: {e}"
        finally:
            con.close()


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# --- Class Related Routes ---
@app.route("/student_list", methods=["GET", "POST"])
def student_list():
    if request.method == "POST":

        class_id = request.form.get("class_id")

        if not class_id:
            # TODO Error message
            print("ERROR - NO CLASS ID!")

        # Return dicts instead of tuples
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        try:
            query = """SELECT * FROM student WHERE class_id = (?);"""
            cur.execute(query, (class_id,))
            results = cur.fetchall()
            students = [dict(row) for row in results]

            # Pagination
            page = request.args.get("page", 1, type=int)
            per_page = 12
            start = (page - 1) * per_page
            end = start + per_page
            total_pages = (len(students) + per_page - 1) // per_page
            students_per_page = students[start:end]

            return render_template(
                "course_class/student-list.html",
                students=students,
                class_id=class_id,
                students_per_page=students_per_page,
                total_pages=total_pages,
                page=page,
            )

        except sqlite3.Error as e:
            return f"Database error: {e}"
        finally:
            con.close()


@app.route("/list")
def list():
    class_id = request.args.get("class_id")

    if not class_id:
        # TODO Error message
        print("ERROR - NO CLASS ID!")

    # Return dicts instead of tuples
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    try:
        query = """SELECT * FROM student WHERE class_id = (?);"""
        cur.execute(query, (class_id,))
        results = cur.fetchall()
        students = [dict(row) for row in results]

        # Pagination
        page = request.args.get("page", 1, type=int)
        per_page = 12
        start = (page - 1) * per_page
        end = start + per_page
        total_pages = (len(students) + per_page - 1) // per_page
        students_per_page = students[start:end]

        return render_template(
            "course_class/student-list.html",
            students=students,
            class_id=class_id,
            students_per_page=students_per_page,
            total_pages=total_pages,
            page=page,
        )

    except sqlite3.Error as e:
        return f"Database error: {e}"
    finally:
        con.close()


# --- Student Related Routes ---
@app.route("/edit_student", methods=["GET", "POST"])
def edit_student():
    if request.method == "POST":
        student_id = request.form.get("student_id")

        if not student_id:
            error = "Sorry, an error has occurred."
            return render_template("course_class/homepage", error=error)

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

            return render_template(
                "student/edit-student.html",
                student=student,
                locations=LOCATIONS,
                class_types=CLASS_TYPES,
            )

        except sqlite3.Error as e:
            return f"Database error: {e}"
        finally:
            con.close()


@app.route("/confirm_edit", methods=["GET", "POST"])
def confirm_edit():
    if request.method == "POST":

        print(request.form)

        # If it's not a valid phone number, keep old info but reset the phone field
        if not validate_phone_num(request.form.get("phone")):
            unedited_student = {
                "name": request.form.get("name"),
                "email": request.form.get("email"),
                "phone": "",
                "location": request.form.get("location"),
                "class_type": request.form.get("class_type"),
            }

            msg = "That's not a valid phone number."
            return render_template(
                "student/edit-student.html",
                msg=msg,
                student=unedited_student,
                locations=LOCATIONS,
                class_types=CLASS_TYPES,
            )

        try:
            upd_student = {
                "student_id": request.form.get("student_id"),
                "class_id": request.form.get("class_id"),
                "upd_name": request.form.get("name"),
                "upd_email": request.form.get("email"),
                "upd_phone": request.form.get("phone"),
                "upd_location": request.form.get("location"),
                "upd_class_type": request.form.get("class_type"),
            }

            # Return dicts instead of tuples
            con = sqlite3.connect(db_path)
            con.row_factory = sqlite3.Row
            cur = con.cursor()

            cur.execute(
                """UPDATE student SET name = (?), email = (?), phone = (?), location = (?), class_type = (?) WHERE student_id = (?)""",
                (
                    upd_student["upd_name"],
                    upd_student["upd_email"],
                    upd_student["upd_phone"],
                    upd_student["upd_location"],
                    upd_student["upd_class_type"],
                    upd_student["student_id"],
                ),
            )
            con.commit()

            msg = "You have sucsessfully edited a student."
            return render_template(
                "user_feedback/confirm-edit.html",
                msg=msg,
                class_id=upd_student["class_id"],
            )
        finally:
            con.close()


@app.route("/add_student", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":

        class_id = request.form.get("class_id")

        return render_template(
            "student/add-student.html",
            class_id=class_id,
            class_types=CLASS_TYPES,
            locations=LOCATIONS,
        )


@app.route("/confirm_add", methods=["GET", "POST"])
def confirm_add():
    if request.method == "POST":

        valid_phone = validate_phone_num(request.form.get("phone"))
        if not valid_phone:
            msg = "That's not a valid phone number."
            return render_template(
                "student/add-student.html",
                msg=msg,
                locations=LOCATIONS,
                class_types=CLASS_TYPES,
            )

        try:

            new_student = {
                "class_id": request.form.get("class_id"),
                "name": request.form.get("name"),
                "email": request.form.get("email"),
                "phone": valid_phone,
                "location": request.form.get("location"),
                "course": "Junior Fullstack Developer",
                "class_type": request.form.get("class_type"),
            }

            if (
                new_student["name"] == None
                or new_student["email"] == None
                or new_student["phone"] == None
            ):
                msg = "Please fill in the student's information."
                return render_template("student/add-student.html", msg=msg)

            # Return dicts instead of tuples
            con = sqlite3.connect(db_path)
            con.row_factory = sqlite3.Row
            cur = con.cursor()

            cur.execute(
                """INSERT into student (name, email, phone, location, course, class_type, class_id) VALUES (?, ?, ?, ? ,?, ?, ? )""",
                (
                    new_student["name"],
                    new_student["email"],
                    new_student["phone"],
                    new_student["location"],
                    new_student["course"],
                    new_student["class_type"],
                    new_student["class_id"],
                ),
            )
            con.commit()

            msg = "Student has sucessfully been added."
            return render_template(
                "user_feedback/confirm-add.html",
                class_id=new_student["class_id"],
                msg=msg,
            )
        finally:
            con.close()


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
            finally:
                con.close()

        msg = "You have sucsessfully deleted a student."
        return render_template(
            "user_feedback/confirm-delete.html", msg=msg, class_id=class_id
        )


# --- Navigation Related Routes ---
@app.route("/homepage", methods=["GET", "POST"])
def homepage():
    try:
        # Return dicts instead of tuples
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        classes = cur.execute("SELECT * from class")
        if classes:
            return render_template("course_class/homepage.html", classes=classes)
    finally:
        con.close()


# --- Class Related Routes ---
