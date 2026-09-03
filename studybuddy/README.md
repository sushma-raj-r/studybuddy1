# StudyBuddy — Lecture Catch-up Tool

For students who missed class: upload a lecture **video**, a **URL**, or a **PDF**,
and get:
1. A **summary** with filler words/sounds removed ("umm", "uhh", etc.)
2. An auto-generated **quiz** (MCQs) built only from the summary — shows the
   correct answer after you submit
3. **Flashcards** built from the summary

Supports **English, Hindi, Kannada** output — designed so adding more
languages later takes one line of code (see "Adding a new language" below).

---

## Architecture

```
Input (PDF / video / URL)
        │
        ▼
 extractor.py  ──► raw text (PDF) or raw audio .wav (video/URL, via ffmpeg/yt-dlp)
        │
        ▼
 transcriber.py (Whisper) ──► raw transcript + detected language
        │
        ▼
 translator.py ──► pivot to English (only if source ≠ English)
        │
        ▼
 cleaner.py (NLTK) ──► removes "umm/uhh/like" filler words, stutter repeats,
        │               tokenizes into clean sentences
        ▼
 summarizer.py (TextRank / sumy) ──► extractive summary (key sentences only)
        │
        ├──► quiz_generator.py (NLTK POS-tagging + WordNet) ──► MCQ quiz
        │
        └──► flashcard_generator.py (NLTK noun-phrase chunking) ──► flashcards
        │
        ▼
 translator.py ──► translate summary/quiz/flashcards to student's chosen
                    output language (English/Hindi/Kannada)
```

**Why "pivot through English"?** NLTK's POS tagger, WordNet, and the
TextRank summarizer are tuned for English. Rather than writing separate
NLP logic per language, non-English transcripts are translated to English
once, processed, then the *output* (summary/quiz/flashcards) is translated
back to the student's chosen language. This keeps quality consistent and
means new languages need zero new NLP code.

---

## Setup

```bash
# 1. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install ffmpeg (required for video/URL audio extraction — NOT a pip package)
#    Windows : choco install ffmpeg   (or download from ffmpeg.org, add to PATH)
#    macOS   : brew install ffmpeg
#    Linux   : sudo apt install ffmpeg

# 4. Download required NLTK data (one-time)
python setup_nltk.py

# 5. Run the app
python app.py
```

Then open **http://localhost:5000** in your browser.

The first time you process a video/URL, faster-whisper will download its
model weights (one-time, needs internet). The `base` model (used by default)
is a good balance of speed/accuracy for a laptop CPU — change
`whisper_model_size` in `pipeline.py` if you want higher accuracy
(`small`, `medium`, `large-v3`), or have a GPU (set `device="cuda"` in
`modules/transcriber.py`).

> **Windows note:** we use `faster-whisper` instead of `openai-whisper`
> specifically because `openai-whisper`'s dependencies (`numba`/`llvmlite`)
> often fail to build on Windows (missing `pkg_resources` during compile).
> `faster-whisper` ships prebuilt wheels, so `pip install` just works.

---

## Project structure

```
studybuddy/
├── app.py                     Flask routes
├── pipeline.py                Orchestrates the full pipeline
├── setup_nltk.py              One-time NLTK data downloader
├── requirements.txt
├── modules/
│   ├── languages.py           ⭐ add new languages here
│   ├── extractor.py           PDF text / video+URL → audio (ffmpeg, yt-dlp)
│   ├── transcriber.py         Whisper speech-to-text
│   ├── translator.py          English pivot translation (deep-translator)
│   ├── cleaner.py             NLTK filler-word removal
│   ├── summarizer.py          TextRank extractive summarization
│   ├── quiz_generator.py      MCQ generation from summary
│   └── flashcard_generator.py Flashcard generation from summary
├── templates/                 Jinja2 HTML (upload page, results, quiz, flashcards)
├── static/
│   ├── css/style.css          Dark/light theme (CSS variables)
│   └── js/theme.js            Theme toggle (persisted in localStorage)
├── uploads/                   Temp storage for uploaded files (auto-cleared)
└── data/                      Per-result JSON cache (swap for a DB later)
```

---

## Troubleshooting

**Use Google Drive links instead of YouTube where possible.** Drive links
go through `gdown` (a simple direct download, no bot-checks) and are far
more reliable than YouTube in practice. Just make sure the file's sharing
setting is **"Anyone with the link."**

**"Processing failed: ERROR: [youtube] ... Please sign in"**

YouTube frequently bot-checks download requests, even for normal public
videos. Two fixes:

1. **Update yt-dlp** (most common fix — YouTube changes its checks often):
   ```bash
   pip install -U yt-dlp
   ```

2. **Use your browser's cookies** — open `pipeline.py` and set:
   ```python
   YT_COOKIES_FROM_BROWSER = "chrome"   # or "firefox", "edge", etc.
   ```
   yt-dlp will then use your logged-in YouTube session to authenticate the
   download. If that doesn't work (e.g. running on a server with no
   browser), export a `cookies.txt` via a browser extension like
   *"Get cookies.txt LOCALLY"* and set `YT_COOKIES_FILE = "cookies.txt"`
   instead.

---



Open `modules/languages.py` and add one entry:

```python
SUPPORTED_LANGUAGES = {
    ...
    "ta": {"name": "Tamil", "whisper_code": "ta", "translate_code": "ta"},
}
```

That's it — the upload page dropdown, the translator, and the pipeline all
read from this dict automatically. No other code changes needed (as long
as `deep-translator` / Whisper support that language code, which covers
100+ languages already).

---

## Notes / things to extend for a stronger final-year submission

- **Storage**: results are currently cached as JSON files in `data/`.
  For a multi-user deployment, swap this for SQLite/PostgreSQL
  (SQLAlchemy) and add user accounts.
- **Async processing**: Whisper transcription can take a while for long
  lectures. For a smoother UX, move `pipeline.process_upload()` into a
  background task (Celery + Redis, or even a simple thread + polling
  endpoint) instead of blocking the request.
- **Abstractive summarization**: the current summarizer is extractive
  (TextRank) — explainable and fast. As a stretch goal / comparison
  section in your report, you could add a transformer-based abstractive
  summarizer (e.g. `facebook/bart-large-cnn` via HuggingFace) as a
  second mode.
- **Quiz difficulty**: the quiz generator currently blanks the longest
  noun in a sentence. You could extend it to generate short-answer or
  true/false questions too, for variety.
