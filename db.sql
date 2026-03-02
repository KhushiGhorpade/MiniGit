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

CREATE TABLE repositories (
    repo_id INT AUTO_INCREMENT PRIMARY KEY,
    repo_name VARCHAR(150) NOT NULL,
    description TEXT,
    owner_id INT NOT NULL,
    visibility ENUM('public', 'private') DEFAULT 'public',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_repo_owner
        FOREIGN KEY (owner_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

CREATE TABLE commits (
    commit_id INT AUTO_INCREMENT PRIMARY KEY,
    repo_id INT NOT NULL,
    user_id INT NOT NULL,
    commit_message VARCHAR(255) NOT NULL,
    commit_hash VARCHAR(40),
    committed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_commit_repo
        FOREIGN KEY (repo_id)
        REFERENCES repositories(repo_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_commit_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

CREATE TABLE issues (
    issue_id INT AUTO_INCREMENT PRIMARY KEY,
    repo_id INT NOT NULL,
    user_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status ENUM('open', 'in_progress', 'closed') DEFAULT 'open',
    priority ENUM('low', 'medium', 'high') DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_issue_repo
        FOREIGN KEY (repo_id)
        REFERENCES repositories(repo_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_issue_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

CREATE TABLE repo_stars (
    star_id INT AUTO_INCREMENT PRIMARY KEY,
    repo_id INT NOT NULL,
    user_id INT NOT NULL,
    starred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_star_repo
        FOREIGN KEY (repo_id)
        REFERENCES repositories(repo_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_star_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    UNIQUE (repo_id, user_id)
);

CREATE TABLE repo_views (
    view_id INT AUTO_INCREMENT PRIMARY KEY,
    repo_id INT NOT NULL,
    user_id INT,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_view_repo
        FOREIGN KEY (repo_id)
        REFERENCES repositories(repo_id)
        ON DELETE CASCADE
);

CREATE TABLE activity_logs (
    activity_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    repo_id INT,
    activity_type ENUM(
        'repo_created',
        'commit',
        'issue_opened',
        'issue_closed',
        'starred'
    ) NOT NULL,
    reference_id INT,
    activity_message VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_activity_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_activity_repo
        FOREIGN KEY (repo_id)
        REFERENCES repositories(repo_id)
        ON DELETE SET NULL
);

CREATE TABLE feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    experience VARCHAR(20) NOT NULL,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);





