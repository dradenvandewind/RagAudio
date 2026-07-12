from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    base_dir: Path = Path("data")
    default_whisper_model: str = "medium"
    default_language: str = "fr"

    @property
    def audio_dir(self) -> Path:
        return self.base_dir / "audio"

    @property
    def srt_dir(self) -> Path:
        return self.base_dir / "srt"

    @property
    def index_dir(self) -> Path:
        return self.base_dir / "index"

    def ensure_dirs(self) -> None:
        for d in (self.audio_dir, self.srt_dir, self.index_dir):
            d.mkdir(parents=True, exist_ok=True)

    class Config:
        env_prefix = "APP_"


settings = Settings()
