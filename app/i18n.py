from __future__ import annotations

from app.bold import bold
from app.constants import SUPPORT_LABEL

LANGUAGES = {
    "en": "🇬🇧 𝗘𝗡𝗚𝗟𝗜𝗦𝗛",
    "hi": "🇮🇳 𝗛𝗜𝗡𝗗𝗜",
    "hinglish": "🇮🇳 𝗛𝗜𝗡𝗚𝗟𝗜𝗦𝗛",
    "ur": "🇵🇰 𝗨𝗥𝗗𝗨",
}

TEXT = {
    "en": {
        "choose_language": "𝗖𝗛𝗢𝗢𝗦𝗘 𝗬𝗢𝗨𝗥 𝗟𝗔𝗡𝗚𝗨𝗔𝗚𝗘",
        "start": (
            "𝗝𝗨𝗦𝗧 𝗔𝗗𝗗 𝗧𝗛𝗜𝗦 𝗕𝗢𝗧 𝗧𝗢 𝗬𝗢𝗨𝗥 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗢𝗥 𝗚𝗥𝗢𝗨𝗣 — "
            "𝗡𝗘𝗪 𝗝𝗢𝗜𝗡 𝗥𝗘𝗤𝗨𝗘𝗦𝗧𝗦 𝗪𝗜𝗟𝗟 𝗕𝗘 𝗔𝗖𝗖𝗘𝗣𝗧𝗘𝗗 𝗔𝗨𝗧𝗢𝗠𝗔𝗧𝗜𝗖𝗔𝗟𝗟𝗬.\n\n"
            f"𝗦𝗨𝗣𝗣𝗢𝗥𝗧: {SUPPORT_LABEL}"
        ),
        "add_channel": "➕ 𝗔𝗗𝗗 𝗧𝗢 𝗖𝗛𝗔𝗡𝗡𝗘𝗟",
        "add_group": "➕ 𝗔𝗗𝗗 𝗧𝗢 𝗚𝗥𝗢𝗨𝗣",
        "bulk": "⚡ 𝗕𝗨𝗟𝗞 𝗔𝗣𝗣𝗥𝗢𝗩𝗘 𝗢𝗟𝗗 𝗥𝗘𝗤𝗨𝗘𝗦𝗧𝗦",
        "my_chats": "📊 𝗠𝗬 𝗖𝗛𝗔𝗡𝗡𝗘𝗟𝗦 / 𝗚𝗥𝗢𝗨𝗣𝗦",
        "support": "🔗 𝗝𝗢𝗜𝗡 𝗩𝗘𝗡𝗢𝗠 𝗦𝗧𝗢𝗡𝗘 𝗡𝗘𝗧𝗪𝗢𝗥𝗞",
        "settings": "⚙️ 𝗦𝗘𝗧𝗧𝗜𝗡𝗚𝗦",
        "home": "🏠 𝗛𝗢𝗠𝗘",
        "back": "⬅️ 𝗕𝗔𝗖𝗞",
        "refresh": "🔄 𝗥𝗘𝗙𝗥𝗘𝗦𝗛",
        "cancel": "✖️ 𝗖𝗔𝗡𝗖𝗘𝗟",
        "force_title": "🔒 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘 𝗥𝗘𝗤𝗨𝗜𝗥𝗘𝗗 𝗖𝗛𝗔𝗡𝗡𝗘𝗟𝗦",
        "force_body": "𝗝𝗼𝗶𝗻 𝗼𝗿 𝗿𝗲𝗾𝘂𝗲𝘀𝘁 𝘁𝗼 𝗷𝗼𝗶𝗻 𝘁𝗵𝗲 𝗺𝗶𝘀𝘀𝗶𝗻𝗴 𝗰𝗵𝗮𝘁𝘀 𝗯𝗲𝗹𝗼𝘄, 𝘁𝗵𝗲𝗻 𝗽𝗿𝗲𝘀𝘀 𝗰𝗵𝗲𝗰𝗸.",
        "check": "✅ 𝗖𝗛𝗘𝗖𝗞 𝗔𝗖𝗖𝗘𝗦𝗦",
        "verified": "✅ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝘃𝗲𝗿𝗶𝗳𝗶𝗲𝗱 𝗻𝗼𝘄. 𝗬𝗼𝘂𝗿 𝗿𝗲𝗾𝘂𝗲𝘀𝘁 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗮𝗰𝗰𝗲𝗽𝘁𝗲𝗱. 𝗬𝗼𝘂 𝗰𝗮𝗻 𝗻𝗼𝘄 𝗼𝗽𝗲𝗻 {chat_title}.",
        "robot": "✅ 𝗜’𝗠 𝗡𝗢𝗧 𝗔 𝗥𝗢𝗕𝗢𝗧",
        "need_add_first": "⚠️ 𝗙𝗶𝗿𝘀𝘁 𝗮𝗱𝗱 𝘁𝗵𝗶𝘀 𝗯𝗼𝘁 𝘁𝗼 𝘆𝗼𝘂𝗿 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝗼𝗿 𝗴𝗿𝗼𝘂𝗽.",
        "no_chats": "📭 𝗡𝗼 𝗰𝗼𝗻𝗻𝗲𝗰𝘁𝗲𝗱 𝗰𝗵𝗮𝘁𝘀 𝘆𝗲𝘁.",
    },
    "hi": {
        "choose_language": "𝗔𝗣𝗡𝗜 𝗕𝗛𝗔𝗦𝗛𝗔 𝗖𝗛𝗨𝗡𝗜𝗬𝗘",
        "start": "𝗕𝗢𝗧 𝗞𝗢 𝗔𝗣𝗡𝗘 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗬𝗔 𝗚𝗥𝗢𝗨𝗣 𝗠𝗘𝗜𝗡 𝗔𝗗𝗗 𝗞𝗔𝗥𝗘𝗜𝗡 — 𝗡𝗔𝗬𝗜 𝗝𝗢𝗜𝗡 𝗥𝗘𝗤𝗨𝗘𝗦𝗧𝗦 𝗔𝗨𝗧𝗢𝗠𝗔𝗧𝗜𝗖 𝗔𝗖𝗖𝗘𝗣𝗧 𝗛𝗢𝗡𝗚𝗜.",
    },
    "hinglish": {
        "choose_language": "𝗔𝗣𝗡𝗜 𝗟𝗔𝗡𝗚𝗨𝗔𝗚𝗘 𝗖𝗛𝗢𝗢𝗦𝗘 𝗞𝗔𝗥𝗢",
        "start": "𝗕𝗔𝗦 𝗜𝗦 𝗕𝗢𝗧 𝗞𝗢 𝗔𝗣𝗡𝗘 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗬𝗔 𝗚𝗥𝗢𝗨𝗣 𝗠𝗘𝗜𝗡 𝗔𝗗𝗗 𝗞𝗔𝗥𝗢 — 𝗡𝗘𝗪 𝗝𝗢𝗜𝗡 𝗥𝗘𝗤𝗨𝗘𝗦𝗧𝗦 𝗔𝗨𝗧𝗢 𝗔𝗣𝗣𝗥𝗢𝗩𝗘 𝗛𝗢 𝗝𝗔𝗬𝗘𝗡𝗚𝗜.",
    },
    "ur": {
        "choose_language": "𝗔𝗣𝗡𝗜 𝗭𝗔𝗕𝗔𝗡 𝗠𝗨𝗡𝗧𝗔𝗞𝗛𝗔𝗕 𝗞𝗔𝗥𝗘𝗜𝗡",
        "start": "𝗕𝗢𝗧 𝗞𝗢 𝗔𝗣𝗡𝗘 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗬𝗔 𝗚𝗥𝗢𝗨𝗣 𝗠𝗘𝗜𝗡 𝗔𝗗𝗗 𝗞𝗔𝗥𝗘𝗜𝗡 — 𝗡𝗔𝗬𝗜 𝗝𝗢𝗜𝗡 𝗥𝗘𝗤𝗨𝗘𝗦𝗧𝗦 𝗔𝗨𝗧𝗢𝗠𝗔𝗧𝗜𝗖 𝗔𝗖𝗖𝗘𝗣𝗧 𝗛𝗢𝗡𝗚𝗜.",
    },
}

COMMON_FALLBACK_KEYS = ["add_channel", "add_group", "bulk", "my_chats", "support", "settings", "home", "back", "refresh", "cancel", "force_title", "force_body", "check", "verified", "robot", "need_add_first", "no_chats"]


def t(lang: str | None, key: str, **kwargs: object) -> str:
    lang = lang if lang in TEXT else "en"
    value = TEXT.get(lang, {}).get(key) or TEXT["en"].get(key) or bold(key.replace("_", " ").upper())
    return value.format(**kwargs)
