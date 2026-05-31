from __future__ import annotations

from urllib.parse import quote_plus

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.constants import SUPPORT_URL
from app.i18n import LANGUAGES


BUTTON_LABELS = {
    "en": {
        "add_channel": "➕ Add Channel",
        "add_group": "➕ Add Group",
        "my_chats": "📊 My Chats",
        "bulk": "⚡ Bulk Approval",
        "settings": "⚙️ Settings",
        "support": "💬 Support",
        "home": "🏠 Home",
        "back": "⬅️ Back",
        "refresh": "🔄 Refresh",
        "check": "✅ Check Access",
        "join_mode": "Join",
        "request_mode": "Request",
        "approve_pending": "⚡ Approve Pending",
        "deactivate_chat": "🗑 Deactivate",
        "confirm_deactivate": "✅ Confirm Deactivate",
        "pause": "⏸ Pause",
        "resume": "▶️ Resume",
        "stop": "⛔ Stop",
        "verify": "🛡 Verify Request",
        "done": "✅ Done",
    },
    "hi": {
        "add_channel": "➕ चैनल जोड़ें",
        "add_group": "➕ ग्रुप जोड़ें",
        "my_chats": "📊 मेरे चैट",
        "bulk": "⚡ बल्क अप्रूवल",
        "settings": "⚙️ सेटिंग्स",
        "support": "💬 सपोर्ट",
        "home": "🏠 होम",
        "back": "⬅️ वापस",
        "refresh": "🔄 रिफ्रेश",
        "check": "✅ एक्सेस चेक करें",
        "join_mode": "जॉइन",
        "request_mode": "रिक्वेस्ट",
        "approve_pending": "⚡ पेंडिंग अप्रूव करें",
        "deactivate_chat": "🗑 बंद करें",
        "confirm_deactivate": "✅ पुष्टि करें",
        "pause": "⏸ रोकें",
        "resume": "▶️ जारी करें",
        "stop": "⛔ बंद करें",
        "verify": "🛡 रिक्वेस्ट वेरिफाई करें",
        "done": "✅ पूरा",
    },
    "hinglish": {
        "add_channel": "➕ Add Channel",
        "add_group": "➕ Add Group",
        "my_chats": "📊 My Chats",
        "bulk": "⚡ Bulk Approval",
        "settings": "⚙️ Settings",
        "support": "💬 Support",
        "home": "🏠 Home",
        "back": "⬅️ Back",
        "refresh": "🔄 Refresh",
        "check": "✅ Access Check",
        "join_mode": "Join",
        "request_mode": "Request",
        "approve_pending": "⚡ Pending Approve",
        "deactivate_chat": "🗑 Deactivate",
        "confirm_deactivate": "✅ Confirm",
        "pause": "⏸ Pause",
        "resume": "▶️ Resume",
        "stop": "⛔ Stop",
        "verify": "🛡 Verify Request",
        "done": "✅ Done",
    },
    "ur": {
        "add_channel": "➕ چینل شامل کریں",
        "add_group": "➕ گروپ شامل کریں",
        "my_chats": "📊 میرے چیٹس",
        "bulk": "⚡ بلک اپروول",
        "settings": "⚙️ سیٹنگز",
        "support": "💬 سپورٹ",
        "home": "🏠 ہوم",
        "back": "⬅️ واپس",
        "refresh": "🔄 ریفریش",
        "check": "✅ رسائی چیک کریں",
        "join_mode": "جوائن",
        "request_mode": "ریکویسٹ",
        "approve_pending": "⚡ پینڈنگ اپروو کریں",
        "deactivate_chat": "🗑 غیر فعال کریں",
        "confirm_deactivate": "✅ تصدیق کریں",
        "pause": "⏸ روکیں",
        "resume": "▶️ جاری کریں",
        "stop": "⛔ بند کریں",
        "verify": "🛡 ریکویسٹ ویریفائی کریں",
        "done": "✅ مکمل",
    },
}


def label(lang: str | None, key: str) -> str:
    return BUTTON_LABELS.get(lang or "en", BUTTON_LABELS["en"]).get(key, BUTTON_LABELS["en"][key])


