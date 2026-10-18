# Historical Manuscript Fragment Reconstruction & Evidence Explorer

## Project Description

I am developing a Python application that helps researchers compare incomplete or separated historical manuscript pages. The application uses image similarity, text similarity, and available page metadata to suggest possible page matches and page sequences.

The system displays matching scores and supporting evidence so researchers can review the results. It does not guarantee the original page order or attempt to recreate missing historical content.

## Technologies Used

- Python
- Streamlit
- Pandas
- NumPy
- Pillow
- OpenCV
- scikit-image
- RapidFuzz
- NetworkX
- OR-Tools
- SQLite

## Features

- Upload multiple manuscript page images.
- Enter page numbers and transcribed text.
- Compare page images using visual similarity.
- Compare text using approximate text matching.
- Calculate combined matching scores.
- Represent candidate page relationships using a graph.
- Generate proposed page sequences using ordering constraints.
- Display ranked candidate matches and their supporting evidence.
- Store manuscript records and analysis results in SQLite.
- Export candidate matching results as a CSV file.
- View previously saved analysis records.

## Requirements

I use Python 3.10 or a compatible newer version. I recommend using a virtual environment to keep the project dependencies separate from other Python projects.

## Installation

First, I create and activate a virtual environment.

On Windows:

```
python -m venv .venv
.venv\Scripts\activate
```

On macOS or Linux:

```
python3 -m venv .venv
source .venv/bin/activate
```

I install the required packages with the following command:

```
python -m pip install streamlit pandas numpy Pillow opencv-python-headless scikit-image rapidfuzz networkx ortools
```

## Running the Application

I save the main application as:

`manuscript_reconstruction_poc.py`

I start the application using:

```
python -m streamlit run manuscript_reconstruction_poc.py
```

Streamlit opens the application in a browser. If it does not open automatically, I can visit:

http://localhost:8501

## How I Use the Application

1. I enter a manuscript title and source collection.
2. I upload at least two manuscript page images.
3. I enter known page numbers and available transcribed text.
4. I run the analysis.
5. I review the proposed page sequence and ranked candidate matches.
6. I inspect the evidence scores for individual page pairs.
7. I download the candidate matching results as a CSV file.

## Data Storage

The application creates a local SQLite database named `manuscript_poc.db`. It stores manuscript records, page information, extracted features, candidate matches, and proposed sequences.

The database is generated automatically when the application starts.

## Data Sources

I plan to evaluate the application using publicly accessible digitized manuscript collections from:

- British Library: [https://www.bl.uk/manuscripts/](<https://www.bl.uk/manuscripts/>)
- Digital Bodleian: [https://digital.bodleian.ox.ac.uk/](<https://digital.bodleian.ox.ac.uk/>)
- Internet Archive: [https://archive.org/](<https://archive.org/>)

I will check the availability and reuse conditions of selected materials before including them in my tests.

## Testing and Evaluation

I will test the application using manuscript pages with known original sequences. I will compare the proposed results with those known sequences and measure whether correct page matches appear among the highest-ranked candidates.

I will also test image processing, text matching, database operations, ordering constraints, and application response time.

My initial performance target is to process 50 page images and display results within 30 seconds on my development laptop. I will record actual measurements during testing rather than assume that the target has been achieved.

## Limitations

- The application depends on the quality of the available images and transcribed text.
- Missing metadata may reduce the quality of matching results.
- Similarity scores do not prove that two pages originally appeared together.
- Proposed sequences are suggestions and require human review.
- The initial version does not include advanced handwriting recognition or automatic reconstruction of missing text.

## Author

Sai Ruthvik Reddy Aella

FA26 - COMP-699-A - PROFESSIONAL SEMINAR
