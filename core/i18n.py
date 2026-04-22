"""
Internationalization module for Hexarelational Significance Platform.
Supports: en, pt_BR, zh, ja, ar (RTL)
"""

import json
import os
from pathlib import Path
from typing import Optional

LOCALES_DIR = Path(__file__).parent.parent / "locales"
SUPPORTED_LANGS = ["en", "pt_BR", "zh", "ja", "ar"]
RTL_LANGS = ["ar"]
DEFAULT_LANG = "en"

_cache: dict[str, dict[str, str]] = {}


def _load_locale(lang: str) -> dict[str, str]:
    if lang in _cache:
        return _cache[lang]
    filepath = LOCALES_DIR / f"{lang}.json"
    if not filepath.exists():
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    _cache[lang] = data
    return data


def t(key: str, lang: Optional[str] = None, **params) -> str:
    """Translate a key to the given language with parameter interpolation.
    
    Args:
        key: Translation key (e.g. "nav.dashboard")
        lang: Target language code. Falls back to DEFAULT_LANG.
        **params: Interpolation parameters (e.g. count=10 for "{count} items")
    
    Returns:
        Translated string with interpolated parameters.
    """
    if lang is None:
        lang = DEFAULT_LANG
    strings = _load_locale(lang)
    text = strings.get(key)
    if text is None:
        # Fallback to English
        if lang != DEFAULT_LANG:
            strings = _load_locale(DEFAULT_LANG)
            text = strings.get(key)
        if text is None:
            return key  # Return the key itself as last resort
    # Parameter interpolation
    if params:
        try:
            text = text.format(**params)
        except (KeyError, ValueError):
            pass
    return text


def is_rtl(lang: str) -> bool:
    """Check if the language uses right-to-left layout."""
    return lang in RTL_LANGS


def get_supported_langs() -> list[str]:
    """Return list of supported language codes."""
    return SUPPORTED_LANGS.copy()


def get_lang_label(lang: str, display_lang: str = "en") -> str:
    """Get the display name of a language in a given language."""
    labels = {
        "en": {"en": "English", "pt_BR": "Inglês", "zh": "英语", "ja": "英語", "ar": "الإنجليزية"},
        "pt_BR": {"en": "Português (BR)", "pt_BR": "Português (BR)", "zh": "葡萄牙语", "ja": "ポルトガル語", "ar": "البرتغالية"},
        "zh": {"en": "Chinese (Simplified)", "pt_BR": "Chinês", "zh": "简体中文", "ja": "簡体字中国語", "ar": "الصينية"},
        "ja": {"en": "Japanese", "pt_BR": "Japonês", "zh": "日语", "ja": "日本語", "ar": "اليابانية"},
        "ar": {"en": "Arabic", "pt_BR": "Árabe", "zh": "阿拉伯语", "ja": "アラビア語", "ar": "العربية"},
    }
    return labels.get(lang, {}).get(display_lang, lang)


def reload():
    """Clear the translation cache (useful for testing or hot-reload)."""
    _cache.clear()
