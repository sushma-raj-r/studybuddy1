"""
pipeline.py
-----------
Orchestrates the full flow:

    Input (PDF / video file / URL)
        -> text (via extractor + transcriber)
        -> English text (via translator, if needed)
        -> cleaned text (via cleaner, strips filler words)
        -> summary (via summarizer)
        -> quiz + flashcards (from summary only)
        -> translated back to student's chosen output language
"""

import os

from modules import extractor, transcriber, cleaner, summarizer
from modules import quiz_generator, flashcard_generator, translator, languages

# ---- yt-dlp auth config ----
# If you hit "Please sign in" errors downloading from YouTube, set ONE of
# these (see modules/extractor.py for details), e.g.:
#   YT_COOKIES_FROM_BROWSER = "chrome"
YT_COOKIES_FROM_BROWSER = None   # e.g. "chrome", "firefox", "edge"
YT_COOKIES_FILE = None           # e.g. "cookies.txt"


def process_upload(input_type: str, input_path_or_url: str, output_language: str = "en",
                    whisper_model_size: str = "base", num_quiz_questions: int = 5):
    """
    input_type: "pdf" | "video" | "url"
    input_path_or_url: local file path (pdf/video) or a lecture URL
    output_language: language code student wants results in (from modules/languages.py)

    Returns a dict with transcript, summary, quiz, flashcards — all in output_language.
    """
    if not languages.is_supported(output_language):
        output_language = languages.DEFAULT_LANGUAGE

    detected_language = "en"

    # ---- Step 1: get raw text ----
    if input_type == "pdf":
        raw_text = extractor.extract_text_from_pdf(input_path_or_url)

    elif input_type in ("video", "url"):
        if input_type == "video":
            audio_path = extractor.extract_audio_from_video(input_path_or_url)
        elif extractor.is_google_drive_url(input_path_or_url):
            # Google Drive links: download the video file, then extract
            # audio the same way we do for direct video uploads. More
            # reliable than YouTube — no bot-check gauntlet to fight.
            video_path = extractor.download_from_google_drive(input_path_or_url)
            audio_path = extractor.extract_audio_from_video(video_path)
            try:
                os.remove(video_path)
            except OSError:
                pass
        else:
            audio_path = extractor.download_audio_from_url(
                input_path_or_url,
                cookies_from_browser=YT_COOKIES_FROM_BROWSER,
                cookies_file=YT_COOKIES_FILE,
            )

        result = transcriber.transcribe_audio(audio_path, model_size=whisper_model_size)
        raw_text = result["text"]
        detected_language = result["detected_language"]

        # clean up temp audio file
        try:
            os.remove(audio_path)
        except OSError:
            pass
    else:
        raise ValueError(f"Unsupported input_type: {input_type}")

    if not raw_text.strip():
        raise ValueError("No text/speech could be extracted from the input.")

    # ---- Step 2: pivot to English for NLP processing ----
    working_text = raw_text
    if detected_language != "en":
        working_text = translator.to_english(raw_text, detected_language)

    # ---- Step 3: clean filler words/sounds ----
    clean_sentences = cleaner.get_clean_sentences(working_text)
    clean_text = " ".join(clean_sentences)

    # ---- Step 4: summarize (English, extractive TextRank) ----
    summary_sentences_en = summarizer.summarize_text(clean_text, sentence_count=8)

    # ---- Step 5: quiz + flashcards, generated from the SUMMARY ONLY ----
    quiz_en = quiz_generator.generate_quiz(summary_sentences_en, num_questions=num_quiz_questions)
    flashcards_en = flashcard_generator.generate_flashcards(summary_sentences_en)

    # ---- Step 6: translate everything to the student's chosen output language ----
    summary_out = translator.translate_list(summary_sentences_en, "en", output_language)

    quiz_out = []
    for q in quiz_en:
        quiz_out.append({
            "id": q["id"],
            "question": translator.translate_text(q["question"], "en", output_language),
            "options": translator.translate_list(q["options"], "en", output_language),
            "correct_answer": translator.translate_text(q["correct_answer"], "en", output_language),
        })

    flashcards_out = []
    for c in flashcards_en:
        flashcards_out.append({
            "id": c["id"],
            "front": translator.translate_text(c["front"], "en", output_language),
            "back": translator.translate_text(c["back"], "en", output_language),
        })

    return {
        "detected_language": detected_language,
        "output_language": output_language,
        "raw_transcript": raw_text,
        "summary": summary_out,
        "quiz": quiz_out,
        "flashcards": flashcards_out,
    }
