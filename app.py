from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "secret_key_here"

# ======== SET ADMIN CREDENTIALS HERE ========
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
# ============================================

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root111",
        database="repo_management"
    )

# ========================= BEFORE LOGIN PAGES =========================
@app.route("/")
def home():
    return render_template("index.html", active_page="home")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Check if it's admin login
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            session['is_admin'] = True
            flash("Admin login successful!", "success")
            return redirect(url_for("admin"))
        
        # Check if it's regular user login
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user and check_password_hash(user["password"], password):
            session['logged_in'] = True
            session['username'] = username
            session['is_admin'] = False
            session['user_id'] = user['user_id']
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password!", "error")
            return redirect(url_for("login"))

    return render_template("login.html", active_page="login")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form["full_name"]
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute(
                "INSERT INTO users (full_name, username, email, password) VALUES (%s, %s, %s, %s)",
                (full_name, username, email, hashed_password)
            )
            db.commit()
            flash("Account created successfully!", "success")
            cursor.close()
            db.close()
            return redirect(url_for("login"))
        except mysql.connector.IntegrityError:
            flash("Username or email already exists!", "error")
            cursor.close()
            db.close()
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

        db = get_db_connection()
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO feedback (name, category, experience, message) VALUES (%s, %s, %s, %s)",
                (name, category, experience, message)
            )
            db.commit()
            flash("Thank you for your feedback!", "success")
        except Exception as e:
            db.rollback()
            flash("Something went wrong. Please try again.", "error")
        finally:
            cursor.close()
            db.close()

        return redirect(url_for("feedback"))

    return render_template("feedback.html", active_page="feedback")

# ========================= AFTER LOGIN PAGES =========================
@app.route("/dashboard")
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for("login"))
    
    # TEMPORARY SAMPLE DATA - Replace with real database queries later
    username = session.get('username', 'User')
    
    # Sample stats
    user_stats = {
        'total_repos': 3,
        'total_commits': 35,
        'open_issues': 2
    }
    
    # Sample repositories
    user_repos = [
        {'repo_name': 'mini-git-core', 'star_count': 5, 'commit_count': 12, 'created_date': datetime.now()},
        {'repo_name': 'ui-dashboard', 'star_count': 3, 'commit_count': 8, 'created_date': datetime.now()},
        {'repo_name': 'auth-service', 'star_count': 2, 'commit_count': 5, 'created_date': datetime.now()}
    ]
    
    # Sample activity
    recent_activity = [
        {'icon': '📝', 'description': 'Committed to mini-git-core', 'time_ago': '2 hours ago'},
        {'icon': '📁', 'description': 'Created repository ui-dashboard', 'time_ago': '1 day ago'},
        {'icon': '⭐', 'description': 'Starred repo auth-service', 'time_ago': '3 days ago'},
        {'icon': '🐛', 'description': 'Opened issue #42', 'time_ago': '1 week ago'}
    ]
    
    # Sample commits
    recent_commits = [
        {'commit_message': 'Fixed authentication bug in login page', 'repo_name': 'mini-git-core', 'commit_date': datetime.now()},
        {'commit_message': 'Updated README documentation', 'repo_name': 'mini-git-core', 'commit_date': datetime.now()},
        {'commit_message': 'Refactored dashboard UI components', 'repo_name': 'ui-dashboard', 'commit_date': datetime.now()},
        {'commit_message': 'Optimized database queries', 'repo_name': 'auth-service', 'commit_date': datetime.now()}
    ]
    
    return render_template("dashboard.html", 
                         active_page="dashboard",
                         username=username,
                         user_stats=user_stats,
                         user_repos=user_repos,
                         recent_activity=recent_activity,
                         recent_commits=recent_commits)

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

# ========================= ADMIN PAGES =========================
@app.route("/admin")
def admin():
    # Only allow access if user is logged in AND is admin
    if not session.get('logged_in') or not session.get('is_admin'):
        return redirect(url_for("login"))
    
    # Get which report to show (default: user report)
    report_type = request.args.get('report', 'user')
    
    # Fetch data based on report type
    if report_type == 'user':
        data = get_user_report_data_simple()
    elif report_type == 'feedback':
        data = get_feedback_report_data_simple()
    else:
        data = get_user_report_data_simple()
        report_type = 'user'
    
    # Pass active report to template
    data['active_report'] = report_type
    
    return render_template("admin.html", **data)

# ========================= SIMPLIFIED ADMIN FUNCTIONS (NO ERRORS) =========================
def get_user_report_data_simple():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # Get user stats - simplified without activity_logs
    cursor.execute("SELECT COUNT(*) as total_users FROM users")
    total_users = cursor.fetchone()['total_users']
    
    # Simple active users calculation (users with recent created_at)
    cursor.execute("""
        SELECT COUNT(*) as active_users 
        FROM users 
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    """)
    active_users = cursor.fetchone()['active_users']
    
    cursor.execute("""
        SELECT COUNT(*) as new_today 
        FROM users 
        WHERE DATE(created_at) = CURDATE()
    """)
    new_today = cursor.fetchone()['new_today']
    
    # Get all users
    cursor.execute("""
        SELECT user_id, username, email, created_at, 'active' as status
        FROM users
        ORDER BY created_at DESC
        LIMIT 50
    """)
    users = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return {
        'user_stats': {
            'total_users': total_users,
            'active_users': active_users,
            'new_today': new_today
        },
        'users': users
    }

def get_feedback_report_data_simple():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # Get feedback stats
    cursor.execute("SELECT COUNT(*) as total_feedback FROM feedback")
    total_feedback = cursor.fetchone()['total_feedback']
    
    cursor.execute("""
        SELECT COUNT(*) as positive_feedback 
        FROM feedback 
        WHERE experience IN ('Excellent', 'Good', 'Very Good')
    """)
    positive_feedback = cursor.fetchone()['positive_feedback']
    
    cursor.execute("""
        SELECT COUNT(*) as action_needed 
        FROM feedback 
        WHERE experience IN ('Poor', 'Very Poor')
    """)
    action_needed = cursor.fetchone()['action_needed']
    
    # Get all feedback
    cursor.execute("""
        SELECT feedback_id, name, category, experience, 
               DATE(created_at) as date, 
               CASE 
                   WHEN experience IN ('Excellent', 'Good') THEN 'Resolved'
                   WHEN experience = 'Average' THEN 'In Progress'
                   ELSE 'Pending'
               END as status
        FROM feedback
        ORDER BY created_at DESC
        LIMIT 50
    """)
    feedbacks = cursor.fetchall()
    
    # Prepare data for chart
    cursor.execute("""
        SELECT category, COUNT(*) as count
        FROM feedback
        GROUP BY category
        ORDER BY count DESC
        LIMIT 10
    """)
    chart_data = cursor.fetchall()
    
    feedback_labels = [item['category'] for item in chart_data]
    feedback_values = [item['count'] for item in chart_data]
    
    cursor.close()
    db.close()
    
    return {
        'feedback_stats': {
            'total_feedback': total_feedback,
            'positive_feedback': positive_feedback,
            'action_needed': action_needed
        },
        'feedbacks': feedbacks,
        'feedback_labels': feedback_labels,
        'feedback_values': feedback_values
    }

# ========================= RUN APP =========================
if __name__ == "__main__":
    app.run(debug=True)