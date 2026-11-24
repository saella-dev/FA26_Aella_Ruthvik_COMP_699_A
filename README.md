# Historical Manuscript Fragment Reconstruction & Evidence Explorer

## 1. Project Overview

The **Historical Manuscript Fragment Reconstruction & Evidence Explorer** is a web-based application developed to organize, examine, search, and compare historical manuscript fragments.

Historical manuscripts are important sources of information about literature, history, culture, language, religion, and earlier civilizations. However, many historical manuscripts are damaged, incomplete, separated into different pieces, or preserved in different collections. Researchers may find it difficult to identify related fragments and compare their available information.

This project provides a centralized system where users can register manuscript fragments, store their descriptions and transcriptions, upload fragment images, search existing records, and identify visually or textually similar fragments.

The application uses image-processing techniques and text comparison to generate preliminary similarity scores between manuscript fragments. These scores help researchers identify possible relationships that may require further examination.

The system is designed as a research-support tool. It does not automatically confirm that two fragments belong to the same original manuscript. Historical reconstruction requires additional evidence and expert verification.

## 2. Problem Statement

Historical manuscript fragments are frequently stored separately in libraries, museums, archives, universities, and private collections. Information about these fragments may be maintained in different formats and locations.

Researchers can face several problems:

- Manuscript fragments may be separated from their original documents.
- Fragment information may be recorded in different formats.
- Searching for related fragments can require considerable manual effort.
- Images of fragments may contain similar handwriting, patterns, edges, or visual characteristics.
- Textual information may be incomplete or damaged.
- Researchers may have difficulty comparing fragments from different collections.
- Possible fragment relationships may not be documented in one centralized location.

The proposed system addresses these problems by providing a web application for fragment registration, information management, searching, image comparison, text comparison, and preliminary matching.

## 3. Project Objectives

The main objectives are:

1. Develop a web-based application for managing historical manuscript fragments.
2. Provide a structured database for storing fragment information.
3. Allow users to upload and manage manuscript fragment images.
4. Support searching and filtering using fragment identifiers, titles, collections, categories, and other available information.
5. Implement an image-processing method to compare manuscript fragment images.
6. Compare available transcription text to identify possible textual similarities.
7. Generate combined similarity scores when both image and text information are available.
8. Display possible matching fragments for further examination.
9. Allow users to record review decisions for suggested matches.
10. Provide CSV export functionality for research and reporting.
11. Establish a foundation for future improvements in manuscript analysis and reconstruction.

## 4. Main Features

### 4.1 Manuscript Fragment Registration

Users can add manuscript fragment records through a web form.

The registration form supports the following information:

- Fragment title
- Unique fragment identifier
- Fragment category
- Collection name
- Page number
- Manuscript reference
- Fragment description
- Transcription text
- Manuscript fragment image

Each fragment is stored as an individual record in the SQLite database.

The unique fragment identifier helps distinguish one record from another and supports accurate searching.

### 4.2 Fragment Categories

The application supports three fragment categories:

| Category | Description |
|---|---|
| Complete | A fragment or manuscript record classified as complete for the project's cataloguing purposes. |
| Paired | A fragment identified or classified as having a possible relationship with another fragment. |
| Orphan | A fragment without an identified matching or related fragment. |

These categories help organize records and support the examination of possible fragment relationships.

The category is a cataloguing value. It does not independently prove that a fragment has been historically reconstructed.

### 4.3 Fragment Image Upload

Users can upload images associated with manuscript fragments.

The application uses image validation before accepting an uploaded file. The image is stored in the application's upload directory, while its filename is recorded in the database.

The system uses the Pillow library to process images.

Supported image formats depend on the validation rules implemented in the application. The application should reject unsupported file types and files that cannot be read as valid images.

### 4.4 Fragment Dashboard

The dashboard provides an overview of the stored manuscript fragments.

It displays summary information such as:

- Total number of registered fragments
- Number of complete fragments
- Number of paired fragments
- Number of orphan fragments

The dashboard also displays the available fragment records.

Users can open individual records to examine their information or edit existing records.

### 4.5 Search and Filtering

