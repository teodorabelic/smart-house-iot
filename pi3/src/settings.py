import json
from pathlib import Path

def load_settings(path: str):
    settings_path = Path(__file__).parent / path
    with open(settings_path, "r", encoding="utf-8") as f:
        return json.load(f)