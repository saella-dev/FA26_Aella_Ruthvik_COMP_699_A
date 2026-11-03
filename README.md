# Historical Manuscript Fragment Reconstruction & Evidence Explorer

## Project Description

This Python Flask application helps researchers and archivists organize and examine incomplete or separated historical manuscript pages.

Users can upload manuscript images, enter page information, save records, and search for manuscript fragments. Future development will compare text, images, and metadata to suggest possible page sequences.

## Technologies Used

- Python
- Flask
- HTML5 and CSS3
- SQLite3
- pytest

Planned analysis libraries: OpenCV, RapidFuzz, NumPy, Pandas, NetworkX, and OR-Tools.

## Project Structure

| File or Folder | Description |
|---|---|
| `app/` | Contains the main Flask application files. |
| `app/__init__.py` | Creates and configures the Flask application. |
| `app/database.py` | Connects to SQLite and creates the database table. |
| `app/fragments.py` | Handles adding, viewing, and searching manuscript fragments. |
| `app/templates/` | Contains the HTML templates. |
| `app/templates/base.html` | Provides the common page layout and navigation. |
| `app/templates/fragments/index.html` | Displays manuscript fragments and search results. |
| `app/templates/fragments/new.html` | Contains the form for adding a manuscript fragment. |
| `app/templates/fragments/detail.html` | Displays the details of a selected fragment. |
| `app/static/css/style.css` | Contains the styles for the application pages. |
| `tests/` | Contains automated tests. |
| `tests/conftest.py` | Sets up the Flask test application and test database. |
| `tests/test_fragments.py` | Tests the manuscript fragment functions. |
| `docs/step_2/week_2/` | Stores Week 2 implementation notes and documentation. |
| `config.py` | Contains application settings and allowed image formats. |
| `run.py` | Starts the Flask application. |
| `requirements.txt` | Lists the Python packages required to run the project. |
| `README.md` | Provides project information and setup instructions. |
| `.gitignore` | Lists files and folders that Git should ignore. |
| `instance/` | Created when the application runs; stores the local database and uploaded images. |

## Installation and Setup

1. Clone the repository:

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

2. Open the project folder in VS Code.

3. Create a virtual environment:

```bash
python -m venv .venv
```

4. Activate it on Windows:

```powershell
.venv\\Scripts\\activate
```

5. Install dependencies:

```bash
pip install -r requirements.txt
```

6. Start the application:

```bash
python run.py
```

7. Open this address in your browser:

```text
http://127.0.0.1:5000/
```

## Current Implemented Features

- **FR-13:** Upload manuscript page images.
- **FR-14:** Add manuscript title, identifier, and description.
- **FR-15:** Enter page numbers and manuscript references.
- **FR-19:** View uploaded manuscript images and details.
- **FR-20:** Search fragments by title, identifier, and page number.

## Current Development Stage

The initial Flask application and SQLite database have been created. Manuscript image uploading, information storage, detail viewing, and fragment searching have been manually checked in the browser.

Automated tests have been added. Run them using:

```bash
python -m pytest -v
```

Check the terminal output to confirm the test results.

## Future Development

- User registration and login.
- Editing and deleting manuscript records.
- Text similarity comparison.
- Image comparison.
- Metadata analysis.
- Graph-based fragment relationships.
- Candidate page sequence generation.
- Evidence scoring and result display.


