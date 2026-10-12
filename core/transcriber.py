
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from pydub import AudioSegment

PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_URL = "https://api.sarvam.ai/speech-to-text"
SARVAM_MODEL = "saaras:v4"
PIECE_SECONDS = 25


def transcribe_piece(audio: AudioSegment, index: int, total: int) -> str:
    """Transcribe one short audio piece into Roman Hinglish."""
    piece_path = PROJECT_DIR / "downloads" / f"sarvam_piece_{index}.wav"

    try:
        audio.export(piece_path, format="wav")

        with open(piece_path, "rb") as audio_file:
            response = requests.post(
                SARVAM_URL,
                headers={"api-subscription-key": SARVAM_API_KEY},
                files={
                    "file": (
                        piece_path.name,
                        audio_file,
                        "audio/wav",
                    )
                },
                data={
                    "model": SARVAM_MODEL,
                    "mode": "translit",
                    "language_code": "hi-IN",
                },
                timeout=120,
            )

        if not response.ok:
            print(f"Sarvam error {response.status_code}: {response.text}")
            response.raise_for_status()

        text = response.json().get("transcript", "").strip()
        print(f"  Piece {index}/{total} completed")
        return text

    finally:
        if piece_path.exists():
            piece_path.unlink()


def transcribe_chunk_sarvam(chunk_path: str) -> str:
    """Split a WAV chunk into 25-second pieces and transcribe them."""
    if not SARVAM_API_KEY:
        raise RuntimeError(
            "SARVAM_API_KEY missing. Check your project-root .env file."
        )

    audio = AudioSegment.from_file(chunk_path)
    piece_ms = PIECE_SECONDS * 1000
    total = (len(audio) + piece_ms - 1) // piece_ms
    transcripts = []

    for index, start in enumerate(range(0, len(audio), piece_ms), start=1):
        piece = audio[start:start + piece_ms]
        text = transcribe_piece(piece, index, total)

        if text:
            transcripts.append(text)

    return " ".join(transcripts)


def transcribe_all(chunks: list, language: str = "hinglish") -> str:
    """Transcribe all chunks and combine them into one transcript."""
    print("Using Sarvam AI for Roman Hinglish transcription.")

    transcripts = []

    for index, chunk in enumerate(chunks, start=1):
        print(f"\nTranscribing chunk {index}/{len(chunks)}...")
        text = transcribe_chunk_sarvam(str(chunk))

        if text:
            transcripts.append(text)

    print("\nTranscription complete.")
    return "\n".join(transcripts)


