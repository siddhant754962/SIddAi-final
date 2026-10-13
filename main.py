
import os
import time
import requests
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
# SUPADATA TRANSCRIPT HELPER
# ----------------------------------

def get_supadata_api_key() -> str:
    """Read the API key from environment variables or Streamlit Secrets."""
    key = os.getenv("SUPADATA_API_KEY", "").strip()

    if not key:
        try:
            import streamlit as st
            key = str(st.secrets.get("SUPADATA_API_KEY", "")).strip()
        except Exception:
            key = ""

    if not key:
        raise RuntimeError(
            "SUPADATA_API_KEY is missing. Add it in Streamlit Cloud "
            "under Manage app > Settings > Secrets."
        )

    return key


def extract_transcript_text(data: dict) -> str:
    """Extract transcript text from Supadata's response."""
    content = data.get("content", "")

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text", "")
                if text:
                    parts.append(str(text))
            elif isinstance(item, str):
                parts.append(item)

        return " ".join(parts).strip()

    return ""


def fetch_supadata_transcript(url: str) -> str:
    """Fetch a YouTube transcript without downloading its audio."""
    api_key = get_supadata_api_key()
    headers = {"x-api-key": api_key}

    response = requests.get(
        "https://api.supadata.ai/v1/transcript",
        params={
            "url": url,
            "text": "true",
            "mode": "auto",
        },
        headers=headers,
        timeout=60,
    )

    # Some transcript jobs finish immediately; others return HTTP 202.
    if response.status_code == 202:
        job_data = response.json()
        job_id = job_data.get("jobId")

        if not job_id:
            raise RuntimeError(
                f"Supadata queued the request but returned no jobId: {job_data}"
            )

        job_url = f"https://api.supadata.ai/v1/transcript/{job_id}"

        for _ in range(90):
            time.sleep(2)

            job_response = requests.get(
                job_url,
                headers=headers,
                timeout=30,
            )
            job_response.raise_for_status()
            job_data = job_response.json()

            status = str(job_data.get("status", "")).lower()

            if status in ("completed", "complete", "success"):
                break

            if status in ("failed", "error"):
                raise RuntimeError(
                    f"Supadata transcript job failed: "
                    f"{job_data.get('error', job_data)}"
                )
        else:
            raise TimeoutError(
                "Supadata transcript is taking too long. Please try again."
            )

    else:
        response.raise_for_status()
        job_data = response.json()

    transcript = extract_transcript_text(job_data)

    if not transcript:
        raise RuntimeError(
            "Supadata returned an empty transcript. Check the YouTube URL "
            "and whether a transcript is available."
        )

    return transcript


# ----------------------------------
# MAIN AI VIDEO PIPELINE
# ----------------------------------

def run_pipeline(source: str, language: str = "english") -> dict:
    print("Starting AI Video Assistant...")

    source = source.strip()

    # YouTube links use Supadata, avoiding yt-dlp audio-download 403 errors.
    if source.lower().startswith(("https://", "http://")):
        print("Fetching YouTube transcript through Supadata...")
        transcript = fetch_supadata_transcript(source)
    else:
        # Local audio/video files keep the existing transcription flow.
        print("Processing local media file...")
        chunks = process_input(source)
        transcript = transcribe_all(chunks, language)

    if not transcript or not transcript.strip():
        raise ValueError("Transcription is empty. Cannot continue.")

    print(f"Raw transcription (first 300 characters): {transcript[:300]}")

    # Generate video title
    title = generate_title(transcript)

    # Generate summary
    summary = summarize(transcript)

    # Extract useful information
    action_items = extract_action_items(transcript)
    decisions = extract_key_decisions(transcript)
    open_questions = extract_questions(transcript)

    # Build RAG chain using the transcript
    rag_chain = build_rag_chain(transcript, source)

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
    source = input("Enter YouTube URL or local file path: ").strip()

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

    # Chat with video
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
