import hashlib
import io
import json
import sqlite3
from datetime import datetime
from pathlib import Path

import cv2
import networkx as nx
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from ortools.sat.python import cp_model
from PIL import Image, UnidentifiedImageError
from rapidfuzz import fuzz
from skimage.metrics import structural_similarity

DB_PATH = Path("manuscript_poc.db")
MAX_PAGES = 12
IMAGE_SIZE = (256, 256)

st.set_page_config(
    page_title="Historical Manuscript Reconstruction",
    page_icon="📜",
    layout="wide"
)

st.title("Historical Manuscript Fragment Reconstruction")
st.write(
    "Compare manuscript pages using image, text, and metadata evidence. "
    "Review candidate matches and a proposed page sequence."
)
st.warning(
    "Suggested matches and sequences are not historically confirmed. "
    "Similarity scores cannot establish the original page order."
)


def connect_db():
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db():
    with connect_db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS Manuscripts (
            manuscript_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            source_collection TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS Pages (
            page_id INTEGER PRIMARY KEY AUTOINCREMENT,
            manuscript_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            page_number INTEGER,
            transcribed_text TEXT,
            image_bytes BLOB NOT NULL,
            image_sha256 TEXT NOT NULL,
            width INTEGER NOT NULL,
            height INTEGER NOT NULL,
            FOREIGN KEY (manuscript_id)
                REFERENCES Manuscripts(manuscript_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS PageFeatures (
            feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id INTEGER NOT NULL UNIQUE,
            histogram_json TEXT NOT NULL,
            image_mean REAL NOT NULL,
            image_std REAL NOT NULL,
            text_length INTEGER NOT NULL,
            FOREIGN KEY (page_id)
                REFERENCES Pages(page_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS CandidateMatches (
            match_id INTEGER PRIMARY KEY AUTOINCREMENT,
            manuscript_id INTEGER NOT NULL,
            page_a_id INTEGER NOT NULL,
            page_b_id INTEGER NOT NULL,
            image_score REAL,
            text_score REAL,
            metadata_score REAL,
            overall_score REAL NOT NULL,
            evidence_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(manuscript_id, page_a_id, page_b_id),
            FOREIGN KEY (manuscript_id)
                REFERENCES Manuscripts(manuscript_id) ON DELETE CASCADE,
            FOREIGN KEY (page_a_id)
                REFERENCES Pages(page_id) ON DELETE CASCADE,
            FOREIGN KEY (page_b_id)
                REFERENCES Pages(page_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ProposedSequences (
            sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
            manuscript_id INTEGER NOT NULL,
            sequence_json TEXT NOT NULL,
            objective_score REAL,
            solver_status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (manuscript_id)
                REFERENCES Manuscripts(manuscript_id) ON DELETE CASCADE
        );
        """)


def image_to_features(raw_bytes):
    try:
        with Image.open(io.BytesIO(raw_bytes)) as image:
            image = image.convert("RGB")
            width, height = image.size

            if width < 2 or height < 2:
                raise ValueError("Image dimensions are too small.")

            rgb = np.asarray(image)
            resized = cv2.resize(
                rgb,
                IMAGE_SIZE,
                interpolation=cv2.INTER_AREA
            )
            gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)

            histogram = cv2.calcHist(
                [resized],
                [0, 1, 2],
                None,
                [8, 8, 8],
                [0, 256, 0, 256, 0, 256]
            )
            histogram = cv2.normalize(
                histogram, histogram
            ).flatten().astype(float)

            return {
                "rgb": resized,
                "gray": gray,
                "hist": histogram,
                "width": int(width),
                "height": int(height),
                "mean": float(gray.mean()),
                "std": float(gray.std()),
                "sha256": hashlib.sha256(raw_bytes).hexdigest()
            }

    except (UnidentifiedImageError, OSError, ValueError, cv2.error) as exc:
        raise ValueError(f"Could not read image: {exc}") from exc


def image_similarity(first, second):
    ssim = structural_similarity(
        first["gray"],
        second["gray"],
        data_range=255
    )
    ssim = float(np.clip((ssim + 1.0) / 2.0, 0.0, 1.0))

    histogram_score = cv2.compareHist(
        first["hist"].astype(np.float32),
        second["hist"].astype(np.float32),
        cv2.HISTCMP_CORREL
    )
    histogram_score = float(
        np.clip((histogram_score + 1.0) / 2.0, 0.0, 1.0)
    )

    combined = 0.7 * ssim + 0.3 * histogram_score

    return float(combined), ssim, histogram_score


def compare_text(text_a, text_b):
    text_a = (text_a or "").strip()
    text_b = (text_b or "").strip()

    if not text_a or not text_b:
        return None

    return float(fuzz.token_set_ratio(text_a, text_b) / 100.0)


def compare_metadata(page_a, page_b):
    number_a = page_a["page_number"]
    number_b = page_b["page_number"]

    if number_a is None or number_b is None:
        return None, (
            "Page-number evidence is unavailable because "
            "at least one page number is missing."
        )

    difference = abs(number_a - number_b)
    score = 1.0 / (1.0 + max(0, difference - 1))

    if difference == 1:
        explanation = (
            "Known page numbers are consecutive. "
            "This supports adjacency but does not prove it."
        )
    else:
        explanation = (
            f"Known page numbers differ by {difference}. "
            "This is supporting evidence, not proof of adjacency."
        )

    return float(score), explanation


def compare_pair(page_a, page_b, image_weight=0.65, text_weight=0.25, metadata_weight=0.10):
    image_score, ssim_score, histogram_score = image_similarity(
        page_a["features"],
        page_b["features"]
    )
    text_score = compare_text(page_a["text"], page_b["text"])
    metadata_score, metadata_note = compare_metadata(page_a, page_b)

    evidence_parts = [(image_score, image_weight)]

    if text_score is not None:
        evidence_parts.append((text_score, text_weight))

    if metadata_score is not None:
        evidence_parts.append((metadata_score, metadata_weight))

    evidence_parts = [
        (score, weight)
        for score, weight in evidence_parts
        if weight > 0
    ]

    if not evidence_parts:
        evidence_parts = [(image_score, 1.0)]

    total_weight = sum(weight for _, weight in evidence_parts)
    overall = sum(
        score * weight for score, weight in evidence_parts
    ) / total_weight

    evidence = [
        f"Image score combines SSIM ({ssim_score:.3f}) "
        f"and histogram similarity ({histogram_score:.3f})."
    ]

    if text_score is not None:
        evidence.append(
            f"Transcribed text similarity is {text_score:.3f}."
        )
    else:
        evidence.append(
            "Text comparison was excluded because one or both "
            "pages have no transcription."
        )

    evidence.append(metadata_note)

    return {
        "page_a": page_a["label"],
        "page_b": page_b["label"],
        "page_a_index": page_a["index"],
        "page_b_index": page_b["index"],
        "image_similarity": image_score,
        "ssim_similarity": ssim_score,
        "histogram_similarity": histogram_score,
        "text_similarity": text_score,
        "metadata_score": metadata_score,
        "overall_score": float(overall),
        "evidence": evidence
    }


def propose_sequence(pages, matches, time_limit=10):
    count = len(pages)

    if count < 2:
        return [], "NOT_RUN", None, "At least two pages are required."

    model = cp_model.CpModel()

    assignment = {
        (i, position): model.NewBoolVar(f"x_{i}_{position}")
        for i in range(count)
        for position in range(count)
    }

    for i in range(count):
        model.Add(
            sum(assignment[i, position] for position in range(count)) == 1
        )

    for position in range(count):
        model.Add(
            sum(assignment[i, position] for i in range(count)) == 1
        )

    positions = {}
    for i in range(count):
        positions[i] = model.NewIntVar(
            0, count - 1, f"position_{i}"
        )
        model.Add(
            positions[i] == sum(
                position * assignment[i, position]
                for position in range(count)
            )
        )

    known_numbers = [
        (i, page["page_number"])
        for i, page in enumerate(pages)
        if page["page_number"] is not None
    ]

    for i, number_i in known_numbers:
        for j, number_j in known_numbers:
            if number_i < number_j:
                model.Add(positions[i] < positions[j])

    scores = {}
    for match in matches:
        i = match["page_a_index"]
        j = match["page_b_index"]
        scores[i, j] = match["overall_score"]
        scores[j, i] = match["overall_score"]

    objective_terms = []

    for position in range(count - 1):
        for i in range(count):
            for j in range(count):
                if i == j:
                    continue

                adjacent = model.NewBoolVar(
                    f"adjacent_{i}_{j}_{position}"
                )

                model.Add(assignment[i, position] >= adjacent)
                model.Add(assignment[j, position + 1] >= adjacent)
                model.Add(
                    adjacent >=
                    assignment[i, position]
                    + assignment[j, position + 1] - 1
                )

                score = int(round(scores.get((i, j), 0.0) * 10000))
                objective_terms.append(score * adjacent)

    model.Maximize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit)
    solver.parameters.num_search_workers = 8

    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        sequence = [None] * count

        for i in range(count):
            sequence[solver.Value(positions[i])] = i

        status_name = (
            "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE"
        )

        return (
            sequence,
            status_name,
            solver.ObjectiveValue() / 10000.0,
            "The sequence maximizes adjacent match scores while "
            "preserving the relative order of known page numbers."
        )

    if status == cp_model.INFEASIBLE:
        return (
            [],
            "INFEASIBLE",
            None,
            "The page-number constraints could not be satisfied."
        )

    return (
        [],
        "UNKNOWN_OR_TIMEOUT",
        None,
        "No sequence was found within the solver time limit."
    )


def save_analysis(
    title, collection, pages, matches,
    sequence, solver_status, objective_score
):
    created_at = datetime.now().isoformat(timespec="seconds")

    with connect_db() as con:
        cursor = con.execute(
            """
            INSERT INTO Manuscripts(title, source_collection, created_at)
            VALUES (?, ?, ?)
            """,
            (title.strip(), collection.strip(), created_at)
        )
        manuscript_id = cursor.lastrowid
        page_ids = {}

        for page in pages:
            features = page["features"]

            cursor = con.execute(
                """
                INSERT INTO Pages(
                    manuscript_id, filename, page_number,
                    transcribed_text, image_bytes, image_sha256,
                    width, height
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    manuscript_id,
                    page["filename"],
                    page["page_number"],
                    page["text"],
                    sqlite3.Binary(page["raw_bytes"]),
                    features["sha256"],
                    features["width"],
                    features["height"]
                )
            )

            page_id = cursor.lastrowid
            page_ids[page["index"]] = page_id

            con.execute(
                """
                INSERT INTO PageFeatures(
                    page_id, histogram_json, image_mean,
                    image_std, text_length
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    page_id,
                    json.dumps(features["hist"].tolist()),
                    features["mean"],
                    features["std"],
                    len(page["text"])
                )
            )

        for match in matches:
            con.execute(
                """
                INSERT INTO CandidateMatches(
                    manuscript_id, page_a_id, page_b_id,
                    image_score, text_score, metadata_score,
                    overall_score, evidence_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    manuscript_id,
                    page_ids[match["page_a_index"]],
                    page_ids[match["page_b_index"]],
                    match["image_similarity"],
                    match["text_similarity"],
                    match["metadata_score"],
                    match["overall_score"],
                    json.dumps(match["evidence"]),
                    created_at
                )
            )

        sequence_data = [
            {
                "position": position + 1,
                "page": pages[index]["label"],
                "page_number": pages[index]["page_number"]
            }
            for position, index in enumerate(sequence)
        ]

        con.execute(
            """
            INSERT INTO ProposedSequences(
                manuscript_id, sequence_json,
                objective_score, solver_status, created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                manuscript_id,
                json.dumps(sequence_data),
                objective_score,
                solver_status,
                created_at
            )
        )

    return manuscript_id


def load_history():
    with connect_db() as con:
        return pd.read_sql_query(
            """
            SELECT
                m.manuscript_id,
                m.title,
                m.source_collection,
                m.created_at,
                COUNT(DISTINCT p.page_id) AS page_count,
                COUNT(DISTINCT cm.match_id) AS match_count
            FROM Manuscripts m
            LEFT JOIN Pages p ON p.manuscript_id = m.manuscript_id
            LEFT JOIN CandidateMatches cm
                ON cm.manuscript_id = m.manuscript_id
            GROUP BY m.manuscript_id
            ORDER BY m.manuscript_id DESC
            """,
            con
        )


try:
    init_db()
except sqlite3.Error as exc:
    st.error(f"Could not initialize the database: {exc}")
    st.stop()

with st.sidebar:
    st.header("Manuscript details")
    manuscript_title = st.text_input("Manuscript title")
    source_collection = st.text_input("Source collection")
    st.caption(f"Maximum pages per analysis: {MAX_PAGES}")
    st.subheader("Match scoring weights")
    image_weight_pct = st.slider("Image evidence (%)", 0, 100, 65, 5, key="image_weight_pct")
    text_weight_pct = st.slider("Text evidence (%)", 0, 100, 25, 5, key="text_weight_pct")
    metadata_weight_pct = st.slider("Page-number evidence (%)", 0, 100, 10, 5, key="metadata_weight_pct")
    st.caption("Weights are normalized across the evidence available for each page pair.")

st.subheader("Upload and describe pages")

uploads = st.file_uploader(
    "Upload manuscript page images",
    type=["png", "jpg", "jpeg", "bmp", "tif", "tiff"],
    accept_multiple_files=True
)

if uploads and len(uploads) > MAX_PAGES:
    st.error(f"Upload no more than {MAX_PAGES} images.")
    uploads = uploads[:MAX_PAGES]

pages = []

if uploads:
    st.caption(
        "Page numbers are optional. Known page numbers will constrain "
        "the proposed relative order."
    )

    for index, upload in enumerate(uploads):
        with st.expander(f"Page {index + 1}: {upload.name}"):
            try:
                raw_bytes = upload.getvalue()
                features = image_to_features(raw_bytes)

                left, right = st.columns([1, 2])

                with left:
                    st.image(
                        features["rgb"],
                        caption=upload.name,
                        use_container_width=True
                    )
                    st.write(
                        f"Original size: {features['width']} × "
                        f"{features['height']}"
                    )

                with right:
                    page_number = st.number_input(
                        "Known page number (0 means unknown)",
                        min_value=0,
                        max_value=100000,
                        value=0,
                        step=1,
                        key=f"number_{index}"
                    )

                    text = st.text_area(
                        "Transcribed text or keywords",
                        key=f"text_{index}",
                        height=100
                    )

                pages.append({
                    "index": index,
                    "filename": upload.name,
                    "label": f"{index + 1}. {upload.name}",
                    "page_number": int(page_number) if page_number > 0 else None,
                    "text": text,
                    "raw_bytes": raw_bytes,
                    "features": features
                })

            except ValueError as exc:
                st.error(f"{upload.name}: {exc}")

if pages:
    seen_hashes = {}
    duplicate_pairs = []
    for page in pages:
        digest = page["features"]["sha256"]
        if digest in seen_hashes:
            duplicate_pairs.append((seen_hashes[digest], page["filename"]))
        else:
            seen_hashes[digest] = page["filename"]
    if duplicate_pairs:
        st.warning(
            "Identical image files detected: " +
            "; ".join(f"{a} and {b}" for a, b in duplicate_pairs) +
            ". Confirm these duplicates are intentional."
        )

if st.button("Analyze pages", type="primary", use_container_width=True):
    if not manuscript_title.strip():
        st.error("Enter a manuscript title.")
    elif len(pages) < 2:
        st.error("Upload at least two valid page images.")
    elif image_weight_pct + text_weight_pct + metadata_weight_pct == 0:
        st.error("At least one match scoring weight must be greater than zero.")
    else:
        known_numbers = [
            page["page_number"]
            for page in pages
            if page["page_number"] is not None
        ]

        if len(known_numbers) != len(set(known_numbers)):
            st.error(
                "Known page numbers must be unique. Correct repeated "
                "page numbers or leave unknown numbers as zero."
            )
        else:
            try:
                with st.spinner("Comparing page evidence..."):
                    matches = []

                    for i in range(len(pages)):
                        for j in range(i + 1, len(pages)):
                            matches.append(
                                compare_pair(
                                    pages[i],
                                    pages[j],
                                    image_weight=image_weight_pct / 100.0,
                                    text_weight=text_weight_pct / 100.0,
                                    metadata_weight=metadata_weight_pct / 100.0,
                                )
                            )

                    matches.sort(
                        key=lambda match: match["overall_score"],
                        reverse=True
                    )

                with st.spinner("Finding a proposed sequence..."):
                    sequence, status, objective, sequence_note = (
                        propose_sequence(pages, matches)
                    )

                manuscript_id = save_analysis(
                    manuscript_title,
                    source_collection,
                    pages,
                    matches,
                    sequence,
                    status,
                    objective
                )

                graph = nx.Graph()
                for page in pages:
                    graph.add_node(page["index"], label=page["label"])

                for match in matches:
                    graph.add_edge(
                        match["page_a_index"],
                        match["page_b_index"],
                        weight=match["overall_score"]
                    )

                st.session_state["latest_analysis"] = {
                    "manuscript_id": manuscript_id,
                    "title": manuscript_title,
                    "pages": pages,
                    "matches": matches,
                    "sequence": sequence,
                    "status": status,
                    "objective": objective,
                    "sequence_note": sequence_note,
                    "scoring_weights": {
                        "image_percent": image_weight_pct,
                        "text_percent": text_weight_pct,
                        "metadata_percent": metadata_weight_pct,
                    },
                    "nodes": graph.number_of_nodes(),
                    "edges": graph.number_of_edges()
                }

                st.success(f"Analysis saved. Record number: {manuscript_id}")

            except (sqlite3.Error, ValueError, RuntimeError) as exc:
                st.error(f"Analysis could not be completed: {exc}")
            except Exception as exc:
                st.error(f"An unexpected error occurred: {exc}")

analysis = st.session_state.get("latest_analysis")

if analysis:
    st.divider()
    st.header("Analysis results")

    pages = analysis["pages"]
    matches = analysis["matches"]
    sequence = analysis["sequence"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Pages analyzed", len(pages))
    col2.metric("Candidate relationships", len(matches))
    col3.metric(
        "Graph nodes / edges",
        f"{analysis['nodes']} / {analysis['edges']}"
    )

    st.subheader("Proposed page sequence")
    st.write(f"Solver status: {analysis['status']}")
    st.write(analysis["sequence_note"])

    if sequence:
        sequence_rows = [
            {
                "Proposed position": position + 1,
                "Page image": pages[index]["filename"],
                "Known page number": (
                    pages[index]["page_number"]
                    if pages[index]["page_number"] is not None
                    else "Unknown"
                ),
                "Transcription available": (
                    "Yes" if pages[index]["text"].strip() else "No"
                )
            }
            for position, index in enumerate(sequence)
        ]

        st.dataframe(
            pd.DataFrame(sequence_rows),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning(
            "No sequence was produced. Review the page-number constraints."
        )

    st.subheader("Ranked candidate matches")

    table_rows = []

    for rank, match in enumerate(matches, start=1):
        table_rows.append({
            "Rank": rank,
            "Page A": match["page_a"],
            "Page B": match["page_b"],
            "Overall": round(match["overall_score"], 3),
            "Image": round(match["image_similarity"], 3),
            "Text": (
                round(match["text_similarity"], 3)
                if match["text_similarity"] is not None
                else "Unavailable"
            ),
            "Metadata": (
                round(match["metadata_score"], 3)
                if match["metadata_score"] is not None
                else "Unavailable"
            ),
            "SSIM": round(match["ssim_similarity"], 3),
            "Histogram": round(match["histogram_similarity"], 3)
        })

    results_df = pd.DataFrame(table_rows)

    if not results_df.empty:
        chart_df = results_df.copy()
        chart_df["Score (%)"] = chart_df["Overall"] * 100
        chart_df["Page pair"] = chart_df["Page A"] + " ↔ " + chart_df["Page B"]
        st.plotly_chart(
            px.bar(
                chart_df.head(20).sort_values("Score (%)"),
                x="Score (%)",
                y="Page pair",
                orientation="h",
                title="Top candidate page-pair scores",
                hover_data=["Image", "Text", "Metadata", "SSIM", "Histogram"],
            ),
            use_container_width=True,
        )

        minimum_score_pct = st.slider(
            "Show matches with at least this overall score (%)",
            min_value=0,
            max_value=100,
            value=0,
            step=5,
            key="minimum_score_pct",
        )
        filtered_results_df = results_df[results_df["Overall"] >= minimum_score_pct / 100]
    else:
        filtered_results_df = results_df

    st.dataframe(
        filtered_results_df,
        use_container_width=True,
        hide_index=True
    )
    st.caption(f"Showing {len(filtered_results_df)} of {len(results_df)} candidate pairs.")

    st.download_button(
        "Download filtered candidate matches as CSV",
        data=filtered_results_df.to_csv(index=False).encode("utf-8"),
        file_name="candidate_matches.csv",
        mime="text/csv"
    )

    analysis_report = {
        "manuscript_id": analysis["manuscript_id"],
        "title": analysis["title"],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "solver_status": analysis["status"],
        "sequence_note": analysis["sequence_note"],
        "objective_score": analysis["objective"],
        "scoring_weights": analysis.get("scoring_weights", {}),
        "pages": [
            {
                "filename": page["filename"],
                "page_number": page["page_number"],
                "transcribed_text": page["text"],
                "sha256": page["features"]["sha256"],
                "width": page["features"]["width"],
                "height": page["features"]["height"],
            }
            for page in pages
        ],
        "candidate_matches": [
            {
                "page_a": match["page_a"],
                "page_b": match["page_b"],
                "overall_score": match["overall_score"],
                "image_similarity": match["image_similarity"],
                "ssim_similarity": match["ssim_similarity"],
                "histogram_similarity": match["histogram_similarity"],
                "text_similarity": match["text_similarity"],
                "metadata_score": match["metadata_score"],
                "evidence": match["evidence"],
            }
            for match in matches
        ],
        "proposed_sequence": [
            {
                "position": position + 1,
                "filename": pages[index]["filename"],
                "page_number": pages[index]["page_number"],
            }
            for position, index in enumerate(sequence)
        ],
        "notice": "Candidate scores and proposed sequence are suggestions, not historical confirmation.",
    }
    st.download_button(
        "Download complete analysis report as JSON",
        data=json.dumps(analysis_report, indent=2, ensure_ascii=False, default=str),
        file_name=f"manuscript_{analysis['manuscript_id']}_report.json",
        mime="application/json",
    )

    st.subheader("Evidence for a candidate match")

    match_labels = [
        f"{match['page_a']} and {match['page_b']} "
        f"(score {match['overall_score']:.3f})"
        for match in matches
    ]

    selected_label = st.selectbox(
        "Select a page pair",
        match_labels
    )

    selected = matches[match_labels.index(selected_label)]

    left, right = st.columns(2)

    with left:
        st.image(
            pages[selected["page_a_index"]]["features"]["rgb"],
            caption=selected["page_a"],
            use_container_width=True
        )

    with right:
        st.image(
            pages[selected["page_b_index"]]["features"]["rgb"],
            caption=selected["page_b"],
            use_container_width=True
        )

    st.write(f"Overall score: {selected['overall_score']:.3f}")
    st.write(f"Image similarity: {selected['image_similarity']:.3f}")
    st.write(f"Structural similarity: {selected['ssim_similarity']:.3f}")
    st.write(
        f"Histogram similarity: {selected['histogram_similarity']:.3f}"
    )

    text_score = selected["text_similarity"]
    metadata_score = selected["metadata_score"]

    st.write(
        "Text similarity: "
        + (f"{text_score:.3f}" if text_score is not None else "Unavailable")
    )
    st.write(
        "Metadata score: "
        + (
            f"{metadata_score:.3f}"
            if metadata_score is not None
            else "Unavailable"
        )
    )

    st.write("Evidence supporting this candidate:")
    for evidence in selected["evidence"]:
        st.write(f"- {evidence}")

    st.subheader("Candidate relationship graph")

    graph = nx.Graph()

    for page in pages:
        graph.add_node(page["index"], label=page["filename"])

    for match in matches:
        graph.add_edge(
            match["page_a_index"],
            match["page_b_index"],
            weight=match["overall_score"]
        )

    positions = nx.spring_layout(graph, seed=42)
    figure, axis = plt.subplots(figsize=(10, 6))

    nx.draw_networkx_nodes(
        graph, positions, node_size=900, ax=axis
    )
    nx.draw_networkx_labels(
        graph,
        positions,
        labels={
            page["index"]: page["filename"][:18]
            for page in pages
        },
        font_size=8,
        ax=axis
    )
    nx.draw_networkx_edges(
        graph,
        positions,
        width=[
            1 + 3 * graph[u][v]["weight"]
            for u, v in graph.edges
        ],
        alpha=0.7,
        ax=axis
    )
    nx.draw_networkx_edge_labels(
        graph,
        positions,
        edge_labels={
            (u, v): f"{graph[u][v]['weight']:.2f}"
            for u, v in graph.edges
        },
        font_size=8,
        ax=axis
    )

    axis.set_axis_off()
    st.pyplot(figure)
    plt.close(figure)

    st.info(
        "Similarity scores show possible relationships only. Image layout, "
        "text, and page-number evidence may be incomplete or misleading. "
        "The proposed sequence is not a confirmed historical reconstruction."
    )

st.divider()
st.header("Saved analysis history")

try:
    history = load_history()

    if history.empty:
        st.write("No saved analyses yet.")
    else:
        st.dataframe(
            history,
            use_container_width=True,
            hide_index=True
        )

        record_id = st.selectbox(
            "Select a saved record",
            history["manuscript_id"].astype(int).tolist()
        )

        if st.button("Load saved record summary"):
            with connect_db() as con:
                manuscript = con.execute(
                    """
                    SELECT title, source_collection, created_at
                    FROM Manuscripts WHERE manuscript_id=?
                    """,
                    (int(record_id),)
                ).fetchone()

                saved_pages = con.execute(
                    """
                    SELECT filename, page_number, transcribed_text,
                           width, height, image_sha256
                    FROM Pages
                    WHERE manuscript_id=?
                    ORDER BY page_id
                    """,
                    (int(record_id),)
                ).fetchall()

                saved_sequence = con.execute(
                    """
                    SELECT sequence_json, solver_status,
                           objective_score, created_at
                    FROM ProposedSequences
                    WHERE manuscript_id=?
                    ORDER BY sequence_id DESC LIMIT 1
                    """,
                    (int(record_id),)
                ).fetchone()

                saved_matches = con.execute(
                    """
                    SELECT pa.filename, pb.filename, cm.image_score,
                           cm.text_score, cm.metadata_score,
                           cm.overall_score, cm.evidence_json
                    FROM CandidateMatches cm
                    JOIN Pages pa ON pa.page_id=cm.page_a_id
                    JOIN Pages pb ON pb.page_id=cm.page_b_id
                    WHERE cm.manuscript_id=?
                    ORDER BY cm.overall_score DESC
                    """,
                    (int(record_id),)
                ).fetchall()

            if manuscript:
                st.write({
                    "Title": manuscript[0],
                    "Source collection": manuscript[1],
                    "Created": manuscript[2]
                })

                st.write("Saved pages")
                st.dataframe(
                    pd.DataFrame(
                        saved_pages,
                        columns=[
                            "Filename", "Page number", "Transcribed text",
                            "Width", "Height", "SHA-256"
                        ]
                    ),
                    use_container_width=True,
                    hide_index=True
                )

                if saved_sequence:
                    st.write("Saved proposed sequence")
                    st.json({
                        "sequence": json.loads(saved_sequence[0]),
                        "solver_status": saved_sequence[1],
                        "objective_score": saved_sequence[2],
                        "created_at": saved_sequence[3]
                    })

                st.write("Saved candidate matches")

                if saved_matches:
                    st.dataframe(
                        pd.DataFrame([
                            {
                                "Page A": row[0],
                                "Page B": row[1],
                                "Image score": row[2],
                                "Text score": row[3],
                                "Metadata score": row[4],
                                "Overall score": row[5],
                                "Evidence": "; ".join(json.loads(row[6]))
                            }
                            for row in saved_matches
                        ]),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.write("No candidate matches were saved.")

        st.warning("Deleting a saved analysis permanently removes its pages, matches, and proposed sequence.")
        confirm_delete = st.checkbox(
            f"I understand that deleting record #{int(record_id)} is permanent.",
            key=f"confirm_delete_{int(record_id)}",
        )
        if st.button(
            "Delete selected saved analysis",
            disabled=not confirm_delete,
            key=f"delete_record_{int(record_id)}",
        ):
            with connect_db() as con:
                con.execute(
                    "DELETE FROM Manuscripts WHERE manuscript_id = ?",
                    (int(record_id),)
                )
            if st.session_state.get("latest_analysis", {}).get("manuscript_id") == int(record_id):
                del st.session_state["latest_analysis"]
            st.success(f"Deleted saved analysis #{int(record_id)}.")
            st.rerun()

        if DB_PATH.exists():
            st.download_button(
                "Download SQLite database backup",
                data=DB_PATH.read_bytes(),
                file_name="manuscript_poc_backup.db",
                mime="application/x-sqlite3",
            )

except sqlite3.Error as exc:
    st.error(f"Could not load analysis history: {exc}")
