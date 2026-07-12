"""
Download a Dailymotion video and extract its audio.

yt-dlp drives ffmpeg internally for conversion (--audio-format mp3),
so ffmpeg must be installed and available in the system PATH
(e.g. `apt install ffmpeg` / `brew install ffmpeg`).
"""
import asyncio
from pathlib import Path


async def download_audio(url: str, output_basename: str) -> str:
    """
    Download the audio track of a video (Dailymotion, YouTube, etc.)
    and convert it to mp3.

    :param url: Video URL (e.g. https://www.dailymotion.com/video/xxxxx)
    :param output_basename: output path without extension (e.g. data/audio/<job_id>)
    :return: generated .mp3 file path
    """
    Path(output_basename).parent.mkdir(parents=True, exist_ok=True)
    output_template = f"{output_basename}.%(ext)s"

    cmd = [
        "yt-dlp",
        "-x",                       # extract audio only
        "--audio-format", "mp3",
        "--audio-quality", "0",     # highest VBR quality
        "--no-playlist",
        "-o", output_template,
        url,
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(
            f"yt-dlp failed while downloading {url}:\n{stderr.decode(errors='replace')}"
        )

    mp3_path = f"{output_basename}.mp3"
    if not Path(mp3_path).exists():
        raise RuntimeError("Audio file not found after extraction (check that ffmpeg is installed).")
    return mp3_path