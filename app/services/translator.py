"""SRT subtitle translation using an Ollama chat model (e.g. Qwen2.5)."""
import os
import re
from dataclasses import dataclass

import httpx

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_TRANSLATE_MODEL = os.getenv("OLLAMA_TRANSLATE_MODEL", "qwen2.5:7b")

# Delimiter unlikely to appear in normal subtitle text, used to keep
# segment alignment when translating multiple lines in a single LLM call.
_SEP = "\u2726"  # ✦

# Number of subtitle segments translated per LLM call. Smaller chunks are
# more robust (less risk of the model breaking alignment) but slower.
_CHUNK_SIZE = 20


@dataclass
class SrtBlock:
    index: int
    start: str
    end: str
    text: str


_SRT_BLOCK_RE = re.compile(
    r"(\d+)\s*\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\s*\n(.*?)(?=\n\d+\s*\n\d{2}:\d{2}:\d{2},\d{3}|\Z)",
    re.DOTALL,
)


def parse_srt(srt_text: str) -> list[SrtBlock]:
    blocks = []
    for m in _SRT_BLOCK_RE.finditer(srt_text.strip() + "\n"):
        index, start, end, text = m.groups()
        blocks.append(SrtBlock(int(index), start, end, text.strip()))
    return blocks


def render_srt(blocks: list[SrtBlock]) -> str:
    lines = []
    for b in blocks:
        lines.append(f"{b.index}\n{b.start} --> {b.end}\n{b.text}\n")
    return "\n".join(lines)


def _translate_chunk(texts: list[str], target_lang: str) -> list[str]:
    joined = f" {_SEP} ".join(t.replace("\n", " ") for t in texts)

    prompt = (
        f"Traduis les segments de sous-titres suivants vers la langue "
        f"'{target_lang}'. Les segments sont séparés par le symbole {_SEP}. "
        f"Réponds UNIQUEMENT avec les traductions, dans le même ordre, "
        f"séparées par le même symbole {_SEP}. Ne rajoute aucun commentaire, "
        f"aucune numérotation, aucune explication.\n\n{joined}"
    )

    resp = httpx.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json={
            "model": OLLAMA_TRANSLATE_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
        timeout=300,
    )
    resp.raise_for_status()
    content = resp.json()["message"]["content"].strip()

    translated = [t.strip() for t in content.split(_SEP)]

    if len(translated) != len(texts):
        # Alignment broke (model added/removed a separator). Fall back to
        # translating each segment individually for this chunk.
        return [_translate_chunk([t], target_lang)[0] for t in texts]

    return translated


def translate_srt_file(srt_path: str, output_path: str, target_lang: str = "en") -> None:
    with open(srt_path, "r", encoding="utf-8") as f:
        blocks = parse_srt(f.read())

    if not blocks:
        raise ValueError("Fichier SRT vide ou illisible")

    for i in range(0, len(blocks), _CHUNK_SIZE):
        chunk = blocks[i : i + _CHUNK_SIZE]
        translated_texts = _translate_chunk([b.text for b in chunk], target_lang)
        for b, translated in zip(chunk, translated_texts):
            b.text = translated

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(render_srt(blocks))