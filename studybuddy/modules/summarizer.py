"""
summarizer.py
-------------
Extractive summarization using TextRank (via sumy).

Why extractive instead of a black-box abstractive model?
  - Fully explainable for a viva / project report (you can show exactly
    why each sentence was picked — it's a graph-ranking algorithm, not
    a neural net you can't inspect).
  - No heavy model download needed, runs fast on CPU.

NOTE: This always summarizes the *English* text. For Hindi/Kannada
input, the pipeline (see pipeline.py) translates the cleaned transcript
to English first, summarizes, then translates the summary back — this
keeps summarization quality consistent across languages and means you
don't need language-specific summarizer tuning for every new language.
"""

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words


def summarize_text(text: str, sentence_count: int = 8, language: str = "english"):
    """
    Returns a list of the most important sentences from `text`,
    in their original order of importance (TextRank score).
    """
    if not text or not text.strip():
        return []

    parser = PlaintextParser.from_string(text, Tokenizer(language))
    stemmer = Stemmer(language)

    summarizer = TextRankSummarizer(stemmer)
    summarizer.stop_words = get_stop_words(language)

    sentence_count = min(sentence_count, max(1, text.count(".") // 2 or 1))
    summary_sentences = summarizer(parser.document, sentence_count)

    return [str(s) for s in summary_sentences]


def summarize_to_text(text: str, sentence_count: int = 8, language: str = "english") -> str:
    return " ".join(summarize_text(text, sentence_count, language))
