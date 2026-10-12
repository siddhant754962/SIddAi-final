
import hashlib
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import chromadb
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


# Project paths
PROJECT_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = str(PROJECT_DIR / "vector_db")

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def get_embeddings():
    """Load the existing lightweight embedding model on CPU."""
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def get_video_id(source: str) -> str:
    """Create a stable ID from a YouTube URL or local file path."""
    source = source.strip()

    if not source:
        raise ValueError("Video URL or source cannot be empty.")

    parsed = urlparse(source)

    if parsed.hostname in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.strip("/").split("/")[0]

    elif parsed.hostname and (
        parsed.hostname.endswith("youtube.com")
        or parsed.hostname.endswith("youtube-nocookie.com")
    ):
        video_id = parse_qs(parsed.query).get("v", [""])[0]

        if not video_id:
            match = re.match(
                r"^/(?:shorts|embed|live)/([^/?]+)",
                parsed.path,
            )
            video_id = match.group(1) if match else ""

    else:
        # Stable identifier for a local audio file or another source.
        video_id = hashlib.sha256(
            str(Path(source).resolve()).encode("utf-8")
        ).hexdigest()[:20]

    if not video_id:
        video_id = hashlib.sha256(source.encode("utf-8")).hexdigest()[:20]

    return video_id


def get_collection_name(video_id: str) -> str:
    """Give every video its own valid ChromaDB collection."""
    safe_id = hashlib.sha256(
        video_id.encode("utf-8")
    ).hexdigest()[:20]

    return f"video_{safe_id}"


def build_vector_store(transcript: str, video_id: str) -> Chroma:
    """Store transcript chunks in a collection dedicated to one video."""

    if not transcript or not transcript.strip():
        raise ValueError("Transcript is empty.")

    if not video_id or not video_id.strip():
        raise ValueError("A video ID is required.")

    collection_name = get_collection_name(video_id.strip())

    print(f"Processing video: {video_id}")
    print(f"Using collection: {collection_name}")
    print("Splitting transcript...")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )

    chunks = splitter.split_text(transcript)

    if not chunks:
        raise ValueError("No transcript chunks were created.")

    docs = [
        Document(
            page_content=chunk,
            metadata={
                "chunk_index": i,
                "video_id": video_id.strip(),
            },
        )
        for i, chunk in enumerate(chunks)
    ]

    print(f"Creating embeddings for {len(docs)} chunks...")

    # Replace only this video's old collection when reprocessing it.
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    try:
        client.delete_collection(name=collection_name)
        print("Removed previous data for this video.")
    except Exception as exc:
        # A missing collection is expected for a video processed for
        # the first time. Do not hide unrelated ChromaDB errors.
        if "does not exist" not in str(exc).lower() and not isinstance(
            exc, ValueError
        ):
            raise

    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=get_embeddings(),
        collection_name=collection_name,
        persist_directory=CHROMA_DIR,
    )

    print("Video-specific vector store created successfully!")
    return vector_store


def load_vector_store(video_id: str) -> Chroma:
    """Load only the vector collection belonging to the selected video."""

    if not video_id or not video_id.strip():
        raise ValueError("A video ID is required to load a vector store.")

    if not Path(CHROMA_DIR).exists():
        raise FileNotFoundError(
            "Vector database not found. Process a video first."
        )

    collection_name = get_collection_name(video_id.strip())
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    try:
        client.get_collection(name=collection_name)
    except Exception as exc:
        raise FileNotFoundError(
            "No vector database found for this video. "
            "Process this video first."
        ) from exc

    return Chroma(
        collection_name=collection_name,
        embedding_function=get_embeddings(),
        persist_directory=CHROMA_DIR,
    )


def get_retriever(vector_store: Chroma, k: int = 6):
    """Return a retriever for the selected video's collection."""

    if k < 1:
        raise ValueError("k must be at least 1.")

    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )
