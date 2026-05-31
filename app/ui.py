from __future__ import annotations

from html import escape
from typing import Any

from app.bold import bold
from app.constants import SUPPORT_LABEL


def _name(user: Any) -> str:
    first = getattr(user, "first_name", None) or "there"
    return escape(str(first))


def _chat_title(title: Any) -> str:
    return escape(str(title or "this channel"))


def render_home_text(user: Any, lang: str | None = None) -> str:
    return (
        f"🛡 {bold('JOIN REQUEST COMMAND CENTER')}\n\n"
        f"Hello {_name(user)}, this bot keeps your channel and group entry flow clean, fast, and controlled.\n\n"
        f"✅ {bold('AUTO APPROVAL')} - new requests are handled instantly.\n"
        f"🧭 {bold('CHAT CONTROL')} - manage every connected channel or group.\n"
        f"⚡ {bold('BULK APPROVAL')} - clear stored pending requests with progress.\n\n"
        f"{bold('Choose an action below.')}\n\n"
        f"{SUPPORT_LABEL}"
    )


def render_language_text() -> str:
    return (
        f"🌐 {bold('CHOOSE YOUR LANGUAGE')}\n\n"
        "Pick the language you want for menus and status messages. You can change it later from Settings."
    )


def render_force_text(lang: str | None, missing: list[dict]) -> str:
    count = len(missing)
    broken = [item for item in missing if item.get("last_error")]
    text = (
        f"🔒 {bold('ACCESS CHECK REQUIRED')}\n\n"
        f"{count} required chat{'s' if count != 1 else ''} still need your action.\n\n"
        "Tap each channel/group below, complete the join or request step, then press Check Access."
    )
    if broken:
        text += (
            "\n\n"
            f"⚠️ {bold('OWNER ACTION NEEDED')}\n"
            "Some required chats cannot be checked right now because the bot cannot access them."
        )
    return text


def render_verification_request_text(chat_title: Any) -> str:
    return (
        f"🛡 {bold('VERIFY JOIN REQUEST')}\n\n"
        f"Your request for <b>{_chat_title(chat_title)}</b> is waiting.\n\n"
        "Tap the button below once. Approval continues immediately after verification."
    )


def render_verified_text(chat_title: Any) -> str:
    return (
        f"✅ {bold('JOIN REQUEST ACCEPTED')}\n\n"
        f"Your request for <b>{_chat_title(chat_title)}</b> has been approved.\n\n"
        "Use the Open the Channel button below. The link is prepared for this channel."
    )


def render_no_active_request_text() -> str:
    return (
        f"ℹ️ {bold('NO ACTIVE REQUEST FOUND')}\n\n"
        "This verification link is no longer active. If you still need access, send a fresh join request from the channel."
    )


def render_verification_retry_text() -> str:
    return (
        f"⏳ {bold('APPROVAL QUEUED')}\n\n"
        "Telegram did not complete the approval immediately. The bot has saved it and will retry automatically."
    )


def render_verification_terminal_text() -> str:
    return (
        f"⚠️ {bold('REQUEST NO LONGER AVAILABLE')}\n\n"
        "Telegram no longer exposes this pending request to the bot. The reason has been logged for the owner."
    )


def render_invalid_verification_text(reason: str = "invalid") -> str:
    if reason == "wrong_user":
        body = "This verification link belongs to another Telegram account."
    else:
        body = "This verification link is invalid or expired."
    return f"⚠️ {bold('VERIFICATION LINK ISSUE')}\n\n{body}"


def render_settings_text() -> str:
    return (
        f"⚙️ {bold('SETTINGS')}\n\n"
        "Choose your menu language. The bot will return you to the main screen after selection."
    )


def render_chats_list_text(chats: list[dict]) -> str:
    if not chats:
        return (
            f"📭 {bold('NO CONNECTED CHATS')}\n\n"
            "Add this bot as an admin to a channel or group to start approving join requests."
        )
    active = sum(1 for chat in chats if chat.get("active"))
    return (
        f"📊 {bold('MY CHANNELS AND GROUPS')}\n\n"
        f"{bold('Connected')}: {len(chats)}\n"
        f"{bold('Ready')}: {active}\n\n"
        "Select a chat to view status, permissions, and approval tools."
    )


def render_chat_not_found_text() -> str:
    return (
        f"⚠️ {bold('CHAT NOT FOUND')}\n\n"
        "This chat is not connected to your account or has already been removed."
    )


def render_remove_chat_text(chat: dict, chat_id: int) -> str:
    return (
        f"🗑 {bold('DEACTIVATE CHAT')}\n\n"
        f"{bold('Name')}: {_chat_title(chat.get('title'))}\n"
        f"{bold('ID')}: <code>{chat_id}</code>\n\n"
        "This stops automatic approval for this chat in your panel. It does not remove the bot from Telegram."
    )


def render_chat_removed_text() -> str:
    return (
        f"✅ {bold('CHAT DEACTIVATED')}\n\n"
        "Automatic approval is now off for this chat. You can add it again later if needed."
    )


def render_bulk_disabled_text() -> str:
    return f"⛔ {bold('BULK APPROVAL IS OFF')}\n\nEnable it from the owner panel before starting a bulk run."


def render_bulk_select_text(chats: list[dict]) -> str:
    return (
        f"⚡ {bold('SELECT BULK TARGET')}\n\n"
        f"{len(chats)} connected chats are available. Choose the chat whose stored pending requests should be processed."
    )


def render_bulk_empty_text(chat: dict | None = None) -> str:
    title = f" for <b>{_chat_title(chat.get('title'))}</b>" if chat else ""
    return (
        f"✅ {bold('QUEUE IS CLEAR')}\n\n"
        f"No stored pending requests were found{title}."
    )


def render_bulk_starting_text() -> str:
    return (
        f"⚡ {bold('BULK APPROVAL STARTING')}\n\n"
        "Preparing the queue and progress controls..."
    )


def render_job_not_found_text() -> str:
    return (
        f"⚠️ {bold('JOB NOT FOUND')}\n\n"
        "This bulk job is no longer available. Open Bulk Approval again from the main menu."
    )


def render_force_target_error_text() -> str:
    return "This required target has no usable invite link. Please contact the bot owner."
