"""
flashcard_generator.py
-----------------------
Builds flashcards (front = key term, back = the sentence explaining it)
from the summary — using NLTK noun-phrase chunking to find the "term"
for the front of the card.
"""

import nltk
from nltk import pos_tag, word_tokenize, RegexpParser

# Grammar: an optional determiner/adjective run followed by 1+ nouns = noun phrase
NP_GRAMMAR = r"NP: {<DT>?<JJ>*<NN.*>+}"


def _extract_key_phrase(sentence: str) -> str:
    tokens = word_tokenize(sentence)
    tagged = pos_tag(tokens)
    parser = RegexpParser(NP_GRAMMAR)
    tree = parser.parse(tagged)

    noun_phrases = []
    for subtree in tree.subtrees(filter=lambda t: t.label() == "NP"):
        phrase = " ".join(word for word, tag in subtree.leaves())
        noun_phrases.append(phrase)

    if not noun_phrases:
        return sentence.split()[0] if sentence.split() else "Concept"

    # Longest noun phrase is usually the most specific/topical term.
    return max(noun_phrases, key=len)


def generate_flashcards(summary_sentences):
    """
    Returns a list of flashcard dicts:
        {"id": int, "front": "solar panel", "back": "A solar panel converts sunlight..."}
    """
    flashcards = []
    seen_fronts = set()

    for i, sent in enumerate(summary_sentences):
        term = _extract_key_phrase(sent).strip().lower()
        if not term or term in seen_fronts:
            continue
        seen_fronts.add(term)
        flashcards.append({
            "id": len(flashcards) + 1,
            "front": term.capitalize(),
            "back": sent.strip(),
        })

    return flashcards
