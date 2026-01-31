-- ============================================
-- MINIGIT DATABASE SETUP - COMPLETE SQL
-- Save as: setup_minigit.sql
-- ============================================

-- 1. USE YOUR DATABASE
USE repo_management;

-- 2. DROP TABLES IF THEY EXIST (Optional - for fresh start)
DROP TABLE IF EXISTS activity_logs;
DROP TABLE IF EXISTS repo_views;
DROP TABLE IF EXISTS repo_stars;
DROP TABLE IF EXISTS issues;
DROP TABLE IF EXISTS commits;
DROP TABLE IF EXISTS repositories;
DROP TABLE IF EXISTS feedback;
DROP TABLE IF EXISTS users;

-- ============================================
-- CREATE TABLES IN PROPER ORDER
-- ============================================

-- 3. USERS TABLE (Base table - created first)
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);

-- 4. FEEDBACK TABLE
CREATE TABLE feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    experience VARCHAR(20),
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. REPOSITORIES TABLE (Depends on users)
CREATE TABLE repositories (
    repo_id INT AUTO_INCREMENT PRIMARY KEY,
    repo_name VARCHAR(100) NOT NULL,
    description TEXT,
    owner_id INT NOT NULL,
    visibility ENUM('public', 'private') DEFAULT 'public',
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 6. COMMITS TABLE (Depends on users and repositories)
CREATE TABLE commits (
    commit_id INT AUTO_INCREMENT PRIMARY KEY,
    repo_id INT NOT NULL,
    commit_message VARCHAR(500) NOT NULL,
    author_id INT NOT NULL,
    commit_type ENUM('feature', 'bugfix', 'documentation', 'other') DEFAULT 'other',
    files_changed TEXT,
    commit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repo_id) REFERENCES repositories(repo_id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 7. ISSUES TABLE (Depends on users and repositories)
CREATE TABLE issues (
    issue_id INT AUTO_INCREMENT PRIMARY KEY,
    repo_id INT NOT NULL,
    issue_title VARCHAR(200) NOT NULL,
    description TEXT,
    created_by INT NOT NULL,
    status ENUM('open', 'closed', 'in_progress') DEFAULT 'open',
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repo_id) REFERENCES repositories(repo_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 8. REPO_STARS TABLE (Depends on users and repositories)
CREATE TABLE repo_stars (
    star_id INT AUTO_INCREMENT PRIMARY KEY,
    repo_id INT NOT NULL,
    user_id INT NOT NULL,
    starred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repo_id) REFERENCES repositories(repo_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY unique_star (repo_id, user_id)
);

-- 9. REPO_VIEWS TABLE (Depends on users and repositories)
CREATE TABLE repo_views (
    view_id INT AUTO_INCREMENT PRIMARY KEY,
    repo_id INT NOT NULL,
    user_id INT NOT NULL,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repo_id) REFERENCES repositories(repo_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 10. ACTIVITY_LOGS TABLE (Depends on users)
CREATE TABLE activity_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    activity_type VARCHAR(50),
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ============================================
-- INSERT SAMPLE DATA FOR TESTING
-- ============================================

-- 11. INSERT SAMPLE USERS (Password: 'password123' hashed)
INSERT INTO users (full_name, username, email, password, role) VALUES
('Admin User', 'admin', 'admin@minigit.com', '$2b$12$M4I7vWYdJNv4kE7Q8Z9pOeKJmN1bVcXzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOo', 'admin'),
('John Developer', 'johndev', 'john@dev.com', '$2b$12$M4I7vWYdJNv4kE7Q8Z9pOeKJmN1bVcXzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOo', 'user'),
('Jane Designer', 'janedesign', 'jane@design.com', '$2b$12$M4I7vWYdJNv4kE7Q8Z9pOeKJmN1bVcXzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOo', 'user'),
('Bob Tester', 'bobtest', 'bob@test.com', '$2b$12$M4I7vWYdJNv4kE7Q8Z9pOeKJmN1bVcXzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOo', 'user'),
('Alice Manager', 'alicemgr', 'alice@mgr.com', '$2b$12$M4I7vWYdJNv4kE7Q8Z9pOeKJmN1bVcXzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOo', 'user');

-- 12. INSERT SAMPLE FEEDBACK
INSERT INTO feedback (name, category, experience, message) VALUES
('John Developer', 'Bug Report', 'Poor', 'Login page not working on mobile devices'),
('Jane Designer', 'Feature Request', 'Good', 'Please add dark mode theme'),
('Bob Tester', 'UI/UX', 'Average', 'Dashboard layout could be improved'),
('Alice Manager', 'Performance', 'Excellent', 'Very fast loading times, great job!'),
('Charlie User', 'Documentation', 'Good', 'API documentation is comprehensive'),
('David Newbie', 'Bug Report', 'Poor', 'Search functionality returns no results'),
('Eva Pro', 'Feature Request', 'Excellent', 'Love the new commit tracking feature');

-- 13. INSERT SAMPLE REPOSITORIES
INSERT INTO repositories (repo_name, description, owner_id, visibility) VALUES
('MiniGit-Core', 'Main version control system core', 1, 'public'),
('UI-Components', 'Reusable React components library', 2, 'public'),
('Mobile-App', 'Cross-platform mobile application', 3, 'public'),
('API-Service', 'Backend REST API service', 1, 'private'),
('Docs-Website', 'Documentation website', 4, 'public'),
('Testing-Suite', 'Automated testing framework', 5, 'private');

-- 14. INSERT SAMPLE COMMITS
INSERT INTO commits (repo_id, commit_message, author_id, commit_type, files_changed) VALUES
(1, 'Initial project setup', 1, 'feature', 'app.py, requirements.txt, README.md'),
(1, 'Fixed login authentication bug', 1, 'bugfix', 'auth.py, login.html'),
(2, 'Added navbar component', 2, 'feature', 'Navbar.jsx, Navbar.css'),
(2, 'Fixed responsive design issues', 2, 'bugfix', 'Navbar.css, Layout.css'),
(3, 'Implemented user profile page', 3, 'feature', 'Profile.js, Profile.css, api.js'),
(4, 'Updated API endpoints', 1, 'feature', 'routes/api.py, models.py'),
(5, 'Added getting started guide', 4, 'documentation', 'docs/getting-started.md'),
(6, 'Fixed test cases for login', 5, 'bugfix', 'tests/login.test.js');

-- 15. INSERT SAMPLE ISSUES
INSERT INTO issues (repo_id, issue_title, description, created_by, status) VALUES
(1, 'Login page not loading', 'Login page shows blank screen on Chrome browser', 2, 'open'),
(1, 'Add password reset feature', 'Users cannot reset their passwords', 3, 'in_progress'),
(2, 'Mobile menu not working', 'Hamburger menu does not open on mobile', 4, 'open'),
(3, 'Profile image upload broken', 'Cannot upload profile images larger than 1MB', 5, 'closed'),
(4, 'API rate limiting needed', 'Add rate limiting to prevent abuse', 1, 'in_progress'),
(5, 'Update documentation links', 'Some links in docs are broken', 2, 'open');

-- 16. INSERT SAMPLE REPO STARS
INSERT INTO repo_stars (repo_id, user_id) VALUES
(1, 2), (1, 3), (1, 4), (1, 5),  -- MiniGit-Core starred by 4 users
(2, 1), (2, 3), (2, 5),           -- UI-Components starred by 3 users
(3, 1), (3, 2),                    -- Mobile-App starred by 2 users
(4, 2),                            -- API-Service starred by 1 user
(5, 1), (5, 3), (5, 4), (5, 5);   -- Docs-Website starred by 4 users

-- 17. INSERT SAMPLE REPO VIEWS
INSERT INTO repo_views (repo_id, user_id) VALUES
(1, 2), (1, 3), (1, 4), (1, 5),
(2, 1), (2, 3), (2, 4), (2, 5),
(3, 1), (3, 2), (3, 4),
(4, 2), (4, 3),
(5, 1), (5, 2), (5, 3), (5, 4), (5, 5);

-- 18. INSERT SAMPLE ACTIVITY LOGS
INSERT INTO activity_logs (user_id, activity_type, description) VALUES
(1, 'login', 'Admin logged in'),
(2, 'create_repo', 'Created new repository: UI-Components'),
(3, 'commit', 'Committed to Mobile-App: Implemented user profile'),
(4, 'create_issue', 'Opened issue: Mobile menu not working'),
(5, 'star_repo', 'Starred repository: MiniGit-Core'),
(1, 'logout', 'Admin logged out'),
(2, 'login', 'User logged in'),
(3, 'view_repo', 'Viewed repository: API-Service');

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- 19. SHOW ALL TABLES CREATED
SELECT '=== ALL TABLES CREATED ===' as '';
SHOW TABLES;

-- 20. COUNT RECORDS IN EACH TABLE
SELECT '=== RECORD COUNTS ===' as '';
SELECT 
    (SELECT COUNT(*) FROM users) as users_count,
    (SELECT COUNT(*) FROM feedback) as feedback_count,
    (SELECT COUNT(*) FROM repositories) as repos_count,
    (SELECT COUNT(*) FROM commits) as commits_count,
    (SELECT COUNT(*) FROM issues) as issues_count,
    (SELECT COUNT(*) FROM repo_stars) as stars_count,
    (SELECT COUNT(*) FROM repo_views) as views_count,
    (SELECT COUNT(*) FROM activity_logs) as activity_count;

-- 21. SHOW SAMPLE DATA FROM EACH TABLE
SELECT '=== SAMPLE USERS ===' as '';
SELECT user_id, username, email, role, created_at FROM users LIMIT 5;

SELECT '=== SAMPLE FEEDBACK ===' as '';
SELECT feedback_id, name, category, experience, DATE(created_at) as date FROM feedback LIMIT 5;

SELECT '=== SAMPLE REPOSITORIES ===' as '';
SELECT repo_id, repo_name, owner_id, visibility, created_date FROM repositories LIMIT 5;

SELECT '=== SAMPLE COMMITS ===' as '';
SELECT commit_id, repo_id, LEFT(commit_message, 30) as message, author_id, commit_date FROM commits LIMIT 5;

SELECT '=== SAMPLE ISSUES ===' as '';
SELECT issue_id, repo_id, issue_title, status, created_date FROM issues LIMIT 5;

-- 22. CHECK FOREIGN KEY RELATIONSHIPS
SELECT '=== FOREIGN KEY CHECKS ===' as '';
SELECT 
    'users -> repositories' as relationship,
    COUNT(DISTINCT r.owner_id) as users_with_repos,
    COUNT(DISTINCT u.user_id) as total_users,
    CONCAT(ROUND(COUNT(DISTINCT r.owner_id) * 100.0 / COUNT(DISTINCT u.user_id), 1), '%') as percentage
FROM users u
LEFT JOIN repositories r ON u.user_id = r.owner_id
UNION
SELECT 
    'users -> commits' as relationship,
    COUNT(DISTINCT c.author_id) as users_with_commits,
    COUNT(DISTINCT u.user_id) as total_users,
    CONCAT(ROUND(COUNT(DISTINCT c.author_id) * 100.0 / COUNT(DISTINCT u.user_id), 1), '%') as percentage
FROM users u
LEFT JOIN commits c ON u.user_id = c.author_id;

-- ============================================
-- SUCCESS MESSAGE
-- ============================================
SELECT '✅ DATABASE SETUP COMPLETE!' as '';
SELECT '✅ 8 Tables created successfully' as '';
SELECT '✅ Sample data inserted' as '';
SELECT '✅ Ready to run MiniGit application' as '';