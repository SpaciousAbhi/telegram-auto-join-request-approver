from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

from app.i18n import t
from app.keyboards import force_subscription_keyboard, language_keyboard, main_menu, subscriber_join_keyboard, robot_keyboard
from app.services.approval import approval_notification_markup, approve_stored_request
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
                force_text(lang, missing),
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
    
    settings = await db.settings()
    if settings.get("verification_enabled"):
        pending_verifications = await db.active_pendings_for_user_globally(message.from_user.id)
        if pending_verifications:
            me = await bot.get_me()
            for req in pending_verifications:
                chat_title = req.get("chat_title") or f"Chat {req['chat_id']}"
                payload = f"verify_{req['chat_id']}_{req['user_id']}"
                text = (
                    f"𝗛𝗲𝗹𝗹𝗼, 𝘆𝗼𝘂 𝗵𝗮𝘃𝗲 𝗮 𝗽𝗲𝗻𝗱𝗶𝗻𝗴 𝗿𝗲𝗾𝘂𝗲𝘀𝘁 𝘁𝗼 𝗷𝗼𝗶𝗻 {chat_title}. "
                    "𝗣𝗹𝗲𝗮𝘀𝗲 𝗽𝗿𝗼𝘃𝗲 𝘆𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮 𝗿𝗼𝗯𝗼𝘁 𝘁𝗼 𝗴𝗲𝘁 𝗮𝗰𝗰𝗲𝘀𝘀."
                )
                await message.answer(text, reply_markup=robot_keyboard(me.username, payload))
            return

    await continue_start(message, bot, db, force_check=True)


async def _approve_verification(message: Message, bot: Bot, db, chat_id: int, user_id: int) -> bool:
    chat = await db.chat(chat_id) or {"title": str(chat_id)}
    pending = await db.active_pending_for_user(chat_id, user_id)
    if not pending:
        await message.answer("No active pending join request was found for you.")
        return True

    result = await approve_stored_request(bot, db, pending, "verification_click", notify_user=False)
    await db.upsert_user(message.from_user, verified=result.ok)
    if result.ok:
        lang = await _language_or_default(db, user_id)
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
        await message.answer(t(lang, "verified"), reply_markup=reply_markup)
        await db.log_event(
            "verification_approved",
            f"Verified and approved: {chat.get('title', chat_id)}",
            {"chat_id": chat_id, "user_id": user_id, "open_channel_link": bool(channel_link)},
        )
        await _send_subscriber_trick_if_enabled(message, db)
        return True

    if result.retryable:
        await message.answer("Approval is queued and will retry automatically. The owner can see the exact reason in System Health.")
    else:
        await message.answer("Approval could not be completed because Telegram no longer exposes this pending request. The owner can see the exact reason in System Health.")
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
        settings.get("subscriber_trick_message") or "👑 𝗝𝗢𝗜𝗡 𝗢𝗨𝗥 𝗦𝗘𝗟𝗘𝗖𝗧𝗘𝗗 𝗖𝗛𝗔𝗡𝗡𝗘𝗟𝗦.",
        reply_markup=subscriber_join_keyboard(chats, bool(settings.get("subscriber_trick_required"))),
        disable_web_page_preview=True,
    )


def force_text(lang: str | None, missing: list[dict]) -> str:
    text = f"{t(lang, 'force_title')}\n\n{t(lang, 'force_body')}"
    broken = [item for item in missing if item.get("last_error")]
    if broken:
        text += "\n\n⚠️ 𝗦𝗼𝗺𝗲 𝗿𝗲𝗾𝘂𝗶𝗿𝗲𝗱 𝗰𝗵𝗮𝘁𝘀 𝗰𝗮𝗻𝗻𝗼𝘁 𝗯𝗲 𝗰𝗵𝗲𝗰𝗸𝗲𝗱 𝗿𝗶𝗴𝗵𝘁 𝗻𝗼𝘄. 𝗧𝗵𝗲 𝗼𝘄𝗻𝗲𝗿 𝗺𝘂𝘀𝘁 𝗳𝗶𝘅 𝗯𝗼𝘁 𝗮𝗰𝗰𝗲𝘀𝘀 𝗳𝗼𝗿 𝘁𝗵𝗼𝘀𝗲 𝗰𝗵𝗮𝘁𝘀."
    return text


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
        await db.log_event("force_check", "Force access still missing", {"user_id": callback.from_user.id, "missing": len(missing)})
        await safe_edit(callback.message, force_text(lang, missing), force_subscription_keyboard(missing, lang))
        return
    await db.log_event("force_check", "Force access unlocked", {"user_id": callback.from_user.id})
    if not (await db.user(callback.from_user.id) or {}).get("language"):
        await safe_edit(callback.message, t("en", "choose_language"), language_keyboard())
        return
    me = await bot.get_me()
    await safe_edit(callback.message, t(lang, "start"), main_menu(lang, me.username))


@router.callback_query(F.data == "force:target_error")
async def force_target_error(callback: CallbackQuery) -> None:
    await safe_answer(callback, "This force-subscription target has no usable invite link. Please contact the bot owner.", True)


@router.callback_query(F.data == "nav:home")
async def nav_home(callback: CallbackQuery, bot: Bot, db) -> None:
    await safe_answer(callback)
    lang = await _language_or_default(db, callback.from_user.id)
    me = await bot.get_me()
    await safe_edit(callback.message, t(lang, "start"), main_menu(lang, me.username))
