-- ============================================
-- MINIGIT DATABASE SETUP
-- ============================================
-- Password for all sample users: password123
-- ============================================

CREATE DATABASE IF NOT EXISTS repo_management;
USE repo_management;

-- ============================================
-- DROP TABLES (reverse dependency order)
-- ============================================
DROP TABLE IF EXISTS activity_logs;
DROP TABLE IF EXISTS repo_views;
DROP TABLE IF EXISTS repo_stars;
DROP TABLE IF EXISTS issues;
DROP TABLE IF EXISTS commits;
DROP TABLE IF EXISTS repositories;
DROP TABLE IF EXISTS feedback;
DROP TABLE IF EXISTS users;

-- ============================================
-- CREATE TABLES
-- ============================================

-- 1. USERS
CREATE TABLE users (
    user_id    INT AUTO_INCREMENT PRIMARY KEY,
    full_name  VARCHAR(100) NOT NULL,
    username   VARCHAR(50)  NOT NULL UNIQUE,
    email      VARCHAR(100) NOT NULL UNIQUE,
    password   VARCHAR(255) NOT NULL,
    role       ENUM('user', 'admin') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);

-- 2. FEEDBACK
CREATE TABLE feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    category    VARCHAR(50),
    experience  VARCHAR(20),
    message     TEXT NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. REPOSITORIES
CREATE TABLE repositories (
    repo_id      INT AUTO_INCREMENT PRIMARY KEY,
    repo_name    VARCHAR(100) NOT NULL,
    description  TEXT,
    owner_id     INT NOT NULL,
    visibility   ENUM('public', 'private') DEFAULT 'public',
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 4. COMMITS
CREATE TABLE commits (
    commit_id      INT AUTO_INCREMENT PRIMARY KEY,
    repo_id        INT NOT NULL,
    commit_message VARCHAR(500) NOT NULL,
    author_id      INT NOT NULL,
    commit_type    ENUM('feature', 'bugfix', 'documentation', 'other') DEFAULT 'other',
    files_changed  TEXT,
    commit_date    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repo_id)   REFERENCES repositories(repo_id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES users(user_id)        ON DELETE CASCADE
);

-- 5. ISSUES
CREATE TABLE issues (
    issue_id    INT AUTO_INCREMENT PRIMARY KEY,
    repo_id     INT NOT NULL,
    issue_title VARCHAR(200) NOT NULL,
    description TEXT,
    created_by  INT NOT NULL,
    status      ENUM('open', 'in_progress', 'closed') DEFAULT 'open',
    priority    ENUM('low', 'medium', 'high')         DEFAULT 'medium',
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repo_id)    REFERENCES repositories(repo_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(user_id)        ON DELETE CASCADE
);

-- 6. REPO_STARS
CREATE TABLE repo_stars (
    star_id    INT AUTO_INCREMENT PRIMARY KEY,
    repo_id    INT NOT NULL,
    user_id    INT NOT NULL,
    starred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_star (repo_id, user_id),
    FOREIGN KEY (repo_id) REFERENCES repositories(repo_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)        ON DELETE CASCADE
);

-- 7. REPO_VIEWS
CREATE TABLE repo_views (
    view_id   INT AUTO_INCREMENT PRIMARY KEY,
    repo_id   INT NOT NULL,
    user_id   INT NOT NULL,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repo_id) REFERENCES repositories(repo_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)        ON DELETE CASCADE
);

-- 8. ACTIVITY_LOGS
CREATE TABLE activity_logs (
    activity_id      INT AUTO_INCREMENT PRIMARY KEY,
    user_id          INT NOT NULL,
    repo_id          INT NULL,
    activity_type    ENUM('repo_created', 'commit', 'issue_opened', 'issue_closed', 'starred') NOT NULL,
    activity_message VARCHAR(255),
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)        ON DELETE CASCADE,
    FOREIGN KEY (repo_id) REFERENCES repositories(repo_id) ON DELETE SET NULL
);

-- ============================================
-- SAMPLE DATA
-- ============================================

-- All sample user passwords are: password123
INSERT INTO users (full_name, username, email, password, role) VALUES
('Admin User',    'admin',      'admin@minigit.com',  'scrypt:32768:8:1$ZZ1bQAkgCAy9nLaS$a8ffbeab5ba8b77b631d6ec0aec0af6f79468bb28d45e3098877509b1b74a595e5bffefa3e85ac3d932a7a608f89032506b9a6b08a221a9b508866a529c7fd7c', 'admin'),
('John Developer','johndev',    'john@dev.com',       'scrypt:32768:8:1$ZZ1bQAkgCAy9nLaS$a8ffbeab5ba8b77b631d6ec0aec0af6f79468bb28d45e3098877509b1b74a595e5bffefa3e85ac3d932a7a608f89032506b9a6b08a221a9b508866a529c7fd7c', 'user'),
('Jane Designer', 'janedesign', 'jane@design.com',    'scrypt:32768:8:1$ZZ1bQAkgCAy9nLaS$a8ffbeab5ba8b77b631d6ec0aec0af6f79468bb28d45e3098877509b1b74a595e5bffefa3e85ac3d932a7a608f89032506b9a6b08a221a9b508866a529c7fd7c', 'user'),
('Bob Tester',    'bobtest',    'bob@test.com',       'scrypt:32768:8:1$ZZ1bQAkgCAy9nLaS$a8ffbeab5ba8b77b631d6ec0aec0af6f79468bb28d45e3098877509b1b74a595e5bffefa3e85ac3d932a7a608f89032506b9a6b08a221a9b508866a529c7fd7c', 'user'),
('Alice Manager', 'alicemgr',   'alice@mgr.com',      'scrypt:32768:8:1$ZZ1bQAkgCAy9nLaS$a8ffbeab5ba8b77b631d6ec0aec0af6f79468bb28d45e3098877509b1b74a595e5bffefa3e85ac3d932a7a608f89032506b9a6b08a221a9b508866a529c7fd7c', 'user');

