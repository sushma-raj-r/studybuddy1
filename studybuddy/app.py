"""
app.py
------
StudyBuddy — Flask backend.

Routes:
    GET  /                 upload page
    POST /process          runs the pipeline, redirects to /result/<id>
    GET  /result/<id>      dashboard with Summary / Quiz / Flashcards buttons
    GET  /summary/<id>     summary view
    GET  /quiz/<id>        quiz view
    POST /api/grade_quiz   grades submitted answers, returns correct/incorrect + correct answers
    GET  /flashcards/<id>  flashcard view

Results are cached to a JSON file per session under data/ so a page
refresh doesn't re-run the (slow) pipeline. Swap this for a real DB
(e.g. SQLite via SQLAlchemy) if you extend this into a multi-user app.
"""

import os
import json
import uuid
import traceback
import tempfile

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash

from modules import languages
import pipeline

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Uploads go to the SYSTEM temp folder, not a folder inside the project.
# This keeps Flask's file watcher (if ever re-enabled) from seeing new
# files appear mid-download and restarting the server.
UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "studybuddy_uploads")
DATA_DIR = os.path.join(BASE_DIR, "data")
ALLOWED_VIDEO_EXT = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
ALLOWED_PDF_EXT = {".pdf"}

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = "change-this-in-production"  # needed for flash messages


def _save_result(result_id: str, data: dict):
    with open(os.path.join(DATA_DIR, f"{result_id}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_result(result_id: str):
    path = os.path.join(DATA_DIR, f"{result_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.route("/")
def index():
    return render_template("index.html", languages=languages.list_languages_for_dropdown())


@app.route("/process", methods=["POST"])
def process():
    output_language = request.form.get("language", languages.DEFAULT_LANGUAGE)
    source_type = request.form.get("source_type")  # "pdf" | "video" | "url"

    try:
        if source_type == "url":
            url = request.form.get("url", "").strip()
            if not url:
                flash("Please enter a URL.")
                return redirect(url_for("index"))
            result = pipeline.process_upload("url", url, output_language)

        elif source_type in ("pdf", "video"):
            uploaded_file = request.files.get("file")
            if not uploaded_file or uploaded_file.filename == "":
                flash("Please choose a file to upload.")
                return redirect(url_for("index"))

            ext = os.path.splitext(uploaded_file.filename)[1].lower()
            allowed = ALLOWED_PDF_EXT if source_type == "pdf" else ALLOWED_VIDEO_EXT
            if ext not in allowed:
                flash(f"Unsupported file type '{ext}' for {source_type} upload.")
                return redirect(url_for("index"))

            save_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
            uploaded_file.save(save_path)

            result = pipeline.process_upload(source_type, save_path, output_language)

            try:
                os.remove(save_path)
            except OSError:
                pass
        else:
            flash("Invalid source type.")
            return redirect(url_for("index"))

    except Exception as e:
        traceback.print_exc()
        flash(f"Processing failed: {e}")
        return redirect(url_for("index"))

    result_id = uuid.uuid4().hex[:10]
    _save_result(result_id, result)
    return redirect(url_for("result", result_id=result_id))


@app.route("/result/<result_id>")
def result(result_id):
    data = _load_result(result_id)
    if not data:
        flash("Result not found or expired.")
        return redirect(url_for("index"))
    return render_template("result.html", result_id=result_id, data=data,
                            lang_name=languages.get_language_name(data["output_language"]))


@app.route("/summary/<result_id>")
def summary_view(result_id):
    data = _load_result(result_id)
    if not data:
        flash("Result not found or expired.")
        return redirect(url_for("index"))
    return render_template("summary.html", result_id=result_id, data=data)


@app.route("/quiz/<result_id>")
def quiz_view(result_id):
    data = _load_result(result_id)
    if not data:
        flash("Result not found or expired.")
        return redirect(url_for("index"))
    return render_template("quiz.html", result_id=result_id, data=data)


@app.route("/flashcards/<result_id>")
def flashcards_view(result_id):
    data = _load_result(result_id)
    if not data:
        flash("Result not found or expired.")
        return redirect(url_for("index"))
    return render_template("flashcards.html", result_id=result_id, data=data)


@app.route("/api/grade_quiz", methods=["POST"])
def grade_quiz():
    payload = request.get_json()
    result_id = payload.get("result_id")
    answers = payload.get("answers", {})  # {question_id(str): selected_option}

    data = _load_result(result_id)
    if not data:
        return jsonify({"error": "Result not found"}), 404

    graded = []
    score = 0
    for q in data["quiz"]:
        qid = str(q["id"])
        selected = answers.get(qid)
        is_correct = (selected == q["correct_answer"])
        if is_correct:
            score += 1
        graded.append({
            "id": q["id"],
            "selected": selected,
            "correct_answer": q["correct_answer"],
            "is_correct": is_correct,
        })

    return jsonify({
        "score": score,
        "total": len(data["quiz"]),
        "results": graded,
    })


if __name__ == "__main__":
    # use_reloader=False is important: Flask's debug reloader watches every
    # file in the project folder, including uploads/ and data/. While a
    # video/URL is being downloaded, new files get written into uploads/
    # mid-request — the reloader sees that as "code changed" and restarts
    # the server, killing the in-flight request (browser shows
    # ERR_CONNECTION_RESET). Keeping debug=True still gives you the
    # debugger and error pages; it just won't auto-restart on file changes.
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port=5000)
