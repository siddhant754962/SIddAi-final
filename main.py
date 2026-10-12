
from dotenv import load_dotenv

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import (
    extract_action_items,
    extract_key_decisions,
    extract_questions,
)
from core.rag_engine import build_rag_chain, ask_question


load_dotenv()


# ----------------------------------
# MAIN AI VIDEO PIPELINE
# ----------------------------------

def run_pipeline(source: str, language: str = "english") -> dict:
    print("Starting AI Video Assistant...")

    # 1. Process YouTube URL or local file
    chunks = process_input(source)

    # 2. Transcribe audio
    transcript = transcribe_all(chunks, language)

    if not transcript or not transcript.strip():
        raise ValueError("Transcription is empty. Cannot continue.")

    print(
        f"Raw transcription (first 300 characters): "
        f"{transcript[:300]}"
    )

    # 3. Generate video title
    title = generate_title(transcript)

    # 4. Generate summary
    summary = summarize(transcript)

    # 5. Extract useful information
    action_items = extract_action_items(transcript)

    decisions = extract_key_decisions(transcript)

    open_questions = extract_questions(transcript)

    # 6. Build RAG chain using the transcript
    rag_chain = build_rag_chain(transcript, source)

    # 7. Return all results
    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_items,
        "key_decisions": decisions,
        "open_questions": open_questions,
        "rag_chain": rag_chain,
    }


# ----------------------------------
# CLI ENTRY POINT
# ----------------------------------

if __name__ == "__main__":

    source = input(
        "Enter YouTube URL or local file path: "
    ).strip()

    language = (
        input("Language (english/hinglish): ").strip()
        or "english"
    )

    result = run_pipeline(source, language)

    print("\n" + "=" * 60)
    print(f"📌 Title: {result['title']}")
    print(f"\n📋 Summary:\n{result['summary']}")
    print(f"\n✅ Action Items:\n{result['action_items']}")
    print(f"\n🔑 Key Decisions:\n{result['key_decisions']}")
    print(f"\n❓ Open Questions:\n{result['open_questions']}")
    print("=" * 60)

    # ----------------------------------
    # PHASE 2 — CHAT WITH VIDEO
    # ----------------------------------

    print("\n💬 Chat with your video (type 'exit' to quit)\n")

    rag_chain = result["rag_chain"]

    while True:
        question = input("You: ").strip()

        if question.lower() in ["exit", "quit", "q"]:
            print("👋 Goodbye!")
            break

        if not question:
            continue

        try:
            answer = ask_question(rag_chain, question)
            print(f"\n🤖 Assistant: {answer}\n")

        except Exception as error:
            print(f"\n❌ Error answering question: {error}\n")
