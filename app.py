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
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        
        # ---- ADMIN LOGIN ----
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            session["username"] = username
            session["full_name"] = "Administrator"
            session["is_admin"] = True
            session["user_id"] = 0
            flash("Admin login successful!", "success")
            return redirect(url_for("admin"))

        # ---- USER LOGIN ----
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE username = %s OR email = %s",
            (username, username)
        )

        user = cursor.fetchone()
        
        if user and check_password_hash(user["password"], password):
            # Store ALL user data in session
            session["logged_in"] = True
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["full_name"] = user["full_name"]
            session["email"] = user["email"]
            session["is_admin"] = (user["role"] == 'admin')
            
            # Update last login time
            update_cursor = db.cursor()
            update_cursor.execute(
                "UPDATE users SET last_login = NOW() WHERE user_id = %s",
                (user["user_id"],)
            )
            db.commit()
            update_cursor.close()
            
            cursor.close()
            db.close()
            
            flash(f"Welcome back, {user['full_name']}!", "success")
            
            # Redirect based on role
            if user["role"] == 'admin':
                return redirect(url_for("admin"))
            return redirect(url_for("dashboard"))
        else:
            cursor.close()
            db.close()
            flash("Invalid username or password", "error")
            return redirect(url_for("login"))

    return render_template("login.html", active_page="login")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form["full_name"]
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        # Generate password hash
        hashed_password = generate_password_hash(password)
        
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute(
                "INSERT INTO users (full_name, username, email, password) VALUES (%s, %s, %s, %s)",
                (full_name, username, email, hashed_password)
            )
            db.commit()
            
            # Get the new user's ID
            user_id = cursor.lastrowid
            
            # Auto-login the user
            session["logged_in"] = True
            session["user_id"] = user_id
            session["username"] = username
            session["full_name"] = full_name
            session["email"] = email
            session["is_admin"] = False
            
            flash(f"Welcome to MiniGit, {full_name}!", "success")
            cursor.close()
            db.close()
            return redirect(url_for("dashboard"))
            
        except mysql.connector.IntegrityError as e:
            if "username" in str(e):
                flash("Username already exists!", "error")
            elif "email" in str(e):
                flash("Email already exists!", "error")
            else:
                flash("Registration failed!", "error")
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
    
    # Get user data from session
    username = session.get('full_name', session.get('username', 'User'))
    
    # Sample stats (will be replaced with real data later)
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
        {'icon': '⭐', 'description': 'Starred repo auth-service', 'time_ago': '3 days ago'}
    ]
    
    # Sample commits
    recent_commits = [
        {'commit_message': 'Fixed authentication bug', 'repo_name': 'mini-git-core', 'commit_date': datetime.now()},
        {'commit_message': 'Updated README', 'repo_name': 'mini-git-core', 'commit_date': datetime.now()}
    ]
    
    return render_template("dashboard.html", 
                         active_page="dashboard",
                         username=username,
                         user_stats=user_stats,
                         user_repos=user_repos,
                         recent_activity=recent_activity,
                         recent_commits=recent_commits)

@app.route("/repositories")
def repos():
    if not session.get('logged_in'):
        return redirect(url_for("login"))
    return render_template("repositories.html", active_page="repositories")

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
    flash("You have been logged out", "info")
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
        data = get_user_report_data()
    elif report_type == 'feedback':
        data = get_feedback_report_data()
    else:
        data = get_user_report_data()
        report_type = 'user'
    
    # Pass active report to template
    data['active_report'] = report_type
    data['admin_name'] = session.get('full_name', 'Admin')
    
    return render_template("admin.html", **data)

