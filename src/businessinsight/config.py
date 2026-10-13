"""Configuration management for BusinessInsight AI."""

import os
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


if "GEMINI_API_KEY" in os.environ and "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    from pydantic import BaseModel as BaseSettings

    class SettingsConfigDict:
        def __init__(self, **kwargs):
            pass


class AppSettings(BaseSettings):
    """Application settings with environment variable support."""


    google_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"


    dataset_path: Path = Path("data/raw/superstore.csv")


    report_output_dir: Path = Path("outputs/reports")
    charts_output_dir: Path = Path("outputs/charts")


    log_level: str = "INFO"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    streamlit_server_port: int = 8501


    max_verification_rounds: int = 2
    max_recommendations: int = 5


    max_csv_bytes: int = 50 * 1024 * 1024

    if hasattr(BaseSettings, "model_config"):
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )

    def __init__(self, **values):
        super().__init__(**values)

        if not self.google_api_key:
            self.google_api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if "GEMINI_MODEL" in os.environ:
            self.gemini_model = os.environ["GEMINI_MODEL"]
        if "DATASET_PATH" in os.environ:
            self.dataset_path = Path(os.environ["DATASET_PATH"])
        if "REPORT_OUTPUT_DIR" in os.environ:
            self.report_output_dir = Path(os.environ["REPORT_OUTPUT_DIR"])
        if "CHARTS_OUTPUT_DIR" in os.environ:
            self.charts_output_dir = Path(os.environ["CHARTS_OUTPUT_DIR"])
        if "MAX_VERIFICATION_ROUNDS" in os.environ:
            self.max_verification_rounds = int(os.environ["MAX_VERIFICATION_ROUNDS"])


        self.report_output_dir.mkdir(parents=True, exist_ok=True)
        self.charts_output_dir.mkdir(parents=True, exist_ok=True)


settings = AppSettings()
