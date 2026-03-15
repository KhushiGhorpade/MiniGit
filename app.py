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
            session["author_id"] = 0
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
            session["full_name"] = full_name
            session["username"] = username
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
@app.route("/search")
def search():
    if not session.get('logged_in'):
        return jsonify({"error": "Not logged in"}), 401
    
    query = request.args.get('q', '').strip()
    user_id = session.get('user_id')
    
    if not query or len(query) < 2:
        return jsonify({"results": []})
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # Search repositories - FIXED: Now shows ALL repos and includes owner username
    cursor.execute("""
        SELECT 
            'repository' as type,
            r.repo_name as name,
            r.description,
            r.repo_id as id,
            u.username,  -- This gets the actual owner username
            r.created_date as date,
            r.visibility
        FROM repositories r
        JOIN users u ON r.owner_id = u.user_id  -- Join with users table
        WHERE r.repo_name LIKE %s
        LIMIT 10
    """, (f'%{query}%',))
    
    repo_results = cursor.fetchall()
    
    # Search users
    cursor.execute("""
        SELECT 
            'user' as type,
            username as name,
            full_name as description,
            user_id as id,
            username,
            created_at as date
        FROM users
        WHERE username LIKE %s OR full_name LIKE %s
        LIMIT 5
    """, (f'%{query}%', f'%{query}%'))
    
    user_results = cursor.fetchall()
    
    # Search commits
    cursor.execute("""
        SELECT 
            'commit' as type,
            c.commit_message as name,
            r.repo_name as description,
            c.commit_id as id,
            u.username,
            c.commit_date as date
        FROM commits c
        JOIN repositories r ON c.repo_id = r.repo_id
        JOIN users u ON c.author_id = u.user_id
        WHERE c.commit_message LIKE %s
        LIMIT 10
    """, (f'%{query}%',))
    
    commit_results = cursor.fetchall()
    
    # Combine all results
    results = repo_results + user_results + commit_results
    
    cursor.close()
    db.close()
    
    return jsonify({"results": results})
    
@app.route("/dashboard")
def dashboard():
    if not session.get('logged_in'):
        print("Dashboard: Not logged in, redirecting to login")
        return redirect(url_for("login"))

    # Get user data from session
    username = session.get('full_name', session.get('username', 'User'))
    user_id = session.get('user_id')
    
    print(f"=== DASHBOARD DEBUG ===")
    print(f"Logged in as: {username}")
    print(f"User ID from session: {user_id}")
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # Check what users exist in database
    cursor.execute("SELECT user_id, username FROM users")
    users = cursor.fetchall()
    print("Users in database:")
    for u in users:
        print(f"  - {u['username']} (ID: {u['user_id']})")
    
    # Check repositories for this user
    cursor.execute("""
        SELECT * FROM repositories WHERE owner_id = %s
    """, (user_id,))
    
    repos = cursor.fetchall()
    print(f"Repositories found for user_id {user_id}: {len(repos)}")
    for r in repos:
        print(f"  - {r['repo_name']} (ID: {r['repo_id']})")
    
    # Get user stats
    cursor.execute("""
        SELECT 
            (SELECT COUNT(*) FROM repositories WHERE owner_id = %s) as total_repos,
            (SELECT COUNT(*) FROM commits WHERE author_id = %s) as total_commits,
            (SELECT COUNT(*) FROM issues WHERE created_by = %s AND status != 'closed') as open_issues
    """, (user_id, user_id, user_id))
    
    user_stats = cursor.fetchone()
    
    # Get user's latest repositories
    cursor.execute("""
        SELECT 
            repo_name,
            created_date
        FROM repositories 
        WHERE owner_id = %s
        ORDER BY created_date DESC
        LIMIT 5
    """, (user_id,))
    
    user_repos = cursor.fetchall()
    
    # Get latest commits from user's repositories
    cursor.execute("""
        SELECT 
            c.commit_message,
            r.repo_name,
            c.commit_date
        FROM commits c
        JOIN repositories r ON c.repo_id = r.repo_id
        WHERE r.owner_id = %s
        ORDER BY c.commit_date DESC
        LIMIT 5
    """, (user_id,))
    
    recent_commits = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    print(f"Final stats: repos={user_stats['total_repos']}, commits={user_stats['total_commits']}")
    
    return render_template("dashboard.html", 
                         active_page="dashboard",
                         username=username,
                         user_stats=user_stats,
                         user_repos=user_repos,
                         recent_commits=recent_commits)

