"""
Téléchargement d'une vidéo Dailymotion et extraction de l'audio.

yt-dlp pilote ffmpeg en interne pour la conversion (--audio-format mp3) :
il faut donc que ffmpeg soit installé et présent dans le PATH du système
(ex: `apt install ffmpeg` / `brew install ffmpeg`).
"""
import subprocess
from pathlib import Path


def download_audio(url: str, output_basename: str) -> str:
    """
    Télécharge la piste audio d'une vidéo (Dailymotion, YouTube, etc.)
    et la convertit en mp3.

    :param url: URL de la vidéo (ex: https://www.dailymotion.com/video/xxxxx)
    :param output_basename: chemin de sortie sans extension (ex: data/audio/<job_id>)
    :return: chemin du fichier .mp3 généré
    """
    Path(output_basename).parent.mkdir(parents=True, exist_ok=True)
    output_template = f"{output_basename}.%(ext)s"

    cmd = [
        "yt-dlp",
        "-x",                       # extraction audio uniquement
        "--audio-format", "mp3",
        "--audio-quality", "0",     # meilleure qualité VBR
        "--no-playlist",
        "-o", output_template,
        url,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Échec yt-dlp lors du téléchargement de {url}:\n{result.stderr}")

    mp3_path = f"{output_basename}.mp3"
    if not Path(mp3_path).exists():
        raise RuntimeError("Fichier audio introuvable après extraction (vérifier que ffmpeg est installé).")

    return mp3_path
