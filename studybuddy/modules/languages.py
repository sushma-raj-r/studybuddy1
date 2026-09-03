"""
languages.py
------------
Single source of truth for every language the app supports.

TO ADD A NEW LANGUAGE LATER:
    Just add one entry to SUPPORTED_LANGUAGES below. Nothing else in the
    codebase needs to change — the upload form, translator, and pipeline
    all read from this dict automatically.

    Example — adding Tamil:
        "ta": {"name": "Tamil", "whisper_code": "ta", "translate_code": "ta"}

`whisper_code`   -> language code Whisper expects (ISO-639-1, mostly)
`translate_code` -> language code deep-translator / Google Translate expects
(For most languages these two are identical, but keeping them separate
avoids breakage if a language's codes ever differ between the two libs.)
"""

SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "whisper_code": "en", "translate_code": "en"},
    "hi": {"name": "Hindi",   "whisper_code": "hi", "translate_code": "hi"},
    "kn": {"name": "Kannada", "whisper_code": "kn", "translate_code": "kn"},
}

DEFAULT_LANGUAGE = "en"


def is_supported(code: str) -> bool:
    return code in SUPPORTED_LANGUAGES


def get_language_name(code: str) -> str:
    return SUPPORTED_LANGUAGES.get(code, {}).get("name", code)


def get_whisper_code(code: str) -> str:
    return SUPPORTED_LANGUAGES.get(code, {}).get("whisper_code", code)


def get_translate_code(code: str) -> str:
    return SUPPORTED_LANGUAGES.get(code, {}).get("translate_code", code)


def list_languages_for_dropdown():
    """Returns [(code, name), ...] for rendering <select> options."""
    return [(code, meta["name"]) for code, meta in SUPPORTED_LANGUAGES.items()]
