import os
import uuid
from werkzeug.utils import secure_filename
from flask import (
    Blueprint, current_app, flash, redirect, render_template,
    request, url_for, send_from_directory
)
from .database import get_db

fragments_bp = Blueprint("fragments", __name__)

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )

@fragments_bp.route("/")
def index():
    query = request.args.get("q", "").strip()
    db = get_db()
    if query:
        pattern = f"%{query}%"
        fragments = db.execute(
            """SELECT * FROM manuscript_fragments
               WHERE title LIKE ? OR fragment_identifier LIKE ?
                  OR page_number LIKE ?
               ORDER BY created_at DESC, id DESC""",
            (pattern, pattern, pattern)
        ).fetchall()
    else:
        fragments = db.execute(
            """SELECT * FROM manuscript_fragments
               ORDER BY created_at DESC, id DESC"""
        ).fetchall()
    return render_template("fragments/index.html",
                           fragments=fragments, query=query)

@fragments_bp.route("/fragments/new", methods=["GET", "POST"])
def new_fragment():
    if request.method == "GET":
        return render_template("fragments/new.html")

    title = request.form.get("title", "").strip()
    identifier = request.form.get("fragment_identifier", "").strip()
    description = request.form.get("description", "").strip()
    page_number = request.form.get("page_number", "").strip()
    manuscript_reference = request.form.get("manuscript_reference", "").strip()
    transcription = request.form.get("transcription", "").strip()
    image = request.files.get("image")

    if not title or not identifier:
        flash("Title and fragment identifier are required.", "error")
        return render_template("fragments/new.html"), 400

    if image is None or image.filename == "":
        flash("Please select a manuscript image.", "error")
        return render_template("fragments/new.html"), 400

    if not allowed_file(image.filename):
        flash("Unsupported image format. Use PNG, JPG, JPEG, TIF, TIFF, or WEBP.", "error")
        return render_template("fragments/new.html"), 400

    safe_name = secure_filename(image.filename)
    if not safe_name:
        flash("The selected filename is not valid.", "error")
        return render_template("fragments/new.html"), 400

    stored_filename = f"{uuid.uuid4().hex}_{safe_name}"
    upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_filename)
    image.save(upload_path)

    try:
        db = get_db()
        db.execute(
            """INSERT INTO manuscript_fragments
               (title, fragment_identifier, description, page_number,
                manuscript_reference, transcription, image_filename)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (title, identifier, description, page_number,
             manuscript_reference, transcription, stored_filename)
        )
        db.commit()
    except Exception:
        if os.path.exists(upload_path):
            os.remove(upload_path)
        raise

    flash("Manuscript fragment saved successfully.", "success")
    return redirect(url_for("fragments.index"))

@fragments_bp.route("/fragments/<int:fragment_id>")
def fragment_detail(fragment_id):
    fragment = get_db().execute(
        "SELECT * FROM manuscript_fragments WHERE id = ?",
        (fragment_id,)
    ).fetchone()
    if fragment is None:
        flash("Manuscript fragment was not found.", "error")
        return redirect(url_for("fragments.index"))
    return render_template("fragments/detail.html", fragment=fragment)

@fragments_bp.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
