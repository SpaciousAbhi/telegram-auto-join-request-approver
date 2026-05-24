from __future__ import annotations

from bson import ObjectId
from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from app.i18n import t
from app.keyboards import bulk_control_keyboard, chats_keyboard, home_keyboard
from app.services.formatters import bulk_status
from app.services.telegram import safe_answer, safe_edit

router = Router()


@router.callback_query(F.data == "bulk:start")
async def bulk_start(callback: CallbackQuery, bot: Bot, db, bulk_service) -> None:
    await safe_answer(callback)
    lang = ((await db.user(callback.from_user.id)) or {}).get("language") or "en"
    settings = await db.settings()
    if not settings.get("bulk_approval_enabled"):
        await safe_edit(callback.message, "⛔ 𝗕𝗨𝗟𝗞 𝗔𝗣𝗣𝗥𝗢𝗩𝗔𝗟 𝗜𝗦 𝗖𝗨𝗥𝗥𝗘𝗡𝗧𝗟𝗬 𝗗𝗜𝗦𝗔𝗕𝗟𝗘𝗗.")
        return
    chats = await db.chats_for_owner(callback.from_user.id)
    if not chats:
        await safe_edit(callback.message, t(lang, "need_add_first"), home_keyboard(lang))
        return
    if len(chats) == 1:
        await _start_for_chat(callback, bot, db, bulk_service, chats[0]["chat_id"], settings)
        return
    await safe_edit(callback.message, "⚡ 𝗦𝗘𝗟𝗘𝗖𝗧 𝗔 𝗖𝗛𝗔𝗧 𝗙𝗢𝗥 𝗕𝗨𝗟𝗞 𝗔𝗣𝗣𝗥𝗢𝗩𝗔𝗟", chats_keyboard(chats, lang))


@router.callback_query(F.data.startswith("bulk:chat:"))
async def bulk_chat(callback: CallbackQuery, bot: Bot, db, bulk_service) -> None:
    await safe_answer(callback)
    settings = await db.settings()
    await _start_for_chat(callback, bot, db, bulk_service, int(callback.data.rsplit(":", 1)[1]), settings)


async def _start_for_chat(callback: CallbackQuery, bot: Bot, db, bulk_service, chat_id: int, settings: dict) -> None:
    chat = await db.chat(chat_id)
    if not chat or chat.get("owner_id") != callback.from_user.id:
        await safe_edit(callback.message, "⚠️ 𝗖𝗛𝗔𝗧 𝗡𝗢𝗧 𝗙𝗢𝗨𝗡𝗗.\n\n𝗢𝗽𝗲𝗻 /start 𝘁𝗼 𝗿𝗲𝘁𝘂𝗿𝗻 𝗵𝗼𝗺𝗲.", home_keyboard())
        return
    pending = await db.pending_for_chat(chat_id)
    if not pending:
        await safe_edit(callback.message, "✅ 𝗡𝗢 𝗦𝗧𝗢𝗥𝗘𝗗 𝗣𝗘𝗡𝗗𝗜𝗡𝗚 𝗥𝗘𝗤𝗨𝗘𝗦𝗧𝗦 𝗙𝗢𝗨𝗡𝗗 𝗙𝗢𝗥 𝗧𝗛𝗜𝗦 𝗖𝗛𝗔𝗧.\n\n𝗢𝗽𝗲𝗻 /start 𝘁𝗼 𝗿𝗲𝘁𝘂𝗿𝗻 𝗵𝗼𝗺𝗲.", home_keyboard())
        return
    progress = await callback.message.answer("⚡ 𝗕𝗨𝗟𝗞 𝗔𝗣𝗣𝗥𝗢𝗩𝗔𝗟 𝗦𝗧𝗔𝗥𝗧𝗜𝗡𝗚...")
    job = await bulk_service.start(bot, callback.from_user.id, chat_id, progress.chat.id, progress.message_id, int(settings.get("approval_speed_per_minute", 600)))
    await progress.edit_text(bulk_status(job), reply_markup=bulk_control_keyboard(str(job["_id"])))


@router.callback_query(F.data.startswith("bulk:pause:") | F.data.startswith("bulk:resume:") | F.data.startswith("bulk:stop:") | F.data.startswith("bulk:status:"))
async def bulk_control(callback: CallbackQuery, db) -> None:
    await safe_answer(callback)
    _, action, job_id = callback.data.split(":", 2)
    status = {"pause": "paused", "resume": "running", "stop": "stopped"}.get(action)
    job = await db.db.bulk_jobs.find_one({"_id": ObjectId(job_id)})
    if not job or job.get("owner_id") != callback.from_user.id:
        await safe_edit(callback.message, "⚠️ 𝗝𝗢𝗕 𝗡𝗢𝗧 𝗙𝗢𝗨𝗡𝗗.\n\n𝗢𝗽𝗲𝗻 /start 𝘁𝗼 𝗿𝗲𝘁𝘂𝗿𝗻 𝗵𝗼𝗺𝗲.", home_keyboard())
        return
    if status:
        job = await db.update_bulk_job(ObjectId(job_id), status=status)
    await safe_edit(callback.message, bulk_status(job), bulk_control_keyboard(job_id))