@app.route("/repositories")
def repos():
    if not session.get('logged_in'):
        return redirect(url_for("login"))
    
    # Get current user's ID
    user_id = session.get('user_id')
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # Fetch repositories for the logged-in user
    cursor.execute("""
        SELECT 
            r.repo_id as id,
            r.repo_name as name,
            r.description,
            u.username as owner,
            r.created_date as created_at
        FROM repositories r
        JOIN users u ON r.owner_id = u.user_id
        WHERE r.owner_id = %s
        ORDER BY r.created_date DESC
    """, (user_id,))
    
    repositories = cursor.fetchall()
    cursor.close()
    db.close()
    
    return render_template("repositories.html", 
                         active_page="repositories",
                         repositories=repositories)

@app.route("/activity")
def activity():
    if not session.get('logged_in'):
        return redirect(url_for("login"))
    
    user_id = session.get('user_id')
    username = session.get('username')
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # Get user stats
    cursor.execute("""
        SELECT 
            (SELECT COUNT(*) FROM repositories WHERE owner_id = %s) as total_repos,
            (SELECT COUNT(*) FROM commits WHERE author_id = %s) as total_commits,
            (SELECT COUNT(*) FROM issues WHERE created_by = %s AND status != 'closed') as open_issues
    """, (user_id, user_id, user_id))
    
    stats = cursor.fetchone()
    
    # Get last activity time
    cursor.execute("""
        SELECT MAX(activity_time) as last_activity FROM (
            SELECT created_date as activity_time FROM repositories WHERE owner_id = %s
            UNION ALL
            SELECT commit_date as activity_time FROM commits WHERE author_id = %s
            UNION ALL
            SELECT created_date as activity_time FROM issues WHERE created_by = %s
        ) as all_activities
    """, (user_id, user_id, user_id))
    
    last_activity = cursor.fetchone()['last_activity']
    if last_activity:
        from datetime import datetime
        time_diff = datetime.now() - last_activity
        if time_diff.days > 0:
            last_activity_text = f"{time_diff.days} days ago"
        elif time_diff.seconds // 3600 > 0:
            last_activity_text = f"{time_diff.seconds // 3600} hours ago"
        else:
            last_activity_text = f"{time_diff.seconds // 60} minutes ago"
    else:
        last_activity_text = "No activity"
    
    # Get commit data for chart (last 7 days) - FIXED QUERY
    cursor.execute("""
        SELECT 
            DAYNAME(commit_date) as day,
            COUNT(*) as count,
            DATE(commit_date) as commit_day
        FROM commits
        WHERE author_id = %s
        AND commit_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY DATE(commit_date), DAYNAME(commit_date)
        ORDER BY MIN(commit_date)
    """, (user_id,))

    commits_by_day = cursor.fetchall()

    # Prepare chart data (fill missing days with 0)
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    chart_data = {day: 0 for day in days_order}
    for item in commits_by_day:
        chart_data[item['day']] = item['count']
    
    # Get repository activity for bar chart - FIXED QUERY
    cursor.execute("""
        SELECT 
            r.repo_name,
            COUNT(c.commit_id) as commit_count
        FROM repositories r
        LEFT JOIN commits c ON r.repo_id = c.repo_id
        WHERE r.owner_id = %s
        GROUP BY r.repo_id, r.repo_name
        ORDER BY commit_count DESC
        LIMIT 5
    """, (user_id,))
    
    repo_activity = cursor.fetchall()
    
    # Calculate max commits for bar chart percentages
    max_commits = max([r['commit_count'] for r in repo_activity]) if repo_activity else 1
    
    # Get timeline activity (mix of commits, issues, repos)
    cursor.execute("""
        (SELECT 
            'commit' as type,
            commit_message as description,
            commit_date as created_at,
            repo_id,
            commit_id as item_id
        FROM commits 
        WHERE author_id = %s)
        UNION ALL
        (SELECT 
            'issue' as type,
            issue_title as description,
            created_date as created_at,
            repo_id,
            issue_id as item_id
        FROM issues 
        WHERE created_by = %s)
        UNION ALL
        (SELECT 
            'repo' as type,
            repo_name as description,
            created_date as created_at,
            repo_id,
            repo_id as item_id
        FROM repositories 
        WHERE owner_id = %s)
        ORDER BY created_at DESC
        LIMIT 10
    """, (user_id, user_id, user_id))
    
    timeline = cursor.fetchall()
    
    # Get repo names for timeline items
    for item in timeline:
        cursor.execute("SELECT repo_name FROM repositories WHERE repo_id = %s", (item['repo_id'],))
        repo = cursor.fetchone()
        item['repo_name'] = repo['repo_name'] if repo else 'Unknown'
        
        # Format time
        from datetime import datetime
        time_diff = datetime.now() - item['created_at']
        if time_diff.days > 0:
            item['time_ago'] = f"{time_diff.days} days ago"
        elif time_diff.seconds // 3600 > 0:
            item['time_ago'] = f"{time_diff.seconds // 3600} hours ago"
        else:
            item['time_ago'] = f"{time_diff.seconds // 60} minutes ago"
    
    # Get repository cards data - FIXED QUERY
    cursor.execute("""
        SELECT 
            r.repo_name,
            r.repo_id,
            COUNT(DISTINCT c.commit_id) as commit_count,
            COUNT(DISTINCT i.issue_id) as issue_count
        FROM repositories r
        LEFT JOIN commits c ON r.repo_id = c.repo_id
        LEFT JOIN issues i ON r.repo_id = i.repo_id
        WHERE r.owner_id = %s
        GROUP BY r.repo_id, r.repo_name
        ORDER BY commit_count DESC
        LIMIT 3
    """, (user_id,))
    
    repo_cards = cursor.fetchall()
    
    # Get recent feed items
    cursor.execute("""
        (SELECT 
            'commit' as type,
            CONCAT('You committed to ', r.repo_name, ' — "', c.commit_message, '"') as description,
            c.commit_date as created_at
        FROM commits c
        JOIN repositories r ON c.repo_id = r.repo_id
        WHERE c.author_id = %s
        LIMIT 3)
        UNION ALL
        (SELECT 
            'repo' as type,
            CONCAT('You created repository ', r.repo_name) as description,
            r.created_date as created_at
        FROM repositories r
        WHERE r.owner_id = %s
        LIMIT 3)
        UNION ALL
        (SELECT 
            'issue' as type,
            CONCAT('You opened issue in ', r.repo_name, ' — "', i.issue_title, '"') as description,
            i.created_date as created_at
        FROM issues i
        JOIN repositories r ON i.repo_id = r.repo_id
        WHERE i.created_by = %s
        LIMIT 3)
        ORDER BY created_at DESC
        LIMIT 5
    """, (user_id, user_id, user_id))
    
    feed_items = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template(
        "activity.html",
        active_page="activity",
        stats=stats,
        last_activity_text=last_activity_text,
        chart_data=chart_data,
        repo_activity=repo_activity,
        max_commits=max_commits,
        timeline=timeline,
        repo_cards=repo_cards,
        feed_items=feed_items
    )

