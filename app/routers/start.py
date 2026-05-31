from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

from app.keyboards import force_subscription_keyboard, language_keyboard, main_menu, robot_keyboard, subscriber_join_keyboard
from app.services.approval import approval_notification_markup, approve_stored_request
from app.services.telegram import force_target_completed, safe_answer, safe_edit
from app.ui import (
    render_force_target_error_text,
    render_force_text,
    render_home_text,
    render_invalid_verification_text,
    render_language_text,
    render_no_active_request_text,
    render_verification_request_text,
    render_verification_retry_text,
    render_verification_terminal_text,
    render_verified_text,
)

router = Router()


async def _language_or_default(db, user_id: int) -> str:
    user = await db.user(user_id)
    return (user or {}).get("language") or "en"


async def _missing_force_targets(bot: Bot, db, user_id: int) -> list[dict]:
    missing = []
    for target in await db.force_chats():
        completed, error = await force_target_completed(bot, db, user_id, target)
        if error:
            await db.db.force_chats.update_one({"chat_id": target["chat_id"]}, {"$set": {"last_error": error, "last_check_failed_user": user_id}})
            await db.log_event(
                "force_check_error",
                f"Force check failed: {target.get('title', target['chat_id'])}",
                {"chat_id": target["chat_id"], "user_id": user_id, "error": error},
                "warning",
            )
            target = {**target, "last_error": error}
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
                render_force_text(lang, missing),
                reply_markup=force_subscription_keyboard(missing, lang or "en"),
                disable_web_page_preview=True,
            )
            return
    if not lang:
        await message.answer(render_language_text(), reply_markup=language_keyboard())
        return
    me = await bot.get_me()
    await message.answer(render_home_text(message.from_user, lang), reply_markup=main_menu(lang, me.username), disable_web_page_preview=True)


@router.message(Command("start"))
async def start(message: Message, command: CommandObject, bot: Bot, db) -> None:
    await db.upsert_user(message.from_user)
    payload = command.args or ""
    if payload.startswith("verify_"):
        try:
            _, chat_id, user_id = payload.split("_", 2)
            chat_id_int = int(chat_id)
            user_id_int = int(user_id)
        except ValueError:
            await message.answer(render_invalid_verification_text())
            return
        if user_id_int != message.from_user.id:
            await message.answer(render_invalid_verification_text("wrong_user"))
            return
        ok = await _approve_verification(message, bot, db, chat_id_int, user_id_int)
        if ok:
            return

    settings = await db.settings()
    if settings.get("verification_enabled"):
        pending_verifications = await db.active_pendings_for_user_globally(message.from_user.id)
        if pending_verifications:
            me = await bot.get_me()
            lang = await _language_or_default(db, message.from_user.id)
            for req in pending_verifications:
                chat_title = req.get("chat_title") or f"Chat {req['chat_id']}"
                payload = f"verify_{req['chat_id']}_{req['user_id']}"
                await message.answer(render_verification_request_text(chat_title), reply_markup=robot_keyboard(me.username, payload, lang))
            return

    await continue_start(message, bot, db, force_check=True)


async def _approve_verification(message: Message, bot: Bot, db, chat_id: int, user_id: int) -> bool:
    chat = await db.chat(chat_id) or {"title": str(chat_id)}
    pending = await db.active_pending_for_user(chat_id, user_id)
    if not pending:
        await message.answer(render_no_active_request_text())
        return True

    result = await approve_stored_request(bot, db, pending, "verification_click", notify_user=False)
    await db.upsert_user(message.from_user, verified=result.ok)
    if result.ok:
        reply_markup, channel_link, link_warning = await approval_notification_markup(bot, db, pending)
        if channel_link:
            await db.mark_notification(chat_id, user_id, "sent", link=channel_link)
        else:
            await db.mark_notification(chat_id, user_id, "failed", link_warning or "Open Channel link is unavailable.")
        if link_warning:
            await db.log_event(
                "invite_link_creation_error",
                "Open Channel link needed a fallback",
                {"chat_id": chat_id, "user_id": user_id, "error": link_warning},
                "warning",
            )
        await message.answer(render_verified_text(chat.get("title") or pending.get("chat_title") or chat_id), reply_markup=reply_markup)
        await db.log_event(
            "verification_approved",
            f"Verified and approved: {chat.get('title', chat_id)}",
            {"chat_id": chat_id, "user_id": user_id, "open_channel_link": bool(channel_link)},
        )
        await _send_subscriber_trick_if_enabled(message, db)
        return True

    if result.retryable:
        await message.answer(render_verification_retry_text())
    else:
        await message.answer(render_verification_terminal_text())
    await db.log_event(
        "verification_approval_error",
        f"Verification approval failed: {chat.get('title', chat_id)}",
        {"chat_id": chat_id, "user_id": user_id, "error": result.error, "retryable": result.retryable},
        "warning" if result.retryable else "error",
    )
    return True


async def _send_subscriber_trick_if_enabled(message: Message, db) -> None:
    settings = await db.settings()
    if not settings.get("subscriber_trick_enabled"):
        return
    chats = await db.subscriber_trick_chats()
    if not chats:
        return
    await message.answer(
        settings.get("subscriber_trick_message")
        or "👑 Join our selected channels for updates after your request is accepted.",
        reply_markup=subscriber_join_keyboard(chats, bool(settings.get("subscriber_trick_required"))),
        disable_web_page_preview=True,
    )


def force_text(lang: str | None, missing: list[dict]) -> str:
    return render_force_text(lang, missing)


@router.callback_query(F.data.startswith("lang:"))
async def choose_language(callback: CallbackQuery, bot: Bot, db) -> None:
    lang = callback.data.split(":", 1)[1]
    await db.set_language(callback.from_user.id, lang)
    await safe_answer(callback, "Language saved")
    me = await bot.get_me()
    await safe_edit(callback.message, render_home_text(callback.from_user, lang), reply_markup=main_menu(lang, me.username))


@router.callback_query(F.data == "force:check")
async def force_check(callback: CallbackQuery, bot: Bot, db) -> None:
    await safe_answer(callback, "Checking access...")
    missing = await _missing_force_targets(bot, db, callback.from_user.id)
    lang = await _language_or_default(db, callback.from_user.id)
    if missing:
        await db.log_event("force_check", "Force access still missing", {"user_id": callback.from_user.id, "missing": len(missing)})
        await safe_edit(callback.message, render_force_text(lang, missing), force_subscription_keyboard(missing, lang))
        return
    await db.log_event("force_check", "Force access unlocked", {"user_id": callback.from_user.id})
    if not (await db.user(callback.from_user.id) or {}).get("language"):
        await safe_edit(callback.message, render_language_text(), language_keyboard())
        return
    me = await bot.get_me()
    await safe_edit(callback.message, render_home_text(callback.from_user, lang), main_menu(lang, me.username))


@router.callback_query(F.data == "force:target_error")
async def force_target_error(callback: CallbackQuery) -> None:
    await safe_answer(callback, render_force_target_error_text(), True)


@router.callback_query(F.data == "nav:home")
async def nav_home(callback: CallbackQuery, bot: Bot, db) -> None:
    await safe_answer(callback, "Opening home...")
    lang = await _language_or_default(db, callback.from_user.id)
    me = await bot.get_me()
    await safe_edit(callback.message, render_home_text(callback.from_user, lang), main_menu(lang, me.username))
