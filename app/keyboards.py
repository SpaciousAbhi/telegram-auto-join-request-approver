from __future__ import annotations

from urllib.parse import quote_plus

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.constants import SUPPORT_URL
from app.i18n import LANGUAGES, t


def rows(*buttons: InlineKeyboardButton, width: int = 1) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[list(buttons[i : i + width]) for i in range(0, len(buttons), width)])


def language_keyboard() -> InlineKeyboardMarkup:
    buttons = [InlineKeyboardButton(text=label, callback_data=f"lang:{code}") for code, label in LANGUAGES.items()]
    return rows(*buttons, width=2)


def main_menu(lang: str, bot_username: str | None) -> InlineKeyboardMarkup:
    add_url_channel = f"https://t.me/{bot_username}?startchannel=setup&admin=invite_users" if bot_username else SUPPORT_URL
    add_url_group = f"https://t.me/{bot_username}?startgroup=setup&admin=invite_users" if bot_username else SUPPORT_URL
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "add_channel"), url=add_url_channel)],
            [InlineKeyboardButton(text=t(lang, "add_group"), url=add_url_group)],
            [InlineKeyboardButton(text=t(lang, "bulk"), callback_data="bulk:start")],
            [InlineKeyboardButton(text=t(lang, "my_chats"), callback_data="chats:list")],
            [InlineKeyboardButton(text=t(lang, "settings"), callback_data="settings:menu")],
            [InlineKeyboardButton(text=t(lang, "support"), url=SUPPORT_URL)],
        ]
    )


def force_subscription_keyboard(missing: list[dict], lang: str) -> InlineKeyboardMarkup:
    keyboard = []
    for item in missing:
        title = item.get("title") or str(item.get("chat_id"))
        mode = "𝗥𝗘𝗤𝗨𝗘𝗦𝗧" if item.get("mode") == "request" else "𝗝𝗢𝗜𝗡"
        if item.get("invite_link"):
            keyboard.append([InlineKeyboardButton(text=f"{mode} • {title}", url=item["invite_link"])])
        elif item.get("username"):
            username = str(item["username"]).lstrip("@")
            keyboard.append([InlineKeyboardButton(text=f"{mode} • {title}", url=f"https://t.me/{quote_plus(username)}")])
    keyboard.append([InlineKeyboardButton(text=t(lang, "check"), callback_data="force:check")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def chats_keyboard(chats: list[dict], lang: str) -> InlineKeyboardMarkup:
    keyboard = []
    for chat in chats[:50]:
        status = "✅" if chat.get("active") else "⚠️"
        keyboard.append([InlineKeyboardButton(text=f"{status} {chat.get('title', chat['chat_id'])}", callback_data=f"chat:{chat['chat_id']}")])
    keyboard.append([InlineKeyboardButton(text=t(lang, "home"), callback_data="nav:home")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def chat_manage_keyboard(chat_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚡ 𝗔𝗣𝗣𝗥𝗢𝗩𝗘 𝗔𝗟𝗟 𝗢𝗟𝗗 𝗣𝗘𝗡𝗗𝗜𝗡𝗚 𝗥𝗘𝗤𝗨𝗘𝗦𝗧𝗦", callback_data=f"bulk:chat:{chat_id}")],
            [InlineKeyboardButton(text=t(lang, "refresh"), callback_data=f"chat:{chat_id}")],
            [InlineKeyboardButton(text=t(lang, "back"), callback_data="chats:list"), InlineKeyboardButton(text=t(lang, "home"), callback_data="nav:home")],
        ]
    )


def bulk_control_keyboard(job_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⏸ 𝗣𝗔𝗨𝗦𝗘", callback_data=f"bulk:pause:{job_id}"),
                InlineKeyboardButton(text="▶️ 𝗥𝗘𝗦𝗨𝗠𝗘", callback_data=f"bulk:resume:{job_id}"),
            ],
            [
                InlineKeyboardButton(text="⛔ 𝗦𝗧𝗢𝗣", callback_data=f"bulk:stop:{job_id}"),
                InlineKeyboardButton(text="🔄 𝗥𝗘𝗙𝗥𝗘𝗦𝗛 𝗦𝗧𝗔𝗧𝗨𝗦", callback_data=f"bulk:status:{job_id}"),
            ],
        ]
    )


def robot_keyboard(bot_username: str, payload: str, lang: str = "en") -> InlineKeyboardMarkup:
    return rows(InlineKeyboardButton(text=t(lang, "robot"), url=f"https://t.me/{bot_username}?start={payload}"))


def owner_panel_keyboard(settings: dict) -> InlineKeyboardMarkup:
    force = "𝗢𝗡" if settings.get("force_subscription_enabled") else "𝗢𝗙𝗙"
    verify = "𝗢𝗡" if settings.get("verification_enabled") else "𝗢𝗙𝗙"
    bulk = "𝗢𝗡" if settings.get("bulk_approval_enabled") else "𝗢𝗙𝗙"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🔒 𝗙𝗢𝗥𝗖𝗘 𝗦𝗨𝗕: {force}", callback_data="owner:toggle:force_subscription_enabled")],
            [InlineKeyboardButton(text=f"🛡 𝗩𝗘𝗥𝗜𝗙𝗜𝗖𝗔𝗧𝗜𝗢𝗡: {verify}", callback_data="owner:toggle:verification_enabled")],
            [InlineKeyboardButton(text=f"⚡ 𝗕𝗨𝗟𝗞 𝗔𝗣𝗣𝗥𝗢𝗩𝗔𝗟: {bulk}", callback_data="owner:toggle:bulk_approval_enabled")],
            [InlineKeyboardButton(text="➕ 𝗔𝗗𝗗 𝗙𝗢𝗥𝗖𝗘 𝗖𝗛𝗔𝗧", callback_data="owner:force:add")],
            [InlineKeyboardButton(text="📋 𝗙𝗢𝗥𝗖𝗘 𝗖𝗛𝗔𝗧𝗦", callback_data="owner:force:list")],
            [InlineKeyboardButton(text="📣 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧", callback_data="owner:broadcast")],
            [InlineKeyboardButton(text="🔄 𝗥𝗘𝗙𝗥𝗘𝗦𝗛", callback_data="owner:panel")],
        ]
    )
