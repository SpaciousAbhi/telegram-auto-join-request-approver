from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from app.i18n import t
from app.keyboards import chat_manage_keyboard, chats_keyboard, home_keyboard, remove_chat_keyboard
from app.services.formatters import connected_chat_report
from app.services.telegram import inspect_bot_permissions, safe_answer, safe_edit

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


@router.callback_query(F.data.startswith("chat:remove_confirm:"))
async def remove_chat_confirm(callback: CallbackQuery, db) -> None:
    await safe_answer(callback)
    lang = await _lang(db, callback.from_user.id)
    chat_id = int(callback.data.rsplit(":", 1)[1])
    removed = await db.remove_connected_chat(chat_id, callback.from_user.id)
    if not removed:
        await safe_edit(callback.message, "⚠️ 𝗖𝗛𝗔𝗧 𝗡𝗢𝗧 𝗙𝗢𝗨𝗡𝗗 𝗢𝗥 𝗔𝗟𝗥𝗘𝗔𝗗𝗬 𝗥𝗘𝗠𝗢𝗩𝗘𝗗.\n\n𝗢𝗽𝗲𝗻 /start 𝘁𝗼 𝗿𝗲𝘁𝘂𝗿𝗻 𝗵𝗼𝗺𝗲.", home_keyboard(lang))
        return
    await safe_edit(callback.message, "✅ 𝗖𝗛𝗔𝗧 𝗥𝗘𝗠𝗢𝗩𝗘𝗗 / 𝗗𝗘𝗔𝗖𝗧𝗜𝗩𝗔𝗧𝗘𝗗.\n\n𝗜𝘁 𝘄𝗶𝗹𝗹 𝗻𝗼 𝗹𝗼𝗻𝗴𝗲𝗿 𝘀𝗵𝗼𝘄 𝗮𝘀 𝗮𝗻 𝗮𝗰𝘁𝗶𝘃𝗲 𝗰𝗼𝗻𝗻𝗲𝗰𝘁𝗲𝗱 𝗰𝗵𝗮𝘁.", home_keyboard(lang))


@router.callback_query(F.data.startswith("chat:remove:"))
async def remove_chat_prompt(callback: CallbackQuery, db) -> None:
    await safe_answer(callback)
    lang = await _lang(db, callback.from_user.id)
    chat_id = int(callback.data.rsplit(":", 1)[1])
    chat = await db.chat(chat_id)
    if not chat or chat.get("owner_id") != callback.from_user.id:
        await safe_edit(callback.message, "⚠️ 𝗖𝗛𝗔𝗧 𝗡𝗢𝗧 𝗙𝗢𝗨𝗡𝗗.", home_keyboard(lang))
        return
    await safe_edit(
        callback.message,
        f"🗑 𝗥𝗘𝗠𝗢𝗩𝗘 𝗖𝗛𝗔𝗧\n\n𝗡𝗔𝗠𝗘: {chat.get('title')}\n𝗜𝗗: <code>{chat_id}</code>\n\n𝗧𝗵𝗶𝘀 𝘄𝗶𝗹𝗹 𝗱𝗲𝗮𝗰𝘁𝗶𝘃𝗮𝘁𝗲 𝘁𝗵𝗲 𝗰𝗵𝗮𝘁 𝗶𝗻 𝘆𝗼𝘂𝗿 𝗽𝗮𝗻𝗲𝗹. 𝗜𝘁 𝗱𝗼𝗲𝘀 𝗻𝗼𝘁 𝗿𝗲𝗺𝗼𝘃𝗲 𝘁𝗵𝗲 𝗯𝗼𝘁 𝗳𝗿𝗼𝗺 𝗧𝗲𝗹𝗲𝗴𝗿𝗮𝗺.",
        remove_chat_keyboard(chat_id, lang),
    )


@router.callback_query(F.data.startswith("chat:"))
async def chat_detail(callback: CallbackQuery, bot: Bot, db) -> None:
    await safe_answer(callback)
    lang = await _lang(db, callback.from_user.id)
    chat_id = int(callback.data.split(":", 1)[1])
    chat = await db.chat(chat_id)
    if not chat or chat.get("owner_id") != callback.from_user.id:
        await safe_edit(callback.message, "⚠️ 𝗖𝗛𝗔𝗧 𝗡𝗢𝗧 𝗙𝗢𝗨𝗡𝗗.", home_keyboard(lang))
        return
    me = await bot.get_me()
    permissions = await inspect_bot_permissions(bot, chat_id, me.id)
    await db.upsert_connected_chat(
        {
            **chat,
            "bot_is_admin": permissions.is_admin,
            "permissions_ok": permissions.ok,
            "missing_permissions": permissions.missing,
            "permission_status": permissions.status,
            "active": permissions.ok and not chat.get("removed_by_owner"),
            "last_error": None if permissions.ok else f"Missing permissions: {', '.join(permissions.missing) or permissions.status}",
        }
    )
    chat = await db.chat(chat_id)
    await safe_edit(callback.message, connected_chat_report(chat), chat_manage_keyboard(chat_id, lang))