@app.route("/profile")
def profile():
    if not session.get('logged_in'):
        return redirect(url_for("login"))
    
    user_id = session.get('user_id')
    username = session.get('username')
    full_name = session.get('full_name', username)
    email = session.get('email', '')
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # Get user stats and join date
    cursor.execute("""
        SELECT 
            u.created_at as join_date,
            (SELECT COUNT(*) FROM repositories WHERE owner_id = u.user_id) as total_repos,
            (SELECT COUNT(*) FROM commits WHERE author_id = u.user_id) as total_commits,
            (SELECT COUNT(*) FROM issues WHERE created_by = u.user_id AND status != 'closed') as open_issues
        FROM users u
        WHERE u.user_id = %s
    """, (user_id,))
    
    user_data = cursor.fetchone()
    
    # Get repositories for the user
    cursor.execute("""
        SELECT 
            repo_name as name,
            description,
            visibility,
            created_date
        FROM repositories
        WHERE owner_id = %s
        ORDER BY created_date DESC
        LIMIT 3
    """, (user_id,))
    
    repositories = []
    for repo in cursor.fetchall():
        # Get commit count for this repo
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM commits 
            WHERE repo_id = (SELECT repo_id FROM repositories WHERE repo_name = %s AND owner_id = %s)
        """, (repo['name'], user_id))
        commit_count = cursor.fetchone()['count']
        
        # Get issue count for this repo
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM issues 
            WHERE repo_id = (SELECT repo_id FROM repositories WHERE repo_name = %s AND owner_id = %s)
        """, (repo['name'], user_id))
        issue_count = cursor.fetchone()['count']
        
        repositories.append({
            'name': repo['name'],
            'description': repo['description'] or 'No description provided',
            'public': repo['visibility'] == 'public',
            'stats': {
                'commits': commit_count,
                'issues': issue_count,
                'stars': 0
            },
            'updated': repo['created_date'].strftime('%b %d, %Y') if repo['created_date'] else 'Recently',
            'language': 'Python'  # You can make this dynamic later
        })
    
    # Get recent activities
    cursor.execute("""
        (SELECT 
            'commit' as type,
            CONCAT('Committed to ', r.repo_name) as title,
            c.commit_message as description,
            r.repo_name as repo,
            c.commit_date as created_at
        FROM commits c
        JOIN repositories r ON c.repo_id = r.repo_id
        WHERE c.author_id = %s
        LIMIT 3)
        UNION ALL
        (SELECT 
            'repo' as type,
            CONCAT('Created ', repo_name) as title,
            description,
            repo_name as repo,
            created_date as created_at
        FROM repositories
        WHERE owner_id = %s
        LIMIT 3)
        UNION ALL
        (SELECT 
            'issue' as type,
            CONCAT('Opened issue in ', r.repo_name) as title,
            i.issue_title as description,
            r.repo_name as repo,
            i.created_date as created_at
        FROM issues i
        JOIN repositories r ON i.repo_id = r.repo_id
        WHERE i.created_by = %s
        LIMIT 3)
        ORDER BY created_at DESC
        LIMIT 5
    """, (user_id, user_id, user_id))
    
    recent_activities = []
    for act in cursor.fetchall():
        from datetime import datetime
        time_diff = datetime.now() - act['created_at']
        if time_diff.days > 0:
            time_str = f"{time_diff.days} days ago"
        elif time_diff.seconds // 3600 > 0:
            time_str = f"{time_diff.seconds // 3600} hours ago"
        else:
            time_str = f"{time_diff.seconds // 60} minutes ago"
        
        recent_activities.append({
            'type': act['type'],
            'title': act['title'],
            'description': act['description'][:50] + '...' if len(act['description']) > 50 else act['description'],
            'repo': act['repo'],
            'time': time_str
        })
    
    cursor.close()
    db.close()
    
    # Format join date
    join_date = user_data['join_date'].strftime('%B %Y') if user_data and user_data['join_date'] else 'Recently'
    
    # Calculate stats
    total_commits = user_data['total_commits'] if user_data else 0
    total_repos = user_data['total_repos'] if user_data else 0
    total_contributions = total_commits + total_repos
    
    # Calculate efficiency (example: commits per repo ratio)
    efficiency = min(100, int((total_commits / (total_repos or 1)) * 20)) if total_repos > 0 else 0
    
    # Calculate active days (simplified - you can make this more sophisticated)
    active_days = min(30, total_commits) if total_commits > 0 else 0
    
    return render_template("profile.html",
                         active_page="profile",
                         full_name=full_name,
                         username=username,
                         join_date=join_date,
                         total_contributions=total_contributions,
                         total_repos=total_repos,
                         total_commits=total_commits,
                         efficiency=efficiency,
                         active_days=active_days,
                         repositories=repositories,
                         recent_activities=recent_activities)
