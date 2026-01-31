import json
from typing import Any, Dict

def load_settings(path: str = "src/settings.json") -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