def _short_title(value: object, limit: int = 38) -> str:
    title = str(value or "Untitled").strip()
    if len(title) <= limit:
        return title
    return f"{title[: limit - 1]}…"


def rows(*buttons: InlineKeyboardButton, width: int = 1) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[list(buttons[i : i + width]) for i in range(0, len(buttons), width)])


def home_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return rows(InlineKeyboardButton(text=label(lang, "home"), callback_data="nav:home"))


def language_keyboard(with_home: bool = False, home_lang: str = "en") -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text=label_text, callback_data=f"lang:{code}") for code, label_text in pair]
        for pair in (list(LANGUAGES.items())[i : i + 2] for i in range(0, len(LANGUAGES), 2))
    ]
    if with_home:
        keyboard.append([InlineKeyboardButton(text=label(home_lang, "home"), callback_data="nav:home")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def main_menu(lang: str, bot_username: str | None) -> InlineKeyboardMarkup:
    add_url_channel = f"https://t.me/{bot_username}?startchannel=setup&admin=invite_users" if bot_username else SUPPORT_URL
    add_url_group = f"https://t.me/{bot_username}?startgroup=setup&admin=invite_users" if bot_username else SUPPORT_URL
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label(lang, "add_channel"), url=add_url_channel)],
            [InlineKeyboardButton(text=label(lang, "add_group"), url=add_url_group)],
            [InlineKeyboardButton(text=label(lang, "my_chats"), callback_data="chats:list")],
            [InlineKeyboardButton(text=label(lang, "bulk"), callback_data="bulk:start")],
            [
                InlineKeyboardButton(text=label(lang, "settings"), callback_data="settings:menu"),
                InlineKeyboardButton(text=label(lang, "support"), url=SUPPORT_URL),
            ],
        ]
    )


def force_subscription_keyboard(missing: list[dict], lang: str) -> InlineKeyboardMarkup:
    keyboard = []
    for item in missing:
        title = _short_title(item.get("title") or item.get("chat_id"))
        mode = label(lang, "request_mode") if item.get("mode") == "request" else label(lang, "join_mode")
        if item.get("invite_link"):
            keyboard.append([InlineKeyboardButton(text=f"{mode} • {title}", url=item["invite_link"])])
        elif item.get("username"):
            username = str(item["username"]).lstrip("@")
            keyboard.append([InlineKeyboardButton(text=f"{mode} • {title}", url=f"https://t.me/{quote_plus(username)}")])
        else:
            keyboard.append([InlineKeyboardButton(text=f"⚠️ {mode} • {title}", callback_data="force:target_error")])
    keyboard.append([InlineKeyboardButton(text=label(lang, "check"), callback_data="force:check")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def chats_keyboard(chats: list[dict], lang: str) -> InlineKeyboardMarkup:
    keyboard = []
    for chat in chats[:50]:
        status = "✅" if chat.get("active") else "⚠️"
        keyboard.append([InlineKeyboardButton(text=f"{status} {_short_title(chat.get('title', chat['chat_id']))}", callback_data=f"chat:{chat['chat_id']}")])
    keyboard.append([InlineKeyboardButton(text=label(lang, "home"), callback_data="nav:home")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def chat_manage_keyboard(chat_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label(lang, "approve_pending"), callback_data=f"bulk:chat:{chat_id}")],
            [InlineKeyboardButton(text=label(lang, "refresh"), callback_data=f"chat:{chat_id}")],
            [InlineKeyboardButton(text=label(lang, "deactivate_chat"), callback_data=f"chat:remove:{chat_id}")],
            [InlineKeyboardButton(text=label(lang, "back"), callback_data="chats:list")],
        ]
    )


def remove_chat_keyboard(chat_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label(lang, "confirm_deactivate"), callback_data=f"chat:remove_confirm:{chat_id}")],
            [InlineKeyboardButton(text=label(lang, "back"), callback_data=f"chat:{chat_id}")],
        ]
    )