# ========================= ADMIN DATA FUNCTIONS =========================
def get_user_report_data():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # Get user stats
    cursor.execute("SELECT COUNT(*) as total_users FROM users")
    total_users = cursor.fetchone()['total_users']
    
    cursor.execute("""
        SELECT COUNT(*) as active_users 
        FROM users 
        WHERE last_login >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    """)
    active_users = cursor.fetchone()['active_users']
    
    cursor.execute("""
        SELECT COUNT(*) as new_today 
        FROM users 
        WHERE DATE(created_at) = CURDATE()
    """)
    new_today = cursor.fetchone()['new_today']
    
    # Get all users - FIXED DATE FORMAT
    cursor.execute("""
        SELECT 
            user_id,
            username,
            email,
            DATE_FORMAT(created_at, '%Y-%m-%d') as registration_date,
            CASE 
                WHEN last_login IS NULL THEN 'Inactive'
                WHEN last_login >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 'Active'
                ELSE 'Inactive'
            END as status
        FROM users
        ORDER BY created_at DESC
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

def get_feedback_report_data():
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
    
    # Get all feedback - FIXED to use feedback_id not id
    cursor.execute("""
        SELECT 
            feedback_id,
            name,
            category,
            experience,
            DATE_FORMAT(created_at, '%Y-%m-%d') as date,
            CASE 
                WHEN experience IN ('Excellent', 'Good') THEN 'Resolved'
                WHEN experience = 'Average' THEN 'In Progress'
                ELSE 'Pending'
            END as status,
            message
        FROM feedback
        ORDER BY created_at DESC
        LIMIT 50
    """)
    feedbacks = cursor.fetchall()
    
    # Get category counts for chart
    cursor.execute("""
        SELECT category, COUNT(*) as count
        FROM feedback
        GROUP BY category
        ORDER BY count DESC
        LIMIT 10
    """)
    categories = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return {
        'feedback_stats': {
            'total_feedback': total_feedback,
            'positive_feedback': positive_feedback,
            'action_needed': action_needed
        },
        'feedbacks': feedbacks,
        'categories': categories
    }

# ========================= ADMIN API ENDPOINTS =========================
@app.route("/api/admin/users")
def api_admin_users():
    # Only allow access if user is logged in AND is admin
    if not session.get('logged_in') or not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 401
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # Get user stats
    cursor.execute("SELECT COUNT(*) as total_users FROM users")
    total_users = cursor.fetchone()['total_users']
    
    cursor.execute("""
        SELECT COUNT(*) as active_users 
        FROM users 
        WHERE last_login >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    """)
    active_users = cursor.fetchone()['active_users']
    
    cursor.execute("""
        SELECT COUNT(*) as new_today 
        FROM users 
        WHERE DATE(created_at) = CURDATE()
    """)
    new_today = cursor.fetchone()['new_today']
    
    # Get all users - FIXED DATE FORMAT
    cursor.execute("""
        SELECT 
            user_id as id,
            username,
            email,
            DATE_FORMAT(created_at, '%Y-%m-%d') as regDate,
            CASE 
                WHEN last_login IS NULL THEN 'Inactive'
                WHEN last_login >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 'Active'
                ELSE 'Inactive'
            END as status
        FROM users
        ORDER BY created_at DESC
    """)
    
    users = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return jsonify({
        "total": total_users,
        "active": active_users,
        "newToday": new_today,
        "users": users
    })

@app.route("/api/admin/popularity")
def api_admin_popularity():

    # Only allow access if user is logged in AND is admin
    if not session.get('logged_in') or not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 401
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            r.repo_id,
            r.repo_name,
            u.username AS owner,
            COUNT(DISTINCT rs.star_id) AS stars,
            COUNT(DISTINCT rv.view_id) AS views
        FROM repositories r
        JOIN users u ON r.owner_id = u.user_id
        LEFT JOIN repo_stars rs ON r.repo_id = rs.repo_id
        LEFT JOIN repo_views rv ON r.repo_id = rv.repo_id
        GROUP BY r.repo_id
        ORDER BY stars DESC
        LIMIT 5;
    """)

    repos = cursor.fetchall()
    cursor.close()
    db.close()

    return jsonify(repos)

