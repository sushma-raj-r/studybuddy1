"""
transcriber.py
--------------
Speech-to-text using faster-whisper (CTranslate2-based reimplementation
of OpenAI Whisper).

IMPORTANT: This is the one part of the pipeline that genuinely needs
audio ML, not NLTK — NLTK has no speech recognition capability.

Why faster-whisper instead of openai-whisper?
    openai-whisper depends on numba/llvmlite, which try to build from
    source on Windows and frequently fail (missing pkg_resources /
    setuptools during the build). faster-whisper ships prebuilt wheels
    for Windows/Mac/Linux, installs cleanly with plain `pip install`,
    and runs faster on CPU too.

Model size trade-off (pick in config.py / pipeline.py):
    "tiny"   -> fastest, least accurate, fine for a demo
    "base"   -> good default for a project laptop (CPU)
    "small"  -> better accuracy, slower on CPU
    "medium"/"large-v3" -> best accuracy, needs GPU for reasonable speed

First run will download the model weights (one-time, needs internet).
"""

from faster_whisper import WhisperModel

_model_cache = {}


def _get_model(model_size: str = "base"):
    if model_size not in _model_cache:
        # compute_type="int8" keeps this fast and light on CPU-only laptops.
        # Switch device="cuda" if you have a GPU available.
        _model_cache[model_size] = WhisperModel(model_size, device="cpu", compute_type="int8")
    return _model_cache[model_size]


def transcribe_audio(audio_path: str, language: str = None, model_size: str = "base"):
    """
    Transcribes audio at `audio_path`.

    `language`: whisper language code (e.g. "en", "hi", "kn"), or None
                to let Whisper auto-detect the spoken language.

    Returns: {"text": str, "detected_language": str}
    """
    model = _get_model(model_size)

    segments, info = model.transcribe(audio_path, language=language)
    text = " ".join(segment.text.strip() for segment in segments)

    return {
        "text": text.strip(),
        "detected_language": info.language or (language or "en"),
    }
