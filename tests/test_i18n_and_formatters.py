from app.i18n import LANGUAGES, t
from app.services.formatters import bulk_status
from app.services.telegram import is_joined_member


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


class Member:
    def __init__(self, status, is_member=False):
        self.status = status
        self.is_member = is_member


class Status:
    def __init__(self, value):
        self.value = value


def test_force_subscription_membership_accepts_fresh_joined_statuses():
    assert is_joined_member(Member("member"))
    assert is_joined_member(Member(Status("administrator")))
    assert is_joined_member(Member("restricted", is_member=True))
    assert not is_joined_member(Member("left"))
    assert not is_joined_member(Member("restricted", is_member=False))