@app.route("/my-repos")
def my_repos():
    if not session.get('logged_in'):
        return redirect(url_for("login"))
    return redirect(url_for("repos"))  # Redirect to the repositories page

@app.route("/create-repo", methods=["GET", "POST"])
def create_repo():
    # Check if user is logged in
    if not session.get('logged_in'):
        flash("Please login first", "error")
        return redirect(url_for("login"))
    
    if request.method == "POST":
        # Get form data
        repo_name = request.form.get("repo_name")
        description = request.form.get("description")
        visibility = request.form.get("visibility", "public")  # Default to public
        init_readme = request.form.get("init_readme") == "yes"
        
        # Validate required fields
        if not repo_name:
            flash("Repository name is required", "error")
            return redirect(url_for("create_repo"))
        
        # Get owner_id from session
        owner_id = session.get('user_id')
        
        if not owner_id:
            flash("User session error. Please login again.", "error")
            return redirect(url_for("login"))
        
        db = get_db_connection()
        cursor = db.cursor()
        
        try:
            # Insert into repositories table
            cursor.execute("""
                INSERT INTO repositories (repo_name, description, owner_id, visibility)
                VALUES (%s, %s, %s, %s)
            """, (repo_name, description, owner_id, visibility))
            
            db.commit()
            
            # Get the newly created repo_id
            repo_id = cursor.lastrowid
            
            # If initialize README is checked, create an initial commit
            if init_readme:
                # Insert initial commit
                cursor.execute("""
                    INSERT INTO commits (repo_id, commit_message, author_id, commit_type, files_changed)
                    VALUES (%s, %s, %s, %s, %s)
                """, (repo_id, "Initial commit", owner_id, "documentation", "README.md"))
                
                db.commit()
            
            flash(f"Repository '{repo_name}' created successfully!", "success")
            return redirect(url_for("repos"))
            
        except mysql.connector.Error as e:
            db.rollback()
            if "Duplicate" in str(e):
                flash("A repository with this name already exists", "error")
            else:
                flash(f"Error creating repository: {str(e)}", "error")
            return redirect(url_for("create_repo"))
            
        finally:
            cursor.close()
            db.close()
    
    # GET request - show the form
    return render_template("create_repo.html", active_page="create-repo")

