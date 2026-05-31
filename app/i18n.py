from __future__ import annotations

from app.bold import bold
from app.constants import SUPPORT_LABEL

LANGUAGES = {
    "en": "🇬🇧 English",
    "hi": "🇮🇳 हिंदी",
    "hinglish": "🇮🇳 Hinglish",
    "ur": "🇵🇰 اردو",
}

TEXT = {
    "en": {
        "choose_language": "Choose your language",
        "start": (
            "Add this bot to your channel or group. New join requests will be approved automatically.\n\n"
            f"{SUPPORT_LABEL}"
        ),
        "add_channel": "➕ Add Channel",
        "add_group": "➕ Add Group",
        "bulk": "⚡ Bulk Approval",
        "my_chats": "📊 My Channels / Groups",
        "support": "💬 Support",
        "settings": "⚙️ Settings",
        "home": "🏠 Home",
        "back": "⬅️ Back",
        "refresh": "🔄 Refresh",
        "cancel": "✖️ Cancel",
        "confirm": "✅ Confirm",
        "force_title": "🔒 Complete Required Channels",
        "force_body": "Join or request access to the required chats below, then press Check Access.",
        "check": "✅ Check Access",
        "verified": "✅ Your join request has been accepted.",
        "open_channel": "Open the Channel",
        "robot": "🛡 Verify Request",
        "need_add_first": "⚠️ Add this bot to a channel or group first.\n\nOpen /start anytime to return home.",
        "no_chats": "📭 No connected channels or groups yet.",
        "join_mode": "Join",
        "request_mode": "Request",
    },
    "hi": {
        "choose_language": "अपनी भाषा चुनें",
        "start": (
            "इस बोट को अपने चैनल या ग्रुप में जोड़ें। नई जॉइन रिक्वेस्ट अपने-आप स्वीकार होंगी।\n\n"
            f"{SUPPORT_LABEL}"
        ),
        "add_channel": "➕ चैनल जोड़ें",
        "add_group": "➕ ग्रुप जोड़ें",
        "bulk": "⚡ बल्क अप्रूवल",
        "my_chats": "📊 मेरे चैनल / ग्रुप",
        "support": "💬 सपोर्ट",
        "settings": "⚙️ सेटिंग्स",
        "home": "🏠 होम",
        "back": "⬅️ वापस",
        "refresh": "🔄 रिफ्रेश",
        "cancel": "✖️ रद्द करें",
        "confirm": "✅ पुष्टि करें",
        "force_title": "🔒 जरूरी चैनल पूरे करें",
        "force_body": "नीचे दिए गए चैनल/ग्रुप जॉइन करें या रिक्वेस्ट भेजें, फिर Check Access दबाएं।",
        "check": "✅ एक्सेस चेक करें",
        "verified": "✅ आपकी जॉइन रिक्वेस्ट स्वीकार हो गई है।",
        "open_channel": "Open the Channel",
        "robot": "🛡 रिक्वेस्ट वेरिफाई करें",
        "need_add_first": "⚠️ पहले इस बोट को अपने चैनल या ग्रुप में जोड़ें।\n\nहोम पर लौटने के लिए /start खोलें।",
        "no_chats": "📭 अभी कोई चैनल या ग्रुप जुड़ा नहीं है।",
        "join_mode": "जॉइन",
        "request_mode": "रिक्वेस्ट",
    },
    "hinglish": {
        "choose_language": "Apni language choose karo",
        "start": (
            "Is bot ko apne channel ya group mein add karo. New join requests auto approve ho jayengi.\n\n"
            f"{SUPPORT_LABEL}"
        ),
        "add_channel": "➕ Add Channel",
        "add_group": "➕ Add Group",
        "bulk": "⚡ Bulk Approval",
        "my_chats": "📊 My Channels / Groups",
        "support": "💬 Support",
        "settings": "⚙️ Settings",
        "home": "🏠 Home",
        "back": "⬅️ Back",
        "refresh": "🔄 Refresh",
        "cancel": "✖️ Cancel",
        "confirm": "✅ Confirm",
        "force_title": "🔒 Required Channels Complete Karo",
        "force_body": "Neeche wale chats join/request karo, phir Check Access press karo.",
        "check": "✅ Access Check",
        "verified": "✅ Aapki join request accept ho gayi hai.",
        "open_channel": "Open the Channel",
        "robot": "🛡 Verify Request",
        "need_add_first": "⚠️ Pehle bot ko channel ya group mein add karo.\n\nHome ke liye /start open karo.",
        "no_chats": "📭 Abhi koi channel ya group connected nahi hai.",
        "join_mode": "Join",
        "request_mode": "Request",
    },
    "ur": {
        "choose_language": "اپنی زبان منتخب کریں",
        "start": (
            "اس بوٹ کو اپنے چینل یا گروپ میں شامل کریں۔ نئی جوائن درخواستیں خودکار طور پر منظور ہوں گی۔\n\n"
            f"{SUPPORT_LABEL}"
        ),
        "add_channel": "➕ چینل شامل کریں",
        "add_group": "➕ گروپ شامل کریں",
        "bulk": "⚡ بلک اپروول",
        "my_chats": "📊 میرے چینلز / گروپس",
        "support": "💬 سپورٹ",
        "settings": "⚙️ سیٹنگز",
        "home": "🏠 ہوم",
        "back": "⬅️ واپس",
        "refresh": "🔄 ریفریش",
        "cancel": "✖️ منسوخ",
        "confirm": "✅ تصدیق کریں",
        "force_title": "🔒 ضروری چینلز مکمل کریں",
        "force_body": "نیچے دیے گئے چینلز/گروپس جوائن کریں یا درخواست بھیجیں، پھر Check Access دبائیں۔",
        "check": "✅ رسائی چیک کریں",
        "verified": "✅ آپ کی جوائن درخواست منظور ہو گئی ہے۔",
        "open_channel": "Open the Channel",
        "robot": "🛡 ریکویسٹ ویریفائی کریں",
        "need_add_first": "⚠️ پہلے اس بوٹ کو اپنے چینل یا گروپ میں شامل کریں۔\n\nہوم پر واپس آنے کے لیے /start کھولیں۔",
        "no_chats": "📭 ابھی کوئی چینل یا گروپ منسلک نہیں ہے۔",
        "join_mode": "جوائن",
        "request_mode": "ریکویسٹ",
    },
}


def t(lang: str | None, key: str, **kwargs: object) -> str:
    lang = lang if lang in TEXT else "en"
    value = TEXT.get(lang, {}).get(key) or TEXT["en"].get(key) or bold(key.replace("_", " ").upper())
    return value.format(**kwargs)
