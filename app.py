"""SiddAi VideoDost— cinematic Streamlit frontend.



Run from the project directory:

    uv run streamlit run streamlit_app.py



Uses the existing backend:

    main.run_pipeline

    core.rag_engine.ask_question



Note: the animated waiting panel is an activity indicator. Exact stage-by-stage

progress requires the backend to expose progress callbacks.

"""



import html

import threading

import time

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



# ---------------------------------------------------------------------

# DESIGN SYSTEM

# ---------------------------------------------------------------------



CSS = """
<style>
/* Simple, consistent colors for local and deployed Streamlit */
:root { color-scheme: dark; }
/* Hide scrollbar visually while keeping scrolling enabled */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    scrollbar-width: none !important;
    -ms-overflow-style: none !important;
}
html::-webkit-scrollbar, body::-webkit-scrollbar,
[data-testid="stAppViewContainer"]::-webkit-scrollbar,
[data-testid="stMain"]::-webkit-scrollbar,
*::-webkit-scrollbar {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
}
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: #0b1118 !important;
    color: #f1f5f9 !important;
}
[data-testid="stHeader"], [data-testid="stToolbar"] { background: #0b1118 !important; }
/* Remove sidebar and its expand/collapse controls entirely */
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
button[kind="header"] { display: none !important; }
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] {
    background-color: #0b1118 !important;
}
.block-container { max-width: 1120px; padding-top: 1.5rem; padding-bottom: 3rem; }
h1, h2, h3, h4, p, label,
[data-testid="stMarkdownContainer"] { color: #f1f5f9; }
[data-testid="stSidebar"] {
    background: #111923 !important;
    border-right: 1px solid #283443;
}
[data-testid="stSidebar"] * { color: #f1f5f9; }
input, textarea,
[data-baseweb="select"] > div,
[data-testid="stChatInput"],
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] [data-baseweb="select"] {
    background: #17212d !important;
    color: #f1f5f9 !important;
    -webkit-text-fill-color: #f1f5f9 !important;
    border-color: #354354 !important;
}
[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stChatMessage"] {
    background: #151e29 !important;
    border: 1px solid #354354 !important;
    border-radius: 10px;
}
button[kind="primary"] {
    background: #7cffb2 !important;
    color: #102018 !important;
    border: 0 !important;
}
button[kind="primary"] p { color: #102018 !important; }
[data-testid="stMain"] .stButton > button,
[data-testid="stDownloadButton"] button {
    background: #17212d !important;
    color: #f1f5f9 !important;
    border: 1px solid #354354 !important;
}
[data-testid="stMain"] .stButton > button:hover,
[data-testid="stDownloadButton"] button:hover {
    border-color: #7cffb2 !important;
}
.hero, .step, .processing-panel {
    background: #151e29;
    color: #f1f5f9;
    border: 1px solid #354354;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
}
.hero h1, .hero p, .step b, .step span,
.processing-title, .processing-subtitle, .activity-line,
.processing-chip, .small-muted, .section-label, .summary-text,
.result-title, .meta, .stat, .stat b, .eyebrow {
    color: #f1f5f9 !important;
}
.eyebrow { color: #7cffb2 !important; font-size: .8rem; margin-bottom: .5rem; }
.hero h1 { line-height: 1.15; }
.hero p, .step span, .processing-subtitle, .meta, .small-muted { color: #bdc8d5 !important; }
.step { min-height: 100px; }
.step b { display: block; margin-bottom: .4rem; }
.result-title { margin-bottom: .3rem; }
.meta { margin-bottom: 1rem; }
.stat-row { display: flex; flex-wrap: wrap; gap: .5rem; margin: .5rem 0 1rem; }
.stat { background: #17212d; border: 1px solid #354354; border-radius: 20px; padding: .4rem .7rem; }
.stTabs [data-baseweb="tab"] { color: #bdc8d5; }
.stTabs [aria-selected="true"] { color: #7cffb2 !important; }
.stTabs [data-baseweb="tab-highlight"] { background: #7cffb2; }
.summary-text { line-height: 1.7; }
.processing-top { display: flex; align-items: center; gap: 1rem; }
.processing-orb { display: none; }
.processing-track { height: 4px; background: #354354; border-radius: 5px; margin-top: 1rem; overflow: hidden; }
.processing-track span { display: block; width: 40%; height: 100%; background: #7cffb2; }
.processing-chips { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: .8rem; }
.processing-chip { background: #17212d; border: 1px solid #354354; border-radius: 6px; padding: .3rem .5rem; font-size: .8rem; }
@media (max-width: 700px) { .hero { padding: 1rem; } }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)



# ---------------------------------------------------------------------

# SESSION STATE

# ---------------------------------------------------------------------



DEFAULTS = {

    "video_result": None,

    "chat_history": [],

    "processing_error": None,

    "source_label": "",

    "processed_at": None,

    "pending_question": None,

}

for key, value in DEFAULTS.items():

    if key not in st.session_state:

        st.session_state[key] = value





def reset_video():

    st.session_state.video_result = None

    st.session_state.chat_history = []

    st.session_state.processing_error = None

    st.session_state.source_label = ""

    st.session_state.processed_at = None

    st.session_state.pending_question = None





def queue_question(question: str):

    st.session_state.pending_question = question





def build_notes_markdown(result: dict) -> str:

    return (

        f"# {result.get('title', 'SiddAi VideoDost')}\n\n"

        f"## Summary\n{result.get('summary', '')}\n\n"

        f"## Action items\n{result.get('action_items', '')}\n\n"

        f"## Key decisions\n{result.get('key_decisions', '')}\n\n"

        f"## Open questions\n{result.get('open_questions', '')}\n"

    )





def build_chat_markdown(history: list) -> str:

    lines = ["# Chat with video", ""]

    for message in history:

        who = "You" if message["role"] == "user" else "SiddAi VideoDost"

        lines.append(f"**{who}:** {message['content']}\n")

    return "\n".join(lines)





def run_pipeline_in_background(source: str, language: str, outcome: dict):

    """Run backend work off the UI thread; only write to this shared result dict."""

    try:

        outcome["result"] = run_pipeline(source=source, language=language)

    except Exception as exc:

        outcome["error"] = f"{type(exc).__name__}: {exc}"

    finally:

        outcome["done"] = True





def render_processing_panel(activity: str, elapsed_seconds: int):

    safe_activity = html.escape(activity)

    elapsed = f"{elapsed_seconds // 60:02d}:{elapsed_seconds % 60:02d}"

    st.markdown(

        f"""

        <div class="processing-panel">

          <div class="processing-top">

            <div class="processing-orb"></div>

            <div>

              <p class="processing-title">SiddAi VideoDost is building your knowledge base</p>

              <p class="processing-subtitle">Hang tight. Longer videos and first-time embedding setup can take a little while.</p>

            </div>

          </div>

          <div class="processing-track"><span></span></div>

          <div class="activity-line">✦ &nbsp;{safe_activity}</div>

          <div class="processing-chips">

            <span class="processing-chip">01 · Prepare audio</span>

            <span class="processing-chip">02 · Transcribe</span>

            <span class="processing-chip">03 · Create notes</span>

            <span class="processing-chip">04 · Index for chat</span>

          </div>

          <p class="small-muted">Elapsed time: {elapsed} · The bar is an activity animation, not an exact percentage.</p>

        </div>

        """,

        unsafe_allow_html=True,

    )





# ---------------------------------------------------------------------

# MAIN INPUTS (no sidebar)

result = st.session_state.video_result
source = ""
language = "english"
process_clicked = False

st.markdown(
    '<div class="brand"><div class="brand-mark">🎥</div>'
    '<div class="brand-name">SiddAi VideoDost</div></div>',
    unsafe_allow_html=True,
)

if result is None:
    source = st.text_input(
        "Video link or file path",
        placeholder="https://youtube.com/watch?v=...",
        key="video_source_input",
    )
    input_col, button_col = st.columns([3, 1])
    with input_col:
        language = st.selectbox(
            "Spoken language",
            options=["english", "hinglish"],
            format_func=lambda value: value.capitalize(),
            key="video_language_input",
        )
    with button_col:
        st.write("")
        st.write("")
        process_clicked = st.button(
            "✦ Process video", type="primary", use_container_width=True
        )
else:
    if st.button("← Start over"):
        reset_video()
        st.rerun()




# PROCESS VIDEO

# ---------------------------------------------------------------------



if process_clicked:

    if not source.strip():

        st.warning("Paste a YouTube link or a local file path to continue.")

    else:

        reset_video()

        outcome = {"done": False, "result": None, "error": None}

        worker = threading.Thread(

            target=run_pipeline_in_background,

            args=(source.strip(), language, outcome),

            daemon=True,

        )



        activity_messages = [

            "Preparing the video input and checking the audio source…",

            "Extracting speech and turning audio into transcript text…",

            "Reading the transcript and generating your study notes…",

            "Organizing transcript chunks so chat can retrieve relevant context…",

            "Finishing up and preparing your SiddAi VideoDost workspace…",

        ]

        start_time = time.monotonic()

        worker.start()



        waiting_area = st.empty()

        while not outcome["done"]:

            elapsed = int(time.monotonic() - start_time)

            # Rotating messages keep the interface alive, but they are

            # illustrative until the backend provides real progress events.

            phase = min(elapsed // 7, len(activity_messages) - 1)

            with waiting_area.container():

                render_processing_panel(activity_messages[phase], elapsed)

            time.sleep(0.7)



        if outcome["error"]:

            st.session_state.processing_error = outcome["error"]

        elif outcome["result"] is not None:

            st.session_state.video_result = outcome["result"]

            st.session_state.source_label = source.strip()

            st.session_state.processed_at = datetime.now()

            st.toast("Your notes are ready", icon="✅")

            st.rerun()

        else:

            st.session_state.processing_error = (

                "The pipeline finished without returning a result."

            )



# ---------------------------------------------------------------------

# ERROR STATE

# ---------------------------------------------------------------------



if st.session_state.processing_error:

    st.error(

        "SiddAi VideoDost couldn't process this video. Check the URL or file path, "

        "then try again."

    )

    with st.expander("Technical details"):

        st.code(st.session_state.processing_error)



# ---------------------------------------------------------------------

# MAIN VIEW

# ---------------------------------------------------------------------






if result is None:

    st.markdown(

        """

        <div class="hero">

          <div class="eyebrow">Your personal video study space</div>

          <h1>Turn any lecture into notes you can question.</h1>

          <p>Drop in a YouTube link or a local media file. SiddAi VideoDost creates a

          transcript, summarizes the key ideas, extracts action items, and lets

          you chat with the video content.</p>

        </div>

        """,

        unsafe_allow_html=True,

    )



    c1, c2, c3 = st.columns(3)

    c1.markdown(

        '<div class="step"><b>01 · Add a video</b>'

        '<span>Paste a link above to begin.</span></div>',

        unsafe_allow_html=True,

    )

    c2.markdown(

        '<div class="step"><b>02 · Get the notes</b>'

        '<span>Review the summary, action items, decisions, and questions.</span></div>',

        unsafe_allow_html=True,

    )

    c3.markdown(

        '<div class="step"><b>03 · Ask and learn</b>'

        '<span>Ask follow-up questions grounded in the transcript.</span></div>',

        unsafe_allow_html=True,

    )

else:

    transcript = result.get("transcript") or ""

    word_count = len(transcript.split())

    talk_minutes = max(1, round(word_count / 150))

    read_minutes = max(1, round(word_count / 220))

    processed_at = st.session_state.processed_at

    stamp = processed_at.strftime("%d %b %Y, %H:%M") if processed_at else ""

    safe_title = html.escape(str(result.get("title", "Untitled video")))



    st.markdown(

        f'<h1 class="result-title">{safe_title}</h1>'

        f'<div class="meta">Processed {html.escape(stamp)}</div>'

        '<div class="stat-row">'

        f'<span class="stat"><b>~{talk_minutes} min</b> speech</span>'

        f'<span class="stat"><b>{word_count:,}</b> words</span>'

        f'<span class="stat"><b>~{read_minutes} min</b> read</span>'

        '</div>',

        unsafe_allow_html=True,

    )



    notes_tab, transcript_tab = st.tabs(["✦ Notes", "▤ Transcript"])



    with notes_tab:

        st.markdown(

            '<div class="section-label">Summary</div>',

            unsafe_allow_html=True,

        )

        safe_summary = html.escape(str(result.get("summary", ""))).replace("\n", "<br>")

        st.markdown(

            f'<div class="summary-text">{safe_summary}</div>',

            unsafe_allow_html=True,

        )

        st.write("")



        col_a, col_b, col_c = st.columns(3)

        with col_a:

            with st.container(border=True):

                st.markdown('<div class="section-label">Action items</div>', unsafe_allow_html=True)

                st.markdown(str(result.get("action_items", "No action items found.")))

        with col_b:

            with st.container(border=True):

                st.markdown('<div class="section-label">Key decisions</div>', unsafe_allow_html=True)

                st.markdown(str(result.get("key_decisions", "No key decisions found.")))

        with col_c:

            with st.container(border=True):

                st.markdown('<div class="section-label">Open questions</div>', unsafe_allow_html=True)

                st.markdown(str(result.get("open_questions", "No open questions found.")))



        st.write("")

        st.download_button(

            "Download notes (.md)",

            data=build_notes_markdown(result),

            file_name="siddai-videodost-notes.md",

            mime="text/markdown",

        )



    with transcript_tab:

        st.text_area(

            "Full transcript",

            value=transcript,

            height=420,

            disabled=True,

            label_visibility="collapsed",

        )

        st.download_button(

            "Download transcript (.txt)",

            data=transcript,

            file_name="siddai-videodost-transcript.txt",

            mime="text/plain",

        )



    st.divider()

    st.markdown("## Ask about this video")



    if not st.session_state.chat_history:

        st.markdown(

            '<p class="chat-empty">Need a starting point? Try a suggested question.</p>',

            unsafe_allow_html=True,

        )

        suggestions = [

            "What are the main points?",

            "Explain the key concepts simply",

            "Give me 5 revision questions",

        ]

        suggestion_cols = st.columns(len(suggestions))

        for col, suggested_question in zip(suggestion_cols, suggestions):

            col.button(

                suggested_question,

                key=f"suggestion_{suggested_question}",

                on_click=queue_question,

                args=(suggested_question,),

                use_container_width=True,

            )



    for message in st.session_state.chat_history:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])



    typed_question = st.chat_input("Ask a question about this video…")

    question = typed_question or st.session_state.pending_question

    st.session_state.pending_question = None



    if question and question.strip():

        question = question.strip()

        st.session_state.chat_history.append(

            {"role": "user", "content": question}

        )

        with st.chat_message("user"):

            st.markdown(question)



        try:

            with st.chat_message("assistant"):

                with st.spinner("Searching the transcript…"):

                    answer = ask_question(result["rag_chain"], question)

                st.markdown(answer)

            st.session_state.chat_history.append(

                {"role": "assistant", "content": answer}

            )

        except Exception as error:

            error_message = f"I couldn't answer that: {error}"

            with st.chat_message("assistant"):

                st.error(error_message)

            st.session_state.chat_history.append(

                {"role": "assistant", "content": error_message}

            )



    if st.session_state.chat_history:

        st.download_button(

            "Download chat (.md)",

            data=build_chat_markdown(st.session_state.chat_history),

            file_name="siddai-videodost-chat.md",

            mime="text/markdown",

        )
