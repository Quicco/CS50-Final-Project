from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from dotenv import load_dotenv
from io import TextIOWrapper
from utils import validate_phone_num, LOCATIONS, CLASS_TYPES, COURSES, TIME_SLOTS
import sqlite3, datetime, os, csv


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


def fetch_classes(page):
    try:
        con, cur = connect_to_db()

        classes = cur.execute(
            "SELECT * FROM class WHERE archived = 0 ORDER BY location;"
        ).fetchall()
        ongoing_classes = [dict(row) for row in classes]

        classes_per_page, total_pages = pagination(ongoing_classes, page)

        return ongoing_classes, classes_per_page, total_pages

    except sqlite3.Error as e:
        return f"Database error: {e}"
    finally:
        con.close()


def fetch_archived_classes(page):
    try:
        con, cur = connect_to_db()

        archived_classes = cur.execute(
            "SELECT * FROM class WHERE archived = 1 ORDER BY location;"
        ).fetchall()
        archived = [dict(row) for row in archived_classes]

        archived_classes_per_page, total_pages = pagination(archived_classes, page)

        return archived, archived_classes_per_page, total_pages

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
        students_per_page, total_pages = pagination(students, page)

        return students, students_per_page, total_pages

    except sqlite3.Error as e:
        return f"Database error: {e}"
    finally:
        con.close()


def fetch_class_type(class_id):
    con, cur = connect_to_db()
    row = cur.execute(
        "SELECT class_type FROM class WHERE class_id = (?)", (class_id)
    ).fetchone()

    class_type = row["class_type"]
    return class_type


def pagination(items, page):
    # Pagination
    per_page = 8
    start = (page - 1) * per_page
    end = start + per_page
    total_pages = (len(items) + per_page - 1) // per_page
    items_per_page = items[start:end]

    return items_per_page, total_pages


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

                    page = request.args.get("page", 1, type=int)
                    classes, classes_per_page, total_pages = fetch_classes(page)

                    welcome_msg = welcome_user()
                    return render_template(
                        "homepage/homepage.html",
                        page=page,
                        classes_per_page=classes_per_page,
                        total_pages=total_pages,
                        classes=classes,
                        loggedin=True,
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

        class_type = fetch_class_type(class_id)
        page = request.args.get("page", 1, type=int)
        students, students_per_page, total_pages = fetch_students(class_id, page)

        return render_template(
            "student/student-list.html",
            students=students,
            class_id=class_id,
            class_type=class_type,
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
            "archived_classes/archived-student-list.html",
            students=students,
            class_id=class_id,
            students_per_page=students_per_page,
            total_pages=total_pages,
            page=page,
            loggedin=True,
        )


@app.route("/actions/add_class", methods=["GET", "POST"])
def add_class():
    if request.method == "POST":
        # A class has: Class Type, Course, TimeSlot, Location, Year

        current_year = datetime.date.today().year
        years = range(current_year, current_year + 5)

        return render_template(
            "course_classes/add-class.html",
            locations=LOCATIONS,
            time_slots=TIME_SLOTS,
            class_types=CLASS_TYPES,
            courses=COURSES,
            years=years,
        )


@app.route("/confirm/add_class", methods=["GET", "POST"])
def confirm_add_class():
    if request.method == "POST":
        try:
            new_class = {
                "course": request.form.get("course"),
                "class_type": request.form.get("class_type"),
                "time_slot": request.form.get("time_slot"),
                "location": request.form.get("location"),
                "year": request.form.get("year"),
                "archived": 0,
            }

            con, cur = connect_to_db()

            # Insert the new class onto the db
            cur.execute(
                "INSERT INTO class (course, class_type, time_slot, location, year, archived) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    new_class["course"],
                    new_class["class_type"],
                    new_class["time_slot"],
                    new_class["location"],
                    new_class["year"],
                    new_class["archived"],
                ),
            )
            con.commit()

            return redirect(url_for("homepage"))

        except sqlite3.Error as e:
            return f"Database error: {e}"
        finally:
            con.close()


