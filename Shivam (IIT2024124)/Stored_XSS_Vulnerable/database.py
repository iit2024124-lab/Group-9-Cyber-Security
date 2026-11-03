"""
database.py - SQLite helper for the discussion forum demo (VULNERABLE build).

This file is IDENTICAL in the vulnerable and secured projects except for the
database file name. Nothing in here sanitises or escapes data: the database
stores exactly what the user typed. (The XSS fix lives in the template layer.)

Where is the database?
    forum_vulnerable.db  -> in the same folder as this file (created on first run)

Command line helpers:
    python3 database.py reset   # delete the database and recreate it with sample data
    python3 database.py show    # print all comments exactly as stored
"""
import os
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "forum_vulnerable.db")

# Schema. "comments" has the four required columns (id, username, comment,
# created_at) plus post_id, which links a comment to the post it belongs to.
SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username   TEXT NOT NULL,
    title      TEXT NOT NULL,
    body       TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS comments (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id    INTEGER NOT NULL REFERENCES posts(id),
    username   TEXT NOT NULL,
    comment    TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def get_connection(db_path=DEFAULT_DB_PATH):
    """Open a connection; rows can be read like dictionaries (row["comment"])."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def seed_sample_data(conn):
    """Insert harmless sample discussions and comments so the home page is not empty."""
    posts = [
        ("admin", "Welcome to DevTalk",
         "DevTalk is a community for developers to share tips, ask questions and "
         "show what they are building. Say hello in the comments!"),
        ("alice", "Best way to learn Flask in a weekend?",
         "I know basic Python. Which tutorials or small projects would you recommend for learning Flask quickly?"),
        ("rahul", "Python or JavaScript for a first backend project?",
         "I want to build a small API for a college project. Is Python (Flask/FastAPI) or Node.js easier to start with?"),
        ("meera", "A simple Git workflow for a team of three",
         "We keep breaking main. Do you use feature branches and pull requests, or something lighter for small teams?"),
        ("sanjay", "SQLite or PostgreSQL for a side project?",
         "My app will have maybe a hundred users. Is SQLite enough, or should I start with PostgreSQL from day one?"),
        ("priya", "Favourite VS Code extensions for web development",
         "Share the extensions you cannot work without: linters, formatters, themes, anything that saves time."),
        ("kabir", "How do you stay focused while debugging for hours?",
         "Some bugs eat a whole afternoon. What habits help you stay calm and systematic?"),
        ("ananya", "Open-source for beginners: where to start?",
         "I would like to make my first contribution. How do you find a beginner-friendly project and issue?"),
        ("zoya", "Dark mode in developer tools: yes or no?",
         "I switch everything to dark mode, but some people say it hurts readability in daylight. Your thoughts?"),
    ]
    for username, title, body in posts:
        conn.execute(
            "INSERT INTO posts (username, title, body) VALUES (?, ?, ?)",
            (username, title, body),
        )

    # (post_id, username, comment)
    comments = [
        (1, "bob", "Hello everyone, glad to be here! Looking forward to the Flask threads."),
        (1, "carol", "Great to have a place for dev chat. Welcome!"),
        (2, "bob", "Build a tiny to-do app first, then add a database. The official Flask tutorial is a good start."),
        (3, "carol", "Python reads closer to plain English, so it is gentler for a first backend."),
        (3, "alice", "Either works. Pick the one your team already knows."),
        (4, "bob", "Feature branches plus small pull requests worked well for us."),
        (5, "alice", "SQLite is fine for that size. You can migrate later if you need to."),
        (6, "rahul", "Prettier and a good linter changed my workflow."),
        (7, "meera", "Explain the problem out loud, even to a rubber duck. It works surprisingly often."),
        (8, "carol", "Look for the 'good first issue' label on GitHub."),
        (9, "bob", "Dark mode at night, light mode in the day. I use automatic switching."),
    ]
    for post_id, username, comment in comments:
        conn.execute(
            "INSERT INTO comments (post_id, username, comment) VALUES (?, ?, ?)",
            (post_id, username, comment),
        )


def init_db(db_path=DEFAULT_DB_PATH):
    """Create tables if they do not exist; add sample data only when the DB is empty."""
    conn = get_connection(db_path)
    conn.executescript(SCHEMA)
    if conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0] == 0:
        seed_sample_data(conn)
    conn.commit()
    conn.close()


def reset_db(db_path=DEFAULT_DB_PATH):
    """Delete the database file and rebuild it. Use between demonstrations."""
    for suffix in ("", "-journal", "-wal", "-shm"):
        path = db_path + suffix
        if os.path.exists(path):
            os.remove(path)
    init_db(db_path)


def show_comments(db_path=DEFAULT_DB_PATH):
    """Print the comments table exactly as stored (useful for the 'payload in DB' screenshot)."""
    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT id, post_id, username, comment, created_at FROM comments ORDER BY id"
    ).fetchall()
    conn.close()
    print("id | post_id | username | comment | created_at")
    print("-" * 70)
    for row in rows:
        print(f"{row['id']} | {row['post_id']} | {row['username']} | "
              f"{row['comment']} | {row['created_at']}")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "reset":
        reset_db()
        print(f"Database reset: {DEFAULT_DB_PATH}")
    elif command == "show":
        init_db()
        show_comments()
    else:
        print("Usage: python3 database.py [reset|show]")
