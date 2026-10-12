
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from groq import RateLimitError
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough, RunnableLambda


# ==========================================
# 1. PROJECT PATHS
# ==========================================

PROJECT_DIR = Path(__file__).resolve().parent.parent
DOWNLOADS_DIR = PROJECT_DIR / "downloads"

TRANSCRIPT_PATH = DOWNLOADS_DIR / "transcript.txt"
OUTPUT_PATH = DOWNLOADS_DIR / "summary.txt"

load_dotenv(PROJECT_DIR / ".env")

MODEL_NAME = "openai/gpt-oss-20b"


# ==========================================
# 2. CREATE GROQ LLM
# ==========================================

def get_llm():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY not found. "
            "Please add it to your project .env file."
        )

    return ChatGroq(
        model=MODEL_NAME,
        api_key=api_key,
        temperature=0.3,
        max_retries=2,
    )


# ==========================================
# 3. RETRY HELPER
# ==========================================

def invoke_with_retry(chain, inputs, max_attempts=5):
    """Retry requests when Groq temporarily rate-limits us."""

    for attempt in range(max_attempts):
        try:
            return chain.invoke(inputs)

        except RateLimitError:
            if attempt == max_attempts - 1:
                raise

            wait_time = 5 * (attempt + 1)

            print(
                f"Rate limit reached. "
                f"Retrying in {wait_time} seconds..."
            )

            time.sleep(wait_time)


# ==========================================
# 4. SPLIT TRANSCRIPT
# ==========================================

def split_transcript(transcript: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=150,
    )

    return splitter.split_text(transcript)


# ==========================================
# 5. SUMMARIZE TRANSCRIPT
# ==========================================

def summarize(transcript: str) -> str:
    llm = get_llm()

    # Step A: Summarize individual chunks

    map_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are an expert podcast summarizer. "
            "Summarize the provided transcript segment in concise "
            "bullet points. Preserve important facts, arguments, "
            "examples, names, and conclusions. "
            "Do not invent information. Keep the summary short."
        ),
        ("human", "{text}"),
    ])

    map_chain = map_prompt | llm | StrOutputParser()

    chunks = split_transcript(transcript)
    chunk_summaries = []

    print(f"\nTranscript split into {len(chunks)} chunks.")

    for index, chunk in enumerate(chunks, start=1):
        print(f"\nSummarizing chunk {index}/{len(chunks)}...")

        result = invoke_with_retry(
            map_chain,
            {"text": chunk},
        )

        chunk_summaries.append(result)

    # Step B: Combine partial summaries

    combined = "\n\n".join(chunk_summaries)

    combined_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "Combine the following partial podcast summaries into "
            "one coherent final summary. Use clear headings and "
            "bullet points. Remove repetition, preserve important "
            "details, and do not add unsupported claims. "
            "Keep the result concise and useful."
        ),
        ("human", "{text}"),
    ])

    combined_chain = (
        RunnablePassthrough()
        | RunnableLambda(lambda x: {"text": x})
        | combined_prompt
        | llm
        | StrOutputParser()
    )

    print("\nCombining chunk summaries...")

    return invoke_with_retry(
        combined_chain,
        combined,
    )


# ==========================================
# 6. GENERATE TITLE
# ==========================================

def generate_title(transcript: str) -> str:
    llm = get_llm()

    title_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "Generate a meaningful title for this podcast or video. "
            "Use at most 8 words. Return only the title."
        ),
        ("human", "{text}"),
    ])

    title_chain = (
        RunnablePassthrough()
        | RunnableLambda(lambda x: {"text": x})
        | title_prompt
        | llm
        | StrOutputParser()
    )

    # Use a short excerpt to reduce token usage.
    title = invoke_with_retry(
        title_chain,
        transcript[:1500],
    )

    return title.strip().strip('"')


# ==========================================
# 7. MAIN EXECUTION
# ==========================================

def main():
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

    if not TRANSCRIPT_PATH.exists():
        raise FileNotFoundError(
            f"Transcript not found: {TRANSCRIPT_PATH}"
        )

    transcript = TRANSCRIPT_PATH.read_text(
        encoding="utf-8"
    ).strip()

    if not transcript:
        raise ValueError("Transcript file is empty.")

    print(f"Transcript loaded: {len(transcript)} characters")

    print("\nGenerating title...")
    title = generate_title(transcript)
    print(f"Title: {title}")

    print("\nGenerating summary...")
    summary = summarize(transcript)

    output = f"# {title}\n\n{summary}\n"

    OUTPUT_PATH.write_text(
        output,
        encoding="utf-8",
    )

    print("\n========== PODCAST SUMMARY ==========\n")
    print(summary)

    print(f"\nSummary saved to: {OUTPUT_PATH}")