@app.route("/actions/archive", methods=["GET", "POST"])
def archive_class():
    try:
        class_id = request.form.get("class_id")
        if not class_id:
            return render_template("/archived_classes/homepage.html")

        con, cur = connect_to_db()
        cur.execute("UPDATE class SET archived = 1 WHERE class_id = (?)", (class_id,))
        con.commit()
        page = request.args.get("page", 1, type=int)
        classes, classes_per_page, total_pages = fetch_classes(page)
        welcome_msg = welcome_user()

        return render_template(
            "homepage/homepage.html",
            classes=classes,
            loggedin=True,
            welcome_msg=welcome_msg,
            page=page,
            classes_per_page=classes_per_page,
            total_pages=total_pages,
        )
    except sqlite3.Error as e:
        return f"Database error: {e}"
    finally:
        con.close()


@app.route("/actions/unarchive", methods=["GET", "POST"])
def unarchive_class():
    try:
        class_id = request.form.get("class_id")
        con, cur = connect_to_db()

        cur.execute("UPDATE class SET archived = 0 WHERE class_id = (?);", (class_id,))
        con.commit()

        page = request.args.get("page", 1, type=int)
        archived_classes, archived_classes_per_page, total_pages = (
            fetch_archived_classes(page)
        )
        welcome_msg = welcome_user()

        return render_template(
            "archived_classes/archived-classes.html",
            archived_classes=archived_classes,
            loggedin=True,
            welcome_msg=welcome_msg,
            page=page,
            archived_classes_per_page=archived_classes_per_page,
            total_pages=total_pages,
        )
    finally:
        con.close()


@app.route("/actions/delete", methods=["GET", "POST"])
def delete_class():
    if request.method == "POST":
        class_id = request.form.get("class_id")
        try:
            con, cur = connect_to_db()

            # Get student_ids associated with the class
            cur.execute(
                "SELECT student_id FROM class_student WHERE class_id = (?)", (class_id,)
            )
            student_ids = [row[0] for row in cur.fetchall()]

            # Delete students from the student table
            for student_id in student_ids:
                cur.execute("DELETE FROM student WHERE student_id = (?)", (student_id,))

            # Delete all students associated with the class being deleted
            cur.execute("DELETE FROM class_student WHERE class_id = (?);", (class_id,))
            cur.execute("DELETE FROM class WHERE class_id = (?);", (class_id,))
            con.commit()

            page = request.args.get("page", 1, type=int)
            classes, classes_per_page, total_pages = fetch_classes(page)
            return render_template(
                "homepage/homepage.html",
                classes=classes,
                loggedin=True,
                page=page,
                classes_per_page=classes_per_page,
                total_pages=total_pages,
            )
        finally:
            con.close()


@app.route("/actions/import_data", methods=["GET", "POST"])
def import_data():

    class_id = request.form.get("class_id")

    if class_id:
        try:
            con, cur = connect_to_db()

            # Data from the class itself - Location, course, class_type
            class_data = cur.execute(
                "SELECT location, class_type, course FROM class WHERE class_id = (?)",
                (class_id),
            ).fetchone()

            csv_file = request.files.get("import")
            if not csv_file or not csv_file.filename.endswith(".csv"):
                return redirect(url_for("list", class_id=class_id))
            with csv_file.stream as f:
                reader = csv.reader(TextIOWrapper(f, encoding="latin-1"), delimiter=",")
                next(reader, None)

                for row in reader:
                    cur.execute(
                        "INSERT OR IGNORE INTO student (name, email, phone, location, course, class_type) VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            row[0],
                            row[1],
                            row[2],
                            class_data["location"],
                            class_data["course"],
                            class_data["class_type"],
                        ),
                    )
                    student_id = cur.lastrowid
                    cur.execute(
                        "INSERT INTO class_student (student_id, class_id) VALUES (?, ?)",
                        (student_id, class_id),
                    )

                con.commit()

                return redirect(url_for("list", class_id=class_id))

        finally:
            con.close()
    return "Didn't work"


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
            loggedin=True,
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
        class_type = fetch_class_type(class_id)
        page = request.args.get("page", 1, type=int)
        students, students_per_page, total_pages = fetch_students(class_id, page)
        return render_template(
            "student/student-list.html",
            students=students,
            class_id=class_id,
            class_type=class_type,
            students_per_page=students_per_page,
            total_pages=total_pages,
            page=page,
            loggedin=True,
            is_active_class=True,
        )

    except sqlite3.Error as e:
        return f"Database error: {e}"
    finally:
        con.close()


