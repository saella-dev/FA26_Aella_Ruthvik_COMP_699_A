
import os
import uuid

from werkzeug.utils import secure_filename
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    send_from_directory,
    abort,
)

from .database import get_db
from .matching import similarity


fragments_bp = Blueprint("fragments", __name__)


# ---------------------------------------------------------
# File upload helpers
# ---------------------------------------------------------

def allowed_file(filename):
    """Check whether the uploaded file has an allowed extension."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


def save_uploaded_image(image):
    """Save an uploaded image and return its generated filename."""
    safe_filename = secure_filename(image.filename)

    if not safe_filename:
        raise ValueError("Invalid image filename.")

    filename = f"{uuid.uuid4().hex}_{safe_filename}"
    upload_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        filename
    )

    image.save(upload_path)

    return filename


# ---------------------------------------------------------
# Fragment database helpers
# ---------------------------------------------------------

def _fragment_or_404(fragment_id):
    """Retrieve a fragment or return HTTP 404."""
    row = get_db().execute(
        "SELECT * FROM manuscript_fragments WHERE id = ?",
        (fragment_id,)
    ).fetchone()

    if row is None:
        abort(404)

    return row


def _form_values():
    """Read and clean fragment form values."""
    return {
        key: request.form.get(
            key,
            "orphan" if key == "fragment_type" else ""
        ).strip()
        for key in [
            "title",
            "fragment_identifier",
            "description",
            "page_number",
            "manuscript_reference",
            "transcription",
            "fragment_type",
            "collection_name",
        ]
    }


def _validate(form, image=None, required_image=False):
    """Validate fragment information and uploaded image."""

    if not form["title"] or not form["fragment_identifier"]:
        return "Title and fragment identifier are required."

    if form["fragment_type"] not in (
        "complete",
        "paired",
        "orphan"
    ):
        return "Select a valid fragment category."

    if required_image and (
        image is None or not image.filename
    ):
        return "Please select a manuscript image."

    if image and image.filename:
        if not allowed_file(image.filename):
            return (
                "Unsupported image format. Use PNG, JPG, JPEG, "
                "TIF, TIFF, or WEBP."
            )

    return None


# ---------------------------------------------------------
# Dashboard and search
# ---------------------------------------------------------

@fragments_bp.route("/")
def index():
    """Display fragments with search and category filtering."""

    query = request.args.get("q", "").strip()
    kind = request.args.get("type", "").strip()

    db = get_db()

    sql = """
        SELECT *
        FROM manuscript_fragments
        WHERE 1 = 1
    """

    args = []

    if query:
        pattern = f"%{query}%"

        sql += """
            AND (
                title LIKE ?
                OR fragment_identifier LIKE ?
                OR page_number LIKE ?
                OR collection_name LIKE ?
            )
        """

        args.extend([
            pattern,
            pattern,
            pattern,
            pattern,
        ])

    if kind in ("complete", "paired", "orphan"):
        sql += " AND fragment_type = ?"
        args.append(kind)

    rows = db.execute(
        sql + " ORDER BY created_at DESC, id DESC",
        args
    ).fetchall()

    stats = {
        row["fragment_type"]: row["n"]
        for row in db.execute(
            """
            SELECT fragment_type, COUNT(*) AS n
            FROM manuscript_fragments
            GROUP BY fragment_type
            """
        ).fetchall()
    }

    return render_template(
        "fragments/index.html",
        fragments=rows,
        query=query,
        kind=kind,
        stats=stats,
    )


# ---------------------------------------------------------
# Add a new fragment
# ---------------------------------------------------------

@fragments_bp.route("/fragments/new", methods=["GET", "POST"])
def new_fragment():

    if request.method == "GET":
        return render_template(
            "fragments/new.html",
            fragment=None
        )

    form = _form_values()
    image = request.files.get("image")

    error = _validate(
        form,
        image,
        required_image=True
    )

    if error:
        flash(error, "error")

        return render_template(
            "fragments/new.html",
            fragment=form
        ), 400

    filename = save_uploaded_image(image)

    try:
        db = get_db()

        # IMPORTANT:
        # The values must follow exactly the same order
        # as the database columns in the INSERT statement.

        db.execute(
            """
            INSERT INTO manuscript_fragments (
                title,
                fragment_identifier,
                description,
                page_number,
                manuscript_reference,
                transcription,
                image_filename,
                fragment_type,
                collection_name
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                form["title"],
                form["fragment_identifier"],
                form["description"],
                form["page_number"],
                form["manuscript_reference"],
                form["transcription"],
                filename,
                form["fragment_type"],
                form["collection_name"],
            )
        )

        db.commit()

    except Exception:
        image_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"],
            filename
        )

        if os.path.exists(image_path):
            os.remove(image_path)

        raise

    flash(
        "Fragment saved. It is now available for comparison.",
        "success"
    )

    return redirect(url_for("fragments.index"))


# ---------------------------------------------------------
# Fragment details
# ---------------------------------------------------------

@fragments_bp.route("/fragments/<int:fragment_id>")
def fragment_detail(fragment_id):

    fragment = _fragment_or_404(fragment_id)

    matches = get_db().execute(
        """
        SELECT
            m.*,
            f.title,
            f.fragment_identifier,
            f.image_filename,
            f.fragment_type
        FROM fragment_matches m
        JOIN manuscript_fragments f
            ON f.id = m.candidate_fragment_id
        WHERE m.source_fragment_id = ?
        ORDER BY m.score DESC
        """,
        (fragment_id,)
    ).fetchall()

    return render_template(
        "fragments/detail.html",
        fragment=fragment,
        matches=matches
    )


