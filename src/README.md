# Historical Manuscript Fragment Reconstruction & Evidence Explorer

Week 2 preliminary implementation using Python, Flask, HTML, CSS, and SQLite3.
No JavaScript is used.

## Implemented functional requirements

- FR-13: Upload manuscript page images in supported formats.
- FR-14: Enter and save manuscript title, identifier, and description.
- FR-15: Enter page number and manuscript reference information.
- FR-19: View uploaded images and associated fragment details.
- FR-20: Search fragments by title, identifier, or page number.

## Technology

- Python 3
- Flask
- SQLite3 (Python standard library)
- HTML5 and CSS3
- pytest for automated tests

## Project structure

```text
historical_manuscript_week2/
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── fragments.py
│   ├── templates/
│   │   ├── base.html
│   │   └── fragments/
│   │       ├── index.html
│   │       ├── new.html
│   │       └── detail.html
│   └── static/css/style.css
├── tests/
│   ├── conftest.py
│   └── test_fragments.py
├── config.py
├── requirements.txt
├── run.py
└── README.md
```

## Setup on Windows using VS Code

1. Install Python 3.10 or later.
2. Open this project folder in VS Code.
3. Open the VS Code terminal.
4. Create a virtual environment:

   ```powershell
   python -m venv .venv
   ```

5. Activate it:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt:

   ```cmd
   .venv\Scripts\activate.bat
   ```

6. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

7. Start the application:

   ```powershell
   python run.py
   ```

8. Open `http://127.0.0.1:5000/` in your browser.

The SQLite database and uploaded images are created in the `instance/` directory automatically.

## Run automated tests

With the virtual environment activated:

```powershell
python -m pytest -v
```

## Current limitations

- This is a local development prototype.
- User registration, login, and role-based access are not implemented yet.
- Image validation currently checks the filename extension, not the actual image content.
- Text and image similarity analysis, graph construction, and sequence reconstruction are planned for later milestones.
- No JavaScript is included.
- Do not use the development server or default secret key for production deployment.

## Database

The application creates a `manuscript_fragments` table in SQLite3. It stores fragment metadata and the stored image filename. Image files are kept in the local uploads folder rather than stored as binary data in the database.
