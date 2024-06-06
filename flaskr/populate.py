import sqlite3
from argon2 import PasswordHasher


db_path = "database.db"
con = sqlite3.connect(db_path)
cur = con.cursor()
ph = PasswordHasher()


def initialize_db():
    create_tables()
    populate_db()


def create_tables():
    queries = [
        "CREATE TABLE IF NOT EXISTS teacher(teacher_id INTEGER PRIMARY KEY, name TEXT, email TEXT, password TEXT);",
        "CREATE TABLE IF NOT EXISTS class (class_id INTEGER PRIMARY KEY, course TEXT, class_type TEXT, time_slot TEXT, location TEXT, year INTEGER);",
        "CREATE TABLE IF NOT EXISTS student (student_id INTEGER PRIMARY KEY, name TEXT, email TEXT, phone TEXT, location TEXT, course TEXT);",
    ]
    for query in queries:
        cur.execute(query)
    con.commit()


def populate_db():
    # Populate teacher table
    DEV_NAME = "Tiago"
    DEV_MAIL = "admin@dev.com"
    DEV_PW = ph.hash("123")
    cur.execute(
        "INSERT INTO teacher (name, email, password) VALUES (?, ?, ?)",
        (
            DEV_NAME,
            DEV_MAIL,
            DEV_PW,
        ),
    )
    # Populate class table
    classes = [
        {
            "course": "Junior Fullstack Developer",
            "class_type": "PowerUp",
            "time_slot": "Morning",
            "location": "Lisbon",
            "year": 2024,
        },
        {
            "course": "Junior Fullstack Developer",
            "class_type": "PowerUp",
            "time_slot": "Afternoon",
            "location": "Lisbon",
            "year": 2024,
        },
    ]
    for group in classes:
        values = tuple(group.values())
        cur.execute(
            "INSERT INTO class (course, class_type, time_slot, location, year) VALUES (?, ?, ?, ? , ?)",
            values,
        )
    con.commit()
    # Populate student table


initialize_db()
con.close()