# ---------------------------------------------------------
# Edit an existing fragment
# ---------------------------------------------------------

@fragments_bp.route(
    "/fragments/<int:fragment_id>/edit",
    methods=["GET", "POST"]
)
def edit_fragment(fragment_id):

    fragment = _fragment_or_404(fragment_id)

    if request.method == "GET":
        return render_template(
            "fragments/new.html",
            fragment=fragment,
            editing=True
        )

    form = _form_values()
    image = request.files.get("image")

    error = _validate(form, image)

    if error:
        flash(error, "error")

        return render_template(
            "fragments/new.html",
            fragment=form,
            editing=True
        ), 400

    db = get_db()

    # Prepare values in the exact database column order.
    fields = (
        form["title"],
        form["fragment_identifier"],
        form["description"],
        form["page_number"],
        form["manuscript_reference"],
        form["transcription"],
        form["fragment_type"],
        form["collection_name"],
    )

    if image and image.filename:

        new_filename = save_uploaded_image(image)

        try:
            db.execute(
                """
                UPDATE manuscript_fragments
                SET
                    title = ?,
                    fragment_identifier = ?,
                    description = ?,
                    page_number = ?,
                    manuscript_reference = ?,
                    transcription = ?,
                    fragment_type = ?,
                    collection_name = ?,
                    image_filename = ?
                WHERE id = ?
                """,
                fields + (new_filename, fragment_id)
            )

            db.commit()

        except Exception:
            new_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                new_filename
            )

            if os.path.exists(new_path):
                os.remove(new_path)

            raise

        # Remove the previous image after the new one is saved.
        old_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"],
            fragment["image_filename"]
        )

        if os.path.exists(old_path):
            os.remove(old_path)

    else:

        db.execute(
            """
            UPDATE manuscript_fragments
            SET
                title = ?,
                fragment_identifier = ?,
                description = ?,
                page_number = ?,
                manuscript_reference = ?,
                transcription = ?,
                fragment_type = ?,
                collection_name = ?
            WHERE id = ?
            """,
            fields + (fragment_id,)
        )

        db.commit()

    flash(
        "Fragment details updated.",
        "success"
    )

    return redirect(
        url_for(
            "fragments.fragment_detail",
            fragment_id=fragment_id
        )
    )


# ---------------------------------------------------------
# Delete a fragment
# ---------------------------------------------------------

@fragments_bp.route(
    "/fragments/<int:fragment_id>/delete",
    methods=["POST"]
)
def delete_fragment(fragment_id):

    fragment = _fragment_or_404(fragment_id)

    db = get_db()

    db.execute(
        "DELETE FROM manuscript_fragments WHERE id = ?",
        (fragment_id,)
    )

    db.commit()

    image_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        fragment["image_filename"]
    )

    if os.path.exists(image_path):
        os.remove(image_path)

    flash(
        "Fragment deleted.",
        "success"
    )

    return redirect(url_for("fragments.index"))


# ---------------------------------------------------------
# Candidate matching
# ---------------------------------------------------------

@fragments_bp.route(
    "/fragments/<int:fragment_id>/match",
    methods=["POST"]
)
def find_matches(fragment_id):

    source = _fragment_or_404(fragment_id)

    db = get_db()

    source_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        source["image_filename"]
    )

    if not os.path.isfile(source_path):
        flash(
            "The source fragment image could not be found.",
            "error"
        )

        return redirect(
            url_for(
                "fragments.fragment_detail",
                fragment_id=fragment_id
            )
        )

    # Retrieve every other fragment as a possible candidate.
    candidates = db.execute(
        """
        SELECT *
        FROM manuscript_fragments
        WHERE id <> ?
        ORDER BY id
        """,
        (fragment_id,)
    ).fetchall()

    ranked = []

    for candidate in candidates:

        candidate_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"],
            candidate["image_filename"]
        )

        if not os.path.isfile(candidate_path):
            continue

        try:
            score = similarity(
                source_path,
                candidate_path
            )

            ranked.append((candidate, score))

        except Exception:
            # Skip files that cannot be processed.
            current_app.logger.exception(
                "Could not compare fragment ID %s",
                candidate["id"]
            )
            continue

    # Sort candidates from highest to lowest similarity.
    ranked.sort(
        key=lambda item: item[1],
        reverse=True
    )

    # Remove the previous matching results for this source.
    db.execute(
        """
        DELETE FROM fragment_matches
        WHERE source_fragment_id = ?
        """,
        (fragment_id,)
    )

    # Store the top 10 matching candidates.
    for candidate, score in ranked[:10]:

        db.execute(
            """
            INSERT OR REPLACE INTO fragment_matches (
                source_fragment_id,
                candidate_fragment_id,
                score
            )
            VALUES (?, ?, ?)
            """,
            (
                fragment_id,
                candidate["id"],
                score
            )
        )

    db.commit()

    flash(
        f"Compared {len(ranked)} candidate fragments. "
        "Review scores as preliminary suggestions.",
        "success"
    )

    return redirect(
        url_for(
            "fragments.fragment_detail",
            fragment_id=fragment_id
        )
    )


# ---------------------------------------------------------
# Uploaded image access
# ---------------------------------------------------------

@fragments_bp.route("/uploads/<path:filename>")
def uploaded_file(filename):

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        filename
    )
