
from pathlib import Path
import shutil

import yt_dlp
from pydub import AudioSegment


BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

COOKIE_FILE = BASE_DIR / "cookies.txt"


def download_youtube_audio(url: str) -> str:
    """Download audio from a single YouTube video."""

    url = url.strip()
    if not url:
        raise ValueError("YouTube URL cannot be empty.")

    output_template = str(DOWNLOAD_DIR / "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": False,
        "retries": 2,
        "socket_timeout": 30,
        "noprogress": True,
    }

    if COOKIE_FILE.is_file() and COOKIE_FILE.stat().st_size > 0:
        ydl_opts["cookiefile"] = str(COOKIE_FILE)

    deno_path = shutil.which("deno")
    if deno_path:
        ydl_opts["js_runtimes"] = {
            "deno": {"path": deno_path}
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    if not info or not info.get("id"):
        raise RuntimeError("Could not retrieve YouTube video information.")

    video_id = info["id"]

    downloaded_files = [
        path
        for path in DOWNLOAD_DIR.glob(f"{video_id}.*")
        if path.is_file()
        and path.stem == video_id
        and not path.name.endswith(".part")
    ]

    if not downloaded_files:
        raise FileNotFoundError(
            f"Downloaded audio not found for video: {video_id}"
        )

    return str(downloaded_files[0])


def convert_to_wav(input_path: str) -> str:
    """Convert audio to mono, 16 kHz WAV."""

    input_file = Path(input_path).resolve()

    if not input_file.is_file():
        raise FileNotFoundError(f"Audio file not found: {input_file}")

    output_path = input_file.with_name(
        f"{input_file.stem}_clean.wav"
    )

    audio = AudioSegment.from_file(str(input_file))
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(str(output_path), format="wav")

    return str(output_path)


def chunk_audio(
    wav_path: str,
    chunk_minutes: int = 10,
) -> list[str]:
    """Split WAV audio into chunks."""

    if chunk_minutes <= 0:
        raise ValueError("chunk_minutes must be greater than zero.")

    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000
    chunks = []

    wav_file = Path(wav_path)

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start:start + chunk_ms]

        chunk_path = wav_file.with_name(
            f"{wav_file.stem}_chunk_{i}.wav"
        )

        chunk.export(str(chunk_path), format="wav")
        chunks.append(str(chunk_path))

    return chunks


def process_input(source: str) -> list[str]:
    """Accept a YouTube URL or a local audio file."""

    source = source.strip()

    if not source:
        raise ValueError(
            "Please provide a YouTube URL or local audio file path."
        )

    if source.startswith(("https://", "http://")):
        audio_path = download_youtube_audio(source)
    else:
        audio_path = str(Path(source).resolve())

        if not Path(audio_path).is_file():
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

    clean_wav_path = convert_to_wav(audio_path)
    return chunk_audio(clean_wav_path)
