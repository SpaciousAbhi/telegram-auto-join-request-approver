from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.i18n import t
from app.keyboards import language_keyboard
from app.services.telegram import safe_answer, safe_edit

router = Router()


@router.callback_query(F.data == "settings:menu")
async def settings_menu(callback: CallbackQuery, db) -> None:
    await safe_answer(callback)
    lang = ((await db.user(callback.from_user.id)) or {}).get("language") or "en"
    await safe_edit(callback.message, f"⚙️ 𝗦𝗘𝗧𝗧𝗜𝗡𝗚𝗦\n\n{t(lang, 'choose_language')}", language_keyboard())
