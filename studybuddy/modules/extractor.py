"""
extractor.py
------------
Turns whatever the student uploaded (PDF / video file / lecture URL)
into either:
  - plain text (for PDFs), or
  - a local .wav audio file (for videos/URLs), ready for transcriber.py

Video -> audio uses ffmpeg (must be installed on the host machine and
on PATH — see README for install instructions).
URL -> video/audio download uses yt-dlp.
"""

import os
import subprocess
import uuid
import tempfile

from PyPDF2 import PdfReader

# System temp folder, NOT a folder inside the project — this keeps files
# written here from being seen by Flask's dev-server file watcher (which
# would otherwise restart the server mid-download and reset the connection).
DEFAULT_TEMP_DIR = os.path.join(tempfile.gettempdir(), "studybuddy_uploads")


def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_audio_from_video(video_path: str, output_dir: str = None) -> str:
    """
    Uses ffmpeg to pull a mono 16kHz WAV out of a video file
    (16kHz mono is what Whisper expects — also keeps the file small).
    """
    os.makedirs(output_dir or DEFAULT_TEMP_DIR, exist_ok=True)
    output_dir = output_dir or DEFAULT_TEMP_DIR
    audio_path = os.path.join(output_dir, f"{uuid.uuid4().hex}.wav")

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-ar", "16000",
        "-ac", "1",
        "-vn",
        audio_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")

    return audio_path


def is_google_drive_url(url: str) -> bool:
    return "drive.google.com" in url


def download_from_google_drive(url: str, output_dir: str = None) -> str:
    """
    Downloads a publicly-shared Google Drive video file directly.
    Requires gdown: pip install gdown

    This is more reliable than YouTube downloads via yt-dlp — Drive
    doesn't run the same bot-detection challenges YouTube does, so this
    is the recommended URL source if you're hitting "Please sign in"
    errors with YouTube links.

    NOTE: the Drive file's sharing setting must be "Anyone with the link".
    """
    import gdown

    output_dir = output_dir or DEFAULT_TEMP_DIR
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{uuid.uuid4().hex}.mp4")

    gdown.download(url, output_path, fuzzy=True, quiet=True)

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise RuntimeError(
            "Could not download the Google Drive file. Make sure its "
            "sharing setting is 'Anyone with the link' (not restricted)."
        )

    return output_path


def download_audio_from_url(url: str, output_dir: str = None, cookies_from_browser: str = None,
                             cookies_file: str = None) -> str:
    """
    Uses yt-dlp to download a lecture video/audio from a URL (YouTube,
    Google Drive share link, etc.) and extracts it straight to WAV.
    Requires yt-dlp: pip install yt-dlp

    YouTube frequently challenges requests with a "Please sign in" /
    bot-check error, even for normal public videos. To get past this,
    pass ONE of:

      cookies_from_browser: e.g. "chrome", "firefox", "edge" — yt-dlp
          will pull cookies directly from that browser's logged-in
          YouTube session on this machine. Easiest option.

      cookies_file: path to a cookies.txt file exported via a browser
          extension (e.g. "Get cookies.txt LOCALLY"). Use this if
          cookies_from_browser doesn't work (e.g. browser is locked
          while running, or on a server with no browser installed).
    """
    import yt_dlp

    output_dir = output_dir or DEFAULT_TEMP_DIR
    os.makedirs(output_dir, exist_ok=True)
    out_template = os.path.join(output_dir, f"{uuid.uuid4().hex}.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
            "preferredquality": "192",
        }],
        "quiet": True,
        "noplaylist": True,
    }

    if cookies_from_browser:
        ydl_opts["cookiesfrombrowser"] = (cookies_from_browser,)
    elif cookies_file:
        ydl_opts["cookiefile"] = cookies_file

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # yt-dlp renames the file after postprocessing to .wav
        base = ydl.prepare_filename(info)
        wav_path = os.path.splitext(base)[0] + ".wav"

    return wav_path
