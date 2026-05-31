from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from app.keyboards import chat_manage_keyboard, chats_keyboard, home_keyboard, remove_chat_keyboard
from app.services.formatters import connected_chat_report
from app.services.telegram import inspect_bot_permissions, safe_answer, safe_edit
from app.ui import render_chat_not_found_text, render_chat_removed_text, render_chats_list_text, render_remove_chat_text

router = Router()


async def _lang(db, user_id: int) -> str:
    return ((await db.user(user_id)) or {}).get("language") or "en"


@router.callback_query(F.data == "chats:list")
async def list_chats(callback: CallbackQuery, db) -> None:
    await safe_answer(callback, "Opening chats...")
    lang = await _lang(db, callback.from_user.id)
    chats = await db.chats_for_owner(callback.from_user.id)
    await safe_edit(callback.message, render_chats_list_text(chats), chats_keyboard(chats, lang))


@router.callback_query(F.data.startswith("chat:remove_confirm:"))
async def remove_chat_confirm(callback: CallbackQuery, db) -> None:
    await safe_answer(callback, "Deactivating...")
    lang = await _lang(db, callback.from_user.id)
    chat_id = int(callback.data.rsplit(":", 1)[1])
    removed = await db.remove_connected_chat(chat_id, callback.from_user.id)
    if not removed:
        await safe_edit(callback.message, render_chat_not_found_text(), home_keyboard(lang))
        return
    await safe_edit(callback.message, render_chat_removed_text(), home_keyboard(lang))


@router.callback_query(F.data.startswith("chat:remove:"))
async def remove_chat_prompt(callback: CallbackQuery, db) -> None:
    await safe_answer(callback, "Review before deactivating...")
    lang = await _lang(db, callback.from_user.id)
    chat_id = int(callback.data.rsplit(":", 1)[1])
    chat = await db.chat(chat_id)
    if not chat or chat.get("owner_id") != callback.from_user.id:
        await safe_edit(callback.message, render_chat_not_found_text(), home_keyboard(lang))
        return
    await safe_edit(callback.message, render_remove_chat_text(chat, chat_id), remove_chat_keyboard(chat_id, lang))


@router.callback_query(F.data.startswith("chat:"))
async def chat_detail(callback: CallbackQuery, bot: Bot, db) -> None:
    await safe_answer(callback, "Refreshing status...")
    lang = await _lang(db, callback.from_user.id)
    chat_id = int(callback.data.split(":", 1)[1])
    chat = await db.chat(chat_id)
    if not chat or chat.get("owner_id") != callback.from_user.id:
        await safe_edit(callback.message, render_chat_not_found_text(), home_keyboard(lang))
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
