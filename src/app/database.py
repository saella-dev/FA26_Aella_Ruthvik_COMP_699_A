
import os
import sqlite3

from flask import current_app, g


# ---------------------------------------------------------
# Database schema
# ---------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS manuscript_fragments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    fragment_identifier TEXT NOT NULL,
    description TEXT,
    page_number TEXT,
    manuscript_reference TEXT,
    transcription TEXT,
    image_filename TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fragment_type TEXT NOT NULL DEFAULT 'orphan',
    collection_name TEXT
);

CREATE TABLE IF NOT EXISTS fragment_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_fragment_id INTEGER NOT NULL
        REFERENCES manuscript_fragments(id) ON DELETE CASCADE,
    candidate_fragment_id INTEGER NOT NULL
        REFERENCES manuscript_fragments(id) ON DELETE CASCADE,
    score REAL NOT NULL,
    method TEXT NOT NULL DEFAULT 'grayscale-edge baseline',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_fragment_id, candidate_fragment_id)
);

CREATE INDEX IF NOT EXISTS idx_fragments_identifier
ON manuscript_fragments(fragment_identifier);

CREATE INDEX IF NOT EXISTS idx_fragments_type
ON manuscript_fragments(fragment_type);

CREATE INDEX IF NOT EXISTS idx_fragments_collection
ON manuscript_fragments(collection_name);

CREATE INDEX IF NOT EXISTS idx_matches_source
ON fragment_matches(source_fragment_id);

CREATE INDEX IF NOT EXISTS idx_matches_candidate
ON fragment_matches(candidate_fragment_id);
"""


# ---------------------------------------------------------
# Get database connection
# ---------------------------------------------------------

def get_db():
    """
    Get the SQLite connection for the current Flask application context.
    Reuse the connection during the current request.
    """

    if "db" not in g:

        database_path = current_app.config["DATABASE"]

        # Create the database directory when necessary.
        database_directory = os.path.dirname(database_path)

        if database_directory:
            os.makedirs(database_directory, exist_ok=True)

        g.db = sqlite3.connect(
            database_path,
            timeout=20
        )

        # Return database rows as dictionary-like objects.
        g.db.row_factory = sqlite3.Row

        # Enable foreign-key constraints for this connection.
        g.db.execute("PRAGMA foreign_keys = ON")

        # Wait briefly if another connection is writing.
        g.db.execute("PRAGMA busy_timeout = 20000")

    return g.db


# ---------------------------------------------------------
# Initialize database and apply migrations
# ---------------------------------------------------------

def init_db():
    """
    Create database tables and safely add missing columns
    for databases created by earlier versions of the project.
    """

    db = get_db()

    # Create tables and indexes.
    db.executescript(SCHEMA)

    # Read existing manuscript_fragments columns.
    columns = {
        row["name"]
        for row in db.execute(
            "PRAGMA table_info(manuscript_fragments)"
        ).fetchall()
    }

    # Add fragment_type if it does not exist.
    if "fragment_type" not in columns:

        db.execute(
            """
            ALTER TABLE manuscript_fragments
            ADD COLUMN fragment_type TEXT NOT NULL DEFAULT 'orphan'
            """
        )

    # Add collection_name if it does not exist.
    if "collection_name" not in columns:

        db.execute(
            """
            ALTER TABLE manuscript_fragments
            ADD COLUMN collection_name TEXT
            """
        )

    db.commit()


# ---------------------------------------------------------
# Close database connection
# ---------------------------------------------------------

def close_db(error=None):
    """
    Close the SQLite connection when the Flask application
    context ends.
    """

    db = g.pop("db", None)

    if db is not None:
        db.close()


# ---------------------------------------------------------
# Register database functions with Flask
# ---------------------------------------------------------

def init_app(app):
    """
    Configure the database location and register cleanup.
    """

    app.config.setdefault(
        "DATABASE",
        os.path.join(
            app.instance_path,
            "manuscripts.sqlite3"
        )
    )

    app.teardown_appcontext(close_db)
