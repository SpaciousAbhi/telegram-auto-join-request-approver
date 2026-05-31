from __future__ import annotations

from bson import ObjectId
from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from app.i18n import t
from app.keyboards import bulk_control_keyboard, chats_keyboard, home_keyboard
from app.services.formatters import bulk_status
from app.services.telegram import safe_answer, safe_edit
from app.ui import (
    render_bulk_disabled_text,
    render_bulk_empty_text,
    render_bulk_select_text,
    render_bulk_starting_text,
    render_chat_not_found_text,
    render_job_not_found_text,
)

router = Router()


async def _lang(db, user_id: int) -> str:
    return ((await db.user(user_id)) or {}).get("language") or "en"


@router.callback_query(F.data == "bulk:start")
async def bulk_start(callback: CallbackQuery, bot: Bot, db, bulk_service) -> None:
    await safe_answer(callback, "Preparing bulk approval...")
    lang = await _lang(db, callback.from_user.id)
    settings = await db.settings()
    if not settings.get("bulk_approval_enabled"):
        await safe_edit(callback.message, render_bulk_disabled_text(), home_keyboard(lang))
        return
    chats = await db.chats_for_owner(callback.from_user.id)
    if not chats:
        await safe_edit(callback.message, t(lang, "need_add_first"), home_keyboard(lang))
        return
    if len(chats) == 1:
        await _start_for_chat(callback, bot, db, bulk_service, chats[0]["chat_id"], settings)
        return
    await safe_edit(callback.message, render_bulk_select_text(chats), chats_keyboard(chats, lang))


@router.callback_query(F.data.startswith("bulk:chat:"))
async def bulk_chat(callback: CallbackQuery, bot: Bot, db, bulk_service) -> None:
    await safe_answer(callback, "Starting bulk approval...")
    settings = await db.settings()
    await _start_for_chat(callback, bot, db, bulk_service, int(callback.data.rsplit(":", 1)[1]), settings)


async def _start_for_chat(callback: CallbackQuery, bot: Bot, db, bulk_service, chat_id: int, settings: dict) -> None:
    lang = await _lang(db, callback.from_user.id)
    chat = await db.chat(chat_id)
    if not chat or chat.get("owner_id") != callback.from_user.id:
        await safe_edit(callback.message, render_chat_not_found_text(), home_keyboard(lang))
        return
    pending = await db.pending_for_chat(chat_id)
    if not pending:
        await safe_edit(callback.message, render_bulk_empty_text(chat), home_keyboard(lang))
        return
    progress = await callback.message.answer(render_bulk_starting_text())
    job = await bulk_service.start(bot, callback.from_user.id, chat_id, progress.chat.id, progress.message_id, int(settings.get("approval_speed_per_minute", 600)))
    await progress.edit_text(bulk_status(job), reply_markup=bulk_control_keyboard(str(job["_id"])))


@router.callback_query(F.data.startswith("bulk:pause:") | F.data.startswith("bulk:resume:") | F.data.startswith("bulk:stop:") | F.data.startswith("bulk:status:"))
async def bulk_control(callback: CallbackQuery, db) -> None:
    _, action, job_id = callback.data.split(":", 2)
    answer = {
        "pause": "Pausing job...",
        "resume": "Resuming job...",
        "stop": "Stopping job...",
        "status": "Refreshing job...",
    }.get(action, "Updating job...")
    await safe_answer(callback, answer)
    lang = await _lang(db, callback.from_user.id)
    status = {"pause": "paused", "resume": "running", "stop": "stopped"}.get(action)
    job = await db.db.bulk_jobs.find_one({"_id": ObjectId(job_id)})
    if not job or job.get("owner_id") != callback.from_user.id:
        await safe_edit(callback.message, render_job_not_found_text(), home_keyboard(lang))
        return
    if status:
        job = await db.update_bulk_job(ObjectId(job_id), status=status)
    await safe_edit(callback.message, bulk_status(job), bulk_control_keyboard(job_id))