The application provides search and filtering functionality to help users locate manuscript fragments.

Users can search using available information such as:

- Fragment title
- Fragment identifier
- Page number
- Collection name
- Transcription text

Users can also filter records by fragment category.

The search functionality reduces the time required to locate records when the database contains multiple manuscript fragments.

### 4.6 Fragment Details

Each manuscript fragment has an individual detail page.

The detail page displays the available information associated with the selected record, including:

- Fragment title
- Fragment identifier
- Category
- Collection
- Page number
- Manuscript reference
- Description
- Transcription
- Uploaded image
- Available matching results
- Match review information

This page provides a centralized view of the information associated with a particular manuscript fragment.

### 4.7 Edit and Delete Operations

The application supports basic record management.

Users can:

- Edit existing fragment information.
- Update descriptions and transcription text.
- Change the fragment category.
- Replace an uploaded image.
- Delete a fragment record.

These functions help maintain accurate and updated manuscript information.

### 4.8 Image Similarity Analysis

The application includes a preliminary image-comparison method to identify visually similar manuscript fragments.

The current implementation uses basic image processing rather than a trained deep-learning model.

The image-processing workflow includes:

1. Open the uploaded image.
2. Correct image orientation when EXIF orientation information is available.
3. Convert the image into grayscale.
4. Apply edge detection.
5. Generate a numerical image descriptor.
6. Normalize the descriptor.
7. Compare the descriptors using cosine similarity.
8. Convert the comparison result into a percentage score.

The similarity score provides an indication of visual similarity between two processed images.

A higher score indicates greater similarity according to the implemented descriptor. It does not guarantee that the fragments belong to the same manuscript.

### 4.9 Text Similarity Analysis

The application also compares transcription text when text is available.

The current implementation uses Python's `difflib.SequenceMatcher` to calculate a text similarity score.

The general process is:

1. Retrieve the transcription of the source fragment.
2. Retrieve the transcription of a candidate fragment.
3. Compare the available text.
4. Calculate a similarity ratio.
5. Convert the ratio into a percentage score.

If transcription text is unavailable, the application does not treat the missing text as a valid text similarity result.

Text similarity is intended to support preliminary comparison. It does not perform advanced historical language analysis, handwriting recognition, or linguistic reconstruction.

### 4.10 Combined Similarity Score

The application combines image and text similarity when both scores are available.

The current calculation uses the following weights:

- Image similarity: 70%
- Text similarity: 30%

The calculation is:

**Combined Similarity = (Image Similarity × 0.70) + (Text Similarity × 0.30)**

When transcription text is unavailable, the application uses the available visual similarity score instead of treating missing text as zero.

The combined score is used to rank possible matching fragments.

These weights are preliminary implementation choices. They should be evaluated and adjusted using suitable research data and expert feedback before being treated as scientifically validated measures.

### 4.11 Matching Results

After a matching operation, the application compares the selected fragment with other available fragment records.

The system stores the top matching candidates in the database.

The results can include:

- Source fragment
- Candidate fragment
- Visual similarity score
- Text similarity score
- Combined similarity score
- Review status
- Review notes

The application displays possible matching candidates so that users can examine the results.

The matching process is intended to identify candidates for further investigation, not to make final historical decisions.

### 4.12 Match Review

The application supports a review process for generated matching results.

A match can have one of the following statuses:

| Status | Description |
|---|---|
| Pending | The suggested relationship has not yet been reviewed. |
| Accepted | The reviewer has accepted the suggested relationship for the project's records. |
| Rejected | The reviewer has rejected the suggested relationship. |

Users can also provide review notes.

An accepted result represents a recorded review decision within the application. It should not automatically be interpreted as independent scholarly verification.

### 4.13 CSV Export

The application provides CSV export functionality.

Users can export available manuscript fragment information into a CSV file.

The exported information can be opened using spreadsheet applications for further analysis, documentation, or reporting.

## 5. Technologies Used

