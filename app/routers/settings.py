from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.keyboards import language_keyboard
from app.services.telegram import safe_answer, safe_edit
from app.ui import render_settings_text

router = Router()


@router.callback_query(F.data == "settings:menu")
async def settings_menu(callback: CallbackQuery, db) -> None:
    await safe_answer(callback, "Opening settings...")
    lang = ((await db.user(callback.from_user.id)) or {}).get("language") or "en"
    await safe_edit(callback.message, render_settings_text(), language_keyboard(with_home=True, home_lang=lang))