@app.route("/archived_list", methods=["GET", "POST"])
def archived_list():
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
            "archived_classes/archived-student-list.html",
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
            loggedin=True,
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
                loggedin=True,
            )

        except sqlite3.Error as e:
            return f"Database error: {e}"
        finally:
            con.close()


@app.route("/confirm/edit", methods=["GET", "POST"])
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

            msg = "You have successfully edited a student."
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

        con, cur = connect_to_db()

        class_id = request.form.get("class_id")
        class_data = cur.execute(
            "SELECT location, class_type, course FROM class WHERE class_id = (?)",
            (class_id),
        ).fetchone()

        return render_template(
            "student/add-student.html",
            class_id=class_id,
            class_type=class_data[1],
            location=class_data[0],
            loggedin=True,
        )


@app.route("/confirm/add_student", methods=["GET", "POST"])
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

            msg = "Student has successfully been added."
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

                cur.execute(
                    "DELETE FROM class_student WHERE student_id = (?) AND class_id = (?)",
                    (student_id, class_id),
                )

                cur.execute("DELETE FROM student WHERE student_id = (?)", (student_id,))
                con.commit()
            finally:
                con.close()

        class_type = fetch_class_type(class_id)
        page = request.args.get("page", 1, type=int)
        students, students_per_page, total_pages = fetch_students(class_id, page)

        return render_template(
            "student/student-list.html",
            students=students,
            class_id=class_id,
            class_type=class_type,
            students_per_page=students_per_page,
            total_pages=total_pages,
            page=page,
            loggedin=True,
        )


#  Navigation Related Routes
@app.route("/homepage", methods=["GET", "POST"])
def homepage():

    page = request.args.get("page", 1, type=int)
    classes, classes_per_page, total_pages = fetch_classes(page)
    welcome_msg = welcome_user()

    return render_template(
        "homepage/homepage.html",
        classes=classes,
        loggedin=True,
        welcome_msg=welcome_msg,
        page=page,
        classes_per_page=classes_per_page,
        total_pages=total_pages,
    )


@app.route("/archived_classes", methods=["GET", "POST"])
def archived_classes():

    page = request.args.get("page", 1, type=int)
    archived_classes, archived_classes_per_page, total_pages = fetch_archived_classes(
        page
    )

    return render_template(
        "archived_classes/archived-classes.html",
        page=page,
        archived_classes=archived_classes,
        archived_classes_per_page=archived_classes_per_page,
        total_pages=total_pages,
        loggedin=True,
    )


# Search Related Route
@app.route("/search")
def search():
    q = request.args.get("q")
    if q:
        con, cur = connect_to_db()
        like_pattern = f"%{q}%"
        rows = cur.execute(
            f"SELECT * FROM class WHERE (class_id LIKE (?) OR class_type LIKE (?) OR course LIKE (?) OR location LIKE (?) OR time_slot LIKE (?) OR year LIKE (?)) AND archived = 1",
            (
                like_pattern,
                like_pattern,
                like_pattern,
                like_pattern,
                like_pattern,
                like_pattern,
            ),
        ).fetchall()
        con.close()

        results = [dict(row) for row in rows]
    else:
        page = request.args.get("page", 1, type=int)
        archived_classes, archived_classes_per_page, total_pages = (
            fetch_archived_classes(page)
        )
        results = [dict(row) for row in archived_classes]

    return jsonify(results)
