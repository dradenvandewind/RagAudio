"""Whisper transcription and SRT subtitle generation."""
from typing import Optional
import whisper

# Simple cache to avoid reloading a model on each request
_MODEL_CACHE: dict[str, "whisper.Whisper"] = {}


def _get_model(model_name: str, device: Optional[str] = None):
    """
    Load (or reuse) a Whisper model.

    Examples:
        _get_model("small")                      -> auto CPU/GPU
        _get_model("large-v3", device="cuda")     -> forced on GPU
        _get_model("medium", device="cpu")        -> forced on CPU
    """
    key = f"{model_name}:{device}"
    if key not in _MODEL_CACHE:
        if device:
            _MODEL_CACHE[key] = whisper.load_model(model_name, device=device)
        else:
            _MODEL_CACHE[key] = whisper.load_model(model_name)
    return _MODEL_CACHE[key]


def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT format HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def transcribe_to_srt(
    audio_path: str,
    output_path: str,
    language: str = "fr",
    model_name: str = "small",
    device: Optional[str] = None,
) -> dict:
    """
    Transcribe an audio file and write a .srt file.

    :return: raw Whisper result (dict with "text" and "segments")
    """
    model = _get_model(model_name, device)
    result = model.transcribe(audio_path, language=language,fp16=False, verbose=True)

    srt_lines = []
    for i, segment in enumerate(result["segments"], start=1):
        start = format_timestamp(segment["start"])
        end = format_timestamp(segment["end"])
        text = segment["text"].strip()
        srt_lines.append(f"{i}\n{start} --> {end}\n{text}\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))

    return result