INSERT INTO feedback (name, category, experience, message) VALUES
('John Developer', 'Bug Report',      'Poor',      'Login page not working on mobile devices'),
('Jane Designer',  'Feature Request', 'Good',      'Please add dark mode theme'),
('Bob Tester',     'UI/UX',           'Average',   'Dashboard layout could be improved'),
('Alice Manager',  'Performance',     'Excellent', 'Very fast loading times, great job!'),
('Charlie User',   'Documentation',   'Good',      'API documentation is comprehensive'),
('David Newbie',   'Bug Report',      'Poor',      'Search functionality returns no results'),
('Eva Pro',        'Feature Request', 'Excellent', 'Love the new commit tracking feature');

INSERT INTO repositories (repo_name, description, owner_id, visibility) VALUES
('MiniGit-Core',  'Main version control system core',    1, 'public'),
('UI-Components', 'Reusable React components library',   2, 'public'),
('Mobile-App',    'Cross-platform mobile application',   3, 'public'),
('API-Service',   'Backend REST API service',            1, 'private'),
('Docs-Website',  'Documentation website',               4, 'public'),
('Testing-Suite', 'Automated testing framework',         5, 'private');

INSERT INTO commits (repo_id, commit_message, author_id, commit_type, files_changed) VALUES
(1, 'Initial project setup',         1, 'feature',       'app.py, requirements.txt, README.md'),
(1, 'Fixed login authentication bug',1, 'bugfix',        'app.py, login.html'),
(2, 'Added navbar component',        2, 'feature',       'Navbar.jsx, Navbar.css'),
(2, 'Fixed responsive design issues',2, 'bugfix',        'Navbar.css, Layout.css'),
(3, 'Implemented user profile page', 3, 'feature',       'Profile.js, Profile.css, api.js'),
(4, 'Updated API endpoints',         1, 'feature',       'routes/api.py, models.py'),
(5, 'Added getting started guide',   4, 'documentation', 'docs/getting-started.md'),
(6, 'Fixed test cases for login',    5, 'bugfix',        'tests/login.test.js');

INSERT INTO issues (repo_id, issue_title, description, created_by, status, priority) VALUES
(1, 'Login page not loading',     'Login page shows blank screen on Chrome',  2, 'open',        'high'),
(1, 'Add password reset feature', 'Users cannot reset their passwords',       3, 'in_progress', 'medium'),
(2, 'Mobile menu not working',    'Hamburger menu does not open on mobile',   4, 'open',        'medium'),
(3, 'Profile image upload broken','Cannot upload images larger than 1MB',    5, 'closed',      'low'),
(4, 'API rate limiting needed',   'Add rate limiting to prevent abuse',       1, 'in_progress', 'high'),
(5, 'Update documentation links', 'Some links in docs are broken',           2, 'open',        'low');

INSERT INTO repo_stars (repo_id, user_id) VALUES
(1, 2), (1, 3), (1, 4), (1, 5),
(2, 1), (2, 3), (2, 5),
(3, 1), (3, 2),
(4, 2),
(5, 1), (5, 3), (5, 4), (5, 5);

INSERT INTO repo_views (repo_id, user_id) VALUES
(1, 2), (1, 3), (1, 4), (1, 5),
(2, 1), (2, 3), (2, 4), (2, 5),
(3, 1), (3, 2), (3, 4),
(4, 2), (4, 3),
(5, 1), (5, 2), (5, 3), (5, 4), (5, 5);

INSERT INTO activity_logs (user_id, repo_id, activity_type, activity_message) VALUES
(2, 1, 'starred',      'johndev starred MiniGit-Core'),
(3, 1, 'starred',      'janedesign starred MiniGit-Core'),
(2, 2, 'repo_created', 'johndev created UI-Components'),
(3, 3, 'repo_created', 'janedesign created Mobile-App'),
(1, 4, 'repo_created', 'admin created API-Service'),
(1, 1, 'commit',       'admin committed to MiniGit-Core: Initial project setup'),
(1, 1, 'commit',       'admin committed to MiniGit-Core: Fixed login authentication bug'),
(2, 2, 'commit',       'johndev committed to UI-Components: Added navbar component'),
(4, 1, 'issue_opened', 'bobtest opened issue on MiniGit-Core: Login page not loading'),
(3, 1, 'issue_opened', 'janedesign opened issue on MiniGit-Core: Add password reset feature'),
(4, 3, 'issue_closed', 'bobtest closed issue on Mobile-App: Profile image upload broken');

-- ============================================
-- VERIFICATION
-- ============================================
SELECT '=== RECORD COUNTS ===' as '';
SELECT
    (SELECT COUNT(*) FROM users)         as users,
    (SELECT COUNT(*) FROM feedback)      as feedback,
    (SELECT COUNT(*) FROM repositories)  as repositories,
    (SELECT COUNT(*) FROM commits)       as commits,
    (SELECT COUNT(*) FROM issues)        as issues,
    (SELECT COUNT(*) FROM repo_stars)    as stars,
    (SELECT COUNT(*) FROM repo_views)    as views,
    (SELECT COUNT(*) FROM activity_logs) as activity_logs;

SELECT '✅ Setup complete. Sample user password: password123' as '';