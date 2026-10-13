"""SiddAi VideoDost — simple, deployment-friendly Streamlit app."""

from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from main import run_pipeline
from core.rag_engine import ask_question

load_dotenv()

st.set_page_config(
    page_title="SiddAi VideoDost",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Simple fixed theme: dark background, light text, mint buttons.
st.markdown(
    """
    <style>
    :root { color-scheme: dark; }
    html, body, .stApp, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], [data-testid="stMainBlockContainer"] {
        background: #0b1118 !important;
        color: #f1f5f9 !important;
    }
    [data-testid="stHeader"] { background: #0b1118 !important; }
    [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {
        display: none !important;
    }
    .block-container { max-width: 1100px; padding-top: 1.5rem; padding-bottom: 3rem; }
    h1, h2, h3, h4, p, label, [data-testid="stMarkdownContainer"] {
        color: #f1f5f9;
    }
    input, textarea, [data-baseweb="select"] > div {
        background: #17212d !important;
        color: #f1f5f9 !important;
        -webkit-text-fill-color: #f1f5f9 !important;
        border-color: #354354 !important;
    }
    button[kind="primary"] {
        background: #7cffb2 !important;
        color: #102018 !important;
        border: 0 !important;
    }
    button[kind="primary"] p { color: #102018 !important; }
    .stButton > button, [data-testid="stDownloadButton"] button {
        background: #17212d !important;
        color: #f1f5f9 !important;
        border: 1px solid #354354 !important;
    }
    .stButton > button:hover, [data-testid="stDownloadButton"] button:hover {
        border-color: #7cffb2 !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"], [data-testid="stChatMessage"] {
        background: #151e29 !important;
        border: 1px solid #354354 !important;
        border-radius: 10px;
    }
    .hero, .step {
        background: #151e29; border: 1px solid #354354;
        border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem;
    }
    .muted { color: #bdc8d5 !important; }
    .stat-row { display: flex; flex-wrap: wrap; gap: .5rem; margin: .5rem 0 1rem; }
    .stat { background: #17212d; border: 1px solid #354354; border-radius: 20px; padding: .4rem .7rem; }
    .stTabs [aria-selected="true"] { color: #7cffb2 !important; }
    .stTabs [data-baseweb="tab-highlight"] { background: #7cffb2; }
    /* Hide the scrollbar visually but keep scrolling enabled. */
    html, body, *, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        scrollbar-width: none !important; -ms-overflow-style: none !important;
    }
    *::-webkit-scrollbar { width: 0 !important; height: 0 !important; display: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Session state
for key, default in {
    "video_result": None,
    "chat_history": [],
    "processing_error": None,
    "source_label": "",
    "processed_at": None,
    "pending_question": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def reset_video():
    st.session_state.video_result = None
    st.session_state.chat_history = []
    st.session_state.processing_error = None
    st.session_state.source_label = ""
    st.session_state.processed_at = None
    st.session_state.pending_question = None


def notes_markdown(result):
    return (
        f"# {result.get('title', 'SiddAi VideoDost')}\n\n"
        f"## Summary\n{result.get('summary', '')}\n\n"
        f"## Action items\n{result.get('action_items', '')}\n\n"
        f"## Key decisions\n{result.get('key_decisions', '')}\n\n"
        f"## Open questions\n{result.get('open_questions', '')}\n"
    )


def chat_markdown(history):
    lines = ["# Chat with video", ""]
    for message in history:
        who = "You" if message["role"] == "user" else "SiddAi VideoDost"
        lines.append(f"**{who}:** {message['content']}\n")
    return "\n".join(lines)


st.markdown("# 🎥 SiddAi VideoDost")
st.markdown("<p class='muted'>Turn a video into notes you can question.</p>", unsafe_allow_html=True)

result = st.session_state.video_result

if result is None:
    source = st.text_input(
        "YouTube link or local media file path",
        placeholder="https://youtube.com/watch?v=...",
        key="video_source_input",
    )
    language = st.selectbox(
        "Spoken language",
        options=["english", "hinglish"],
        format_func=lambda value: value.capitalize(),
        key="video_language_input",
    )
    process_clicked = st.button("✦ Process video", type="primary", use_container_width=True)

    st.markdown(
        """
        <div class="hero">
          <h3>How it works</h3>
          <p class="muted">1. Add a video · 2. Get study notes · 3. Ask questions about its content.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if process_clicked:
        if not source.strip():
            st.warning("Paste a YouTube link or local file path first.")
        else:
            st.session_state.processing_error = None
            try:
                with st.spinner("Processing video and preparing your notes… this may take a while."):
                    processed_result = run_pipeline(source=source.strip(), language=language)
                if not processed_result:
                    raise RuntimeError("The pipeline finished without returning a result.")
                st.session_state.video_result = processed_result
                st.session_state.source_label = source.strip()
                st.session_state.processed_at = datetime.now()
                st.session_state.chat_history = []
                st.rerun()
            except Exception as exc:
                st.session_state.processing_error = f"{type(exc).__name__}: {exc}"

else:
    if st.button("← Start over"):
        reset_video()
        st.rerun()

if st.session_state.processing_error:
    st.error("SiddAi VideoDost couldn't process this video. Check the URL or file path, then try again.")
    with st.expander("Technical details"):
        st.code(st.session_state.processing_error)

# Video results
result = st.session_state.video_result
if result:
    transcript = result.get("transcript") or ""
    word_count = len(transcript.split())
    speech_minutes = max(1, round(word_count / 150))
    read_minutes = max(1, round(word_count / 220))
    processed_at = st.session_state.processed_at
    stamp = processed_at.strftime("%d %b %Y, %H:%M") if processed_at else ""

    st.title(str(result.get("title") or "Untitled video"))
    st.caption(f"Processed {stamp}" if stamp else "Video processed")
    st.markdown(
        f"<div class='stat-row'><span class='stat'>~{speech_minutes} min speech</span>"
        f"<span class='stat'>{word_count:,} words</span><span class='stat'>~{read_minutes} min read</span></div>",
        unsafe_allow_html=True,
    )

    notes_tab, transcript_tab = st.tabs(["✦ Notes", "▤ Transcript"])
    with notes_tab:
        st.subheader("Summary")
        st.write(result.get("summary") or "No summary returned.")
        col1, col2, col3 = st.columns(3)
        with col1:
            with st.container(border=True):
                st.subheader("Action items")
                st.write(result.get("action_items") or "No action items found.")
        with col2:
            with st.container(border=True):
                st.subheader("Key decisions")
                st.write(result.get("key_decisions") or "No key decisions found.")
        with col3:
            with st.container(border=True):
                st.subheader("Open questions")
                st.write(result.get("open_questions") or "No open questions found.")
        st.download_button(
            "Download notes (.md)", notes_markdown(result),
            file_name="siddai-videodost-notes.md", mime="text/markdown",
        )

    with transcript_tab:
        st.text_area("Full transcript", value=transcript, height=420, disabled=True)
        st.download_button(
            "Download transcript (.txt)", transcript,
            file_name="siddai-videodost-transcript.txt", mime="text/plain",
        )

    st.divider()
    st.subheader("Ask about this video")
    if not st.session_state.chat_history:
        st.caption("Try a suggested question:")
        suggestions = [
            "What are the main points?",
            "Explain the key concepts simply",
            "Give me 5 revision questions",
        ]
        suggestion_cols = st.columns(3)
        for col, suggestion in zip(suggestion_cols, suggestions):
            with col:
                if st.button(suggestion, key=f"suggestion_{suggestion}", use_container_width=True):
                    st.session_state.pending_question = suggestion
                    st.rerun()

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    typed_question = st.chat_input("Ask a question about this video…")
    question = typed_question or st.session_state.pending_question
    st.session_state.pending_question = None

    if question and question.strip():
        question = question.strip()
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        try:
            with st.chat_message("assistant"):
                with st.spinner("Searching the transcript…"):
                    answer = ask_question(result["rag_chain"], question)
                st.markdown(answer)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
        except Exception as exc:
            error_message = f"I couldn't answer that: {exc}"
            with st.chat_message("assistant"):
                st.error(error_message)
            st.session_state.chat_history.append({"role": "assistant", "content": error_message})

    if st.session_state.chat_history:
        st.download_button(
            "Download chat (.md)", chat_markdown(st.session_state.chat_history),
            file_name="siddai-videodost-chat.md", mime="text/markdown",
        )