The project uses the following technologies:

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Flask | Web application framework |
| SQLite | Relational database |
| HTML5 | Web page structure |
| CSS3 | User interface styling |
| Pillow | Image loading and processing |
| difflib | Text similarity comparison |
| NumPy | Numerical operations, where used by the implementation |
| pytest | Automated testing |
| VS Code | Development environment |
| Git and GitHub | Version control and project management |

### 5.1 Python

Python is used for application logic, database operations, image processing, text comparison, and server-side functionality.

### 5.2 Flask

Flask provides the web application framework. It handles HTTP requests, application routes, templates, form submissions, and communication between the user interface and backend.

### 5.3 SQLite

SQLite stores manuscript fragment information and matching results. It provides a lightweight database solution suitable for the current development and demonstration environment.

### 5.4 HTML and CSS

HTML is used to create the application pages, forms, tables, and content structure.

CSS is used to style the dashboard, forms, fragment cards, navigation, and other interface elements.

### 5.5 Pillow

Pillow is used to open, validate, transform, and process manuscript fragment images.

### 5.6 pytest

pytest is used to execute automated tests and verify important application functions.

## 6. System Architecture

The application follows a simple layered web application architecture.

The major components are:

**1. Presentation Layer**

The presentation layer contains HTML templates and CSS files. It displays the dashboard, registration forms, fragment details, search results, and matching results.

**2. Application Layer**

The application layer is implemented using Flask. It receives user requests, validates submitted information, processes application logic, and communicates with the database and matching modules.

**3. Business Logic Layer**

The business logic layer handles fragment registration, editing, deletion, searching, image validation, image similarity, text similarity, combined scoring, and match review operations.

**4. Database Layer**

The database layer uses SQLite to store manuscript fragment records and matching information.

**5. Image Processing Layer**

The image processing module uses Pillow and numerical operations to prepare images and calculate visual similarity.

### 6.1 General Application Workflow

1. The user opens the application in a web browser.
2. Flask receives the request.
3. The application retrieves information from SQLite when required.
4. The appropriate HTML template is rendered.
5. The user can register, search, edit, delete, or compare fragments.
6. When matching is requested, the matching module processes the available image and transcription data.
7. The application stores the matching results.
8. The results are displayed on the fragment detail page.

### 6.2 Architecture Diagram

```text
                  USER
                   |
                   v
             WEB BROWSER
                   |
                   v
          HTML TEMPLATES / CSS
                   |
                   v
              FLASK APP
                   |
          +--------+---------+
          |                  |
          v                  v
   FRAGMENT MANAGEMENT   MATCHING MODULE
          |                  |
          |          +-------+--------+
          |          |                |
          |          v                v
          |     IMAGE ANALYSIS   TEXT ANALYSIS
          |          |                |
          |          +-------+--------+
          |                  |
          |                  v
          |          COMBINED SCORE
          |                  |
          +--------+---------+
                   |
                   v
              SQLITE DATABASE
                   |
                   v
          MATCHING RESULTS
                   |
                   v
              WEB BROWSER
```

## 7. Database Design

The application uses SQLite as its database management system.

The database stores manuscript fragment records and the matching results generated by the application.

### 7.1 Manuscript Fragments Table

The `manuscript_fragments` table stores the main information about each manuscript fragment.

The table includes fields such as:

| Field | Purpose |
|---|---|
| id | Primary key of the fragment record |
| title | Title of the manuscript fragment |
| fragment_identifier | Unique fragment identifier |
| fragment_type | Fragment category |
| collection_name | Name of the collection |
| page_number | Page number, when available |
| manuscript_reference | Manuscript reference information |
| description | Description of the fragment |
| transcription | Available transcription text |
| image_filename | Stored image filename |
| created_at | Record creation timestamp |
| updated_at | Record update timestamp |

The exact field definitions and constraints are maintained in the database implementation.

### 7.2 Fragment Matches Table

The `fragment_matches` table stores the possible matching relationships identified by the application.

The table includes fields such as:

| Field | Purpose |
|---|---|
| id | Primary key of the matching record |
| source_fragment_id | ID of the fragment being compared |
| candidate_fragment_id | ID of the candidate fragment |
| visual_score | Image similarity percentage |
| text_score | Text similarity percentage, when available |
| combined_score | Combined similarity percentage |
| review_status | Current review status |
| review_notes | Notes added during review |
| created_at | Time the matching result was created |

