
from pathlib import Path
import os
import shutil
import subprocess

import yt_dlp
from pydub import AudioSegment


BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

COOKIE_FILE = BASE_DIR / "cookies.txt"


def ensure_deno() -> str:
    """Find Deno or install it if it is missing."""
    deno_path = shutil.which("deno")

    if deno_path:
        return deno_path

    deno_home = Path.home() / ".deno"
    deno_path = deno_home / "bin" / "deno"

    if deno_path.is_file():
        return str(deno_path)

    env = os.environ.copy()
    env["DENO_INSTALL"] = str(deno_home)

    subprocess.run(
        [
            "sh",
            "-c",
            "curl -fsSL https://deno.land/install.sh | sh",
        ],
        check=True,
        env=env,
        timeout=180,
    )

    if not deno_path.is_file():
        raise RuntimeError("Deno installation failed.")

    return str(deno_path)


def download_youtube_audio(url: str) -> str:
    output_path = str(DOWNLOAD_DIR / "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "noplaylist": True,
        "quiet": False,
        "retries": 2,
        "socket_timeout": 30,
    }

    if COOKIE_FILE.is_file() and COOKIE_FILE.stat().st_size > 0:
        ydl_opts["cookiefile"] = str(COOKIE_FILE)

    deno_path = ensure_deno()
    ydl_opts["js_runtimes"] = {
        "deno": {"path": deno_path}
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    video_id = info["id"]

    downloaded_files = list(DOWNLOAD_DIR.glob(f"{video_id}.*"))
    downloaded_files = [
        path for path in downloaded_files
        if not path.stem.endswith("_clean")
        and "_chunk_" not in path.stem
    ]

    if not downloaded_files:
        raise FileNotFoundError(
            f"Downloaded audio not found for video: {video_id}"
        )

    return str(downloaded_files[0])


def convert_to_wav(input_path: str) -> str:
    input_file = Path(input_path)
    output_path = input_file.with_name(
        input_file.stem + "_clean.wav"
    )

    audio = AudioSegment.from_file(str(input_file))
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(str(output_path), format="wav")

    return str(output_path)


def chunk_audio(
    wav_path: str,
    chunk_minutes: int = 10,
) -> list[str]:
    if chunk_minutes <= 0:
        raise ValueError("chunk_minutes must be greater than zero")

    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000
    chunks = []

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start:start + chunk_ms]

        chunk_path = Path(wav_path).with_name(
            f"{Path(wav_path).stem}_chunk_{i}.wav"
        )

        chunk.export(str(chunk_path), format="wav")
        chunks.append(str(chunk_path))

    return chunks


def process_input(source: str) -> list[str]:
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
