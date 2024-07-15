import sqlite3
import random
from utils import validate_phone_num
from argon2 import PasswordHasher
from faker import Faker


db_path = "database.db"
con = sqlite3.connect(db_path)
cur = con.cursor()
ph = PasswordHasher()


# Main function for the database - Create tables, then populate them
def initialize_db():
    create_tables()
    populate_db()


# Handler functions for the database
def create_tables():
    queries = [
        # Teacher table
        "CREATE TABLE IF NOT EXISTS teacher (teacher_id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password TEXT, class_id INTEGER, FOREIGN KEY (class_id) REFERENCES class(class_id));",
        # Class table
        "CREATE TABLE IF NOT EXISTS class (class_id INTEGER PRIMARY KEY, course TEXT, class_type TEXT, time_slot TEXT, location TEXT, year INTEGER, archived INTEGER);",
        # Student table
        """CREATE TABLE IF NOT EXISTS student (
        student_id INTEGER PRIMARY KEY, 
        name TEXT, 
        email TEXT UNIQUE, 
        phone TEXT, 
        location TEXT, 
        course TEXT, 
        class_type TEXT, 
        teacher_id INTEGER,
        FOREIGN KEY (teacher_id) REFERENCES teacher(teacher_id)
        );""",
        # Class_student junction table
        "CREATE TABLE IF NOT EXISTS class_student (class_id INTEGER, student_id INTEGER, PRIMARY KEY (class_id, student_id), FOREIGN KEY (class_id) REFERENCES class(class_id), FOREIGN KEY (student_id) REFERENCES student(student_id));",
        # Class_teacher junction table
        "CREATE TABLE IF NOT EXISTS class_teacher (class_id INTEGER, teacher_id INTEGER, PRIMARY KEY (class_id, teacher_id), FOREIGN KEY (class_id) REFERENCES class(class_id), FOREIGN KEY (teacher_id) REFERENCES teacher(teacher_id));",
    ]

    for query in queries:
        cur.execute(query)
    con.commit()


#  Populate all tables (teacher, class, students) of the db
def populate_db():
    fake = Faker("pt_PT")

    #  Populate teacher table
    DEV_NAME = "Tiago"
    DEV_MAIL = "admin@dev.com"
    DEV_PW = ph.hash("123")
    DEV_CLASS = 1
    cur.execute(
        "INSERT INTO teacher (name, email, password, class_id) VALUES (?, ?, ?, ?)",
        (DEV_NAME, DEV_MAIL, DEV_PW, DEV_CLASS),
    )

    #  Populate class table
    classes = [
        {
            "course": "Junior Fullstack Developer",
            "class_type": "PowerUp",
            "time_slot": "Morning",
            "location": "Lisbon",
            "year": 2024,
            "archived": 0,
        },
        {
            "course": "Junior Fullstack Developer",
            "class_type": "PowerUp",
            "time_slot": "Afternoon",
            "location": "Lisbon",
            "year": 2024,
            "archived": 0,
        },
        {
            "course": "Junior Fullstack Developer",
            "class_type": "PowerUp",
            "time_slot": "Afternoon",
            "location": "Sintra",
            "year": 2024,
            "archived": 1,
        },
    ]
    for group in classes:
        values = tuple(group.values())
        cur.execute(
            "INSERT INTO class (course, class_type, time_slot, location, year, archived) VALUES (?, ?, ?, ? , ?, ?)",
            values,
        )
    con.commit()

    # Create a list with 24 ones and 24 twos adn 24 threes
    class_ids = [1] * 24 + [2] * 24 + [3] * 24
    # Shuffle the list to randomize the order
    random.shuffle(class_ids)

    for class_id in class_ids:
        student = {
            "name": fake.name(),
            "email": fake.email(),
            "phone": validate_phone_num(fake.phone_number()),
            "location": "Lisbon",
            "course": "Junior Fullstack Developer",
            "class_type": "PowerUp",
        }

        if student["phone"]:
            values = tuple(student.values())
            cur.execute(
                "INSERT INTO student (name, email, phone, location, course, class_type) VALUES (?, ?, ?, ? , ?, ?)",
                values,
            )

            student_id = cur.lastrowid

            # Insert into class_student junction table
            cur.execute(
                "INSERT INTO class_student (class_id, student_id) VALUES (?, ?)",
                (class_id, student_id),
            )

    con.commit()


initialize_db()
con.close()