The source and candidate fragment IDs connect matching results with records in the manuscript fragments table.

Database indexes are used for commonly accessed fields where implemented.

### 7.3 Database Relationships

A manuscript fragment can have multiple matching candidates.

The relationship can be represented as:

```text
MANUSCRIPT_FRAGMENTS
          |
          | 1
          |
          | Many
          v
     FRAGMENT_MATCHES
          |
          +---- Source Fragment
          |
          +---- Candidate Fragment
```

The matching table stores references to the manuscript fragment records.

## 8. Image and Text Matching Methodology

### 8.1 Image Processing Method

The current image comparison method uses a basic image descriptor.

The image is first loaded and converted into grayscale. Edge detection is then applied to identify important visual boundaries.

The processed image is represented as numerical values. These values are normalized to create a descriptor that can be compared with another descriptor.

Cosine similarity is used to calculate the similarity between two descriptors.

The cosine similarity formula is:

```text
Similarity(A, B) = (A · B) / (||A|| × ||B||)
```

Where:

- A represents the descriptor of the first image.
- B represents the descriptor of the second image.
- A · B represents the dot product.
- ||A|| and ||B|| represent the vector magnitudes.

The result is converted into a percentage for display.

### 8.2 Text Comparison Method

The application uses `difflib.SequenceMatcher` to compare available transcription strings.

The comparison calculates a similarity ratio based on matching sequences.

The text score is represented as a percentage.

This method is suitable for a preliminary comparison of text strings. It does not understand the historical meaning of words or automatically correct damaged or incomplete text.

### 8.3 Combined Scoring Method

When both image and text scores are available, the application calculates a weighted combined score.

```text
Combined Score =
    (Visual Score × 0.70) +
    (Text Score × 0.30)
```

If text information is unavailable, the visual score is used.

The application ranks the matching candidates based on the calculated score and stores the selected results.

### 8.4 Method Limitations

The current matching method has several limitations:

- Basic edge descriptors cannot identify every important manuscript characteristic.
- Image quality and lighting can affect similarity results.
- Differences in image orientation, scale, and cropping can affect comparisons.
- Similar-looking fragments may not belong to the same manuscript.
- Text comparison does not understand historical language, grammar, or meaning.
- The current method is not a trained machine-learning or deep-learning reconstruction model.
- The current score weights have not been established through a comprehensive scholarly evaluation.

For these reasons, matching results should be treated as preliminary suggestions.

## 9. Project Directory Structure

The project is organized into separate directories for application code, templates, static files, tests, and documentation.

```text
Historical-Manuscript-Reconstruction/
│
├── run.py
├── config.py
├── requirements.txt
├── README.md
├── CHANGELOG.md
├── PROJECT_STRUCTURE.txt
├── seed_demo.py
├── .gitignore
│
├── src/
│   └── app/
│       ├── __init__.py
│       ├── database.py
│       ├── fragments.py
│       ├── matching.py
│       │
│       ├── templates/
│       │   ├── base.html
│       │   │
│       │   └── fragments/
│       │       ├── index.html
│       │       ├── new.html
│       │       └── detail.html
│       │
│       └── static/
│           └── css/
│               └── style.css
│
├── tests/
│   ├── conftest.py
│   ├── test_fragments.py
│   └── test_integration_features.py
│
├── docs/
│   ├── step_2/
│   │   └── week_3/
│   │
│   └── step_3/
│       └── UPDATE_NOTES.md
│
└── instance/
    └── uploads/
```

The directory structure above describes the main application organization. Additional documentation and files may be added as development continues.

## 10. Installation and Setup

### 10.1 Prerequisites

Install the following software before running the application:

- Python 3.10 or later
- Visual Studio Code or another Python-compatible IDE
- Git (optional, for version control)
- A modern web browser

Python 3.13 has been used in the development environment.

### 10.2 Clone the Repository

Open PowerShell or the VS Code terminal.

Run:

```powershell
git clone YOUR_GITHUB_REPOSITORY_URL
```

