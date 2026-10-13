# 🎥 SiddAi VideoDost — AI-Powered Video Intelligence Assistant

**Turn YouTube videos into structured knowledge with AI.**

SiddAi VideoDost is an AI-powered application that helps users understand educational videos and extract useful information without watching the entire video. It retrieves transcripts, generates concise summaries, identifies action items and key decisions, and enables interactive question-answering through Retrieval-Augmented Generation (RAG).

Built with Python and modern AI tools, the application transforms video content into searchable, actionable knowledge.

---

## ✨ Features

- **🎬 YouTube Transcript Extraction:** Retrieves video transcripts through the Supadata API, avoiding the need to download YouTube audio for URL-based processing.
- **📝 AI-Powered Summarization:** Converts lengthy video transcripts into concise, readable summaries.
- **📌 Action Item Extraction:** Identifies tasks, recommendations, and actionable steps discussed in a video.
- **🔑 Key Decision Extraction:** Highlights important decisions and conclusions.
- **❓ Open Question Detection:** Extracts questions or unresolved points from the transcript.
- **💬 Chat with Your Video:** Ask questions about the video's content and receive context-aware answers using RAG.
- **📂 Local Media Processing:** Supports a separate processing path for local audio/video files through the existing transcription pipeline.
- **🌐 Web-Based Interface:** Provides an interactive interface built with Streamlit.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Streamlit | Interactive web interface |
| Supadata API | YouTube transcript retrieval |
| Sarvam AI | Transcription for the local-media pipeline |
| LangChain / RAG components | Context-based question answering |
| Groq API | LLM-powered summarization and information extraction |
| Vector Store | Retrieval of relevant transcript content |
| yt-dlp | Media retrieval in the existing local processing pipeline |
| Pydub / FFmpeg | Audio processing and conversion |

*The exact models and vector-store implementation depend on the configuration in the project source code.*

## 🏗️ How It Works

```text
          YouTube URL / Local Media
                    |
          +---------+----------+
          |                    |
      YouTube URL          Local Media
          |                    |
     Supadata API       Audio Processing
          |                    |
      Transcript       Sarvam Transcription
          |                    |
          +---------+----------+
                    |
              AI Processing
                    |
       +------------+------------+
       |            |            |
     Summary    Action Items   Decisions
       |
   Open Questions
       |
   Transcript Vector Store
       |
    RAG Pipeline
       |
  Ask Questions About Video
```

### Processing workflow

1. The user submits a YouTube URL or a local media file.
2. For YouTube URLs, the application requests a transcript from Supadata.
3. For local media, the existing audio-processing and transcription pipeline is used.
4. The transcript is passed to the AI components.
5. The application generates a title and summary and extracts action items, key decisions, and open questions.
6. A retrieval pipeline is built using the transcript.
7. The user can ask questions and receive answers based on the video content.

## 📁 Project Structure

```text
SiddAi-VideoDost/
│
├── app.py                  # Streamlit application
├── main.py                 # Main AI processing pipeline
├── requirements.txt        # Python dependencies
├── runtime.txt             # Python runtime configuration
├── packages.txt             # System packages
│
├── core/
│   ├── transcriber.py      # Audio transcription
│   ├── summarizer.py       # Title generation and summaries
│   ├── extractor.py        # Action items, decisions, questions
│   └── rag_engine.py       # Retrieval and video Q&A
│
├── utils/
│   └── audio_processor.py  # Media processing and audio chunks
│
└── README.md
```

*This structure describes the main files used by the application; additional project files may also be present.*

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/siddhant754962/SiddAi-VideoDost.git
cd SiddAi-VideoDost
```

Replace the repository URL above if your GitHub repository has a different name.

### 2. Create a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks environment activation, you can run the virtual environment's Python executable directly instead.

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Install any additional system dependencies required by the local audio-processing workflow, including FFmpeg if needed.

### 4. Configure environment variables

Create a `.env` file in the project root for local development:

```env
SUPADATA_API_KEY=your_supadata_api_key
GROQ_API_KEY=your_groq_api_key
SARVAM_API_KEY=your_sarvam_api_key
```

Use the actual API keys from the corresponding providers. Only configure the credentials needed for the features you intend to use.

**Security:** Never commit `.env`, API keys, or private credentials to GitHub.

### 5. Run the application

```bash
streamlit run app.py
```

Open the local URL shown in the terminal, usually `http://localhost:8501`.

## 🔐 Streamlit Cloud Deployment

1. Push the project to GitHub.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/).
3. Create an app and select the repository, branch, and `app.py` as the entry point.
4. Open the app settings and configure the required secrets.

Example secrets configuration:

```toml
SUPADATA_API_KEY = "your_supadata_api_key"
GROQ_API_KEY = "your_groq_api_key"
SARVAM_API_KEY = "your_sarvam_api_key"
```

5. Save the secrets and deploy the application.

Use valid API keys and check each provider's current usage limits and pricing. Do not share secrets publicly.

## 💡 Example Use Cases

- Summarize long educational YouTube videos.
- Extract implementation steps from programming tutorials.
- Review lectures and identify important concepts.
- Convert discussions into actionable tasks.
- Ask questions about a video's transcript instead of manually searching through it.
- Create revision notes from learning material.

## 🚧 Limitations

- Transcript availability depends on the video and the transcript provider.
- Supadata API usage is subject to its current plan, credit limits, and access policies.
- AI-generated summaries and answers may contain inaccuracies and should be checked against the original material.
- Local media processing requires the appropriate API credentials and audio dependencies.
- RAG answers depend on transcript quality and the retrieval configuration.

## 🔮 Future Enhancements

- Timestamp-aware answers with links to relevant video sections.
- Export summaries and notes as PDF or Markdown.
- Support for multilingual summaries and Hinglish explanations.
- Persistent storage for previously processed videos.
- User accounts and saved video collections.
- Improved source citations for RAG answers.
- Additional transcript providers for improved reliability.

## 👨‍💻 Author

**Siddhant Kumar Patel**

- GitHub: [@siddhant754962](https://github.com/siddhant754962)
- LinkedIn: [Connect on LinkedIn](https://www.linkedin.com/in/siddhnat-kumar-patel-699b8a251)
- Portfolio: [Visit Portfolio](https://staticfile-59ccf.wasmer.app/)

## 📄 License

Choose and add an appropriate open-source license before redistributing this project. Until a license is added, do not assume that others have permission to reuse the source code.

---

**If you find this project useful, consider giving the repository a ⭐ on GitHub!**
