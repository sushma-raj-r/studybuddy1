"""
quiz_generator.py
------------------
Generates multiple-choice quiz questions FROM THE SUMMARY ONLY
(never from the full transcript) — matches the requirement that
the quiz should test exactly what was summarized.

Approach (rule-based, explainable for viva):
  1. POS-tag each summary sentence.
  2. Pick a "key" noun (longest / most specific noun in the sentence)
     as the answer.
  3. Blank it out to build the question stem.
  4. Build distractor options from other nouns found across the summary
     (falls back to WordNet-related terms if the summary is short).
"""

import random
import nltk
from nltk import pos_tag, word_tokenize
from nltk.corpus import wordnet


def _extract_nouns(sentence: str):
    tokens = word_tokenize(sentence)
    tagged = pos_tag(tokens)
    nouns = [w for w, tag in tagged if tag in ("NN", "NNS", "NNP", "NNPS") and len(w) > 3]
    return nouns


def _wordnet_distractors(word: str, n: int = 3):
    """Pulls loosely related words from WordNet to pad out MCQ options."""
    distractors = set()
    synsets = wordnet.synsets(word)
    for syn in synsets:
        for hyper in syn.hypernyms():
            for lemma in hyper.lemmas():
                name = lemma.name().replace("_", " ")
                if name.lower() != word.lower():
                    distractors.add(name)
        if len(distractors) >= n:
            break
    return list(distractors)[:n]


def generate_quiz(summary_sentences, num_questions: int = 5):
    """
    Returns a list of question dicts:
        {
            "id": int,
            "question": "The ___ generates electricity from sunlight.",
            "options": ["cell", "panel", "engine", "turbine"],
            "correct_answer": "panel"
        }
    """
    if not summary_sentences:
        return []

    # Collect all nouns across the summary — used as a distractor pool.
    all_nouns = []
    for sent in summary_sentences:
        all_nouns.extend(_extract_nouns(sent))
    all_nouns = list(set(all_nouns))

    candidates = []
    for sent in summary_sentences:
        nouns = _extract_nouns(sent)
        if not nouns:
            continue
        # Pick the longest noun as the "key" answer — usually most specific/topical.
        answer = max(nouns, key=len)
        candidates.append((sent, answer))

    random.shuffle(candidates)
    quiz = []

    for i, (sent, answer) in enumerate(candidates[:num_questions]):
        # Build blanked question stem (case-insensitive whole-word replace, first hit only)
        question_stem = sent.replace(answer, "____", 1)
        if question_stem == sent:
            # exact match failed (case mismatch) - fallback to naive replace
            question_stem = sent.lower().replace(answer.lower(), "____", 1)

        # Build distractor pool: other nouns from summary, excluding the answer
        pool = [n for n in all_nouns if n.lower() != answer.lower()]
        random.shuffle(pool)
        distractors = pool[:3]

        # Pad with WordNet-related terms if summary vocabulary is too small
        if len(distractors) < 3:
            distractors += _wordnet_distractors(answer, 3 - len(distractors))

        # Final fallback so options are never empty
        while len(distractors) < 3:
            distractors.append(f"option-{random.randint(100,999)}")

        options = distractors[:3] + [answer]
        random.shuffle(options)

        quiz.append({
            "id": i + 1,
            "question": question_stem,
            "options": options,
            "correct_answer": answer,
        })

    return quiz