Move into the project directory:

```powershell
cd Historical-Manuscript-Reconstruction
```

Replace the repository URL and directory name with the actual values used in your GitHub repository.

### 10.3 Create a Virtual Environment

Run:

```powershell
python -m venv .venv
```

Activate the environment:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, use the following command for the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the virtual environment again.

### 10.4 Install Dependencies

Run:

```powershell
python -m pip install --upgrade pip
```

Install the project dependencies:

```powershell
python -m pip install -r requirements.txt
```

The requirements file contains the Python packages needed by the application.

## 11. Running the Application

After installing the dependencies, start the application from the project root directory.

Run:

```powershell
python run.py
```

The Flask development server should start.

Open the following address in a web browser:

```text
http://127.0.0.1:5000
```

The application dashboard should appear.

To stop the development server, press:

```text
CTRL + C
```

**Important:** The Flask development server is intended for local development and testing. It is not a production deployment configuration.

## 12. Demo Data

The project includes a `seed_demo.py` file for preparing demonstration records, depending on the current implementation.

If the script is configured for the local database, it can be executed from the project root:

```powershell
python seed_demo.py
```

Use demo records to examine the dashboard, search functionality, fragment details, and matching workflow.

Do not run a data-seeding script against important research records without checking whether it inserts duplicate data or modifies existing records.

## 13. Testing

The project uses pytest for automated testing.

The test files are organized inside the `tests/` directory.

### 13.1 Run All Tests

From the project root, execute:

```powershell
python -m pytest -v
```

This command runs the available automated test cases and displays their results.

### 13.2 Main Testing Areas

The test suite is intended to verify the following application functions:

| Testing Area | Description |
|---|---|
| Application startup | Verify that the Flask application can be created. |
| Dashboard | Verify that the dashboard loads successfully. |
| Fragment registration | Verify that new fragment records can be submitted. |
| Required fields | Verify that required information is validated. |
| Image validation | Verify that unsupported or invalid image files are rejected. |
| Database storage | Verify that fragment information is stored correctly. |
| Fragment details | Verify that individual fragment records can be opened. |
| Search | Verify that records can be searched. |
| Duplicate identifiers | Verify that duplicate fragment identifiers are rejected. |
| Editing | Verify that existing fragment information can be updated. |
| Image matching | Verify that matching candidates can be generated. |
| Match review | Verify that review statuses and notes can be updated. |
| CSV export | Verify that fragment information can be exported. |

### 13.3 Manual Testing

In addition to automated testing, the following manual checks should be performed:

1. Start the application.
2. Open the dashboard.
3. Register a new manuscript fragment.
4. Upload a valid manuscript image.
5. Confirm that the record appears on the dashboard.
6. Open the fragment detail page.
7. Search using the fragment identifier.
8. Filter records by category.
9. Edit the fragment information.
10. Replace the uploaded image.
11. Run the matching operation.
12. Review the suggested matching candidates.
13. Change a match review status.
14. Export the available records to CSV.
15. Confirm that the exported file contains the expected information.

Record actual test results before reporting that a test has passed.

## 14. Application Routes

The Flask application provides routes for the main operations.

The current application includes routes with the following purposes:

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Display the fragment dashboard |
| `/fragments/new` | GET, POST | Display and submit the fragment registration form |
| `/fragments/<id>` | GET | Display fragment details |
| `/fragments/<id>/edit` | GET, POST | Edit an existing fragment |
| `/fragments/<id>/delete` | POST | Delete a fragment |
| `/fragments/<id>/match` | POST | Generate matching candidates |
| `/matches/<match_id>/review` | POST | Update a matching review |
| `/export.csv` | GET | Export fragment records |
| `/uploads/<filename>` | GET | Display an uploaded image |

Route availability and HTTP methods should be confirmed against the current source code whenever routes are modified.

## 15. Security and Data Validation

The application includes basic validation to improve the reliability of stored information.

The current implementation includes or is designed to support:

- Required-field validation.
- Unique fragment identifier validation.
- Image file validation.
- Image content validation.
- File size restrictions.
- Database parameterized queries.
- Separate storage of uploaded image files.
- Controlled review status values.