@app.route("/api/admin/feedback")
def api_admin_feedback():
    # Only allow access if user is logged in AND is admin
    if not session.get('logged_in') or not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 401
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Get feedback stats
        cursor.execute("SELECT COUNT(*) as total_feedback FROM feedback")
        result = cursor.fetchone()
        total_feedback = result['total_feedback'] if result else 0
        
        cursor.execute("""
            SELECT COUNT(*) as positive_feedback 
            FROM feedback 
            WHERE experience IN ('Excellent', 'Good', 'Very Good')
        """)
        result = cursor.fetchone()
        positive_feedback = result['positive_feedback'] if result else 0
        
        cursor.execute("""
            SELECT COUNT(*) as action_needed 
            FROM feedback 
            WHERE experience IN ('Poor', 'Very Poor')
        """)
        result = cursor.fetchone()
        action_needed = result['action_needed'] if result else 0
        
        # Get all feedback - FIXED: using feedback_id as id for JavaScript
        cursor.execute("""
            SELECT 
                feedback_id as id,
                name,
                category,
                experience,
                DATE_FORMAT(created_at, '%Y-%m-%d') as date,
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
        
        # Get category counts for chart
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM feedback
            GROUP BY category
            ORDER BY count DESC
            LIMIT 10
        """)
        categories = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return jsonify({
            "total": total_feedback,
            "positive": positive_feedback,
            "actionNeeded": action_needed,
            "feedbacks": feedbacks,
            "categories": categories
        })
    
    except Exception as e:
        print(f"ERROR in feedback API: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route("/api/admin/commits")
def api_admin_commits():
    # Only allow access if user is logged in AND is admin
    if not session.get('logged_in') or not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Get commit stats - using your actual column names
        cursor.execute("SELECT COUNT(*) as total FROM commits")
        result = cursor.fetchone()
        total_commits = result['total'] if result else 0
        
        cursor.execute("""
            SELECT COUNT(*) as today 
            FROM commits 
            WHERE DATE(committed_at) = CURDATE()
        """)
        result = cursor.fetchone()
        today_commits = result['today'] if result else 0
        
        # Get most active user
        cursor.execute("""
            SELECT u.username, COUNT(c.commit_id) as count
            FROM commits c
            JOIN users u ON c.user_id = u.user_id
            GROUP BY u.user_id, u.username
            ORDER BY count DESC
            LIMIT 1
        """)
        most_active = cursor.fetchone()
        most_active_user = most_active['username'] if most_active else 'N/A'
        
        # Get recent commits - using your actual column names
        cursor.execute("""
            SELECT 
                c.commit_id as id,
                r.repo_name,
                c.commit_message as message,
                u.username as committed_by,
                DATE_FORMAT(c.committed_at, '%Y-%m-%d %H:%i') as date
            FROM commits c
            JOIN repositories r ON c.repo_id = r.repo_id
            JOIN users u ON c.user_id = u.user_id
            ORDER BY c.committed_at DESC
            LIMIT 50
        """)
        commits = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return jsonify({
            "total": total_commits,
            "today": today_commits,
            "mostActiveUser": most_active_user,
            "commits": commits
        })
    
    except Exception as e:
        print(f"ERROR in commits API: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
@app.route("/api/admin/issues")
def api_admin_issues():
    # Only allow access if user is logged in AND is admin
    if not session.get('logged_in') or not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Get issue stats
        cursor.execute("SELECT COUNT(*) as total FROM issues")
        result = cursor.fetchone()
        total_issues = result['total'] if result else 0
        
        # Fix: Use your actual status values from the table
        cursor.execute("""
            SELECT COUNT(*) as open 
            FROM issues 
            WHERE status IN ('open', 'in_progress')
        """)
        result = cursor.fetchone()
        open_issues = result['open'] if result else 0
        
        # Fix: Use created_at instead of updated_at
        cursor.execute("""
            SELECT COUNT(*) as closed_today 
            FROM issues 
            WHERE status = 'closed'
            AND DATE(created_at) = CURDATE()
        """)
        result = cursor.fetchone()
        closed_today = result['closed_today'] if result else 0
        
        # Fix: Use correct column names (user_id instead of created_by)
        cursor.execute("""
            SELECT 
                i.issue_id as id,
                r.repo_name,
                i.title as issue_title,
                u.username as created_by,
                i.status,
                DATE_FORMAT(i.created_at, '%Y-%m-%d') as date
            FROM issues i
            JOIN repositories r ON i.repo_id = r.repo_id
            JOIN users u ON i.user_id = u.user_id
            ORDER BY i.created_at DESC
            LIMIT 50
        """)
        issues = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return jsonify({
            "total": total_issues,
            "open": open_issues,
            "closedToday": closed_today,
            "issues": issues
        })
    
    except Exception as e:
        print(f"ERROR in issues API: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
# ========================= RUN APP =========================
if __name__ == "__main__":
    app.run(debug=True)