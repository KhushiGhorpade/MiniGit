from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = "secret_key_here"

# ======== SET ADMIN CREDENTIALS HERE ========
ADMIN_USERNAME = "admin"  # Change this to your desired admin username
ADMIN_PASSWORD = "admin123"  # Change this to your desired admin password
# ============================================

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root111",
    database="repo_management"
)
cursor = db.cursor(dictionary=True)

# ========================= BEFORE LOGIN PAGES =========================
@app.route("/")
def home():
    return render_template("index.html", active_page="home")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # FIRST: Check if it's admin login
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            session['is_admin'] = True
            flash("Admin login successful!", "success")
            return redirect(url_for("admin"))  # Redirect to admin page
        
        # SECOND: Check if it's regular user login (from database)
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user["password"], password):
            session['logged_in'] = True
            session['username'] = username
            session['is_admin'] = False
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password!", "error")
            return redirect(url_for("login"))  # Fixed: redirect back to login, not dashboard

    return render_template("login.html", active_page="login")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form["full_name"]
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        try:
            cursor.execute(
                "INSERT INTO users (full_name, username, email, password) VALUES (%s, %s, %s, %s)",
                (full_name, username, email, hashed_password)
            )
            db.commit()
            flash("Account created successfully!", "success")
            return redirect(url_for("login"))
        except mysql.connector.IntegrityError:
            flash("Username or email already exists!", "error")
            return redirect(url_for("register"))

    return render_template("register.html", active_page="register")

@app.route("/features")
def features():
    return render_template("features.html", active_page="features")

@app.route("/demo")
def demo():
    return render_template("demo.html", active_page="demo")

@app.route("/help")
def help():
    return render_template("help.html", active_page="help")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html", active_page="privacy")

@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.method == "POST":
        name = request.form.get("name")
        category = request.form.get("category")
        experience = request.form.get("experience")
        message = request.form.get("message")

        try:
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO feedback (name, category, experience, message) VALUES (%s, %s, %s, %s)",
                (name, category, experience, message)
            )
            db.commit()
            cursor.close()

            flash("Thank you for your feedback!", "success")
        except Exception as e:
            db.rollback()
            flash("Something went wrong. Please try again.", "error")
            print(e)

        return redirect(url_for("feedback"))

    return render_template("feedback.html", active_page="feedback")

# ========================= AFTER LOGIN PAGES =========================
@app.route("/dashboard")
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for("login"))
    return render_template("dashboard.html", active_page="dashboard")

@app.route("/repos")
def repos():
    if not session.get('logged_in'):
        return redirect(url_for("login"))
    return render_template("repos.html", active_page="repos")

@app.route("/activity")
def activity():
    if not session.get('logged_in'):
        return redirect(url_for("login"))
        
    repo_commits = [
        {"repo": "Repo A", "commits": 12},
        {"repo": "Repo B", "commits": 8},
        {"repo": "Repo C", "commits": 15},
    ]

    repo_issues = [
        {"repo": "Repo A", "open_issues": 3},
        {"repo": "Repo B", "open_issues": 5},
        {"repo": "Repo C", "open_issues": 2},
    ]

    repo_names = ["Repo A", "Repo B", "Repo C"]

    return render_template(
        "activity.html",
        repo_commits=repo_commits,
        repo_issues=repo_issues,
        repo_names=repo_names,
        active_page="activity"
    )

@app.route("/profile")
def profile():
    if not session.get('logged_in'):
        return redirect(url_for("login"))
    return render_template("profile.html", active_page="profile")

@app.route("/my-repos")
def my_repos():
    if not session.get('logged_in'):
        return redirect(url_for("login"))
    return render_template("my_repos.html", active_page="my-repos")

@app.route("/create-repo")
def create_repo():
    if not session.get('logged_in'):
        return redirect(url_for("login"))
    return render_template("create_repo.html", active_page="create-repo")

@app.route("/create-issue", methods=["GET", "POST"])
def create_issue():
    if not session.get('logged_in'):
        return redirect(url_for("login"))
    return render_template("create_issue.html", active_page="create-issue")

@app.route("/create-commit", methods=["GET", "POST"])
def create_commit():
    if not session.get('logged_in'):
        return redirect(url_for("login"))
    return render_template("create_commit.html", active_page="create-commit")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/admin")
def admin():
    # Only allow access if user is logged in AND is admin
    if not session.get('logged_in') or not session.get('is_admin'):
        return redirect(url_for("login"))
    return render_template("admin.html", active_page="admin")

# ========================= RUN APP =========================
if __name__ == "__main__":
    app.run(debug=True)