The application is currently a development-stage research prototype. Additional security work is required before production deployment.

Future security improvements should include user authentication, authorization, CSRF protection, stronger upload controls, secure configuration management, and appropriate backup procedures.

## 16. Current Project Status

The application provides a foundation for managing and comparing historical manuscript fragments.

The main implementation areas include:

- Flask application structure.
- SQLite database integration.
- Fragment registration and management.
- Fragment image upload.
- Dashboard and search functionality.
- Image similarity analysis.
- Text similarity analysis.
- Combined similarity scoring.
- Matching result storage.
- Match review functionality.
- CSV export.
- Automated test cases.

The application is still a research prototype. Its matching results are preliminary and should not be presented as confirmed historical manuscript reconstruction.

The actual completion status of each feature should be verified using the latest application code and test results.

## 17. Current Limitations

The following limitations should be considered when using the application:

1. The current image comparison method uses basic image processing.
2. The application does not contain a trained Siamese neural network.
3. The application does not implement BFAz or RGAN.
4. The application does not provide automatic handwriting recognition.
5. The application does not perform automatic historical language translation.
6. The application does not establish the historical origin of a manuscript fragment.
7. Similarity scores are not proof that two fragments belong together.
8. The application does not currently provide expert-verified reconstruction results.
9. The application uses SQLite for its current database implementation.
10. The current application is not configured as a production-ready multi-user research platform.

These limitations define the scope of the current implementation and provide direction for future development.

## 18. Future Enhancements

Several improvements can be considered in future development stages.

### 18.1 Advanced Image Processing

Future versions may include improved image preprocessing techniques such as:

- Image rotation correction.
- Image alignment.
- Contrast enhancement.
- Noise reduction.
- Background removal.
- More advanced edge and texture analysis.

These techniques may improve image comparison when manuscript fragments have different orientations, lighting conditions, or image quality.

### 18.2 Advanced Similarity Models

A future research stage may investigate more advanced image-comparison methods, including feature-based matching and trained neural-network approaches.

Any new model should be evaluated using suitable manuscript datasets and documented evaluation procedures.

### 18.3 Optical Character Recognition

OCR functionality could be introduced to extract text from manuscript images.

This could help researchers compare available text without manually entering every transcription.

Historical handwriting and damaged manuscripts may require specialized OCR methods.

### 18.4 Improved Text Analysis

Future improvements may include:

- Historical spelling variation handling.
- Language identification.
- Text normalization.
- Character-level comparison.
- Word-level comparison.
- Linguistic similarity analysis.

### 18.5 Manuscript Reconstruction Visualization

A future version could provide a visual workspace where researchers can examine multiple fragments and arrange possible relationships.

Such a feature should clearly distinguish suggested arrangements from verified reconstruction results.

### 18.6 Research Evaluation

Future evaluation should use a suitable dataset containing known manuscript relationships.

Possible evaluation measures include:

- Precision.
- Recall.
- F1-score.
- Top-k retrieval accuracy.
- Mean Average Precision (mAP).
- Expert review of suggested matches.

The evaluation process should compare system suggestions with documented reference relationships rather than relying only on similarity percentages.

### 18.7 User Accounts and Researcher Roles

Future development may introduce user authentication and different roles, such as:

- Researcher
- Reviewer
- Administrator

This would help manage access to manuscript records and review decisions.

### 18.8 Database Improvements

For larger research collections, the SQLite database could be replaced with a database server such as PostgreSQL.

This would provide a stronger foundation for concurrent access and larger datasets.

## 19. Expected Project Outcomes

The expected outcome is a working web-based prototype that helps organize historical manuscript fragments and supports preliminary comparison.

The application aims to provide:

- A structured manuscript fragment catalog.
- A centralized location for fragment information.
- Image and transcription storage.
- Search and filtering capabilities.
- Preliminary visual similarity results.
- Preliminary text similarity results.
- Combined candidate ranking.
- Review and documentation of matching decisions.
- CSV export for additional research.

The project provides a starting point for further research into digital manuscript analysis and fragment reconstruction.

