"""
translator.py
-------------
Handles translation to/from English.

DESIGN DECISION — why "pivot through English":
    NLTK's summarizer/POS-tagger/WordNet all work best on English.
    Rather than building separate NLP pipelines per language, we:
        1. Translate non-English transcripts -> English
        2. Run the whole NLP pipeline (clean/summarize/quiz/flashcards) in English
        3. Translate the final summary/quiz/flashcards -> the student's chosen language

    This means adding a new language later needs ZERO new NLP code —
    deep-translator already supports 100+ languages. You only need to
    add the language to modules/languages.py.
"""

from deep_translator import GoogleTranslator

MAX_CHUNK_CHARS = 4500  # Google Translate has a ~5000 char request limit


def _chunk_text(text: str, size: int = MAX_CHUNK_CHARS):
    """Splits text into chunks on sentence boundaries where possible."""
    if len(text) <= size:
        return [text]

    chunks, current = [], ""
    for sentence in text.split(". "):
        if len(current) + len(sentence) < size:
            current += sentence + ". "
        else:
            chunks.append(current.strip())
            current = sentence + ". "
    if current.strip():
        chunks.append(current.strip())
    return chunks


def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Translates `text` from source_lang -> target_lang (ISO codes)."""
    if not text or not text.strip() or source_lang == target_lang:
        return text

    translator = GoogleTranslator(source=source_lang, target=target_lang)
    chunks = _chunk_text(text)
    translated_chunks = [translator.translate(chunk) for chunk in chunks]
    return " ".join(translated_chunks)


def translate_list(items, source_lang: str, target_lang: str):
    """Translates a list of strings, preserving order."""
    if source_lang == target_lang:
        return items
    return [translate_text(item, source_lang, target_lang) for item in items]


def to_english(text: str, source_lang: str) -> str:
    return translate_text(text, source_lang, "en")


def from_english(text: str, target_lang: str) -> str:
    return translate_text(text, "en", target_lang)