@app.route("/create-issue", methods=["GET", "POST"])
def create_issue():
    if not session.get('logged_in'):
        flash("Please login first", "error")
        return redirect(url_for("login"))
    
    user_id = session.get('user_id')
    
    if request.method == "POST":
        # Get form data
        repo_id = request.form.get("repo_id")
        issue_title = request.form.get("issue_title")
        description = request.form.get("description")
        priority = request.form.get("priority", "medium")
        
        # Validate required fields
        if not repo_id:
            flash("Please select a repository", "error")
            return redirect(url_for("create_issue"))
        
        if not issue_title:
            flash("Issue title is required", "error")
            return redirect(url_for("create_issue"))
        
        db = get_db_connection()
        cursor = db.cursor()
        
        try:
            # Insert issue into database
            cursor.execute("""
                INSERT INTO issues 
                (repo_id, issue_title, description, created_by, priority, status) 
                VALUES (%s, %s, %s, %s, %s, 'open')
            """, (repo_id, issue_title, description, user_id, priority))
            
            db.commit()
            
            # Get repository name for success message
            cursor.execute("SELECT repo_name FROM repositories WHERE repo_id = %s", (repo_id,))
            repo_name = cursor.fetchone()[0]
            
            flash(f"Issue created successfully in {repo_name}!", "success")
            
        except Exception as e:
            db.rollback()
            flash(f"Error creating issue: {str(e)}", "error")
        finally:
            cursor.close()
            db.close()
        
        return redirect(url_for("activity"))
    
    # GET request - show the form with repositories
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # Fetch user's repositories for dropdown
    cursor.execute("""
        SELECT repo_id, repo_name 
        FROM repositories 
        WHERE owner_id = %s 
        ORDER BY repo_name
    """, (user_id,))
    
    repositories = cursor.fetchall()
    cursor.close()
    db.close()
    
    return render_template("create_issue.html", 
                         active_page="create-issue",
                         repositories=repositories)

