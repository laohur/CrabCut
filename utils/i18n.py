import json
from pathlib import Path
from config import BASE_DIR

I18N_DIR = BASE_DIR / "i18n"

_translations = {}

def load_translations(lang: str):
    lang_file = I18N_DIR / f"{lang}.json"
    if lang_file.exists():
        with open(lang_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_text(key: str, lang: str = "zh") -> str:
    if lang not in _translations:
        _translations[lang] = load_translations(lang)
    
    keys = key.split(".")
    value = _translations.get(lang, {})
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k, key)
        else:
            return key
    return value if isinstance(value, str) else key

def translate_text(key: str, lang: str = "zh") -> str:
    return get_text(key, lang)
