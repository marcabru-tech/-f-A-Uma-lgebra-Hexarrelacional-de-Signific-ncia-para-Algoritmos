"""Tests for core/i18n module."""

import json
import os
import sys
import unittest
from pathlib import Path

# Ensure core is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.i18n import t, is_rtl, get_supported_langs, get_lang_label, reload


class TestI18nBasic(unittest.TestCase):
    def test_supported_langs(self):
        langs = get_supported_langs()
        self.assertIn("en", langs)
        self.assertIn("pt_BR", langs)
        self.assertIn("zh", langs)
        self.assertIn("ja", langs)
        self.assertIn("ar", langs)
        self.assertEqual(len(langs), 5)

    def test_english_fallback(self):
        result = t("app.name", lang="en")
        self.assertEqual(result, "Hexarelational Significance Algebra")

    def test_portuguese(self):
        result = t("nav.dashboard", lang="pt_BR")
        self.assertEqual(result, "Painel")

    def test_chinese(self):
        result = t("nav.dashboard", lang="zh")
        self.assertEqual(result, "仪表盘")

    def test_japanese(self):
        result = t("nav.dashboard", lang="ja")
        self.assertEqual(result, "ダッシュボード")

    def test_arabic(self):
        result = t("nav.dashboard", lang="ar")
        self.assertEqual(result, "لوحة التحكم")

    def test_missing_key_returns_key(self):
        result = t("nonexistent.key", lang="en")
        self.assertEqual(result, "nonexistent.key")

    def test_missing_key_fallback_to_english(self):
        result = t("nonexistent.key", lang="pt_BR")
        self.assertEqual(result, "nonexistent.key")

    def test_default_lang_is_english(self):
        reload()
        result = t("app.name")
        self.assertEqual(result, "Hexarelational Significance Algebra")


class TestI18nRTL(unittest.TestCase):
    def test_arabic_is_rtl(self):
        self.assertTrue(is_rtl("ar"))

    def test_english_is_not_rtl(self):
        self.assertFalse(is_rtl("en"))

    def test_chinese_is_not_rtl(self):
        self.assertFalse(is_rtl("zh"))

    def test_japanese_is_not_rtl(self):
        self.assertFalse(is_rtl("ja"))

    def test_portuguese_is_not_rtl(self):
        self.assertFalse(is_rtl("pt_BR"))


class TestI18nParams(unittest.TestCase):
    def test_plan_runs_per_day(self):
        result = t("plan.runs_per_day", lang="en", count=10)
        self.assertIn("10", result)

    def test_plan_runs_per_day_pt(self):
        result = t("plan.runs_per_day", lang="pt_BR", count=5)
        self.assertIn("5", result)

    def test_error_timeout(self):
        result = t("error.run.timeout", lang="en", seconds=30)
        self.assertIn("30", result)

    def test_error_input_limit(self):
        result = t("error.run.input_too_large", lang="pt_BR", kb=100)
        self.assertIn("100", result)


class TestLangLabels(unittest.TestCase):
    def test_english_label_in_english(self):
        self.assertEqual(get_lang_label("en", "en"), "English")

    def test_portuguese_label_in_portuguese(self):
        self.assertEqual(get_lang_label("pt_BR", "pt_BR"), "Português (BR)")

    def test_chinese_label_in_chinese(self):
        self.assertEqual(get_lang_label("zh", "zh"), "简体中文")

    def test_japanese_label_in_japanese(self):
        self.assertEqual(get_lang_label("ja", "ja"), "日本語")

    def test_arabic_label_in_arabic(self):
        self.assertEqual(get_lang_label("ar", "ar"), "العربية")


if __name__ == "__main__":
    unittest.main()
