from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from app.i18n import t
from app.keyboards import chat_manage_keyboard, chats_keyboard
from app.services.formatters import connected_chat_report
from app.services.telegram import safe_answer, safe_edit

router = Router()


async def _lang(db, user_id: int) -> str:
    return ((await db.user(user_id)) or {}).get("language") or "en"


@router.callback_query(F.data == "chats:list")
async def list_chats(callback: CallbackQuery, db) -> None:
    await safe_answer(callback)
    lang = await _lang(db, callback.from_user.id)
    chats = await db.chats_for_owner(callback.from_user.id)
    if not chats:
        await safe_edit(callback.message, t(lang, "no_chats"), chats_keyboard([], lang))
        return
    await safe_edit(callback.message, "📊 𝗠𝗬 𝗖𝗛𝗔𝗡𝗡𝗘𝗟𝗦 / 𝗚𝗥𝗢𝗨𝗣𝗦", chats_keyboard(chats, lang))


@router.callback_query(F.data.startswith("chat:"))
async def chat_detail(callback: CallbackQuery, bot: Bot, db) -> None:
    await safe_answer(callback)
    lang = await _lang(db, callback.from_user.id)
    chat_id = int(callback.data.split(":", 1)[1])
    chat = await db.chat(chat_id)
    if not chat or chat.get("owner_id") != callback.from_user.id:
        await safe_edit(callback.message, "⚠️ 𝗖𝗛𝗔𝗧 𝗡𝗢𝗧 𝗙𝗢𝗨𝗡𝗗.")
        return
    await safe_edit(callback.message, connected_chat_report(chat), chat_manage_keyboard(chat_id, lang))
