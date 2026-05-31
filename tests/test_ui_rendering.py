from types import SimpleNamespace

from app.bold import bold
from app.keyboards import label, language_keyboard, main_menu, robot_keyboard
from app.services.formatters import owner_dashboard
from app.ui import render_home_text, render_verification_request_text, render_verified_text


def _button_texts(markup):
    return [button.text for row in markup.inline_keyboard for button in row]


def test_home_text_is_personalized_and_sectioned():
    text = render_home_text(SimpleNamespace(first_name="A <B>"), "en")

    assert "A &lt;B&gt;" in text
    assert bold("JOIN REQUEST COMMAND CENTER") in text
    assert bold("AUTO APPROVAL") in text


def test_verification_copy_escapes_chat_titles_and_mentions_open_channel():
    request_text = render_verification_request_text("<VIP Channel>")
    accepted_text = render_verified_text("VIP Channel")

    assert "&lt;VIP Channel&gt;" in request_text
    assert bold("VERIFY JOIN REQUEST") in request_text
    assert "Open the Channel" in accepted_text


def test_main_menu_prioritizes_primary_user_actions():
    texts = _button_texts(main_menu("en", "test_bot"))

    assert texts[:4] == [
        label("en", "add_channel"),
        label("en", "add_group"),
        label("en", "my_chats"),
        label("en", "bulk"),
    ]


def test_settings_language_keyboard_has_home_exit():
    markup = language_keyboard(with_home=True, home_lang="en")

    assert markup.inline_keyboard[-1][0].text == label("en", "home")
    assert markup.inline_keyboard[-1][0].callback_data == "nav:home"


def test_robot_keyboard_uses_verification_language_not_robot_copy():
    button = robot_keyboard("test_bot", "verify_1_2").inline_keyboard[0][0]

    assert button.text == label("en", "verify")
    assert button.url == "https://t.me/test_bot?start=verify_1_2"


def test_owner_dashboard_is_grouped_for_scanning():
    text = owner_dashboard(
        {
            "users": 10,
            "registered": 9,
            "verified": 8,
            "connected_chats": 3,
            "active_chats": 2,
            "today_approvals": 7,
            "active_bulk_jobs": 1,
            "failed_jobs": 0,
            "force_chats": 2,
            "subscriber_trick_chats": 1,
        },
        {
            "verification_enabled": True,
            "force_subscription_enabled": False,
            "subscriber_trick_enabled": True,
            "bulk_approval_enabled": True,
            "approval_speed_per_minute": 600,
        },
    )

    assert bold("LIVE SNAPSHOT") in text
    assert bold("AUTOMATION") in text
    assert bold("OPERATIONS") in text