@app.route("/create-commit", methods=["GET", "POST"])
def create_commit():
    if not session.get('logged_in'):
        flash("Please login first", "error")
        return redirect(url_for("login"))
    
    user_id = session.get('user_id')
    
    if request.method == "POST":
        # Get form data
        repo_id = request.form.get("repo_id")
        commit_message = request.form.get("commit_message")
        files_changed = request.form.get("files_changed")
        commit_type = request.form.get("commit_type", "other")
        
        # Validate required fields
        if not repo_id:
            flash("Please select a repository", "error")
            return redirect(url_for("create_commit"))
        
        if not commit_message:
            flash("Commit message is required", "error")
            return redirect(url_for("create_commit"))
        
        if not files_changed:
            flash("Please list the files you changed", "error")
            return redirect(url_for("create_commit"))
        
        db = get_db_connection()
        cursor = db.cursor()
        
        try:
            # Insert commit into database
            cursor.execute("""
                INSERT INTO commits 
                (repo_id, commit_message, author_id, commit_type, files_changed) 
                VALUES (%s, %s, %s, %s, %s)
            """, (repo_id, commit_message, user_id, commit_type, files_changed))
            
            db.commit()
            
            # Get repository name for success message
            cursor.execute("SELECT repo_name FROM repositories WHERE repo_id = %s", (repo_id,))
            repo_name = cursor.fetchone()[0]
            
            flash(f"Commit created successfully in {repo_name}!", "success")
            
        except Exception as e:
            db.rollback()
            flash(f"Error creating commit: {str(e)}", "error")
        finally:
            cursor.close()
            db.close()
        
        return redirect(url_for("activity"))
    
    # GET request - show the form with repositories
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # Fetch user's repositories for dropdown
    cursor.execute("""
        SELECT repo_id, repo_name 
        FROM repositories 
        WHERE owner_id = %s 
        ORDER BY repo_name
    """, (user_id,))
    
    repositories = cursor.fetchall()
    cursor.close()
    db.close()
    
    return render_template("create_commit.html", 
                         active_page="create-commit",
                         repositories=repositories)

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
    
    # Get all users
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
    
    # Get all feedback
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
@app.route("/api/admin/activity")
def api_admin_activity():
    # Only allow access if user is logged in AND is admin
    if not session.get('logged_in') or not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Get user activity stats (repos + commits + issues per user)
        cursor.execute("""
            SELECT 
                u.user_id,
                u.username,
                COUNT(DISTINCT r.repo_id) as total_repos,
                COUNT(DISTINCT c.commit_id) as total_commits,
                COUNT(DISTINCT i.issue_id) as total_issues,
                GREATEST(
                    COALESCE(MAX(r.created_date), '2000-01-01'),
                    COALESCE(MAX(c.commit_date), '2000-01-01'),
                    COALESCE(MAX(i.created_date), '2000-01-01')
                ) as last_activity_date
            FROM users u
            LEFT JOIN repositories r ON u.user_id = r.owner_id
            LEFT JOIN commits c ON u.user_id = c.author_id
            LEFT JOIN issues i ON u.user_id = i.created_by
            GROUP BY u.user_id, u.username
            HAVING total_repos > 0 OR total_commits > 0 OR total_issues > 0
            ORDER BY total_commits DESC
            LIMIT 20
        """)
        
        activities = cursor.fetchall()
        
        # Format last activity
        from datetime import datetime, timedelta
        for act in activities:
            if act['last_activity_date'] and act['last_activity_date'] != '2000-01-01':
                today = datetime.now()
                last_date = act['last_activity_date']
                
                if isinstance(last_date, datetime):
                    time_diff = today - last_date
                    
                    if time_diff.days == 0:
                        act['last_activity'] = 'Today'
                    elif time_diff.days == 1:
                        act['last_activity'] = 'Yesterday'
                    elif time_diff.days < 7:
                        act['last_activity'] = f"{time_diff.days} days ago"
                    elif time_diff.days < 30:
                        weeks = time_diff.days // 7
                        act['last_activity'] = f"{weeks} week{'s' if weeks > 1 else ''} ago"
                    else:
                        months = time_diff.days // 30
                        act['last_activity'] = f"{months} month{'s' if months > 1 else ''} ago"
                else:
                    act['last_activity'] = 'Recently'
            else:
                act['last_activity'] = 'No activity'
        
        # Get top contributors for chart (top 5)
        top_contributors = activities[:5]
        
        cursor.close()
        db.close()
        
        return jsonify({
            "activities": activities,
            "top_contributors": top_contributors
        })
    
    except Exception as e:
        print(f"ERROR in activity API: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
        
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
    
    # Get all users
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
        
        # Get all feedback
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
        
        # Get commit stats
        cursor.execute("SELECT COUNT(*) as total FROM commits")
        result = cursor.fetchone()
        total_commits = result['total'] if result else 0
        
        cursor.execute("""
            SELECT COUNT(*) as today 
            FROM commits 
            WHERE DATE(commit_date) = CURDATE()
        """)
        result = cursor.fetchone()
        today_commits = result['today'] if result else 0
        
        # Get most active user
        cursor.execute("""
            SELECT u.username, COUNT(c.commit_id) as count
            FROM commits c
            JOIN users u ON c.author_id = u.user_id
            GROUP BY u.user_id, u.username
            ORDER BY count DESC
            LIMIT 1
        """)
        most_active = cursor.fetchone()
        most_active_user = most_active['username'] if most_active else 'N/A'
        
        # Get recent commits
        cursor.execute("""
            SELECT 
                c.commit_id as id,
                r.repo_name,
                c.commit_message as message,
                u.username as committed_by,
                DATE_FORMAT(c.commit_date, '%Y-%m-%d %H:%i') as date
            FROM commits c
            JOIN repositories r ON c.repo_id = r.repo_id
            JOIN users u ON c.author_id = u.user_id
            ORDER BY c.commit_date DESC
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
    
@app.route("/api/admin/repositories")
def api_admin_repositories():
    if not session.get('logged_in') or not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("SELECT COUNT(*) as total FROM repositories")
        total = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as public_count FROM repositories WHERE visibility = 'public'")
        public_count = cursor.fetchone()['public_count']

        cursor.execute("""
            SELECT r.repo_name, COUNT(c.commit_id) as commit_count
            FROM repositories r
            LEFT JOIN commits c ON r.repo_id = c.repo_id
            GROUP BY r.repo_id
            ORDER BY commit_count DESC
            LIMIT 1
        """)
        most_active = cursor.fetchone()

        cursor.execute("""
            SELECT
                r.repo_id,
                r.repo_name,
                u.username AS owner,
                DATE_FORMAT(r.created_date, '%Y-%m-%d') AS created_date,
                COUNT(c.commit_id) AS total_commits
            FROM repositories r
            JOIN users u ON r.owner_id = u.user_id
            LEFT JOIN commits c ON r.repo_id = c.repo_id
            GROUP BY r.repo_id
            ORDER BY r.created_date DESC
        """)
        repos = cursor.fetchall()

        cursor.close()
        db.close()

        return jsonify({
            "total": total,
            "publicCount": public_count,
            "mostActive": most_active['repo_name'] if most_active else "N/A",
            "repos": repos
        })

    except Exception as e:
        print(f"ERROR in repositories API: {str(e)}")
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
        
        cursor.execute("""
            SELECT COUNT(*) as open 
            FROM issues 
            WHERE status IN ('open', 'in_progress')
        """)
        result = cursor.fetchone()
        open_issues = result['open'] if result else 0
        
        cursor.execute("""
            SELECT COUNT(*) as closed_today 
            FROM issues 
            WHERE status = 'closed'
            AND DATE(created_date) = CURDATE()
        """)
        result = cursor.fetchone()
        closed_today = result['closed_today'] if result else 0
        
        cursor.execute("""
            SELECT 
                i.issue_id as id,
                r.repo_name,
                i.issue_title,
                u.username as created_by,
                i.status,
                DATE_FORMAT(i.created_date, '%Y-%m-%d') as date
            FROM issues i
            JOIN repositories r ON i.repo_id = r.repo_id
            JOIN users u ON i.created_by = u.user_id
            ORDER BY i.created_date DESC
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