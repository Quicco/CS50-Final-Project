from flask import Flask, render_template, request, session
from argon2 import PasswordHasher
import sqlite3

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register")
def register():
    return "Register"


@app.route("/login")
def login():
    return "Login"
