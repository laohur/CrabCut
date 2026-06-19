import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "outputs"
ASSETS_DIR = BASE_DIR / "assets"

OUTPUT_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)

def get_output_dir():
    today = datetime.now().strftime("%Y-%m-%d")
    output_path = OUTPUT_DIR / today
    output_path.mkdir(exist_ok=True)
    return output_path

LANGUAGES = {
    "zh": "中文",
    "en": "English"
}

DEFAULT_LANG = "zh"
