from flask import Flask, render_template, request, session, redirect, url_for
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
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


# Handler functions
def connect_to_db():
    # Return dicts instead of tuples
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    return con, cur


def fetch_classes():
    try:
        con, cur = connect_to_db()

        classes = cur.execute(
            "SELECT * FROM class WHERE archived = 0 ORDER BY location;"
        ).fetchall()

        archived = cur.execute(
            "SELECT * FROM class WHERE archived = 1 ORDER BY location;"
        ).fetchall()

        return classes, archived

    except sqlite3.Error as e:
        return f"Database error: {e}"
    finally:
        con.close()


def fetch_students(class_id, page):
    try:
        con, cur = connect_to_db()

        query = """SELECT * FROM student WHERE 
        student_id IN (
        SELECT student_id 
        FROM class_student 
         WHERE class_id = (?)
        ) ORDER BY name ASC;"""
        cur.execute(query, (class_id,))
        results = cur.fetchall()
        students = [dict(row) for row in results]

        # Pagination
        per_page = 8
        start = (page - 1) * per_page
        end = start + per_page
        total_pages = (len(students) + per_page - 1) // per_page
        students_per_page = students[start:end]

        return students, students_per_page, total_pages

    except sqlite3.Error as e:
        return f"Database error: {e}"
    finally:
        con.close()


def welcome_user():
    try:
        email = session["email"]
        con, cur = connect_to_db()
        user = cur.execute(
            "SELECT name FROM teacher WHERE email = (?);", (email,)
        ).fetchone()

        return f"Welcome, {user[0]}"
    finally:
        con.close()


