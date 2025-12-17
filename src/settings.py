import json

def load_settings(filePath='src/settings.json'):
    with open(filePath, 'r', encoding='utf-8') as f:
        return json.load(f)
