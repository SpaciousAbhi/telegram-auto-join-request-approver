from app.i18n import LANGUAGES, t
from app.services.formatters import bulk_status


def test_language_fallback_uses_english_key():
    assert "चैनल" in t("hi", "add_channel")
    assert "چینل" in t("ur", "add_channel")
    assert t("unknown", "choose_language") == "𝗖𝗛𝗢𝗢𝗦𝗘 𝗬𝗢𝗨𝗥 𝗟𝗔𝗡𝗚𝗨𝗔𝗚𝗘"


def test_language_buttons_are_required_four():
    assert set(LANGUAGES) == {"en", "hi", "hinglish", "ur"}


def test_bulk_status_percentage():
    text = bulk_status({"total": 100, "approved": 25, "failed": 5, "skipped": 0, "status": "running"})
    assert "30.0%" in text
    assert "𝗥𝗨𝗡𝗡𝗜𝗡𝗚" in text