# Route functions
@app.route("/")
def index():
    return render_template("index/login-form.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        # Store the form data to the session object
        session["email"] = request.form.get("email")

        email = request.form["email"]
        pw = request.form["password"]

        if not email or not pw:
            error = "Please fill in your email and password."
            return render_template("index/login-form.html", error=error)

        con, cur = connect_to_db()

        try:
            query = """SELECT email, password FROM teacher WHERE email = (?);"""
            cur.execute(query, (email,))
            results = cur.fetchone()

            try:
                if results and ph.verify(results["password"], pw):
                    classes, archived = fetch_classes()

                    welcome_msg = welcome_user()
                    return render_template(
                        "homepage/homepage.html",
                        classes=classes,
                        loggedin=True,
                        archived=archived,
                        welcome_msg=welcome_msg,
                    )
            except VerifyMismatchError:
                error = "Incorrect password"
                return render_template("index/login-form.html", error=error)
            else:
                error = "Incorrect email or password"
                return render_template("index/login-form.html", error=error)
        except sqlite3.Error as e:
            return f"Database error: {e}"
        finally:
            con.close()


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


#  Class Related Routes
@app.route("/actions/select_ongoing_class", methods=["GET", "POST"])
def select_ongoing_class():
    if request.method == "POST":

        class_id = request.form.get("class_id")
        if not class_id:
            return render_template("/archived_classes/archived_classes.html")

        page = request.args.get("page", 1, type=int)
        students, students_per_page, total_pages = fetch_students(class_id, page)

        return render_template(
            "student/student-list.html",
            students=students,
            class_id=class_id,
            students_per_page=students_per_page,
            total_pages=total_pages,
            page=page,
            loggedin=True,
            is_active_class=True,
        )


@app.route("/actions/select_archived_class", methods=["GET", "POST"])
def select_archived_class():
    if request.method == "POST":

        class_id = request.form.get("class_id")
        if not class_id:
            return render_template("/archived_classes/archived_classes.html")

        page = request.args.get("page", 1, type=int)
        students, students_per_page, total_pages = fetch_students(class_id, page)

        return render_template(
            "student/student-list.html",
            students=students,
            class_id=class_id,
            students_per_page=students_per_page,
            total_pages=total_pages,
            page=page,
            loggedin=True,
            is_active_class=False,
        )


@app.route("/actions/archive", methods=["GET", "POST"])
def archive_class():
    try:

        class_id = request.form.get("class_id")
        if not class_id:
            return render_template("/archived_classes/homepage.html")

        con, cur = connect_to_db()
        cur.execute("UPDATE class SET archived = 1 WHERE class_id = (?)", (class_id,))
        con.commit()

        classes, archived = fetch_classes()
        welcome_msg = welcome_user()
        return render_template(
            "homepage/homepage.html",
            classes=classes,
            archived=archived,
            loggedin=True,
            welcome_msg=welcome_msg,
        )
    finally:
        con.close()


@app.route("/actions/unarchive", methods=["GET", "POST"])
def unarchive_class():
    try:
        class_id = request.POST.get("class_id")
        con, cur = connect_to_db()

        cur.execute("UPDATE class SET archived = 0 WHERE class_id = (?);", (class_id,))
        con.commit()

        classes, archived = fetch_classes()
        welcome_msg = welcome_user()
        return render_template(
            "archived_classes/archived_classes.html",
            archived=archived,
            loggedin=True,
            welcome_msg=welcome_msg,
        )
    finally:
        con.close()


@app.route("/actions/delete", methods=["GET", "POST"])
def delete_class(class_id):
    try:
        con, cur = connect_to_db()

        cur.execute("DELETE FROM class WHERE class_id = (?),", (class_id,))
        con.commit()

        classes, archived = fetch_classes()
        return render_template(
            "homepage/homepage.html",
            classes=classes,
            archived=archived,
            loggedin=True,
        )
    finally:
        con.close()


@app.route("/advance", methods=["GET", "POST"])
def advance():
    if request.method == "POST":

        class_id = request.form.get("class_id")

        if not class_id:
            # TODO Error message
            print("ERROR - NO CLASS ID!")

        page = request.args.get("page", 1, type=int)
        students, students_per_page, total_pages = fetch_students(class_id, page)

        return render_template(
            "student/advance-view.html",
            students=students,
            class_id=class_id,
            students_per_page=students_per_page,
            total_pages=total_pages,
            page=page,
            promotion_view=True,
        )


@app.route("/confirm_advance", methods=["GET", "POST"])
def confirm_advance():
    if request.method == "POST":
        class_id = request.form.get("class_id")
        students_ids = request.form.getlist("checked")
        ids = [int(id) for id in students_ids]

        if not students_ids:
            return "NO CHECKED STUDENTS"  # TODO: Add an error message

        try:
            con, cur = connect_to_db()

            # Fetch the existing class details
            cur.execute("SELECT * FROM class WHERE class_id = (?)", (class_id,))
            old_class = cur.fetchone()

            if old_class is None:
                return "CLASS NOT FOUND"

            course, location, year = (
                old_class[1],
                old_class[4],
                old_class[5],
            )

            # Archive the old class
            cur.execute(
                "UPDATE class SET archived = 1 WHERE class_id = (?)", (class_id,)
            )
            con.commit()

            # Check for an existing class
            cur.execute(
                """
                SELECT class_id FROM class 
                WHERE course = ? AND class_type = ? AND location = ? AND year = ?
                """,
                (course, "Advanced", location, year),
            )
            existing_class = cur.fetchone()

            if existing_class:
                new_class_id = existing_class[0]
            else:
                # Create a new advanced class
                cur.execute(
                    """
                    INSERT INTO class (course, class_type, time_slot, location, year, archived) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (course, "Advanced", "All Day", location, year, 0),
                )
                con.commit()
                new_class_id = cur.lastrowid

            # Insert student into the new class, while keeping them in the old one
            for id in ids:
                cur.execute(
                    """
                    INSERT INTO class_student (class_id, student_id) 
                    VALUES (?, ?) 
                    """,
                    (new_class_id, id),
                )

            con.commit()

            return redirect(url_for("homepage"))

        except sqlite3.Error as e:
            return f"Database error: {e}"

        finally:
            con.close()


@app.route("/list", methods=["GET", "POST"])
def list():
    if request.method == "POST":
        class_id = request.form.get("class_id")
    else:
        class_id = request.args.get("class_id")

    if not class_id:
        # TODO Error message
        print("ERROR - NO CLASS ID!")

    con, cur = connect_to_db()
    try:
        page = request.args.get("page", 1, type=int)
        students, students_per_page, total_pages = fetch_students(class_id, page)
        return render_template(
            "student/student-list.html",
            students=students,
            class_id=class_id,
            students_per_page=students_per_page,
            total_pages=total_pages,
            page=page,
            loggedin=True,
        )

    except sqlite3.Error as e:
        return f"Database error: {e}"
    finally:
        con.close()


@app.route("/advance_list", methods=["GET", "POST"])
def advance_list():
    if request.method == "POST":
        class_id = request.form.get("class_id")
    else:
        class_id = request.args.get("class_id")

    if not class_id:
        # TODO Error message
        print("ERROR - NO CLASS ID!")

    con, cur = connect_to_db()
    try:
        page = request.args.get("page", 1, type=int)
        students, students_per_page, total_pages = fetch_students(class_id, page)
        return render_template(
            "student/advance-view.html",
            students=students,
            class_id=class_id,
            students_per_page=students_per_page,
            total_pages=total_pages,
            page=page,
            promotion_view=True,
        )

    except sqlite3.Error as e:
        return f"Database error: {e}"
    finally:
        con.close()


#  Student Related Routes
@app.route("/edit_student", methods=["GET", "POST"])
def edit_student():
    if request.method == "POST":
        student_id = request.form.get("student_id")
        class_id = request.form.get("class_id")

        if not student_id:
            error = "Sorry, an error has occurred."
            return render_template("homepage/homepage.html", error=error)

        con, cur = connect_to_db()

        try:
            query = "SELECT * FROM student WHERE student_id = (?)"
            cur.execute(
                query,
                (student_id,),
            )
            student = cur.fetchone()

            return render_template(
                "student/edit-student.html",
                class_id=class_id,
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
            class_id = request.form.get("class_id")

            upd_student = {
                "student_id": request.form.get("student_id"),
                "upd_name": request.form.get("name"),
                "upd_email": request.form.get("email"),
                "upd_phone": request.form.get("phone"),
                "upd_location": request.form.get("location"),
                "upd_class_type": request.form.get("class_type"),
            }

            con, cur = connect_to_db()

            cur.execute(
                """UPDATE student SET name = (?), email = (?), phone = (?) WHERE student_id = (?)""",
                (
                    upd_student["upd_name"],
                    upd_student["upd_email"],
                    upd_student["upd_phone"],
                    # upd_student["upd_location"],
                    # upd_student["upd_class_type"],
                    upd_student["student_id"],
                ),
            )
            con.commit()

            msg = "You have sucsessfully edited a student."
            return render_template(
                "feedback_msg/confirm-edit.html",
                msg=msg,
                class_id=class_id,
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
            class_id = request.form.get("class_id")

            new_student = {
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

            con, cur = connect_to_db()

            cur.execute(
                """INSERT into student (name, email, phone, location, course, class_type) VALUES (?, ?, ?, ? ,?, ?)""",
                (
                    new_student["name"],
                    new_student["email"],
                    new_student["phone"],
                    new_student["location"],
                    new_student["course"],
                    new_student["class_type"],
                ),
            )
            con.commit()

            # Add the new student to the current
            student_id = cur.lastrowid  # Get the newly inserted student's ID

            cur.execute(
                "INSERT INTO class_student (class_id, student_id) VALUES (?,?);",
                (class_id, student_id),
            )
            con.commit()

            msg = "Student has sucessfully been added."
            return render_template(
                "feedback_msg/confirm-add.html",
                class_id=class_id,
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
                con, cur = connect_to_db()

                cur.execute("DELETE FROM student WHERE student_id = (?)", (student_id,))
                con.commit()
            finally:
                con.close()

        page = request.args.get("page", 1, type=int)
        students, students_per_page, total_pages = fetch_students(class_id, page)

        return render_template(
            "student/student-list.html",
            students=students,
            class_id=class_id,
            students_per_page=students_per_page,
            total_pages=total_pages,
            page=page,
        )


#  Navigation Related Routes
@app.route("/homepage", methods=["GET", "POST"])
def homepage():
    classes, archived = fetch_classes()
    welcome_msg = welcome_user()
    return render_template(
        "homepage/homepage.html",
        classes=classes,
        archived=archived,
        loggedin=True,
        welcome_msg=welcome_msg,
    )


@app.route("/archived_classes", methods=["GET", "POST"])
def archived_classes():
    classes, archived = fetch_classes()
    welcome_msg = welcome_user()
    # return render_template(
    #     "archived_classes/archived_classes.html",
    #     archived=archived,
    #     loggedin=True,
    #     welcome_msg=welcome_msg,
    # )
    return render_template("archived_classes/WIP_archived.html")


# Search Related Route
@app.route("/search")
def searc():
    q = request.args.get("q")

    if q:
        con, cur = connect_to_db()
        archived = cur.execute("SELECT * FROM class WHERE ")
