"""
cleaner.py
----------
Takes a raw transcript (from Whisper) and strips out filler sounds /
disfluencies ("uhh", "umm", "like", "you know", stutter-repeats, etc.)
so the summarizer only sees meaningful content.

Uses NLTK for tokenization + sentence segmentation.
"""

import re
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize

# Common English filler words / disfluencies heard in lecture recordings.
FILLER_WORDS = {
    "uh", "uhh", "uhm", "um", "umm", "umm.", "erm", "er", "ah", "ahh",
    "hmm", "hm", "like", "okay", "ok", "so", "basically", "actually",
    "literally", "right", "y'know", "know", "yeah", "yep", "mm", "mmm",
    "well", "i mean", "sort of", "kind of",
}

# Phrases (multi-word fillers) removed before tokenization.
FILLER_PHRASES = [
    r"\byou know\b", r"\bi mean\b", r"\bsort of\b", r"\bkind of\b",
    r"\byou see\b", r"\bwhat i mean is\b",
]


def _strip_filler_phrases(text: str) -> str:
    cleaned = text
    for phrase in FILLER_PHRASES:
        cleaned = re.sub(phrase, "", cleaned, flags=re.IGNORECASE)
    return cleaned


def _remove_stutter_repeats(tokens):
    """Removes immediate word repeats like 'the the class' -> 'the class'."""
    out = []
    for tok in tokens:
        if out and out[-1].lower() == tok.lower() and tok.isalpha():
            continue
        out.append(tok)
    return out


def clean_transcript(raw_text: str) -> str:
    """
    Full cleaning pipeline:
      1. Strip multi-word filler phrases
      2. Tokenize
      3. Drop single-word fillers
      4. Collapse stutter repeats
      5. Re-join into clean sentences
    """
    if not raw_text or not raw_text.strip():
        return ""

    text = _strip_filler_phrases(raw_text)

    sentences = sent_tokenize(text)
    cleaned_sentences = []

    for sent in sentences:
        tokens = word_tokenize(sent)
        tokens = [t for t in tokens if t.lower() not in FILLER_WORDS]
        tokens = _remove_stutter_repeats(tokens)

        if len(tokens) < 3:
            # Drop very short fragments — usually false starts, not content.
            continue

        rejoined = " ".join(tokens)
        # Fix spacing before punctuation (tokenizer separates "word ." etc.)
        rejoined = re.sub(r"\s+([.,!?;:])", r"\1", rejoined)
        # Collapse leftover punctuation artifacts left behind by removed fillers
        # e.g. "So, Like, photosynthesis" -> ",, photosynthesis" -> "photosynthesis"
        rejoined = re.sub(r"^[,;:\s]+", "", rejoined)
        rejoined = re.sub(r"[,]{2,}", ",", rejoined)
        rejoined = re.sub(r"\s*,\s*,", ",", rejoined)
        rejoined = rejoined.strip(" ,")
        if not rejoined:
            continue
        cleaned_sentences.append(rejoined.strip().capitalize())

    return " ".join(cleaned_sentences)


def get_clean_sentences(raw_text: str):
    """Returns cleaned text as a list of sentences (used by summarizer/quiz)."""
    cleaned = clean_transcript(raw_text)
    return sent_tokenize(cleaned) if cleaned else []
