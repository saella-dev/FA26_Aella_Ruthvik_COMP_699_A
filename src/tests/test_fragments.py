import io
import sqlite3
import os

def sample_form(filename="sample.png"):
    return {
        "title": "Test Manuscript",
        "fragment_identifier": "TEST-001",
        "description": "A test fragment",
        "page_number": "1",
        "manuscript_reference": "Archive A",
        "transcription": "A sample transcription",
        "image": (io.BytesIO(b"fake-image-content"), filename),
    }

def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Manuscript fragments" in response.data

def test_add_fragment_saves_record_and_image(client, app):
    response = client.post(
        "/fragments/new", data=sample_form(),
        content_type="multipart/form-data", follow_redirects=True
    )
    assert response.status_code == 200
    assert b"saved successfully" in response.data
    with sqlite3.connect(app.config["DATABASE"]) as db:
        row = db.execute(
            "SELECT title, fragment_identifier, image_filename FROM manuscript_fragments"
        ).fetchone()
    assert row[0] == "Test Manuscript"
    assert row[1] == "TEST-001"
    assert os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], row[2]))

def test_missing_required_title_is_rejected(client):
    data = sample_form()
    data["title"] = ""
    response = client.post(
        "/fragments/new", data=data,
        content_type="multipart/form-data"
    )
    assert response.status_code == 400
    assert b"Title and fragment identifier are required" in response.data

def test_unsupported_file_type_is_rejected(client):
    response = client.post(
        "/fragments/new", data=sample_form("notes.txt"),
        content_type="multipart/form-data"
    )
    assert response.status_code == 400
    assert b"Unsupported image format" in response.data

def test_detail_page_displays_saved_fragment(client):
    client.post("/fragments/new", data=sample_form(),
                content_type="multipart/form-data")
    response = client.get("/fragments/1")
    assert response.status_code == 200
    assert b"Test Manuscript" in response.data
    assert b"TEST-001" in response.data

def test_search_by_identifier(client):
    client.post("/fragments/new", data=sample_form(),
                content_type="multipart/form-data")
    response = client.get("/?q=TEST-001")
    assert response.status_code == 200
    assert b"Test Manuscript" in response.data
