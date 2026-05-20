from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

from app.i18n import t
from app.keyboards import force_subscription_keyboard, language_keyboard, main_menu, subscriber_join_keyboard
from app.services.telegram import force_target_completed, safe_answer, safe_edit

router = Router()


async def _language_or_default(db, user_id: int) -> str:
    user = await db.user(user_id)
    return (user or {}).get("language") or "en"


async def _missing_force_targets(bot: Bot, db, user_id: int) -> list[dict]:
    missing = []
    for target in await db.force_chats():
        completed, error = await force_target_completed(bot, db, user_id, target)
        if error:
            await db.db.force_chats.update_one({"chat_id": target["chat_id"]}, {"$set": {"last_error": error}})
        if not completed:
            missing.append(target)
    return missing


async def continue_start(message: Message, bot: Bot, db, force_check: bool = True) -> None:
    user_doc = await db.user(message.from_user.id)
    lang = (user_doc or {}).get("language")
    settings = await db.settings()
    if force_check and settings.get("force_subscription_enabled"):
        missing = await _missing_force_targets(bot, db, message.from_user.id)
        if missing:
            await message.answer(
                f"{t(lang, 'force_title')}\n\n{t(lang, 'force_body')}",
                reply_markup=force_subscription_keyboard(missing, lang or "en"),
                disable_web_page_preview=True,
            )
            return
    if not lang:
        await message.answer(t("en", "choose_language"), reply_markup=language_keyboard())
        return
    me = await bot.get_me()
    await message.answer(t(lang, "start"), reply_markup=main_menu(lang, me.username), disable_web_page_preview=True)


@router.message(Command("start"))
async def start(message: Message, command: CommandObject, bot: Bot, db) -> None:
    await db.upsert_user(message.from_user)
    payload = command.args or ""
    if payload.startswith("verify_"):
        try:
            _, chat_id, user_id = payload.split("_", 2)
        except ValueError:
            await message.answer("⚠️ 𝗩𝗘𝗥𝗜𝗙𝗜𝗖𝗔𝗧𝗜𝗢𝗡 𝗟𝗜𝗡𝗞 𝗜𝗦 𝗜𝗡𝗩𝗔𝗟𝗜𝗗.")
            return
        try:
            chat_id_int = int(chat_id)
            user_id_int = int(user_id)
        except ValueError:
            await message.answer("⚠️ 𝗩𝗘𝗥𝗜𝗙𝗜𝗖𝗔𝗧𝗜𝗢𝗡 𝗟𝗜𝗡𝗞 𝗜𝗦 𝗜𝗡𝗩𝗔𝗟𝗜𝗗.")
            return
        if user_id_int != message.from_user.id:
            await message.answer("⚠️ 𝗧𝗛𝗜𝗦 𝗩𝗘𝗥𝗜𝗙𝗜𝗖𝗔𝗧𝗜𝗢𝗡 𝗟𝗜𝗡𝗞 𝗜𝗦 𝗡𝗢𝗧 𝗙𝗢𝗥 𝗬𝗢𝗨.")
            return
        ok = await _approve_verification(message, bot, db, chat_id_int, user_id_int)
        if ok:
            return
    await continue_start(message, bot, db, force_check=True)


async def _approve_verification(message: Message, bot: Bot, db, chat_id: int, user_id: int) -> bool:
    from app.services.telegram import approve_join_request

    chat = await db.chat(chat_id) or {"title": str(chat_id)}
    ok, error = await approve_join_request(bot, chat_id, user_id)
    await db.upsert_user(message.from_user, verified=ok)
    await db.mark_request(chat_id, user_id, "approved" if ok else "failed", error)
    await db.record_approval(chat_id, ok)
    if ok:
        lang = await _language_or_default(db, user_id)
        await message.answer(t(lang, "verified"))
        await _send_subscriber_trick_if_enabled(message, db)
    else:
        await message.answer("⚠️ 𝗩𝗘𝗥𝗜𝗙𝗜𝗖𝗔𝗧𝗜𝗢𝗡 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘𝗗, 𝗕𝗨𝗧 𝗧𝗘𝗟𝗘𝗚𝗥𝗔𝗠 𝗗𝗜𝗗 𝗡𝗢𝗧 𝗔𝗟𝗟𝗢𝗪 𝗔𝗣𝗣𝗥𝗢𝗩𝗔𝗟. 𝗧𝗛𝗘 𝗢𝗪𝗡𝗘𝗥 𝗛𝗔𝗦 𝗕𝗘𝗘𝗡 𝗟𝗢𝗚𝗚𝗘𝗗.")
    return True


async def _send_subscriber_trick_if_enabled(message: Message, db) -> None:
    settings = await db.settings()
    if not settings.get("subscriber_trick_enabled"):
        return
    chats = await db.subscriber_trick_chats()
    if not chats:
        return
    await message.answer(
        settings.get("subscriber_trick_message") or "👑 𝗝𝗢𝗜𝗡 𝗢𝗨𝗥 𝗦𝗘𝗟𝗘𝗖𝗧𝗘𝗗 𝗖𝗛𝗔𝗡𝗡𝗘𝗟𝗦.",
        reply_markup=subscriber_join_keyboard(chats, bool(settings.get("subscriber_trick_required"))),
        disable_web_page_preview=True,
    )


@router.callback_query(F.data.startswith("lang:"))
async def choose_language(callback: CallbackQuery, bot: Bot, db) -> None:
    await safe_answer(callback)
    lang = callback.data.split(":", 1)[1]
    await db.set_language(callback.from_user.id, lang)
    me = await bot.get_me()
    await safe_edit(callback.message, t(lang, "start"), reply_markup=main_menu(lang, me.username))


@router.callback_query(F.data == "force:check")
async def force_check(callback: CallbackQuery, bot: Bot, db) -> None:
    await safe_answer(callback)
    missing = await _missing_force_targets(bot, db, callback.from_user.id)
    lang = await _language_or_default(db, callback.from_user.id)
    if missing:
        await safe_edit(callback.message, f"{t(lang, 'force_title')}\n\n{t(lang, 'force_body')}", force_subscription_keyboard(missing, lang))
        return
    if not (await db.user(callback.from_user.id) or {}).get("language"):
        await safe_edit(callback.message, t("en", "choose_language"), language_keyboard())
        return
    me = await bot.get_me()
    await safe_edit(callback.message, t(lang, "start"), main_menu(lang, me.username))


@router.callback_query(F.data == "nav:home")
async def nav_home(callback: CallbackQuery, bot: Bot, db) -> None:
    await safe_answer(callback)
    lang = await _language_or_default(db, callback.from_user.id)
    me = await bot.get_me()
    await safe_edit(callback.message, t(lang, "start"), main_menu(lang, me.username))