def bulk_control_keyboard(job_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=label("en", "pause"), callback_data=f"bulk:pause:{job_id}"),
                InlineKeyboardButton(text=label("en", "resume"), callback_data=f"bulk:resume:{job_id}"),
            ],
            [
                InlineKeyboardButton(text=label("en", "stop"), callback_data=f"bulk:stop:{job_id}"),
                InlineKeyboardButton(text=label("en", "refresh"), callback_data=f"bulk:status:{job_id}"),
            ],
        ]
    )


def robot_keyboard(bot_username: str, payload: str, lang: str = "en") -> InlineKeyboardMarkup:
    return rows(InlineKeyboardButton(text=label(lang, "verify"), url=f"https://t.me/{bot_username}?start={payload}"))


def force_mode_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Join Mode", callback_data=f"owner:force:mode:{chat_id}:join"),
                InlineKeyboardButton(text="Request Mode", callback_data=f"owner:force:mode:{chat_id}:request"),
            ],
            [InlineKeyboardButton(text="✖️ Cancel", callback_data="owner:panel")],
        ]
    )


def subscriber_trick_keyboard(settings: dict) -> InlineKeyboardMarkup:
    enabled = "ON" if settings.get("subscriber_trick_enabled") else "OFF"
    required = "Required" if settings.get("subscriber_trick_required") else "Optional"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"👑 Status: {enabled}", callback_data="owner:toggle:subscriber_trick_enabled")],
            [InlineKeyboardButton(text=f"🧩 Mode: {required}", callback_data="owner:toggle:subscriber_trick_required")],
            [InlineKeyboardButton(text="➕ Add Channel", callback_data="owner:sub:add")],
            [InlineKeyboardButton(text="📋 List Channels", callback_data="owner:sub:list")],
            [InlineKeyboardButton(text="✏️ Edit Message", callback_data="owner:sub:message")],
            [InlineKeyboardButton(text="⬅️ Back", callback_data="owner:panel")],
        ]
    )


def subscriber_join_keyboard(chats: list[dict], required: bool) -> InlineKeyboardMarkup:
    keyboard = []
    for chat in chats:
        url = chat.get("invite_link") or (f"https://t.me/{chat['username'].lstrip('@')}" if chat.get("username") else None)
        if url:
            keyboard.append([InlineKeyboardButton(text=f"👑 {_short_title(chat.get('title', chat['chat_id']))}", url=url)])
    if not required:
        keyboard.append([InlineKeyboardButton(text=label("en", "done"), callback_data="nav:home")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def owner_panel_keyboard(settings: dict) -> InlineKeyboardMarkup:
    force = "ON" if settings.get("force_subscription_enabled") else "OFF"
    verify = "ON" if settings.get("verification_enabled") else "OFF"
    bulk = "ON" if settings.get("bulk_approval_enabled") else "OFF"
    sub = "ON" if settings.get("subscriber_trick_enabled") else "OFF"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🔒 Force Sub: {force}", callback_data="owner:toggle:force_subscription_enabled")],
            [InlineKeyboardButton(text=f"🛡 Verification: {verify}", callback_data="owner:toggle:verification_enabled")],
            [InlineKeyboardButton(text=f"⚡ Bulk Approval: {bulk}", callback_data="owner:toggle:bulk_approval_enabled")],
            [InlineKeyboardButton(text=f"👑 Subscriber Trick: {sub}", callback_data="owner:sub:panel")],
            [
                InlineKeyboardButton(text="🧠 System Health", callback_data="owner:health"),
                InlineKeyboardButton(text="📣 Broadcast", callback_data="owner:broadcast"),
            ],
            [
                InlineKeyboardButton(text="➕ Force Chat", callback_data="owner:force:add"),
                InlineKeyboardButton(text="📋 Force Chats", callback_data="owner:force:list"),
            ],
            [InlineKeyboardButton(text="🔄 Refresh", callback_data="owner:panel")],
        ]
    )


def owner_health_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧪 Audit Connected Chats", callback_data="owner:audit_chats")],
            [InlineKeyboardButton(text="🔄 Refresh", callback_data="owner:health")],
            [InlineKeyboardButton(text="⬅️ Back", callback_data="owner:panel")],
        ]
    )
