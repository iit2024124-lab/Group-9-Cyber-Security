"""
app.py - DevTalk community forum, SECURED build (Stored XSS mitigated).

Run:  python3 app.py        ->  http://127.0.0.1:5002

This is the SAME application as the vulnerable build. The ONLY security change is
in templates/discussion.html: the comment is printed with a normal {{ c.comment }}
expression (no "|safe"), so Jinja2's HTML auto-escaping converts < > & ' " into
harmless entities. The database still stores the original text unchanged.

Request flow with the exact same payload:
  1. POST /post/<id>/comment   : the comment text is saved in SQLite unchanged.
  2. GET  /post/<id>           : the comment is read back from SQLite.
  3. templates/discussion.html : Jinja2 escapes it -> the browser shows it as TEXT.

MITIGATION: context-aware output encoding via Jinja2 auto-escaping (HTML text context).
No "|safe" filter and no markupsafe.Markup is used on any user-controlled data.

For local, educational use only. The server binds to 127.0.0.1 so it is not
reachable from other machines.
"""
import os

from flask import Flask, redirect, render_template, request, url_for

import database

# Text shown in the coloured banner at the top of every page (see base.html).
BUILD_LABEL = "SECURED BUILD"
BUILD_NOTE = "Stored XSS mitigated by output encoding - local use only - port 5002"
BUILD_CLASS = "secured"

HOST = "127.0.0.1"   # localhost only
PORT = 5002          # the vulnerable build uses 5001

MAX_USERNAME = 30
MAX_TITLE = 100
MAX_BODY = 2000
MAX_COMMENT = 1000


def create_app(db_path=None):
    """Application factory. Tests pass a temporary db_path so they never touch the real DB."""
    app = Flask(__name__)
    app.config["DATABASE"] = db_path or database.DEFAULT_DB_PATH
    database.init_db(app.config["DATABASE"])  # creates tables on first start

    @app.context_processor
    def inject_build_info():
        return {"build_label": BUILD_LABEL, "build_note": BUILD_NOTE, "build_class": BUILD_CLASS}

    def db():
        return database.get_connection(app.config["DATABASE"])

    def get_post(post_id):
        conn = db()
        post = conn.execute(
            "SELECT id, username, title, body, created_at FROM posts WHERE id = ?", (post_id,)
        ).fetchone()
        conn.close()
        return post

    def get_comments(post_id):
        conn = db()
        rows = conn.execute(
            "SELECT id, username, comment, created_at FROM comments "
            "WHERE post_id = ? ORDER BY id",
            (post_id,),
        ).fetchall()
        conn.close()
        return rows

    def render_discussion(post, error=None, status=200, form=None):
        return render_template(
            "discussion.html",
            post=post,
            comments=get_comments(post["id"]),
            error=error,
            form=form or {},
            posted=request.args.get("posted") == "1",
        ), status

    # ---------------------------------------------------------------- home page
    @app.route("/")
    def index():
        conn = db()
        posts = conn.execute(
            "SELECT p.id, p.username, p.title, p.body, p.created_at, "
            "       (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) AS comment_count "
            "FROM posts p ORDER BY p.id DESC"
        ).fetchall()
        conn.close()
        return render_template("index.html", posts=posts, error=None, form={})

    # ------------------------------------------------------------ create a post
    @app.route("/post/new", methods=["POST"])
    def new_post():
        # strip() only removes leading/trailing spaces. We do NOT remove or alter tags.
        username = request.form.get("username", "").strip()
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        form = {"username": username, "title": title, "body": body}

        if not username or not title or not body:
            return _index_with_error("Username, title and body are all required.", form)
        if len(username) > MAX_USERNAME or len(title) > MAX_TITLE or len(body) > MAX_BODY:
            return _index_with_error("One of the fields is too long.", form)

        conn = db()
        cursor = conn.execute(
            "INSERT INTO posts (username, title, body) VALUES (?, ?, ?)",
            (username, title, body),
        )
        conn.commit()
        post_id = cursor.lastrowid
        conn.close()
        return redirect(url_for("discussion", post_id=post_id))

    def _index_with_error(message, form):
        conn = db()
        posts = conn.execute(
            "SELECT p.id, p.username, p.title, p.body, p.created_at, "
            "       (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) AS comment_count "
            "FROM posts p ORDER BY p.id DESC"
        ).fetchall()
        conn.close()
        return render_template("index.html", posts=posts, error=message, form=form), 400

    # ------------------------------------------------------- discussion (read)
    @app.route("/post/<int:post_id>")
    def discussion(post_id):
        post = get_post(post_id)
        if post is None:
            return render_template("not_found.html"), 404
        return render_discussion(post)

    # ------------------------------------------------------ add a comment (write)
    @app.route("/post/<int:post_id>/comment", methods=["POST"])
    def add_comment(post_id):
        post = get_post(post_id)
        if post is None:
            return render_template("not_found.html"), 404

        # The comment is stored EXACTLY as typed (only surrounding spaces removed).
        # Escaping is deliberately NOT done here: encoding belongs to the OUTPUT step
        # (the template), because the right encoding depends on where data is printed.
        username = request.form.get("username", "").strip()
        comment = request.form.get("comment", "").strip()
        form = {"username": username, "comment": comment}

        if not username or not comment:
            return render_discussion(post, "Username and comment are both required.", 400, form)
        if len(username) > MAX_USERNAME or len(comment) > MAX_COMMENT:
            return render_discussion(post, "Username or comment is too long.", 400, form)

        conn = db()
        # Parameterised query (?) -> no SQL injection. The XSS problem is NOT here.
        conn.execute(
            "INSERT INTO comments (post_id, username, comment) VALUES (?, ?, ?)",
            (post_id, username, comment),
        )
        conn.commit()
        conn.close()
        # Post/Redirect/Get: the browser then does a normal GET, so the page that
        # runs the script is built from the DATABASE, not from this request.
        return redirect(url_for("discussion", post_id=post_id, posted=1) + "#comments")

    return app


if __name__ == "__main__":
    flask_app = create_app()
    print(f"SECURED build running at http://{HOST}:{PORT}  (database: {flask_app.config['DATABASE']})")
    # debug=False on purpose: the Werkzeug debugger is a separate risk we do not want here.
    flask_app.run(host=HOST, port=PORT, debug=False)
