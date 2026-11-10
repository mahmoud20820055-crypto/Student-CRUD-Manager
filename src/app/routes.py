"""HTTP routes: JSON REST API under /api and the web UI at /."""
import sqlite3

from flask import Blueprint, jsonify, render_template, request

from .db import get_db
from .validation import validate_student

api_bp = Blueprint("api", __name__, url_prefix="/api")
web_bp = Blueprint("web", __name__)


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def _conflict(exc: sqlite3.IntegrityError):
    msg = str(exc)
    field = "email" if "email" in msg else "student_code" if "student_code" in msg else "record"
    return jsonify(error="conflict", details={field: "already exists"}), 409


def _get_or_404(student_id: int):
    row = get_db().execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    return row


@web_bp.get("/")
def index():
    return render_template("index.html")


@web_bp.get("/health")
def health():
    try:
        get_db().execute("SELECT 1").fetchone()
    except sqlite3.Error as exc:  # pragma: no cover - only on broken volume
        return jsonify(status="error", database=str(exc)), 503
    return jsonify(status="ok", database="ok")


@api_bp.get("/students")
def list_students():
    q = request.args.get("q", "").strip()
    sql = "SELECT * FROM students"
    params: tuple = ()
    if q:
        like = f"%{q}%"
        sql += (" WHERE first_name LIKE ? OR last_name LIKE ? OR email LIKE ?"
                " OR student_code LIKE ? OR major LIKE ?")
        params = (like,) * 5
    sql += " ORDER BY id DESC"
    rows = get_db().execute(sql, params).fetchall()
    return jsonify([_row_to_dict(r) for r in rows])


@api_bp.get("/students/<int:student_id>")
def get_student(student_id: int):
    row = _get_or_404(student_id)
    if row is None:
        return jsonify(error="not found"), 404
    return jsonify(_row_to_dict(row))


@api_bp.post("/students")
def create_student():
    data, errors = validate_student(request.get_json(silent=True))
    if errors:
        return jsonify(error="validation failed", details=errors), 400
    conn = get_db()
    cols = ", ".join(data)
    marks = ", ".join("?" for _ in data)
    try:
        cur = conn.execute(f"INSERT INTO students ({cols}) VALUES ({marks})", tuple(data.values()))
        conn.commit()
    except sqlite3.IntegrityError as exc:
        return _conflict(exc)
    return jsonify(_row_to_dict(_get_or_404(cur.lastrowid))), 201


@api_bp.put("/students/<int:student_id>")
@api_bp.patch("/students/<int:student_id>")
def update_student(student_id: int):
    if _get_or_404(student_id) is None:
        return jsonify(error="not found"), 404
    data, errors = validate_student(request.get_json(silent=True), partial=request.method == "PATCH")
    if errors:
        return jsonify(error="validation failed", details=errors), 400
    conn = get_db()
    assignments = ", ".join(f"{col} = ?" for col in data)
    try:
        conn.execute(
            f"UPDATE students SET {assignments}, updated_at = datetime('now') WHERE id = ?",
            (*data.values(), student_id),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        return _conflict(exc)
    return jsonify(_row_to_dict(_get_or_404(student_id)))


@api_bp.delete("/students/<int:student_id>")
def delete_student(student_id: int):
    conn = get_db()
    cur = conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    if cur.rowcount == 0:
        return jsonify(error="not found"), 404
    return "", 204


@api_bp.get("/stats")
def stats():
    row = get_db().execute(
        "SELECT COUNT(*) AS total, ROUND(AVG(gpa), 2) AS average_gpa,"
        " COUNT(DISTINCT major) AS majors FROM students"
    ).fetchone()
    return jsonify(_row_to_dict(row))
