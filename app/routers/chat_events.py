from __future__ import annotations

from aiogram import Bot, Router
from aiogram.types import ChatJoinRequest, ChatMemberUpdated

from app.keyboards import chat_manage_keyboard, robot_keyboard
from app.services.formatters import connected_chat_report
from app.services.approval import approve_stored_request, is_permission_error, retry_delay_for, utcnow
from app.services.telegram import can_approve_in_chat, inspect_bot_permissions, member_status_value

router = Router()


@router.my_chat_member()
async def bot_membership_changed(event: ChatMemberUpdated, bot: Bot, db) -> None:
    chat = event.chat
    user = event.from_user
    me = await bot.get_me()
    new_status = member_status_value(event.new_chat_member)
    if new_status in {"left", "kicked"}:
        await db.mark_chat_inactive(chat.id, "Bot removed from chat")
        return
    if new_status not in {"administrator", "member", "creator"}:
        return
    permissions = await inspect_bot_permissions(bot, chat.id, me.id)
    member_count = None
    try:
        member_count = await bot.get_chat_member_count(chat.id)
    except Exception:
        pass
    data = {
        "chat_id": chat.id,
        "title": chat.title or chat.full_name,
        "type": chat.type,
        "username": chat.username,
        "owner_id": user.id,
        "bot_is_admin": permissions.is_admin,
        "permissions_ok": permissions.ok,
        "missing_permissions": permissions.missing,
        "permission_status": permissions.status,
        "member_count": member_count,
        "auto_approve": True,
        "active": permissions.ok,
    }
    await db.upsert_connected_chat(data)
    try:
        saved = await db.chat(chat.id)
        await bot.send_message(
            user.id,
            connected_chat_report(saved),
            reply_markup=chat_manage_keyboard(chat.id, ((await db.user(user.id)) or {}).get("language") or "en"),
            parse_mode="HTML",
        )
    except Exception:
        pass


@router.chat_join_request()
async def join_request(request: ChatJoinRequest, bot: Bot, db) -> None:
    # 1. Fetch settings with fallback
    settings = {}
    try:
        settings = await db.settings()
    except Exception as exc:
        try:
            await db.log_event("settings_fetch_error", f"Failed to fetch settings: {exc}", severity="warning")
        except Exception:
            pass

    chat = request.chat
    user = request.from_user
    invite = request.invite_link.invite_link if request.invite_link else None
    user_chat_id = getattr(request, "user_chat_id", None)

    # 2. Save request to DB with fallback
    db_ok = False
    try:
        await db.add_pending_request(chat, user, invite, user_chat_id=user_chat_id)
        db_ok = True
    except Exception as exc:
        try:
            await db.log_event("db_save_error", f"Failed to save join request: {exc}", severity="error")
        except Exception:
            pass

    # Fallback to immediate approval if DB is down/failing
    if not db_ok:
        await approve_join_request(bot, chat.id, user.id)
        return

    # Normal flow if DB is OK
    force_request_target = None
    try:
        force_request_target = await db.db.force_chats.find_one({"chat_id": chat.id, "active": True, "mode": "request"})
    except Exception:
        pass

    if force_request_target:
        try:
            await db.mark_join_request_sent(user.id, chat.id)
        except Exception:
            pass

    connected_chat = None
    try:
        connected_chat = await db.chat(chat.id)
    except Exception:
        pass

    if not connected_chat and force_request_target:
        await db.mark_request(chat.id, user.id, "force_request_recorded" if force_request_target else "unmanaged_chat")
        return

    if connected_chat and connected_chat.get("removed_by_owner"):
        await db.mark_request(chat.id, user.id, "chat_deactivated_by_owner")
        await db.log_event("join_request_skipped", "Join request skipped because chat is deactivated", {"chat_id": chat.id}, "warning")
        return

    can_approve, permission_error = await can_approve_in_chat(bot, chat.id)
    if not can_approve:
        retry_at = utcnow() + retry_delay_for({"approval_attempts": 0}, permission_error, permission=True)
        await db.schedule_request_retry(chat.id, user.id, "permission_error", permission_error, retry_at)
        if connected_chat and is_permission_error(permission_error):
            await db.mark_chat_inactive(chat.id, permission_error or "Missing approve permission")
        await db.log_event(
            "approval_retry_scheduled",
            f"Approval delayed until bot permissions are fixed: {chat.title or chat.id}",
            {"chat_id": chat.id, "user_id": user.id, "retry_at": retry_at.isoformat(), "error": permission_error},
            "error",
        )
        return

    item_data = {
        "chat_id": chat.id,
        "chat_title": chat.title or chat.full_name or str(chat.id),
        "user_id": user.id,
        "user_chat_id": user_chat_id,
        "invite_link": invite,
    }

    if settings.get("verification_enabled"):
        me = await bot.get_me()
        payload = f"verify_{chat.id}_{user.id}"
        text = (
            f"𝗛𝗲𝗹𝗹𝗼, 𝘆𝗼𝘂 𝗿𝗲𝗾𝘂𝗲𝘀𝘁𝗲𝗱 𝘁𝗼 𝗷𝗼𝗶𝗻 {chat.title}. "
            "𝗣𝗹𝗲𝗮𝘀𝗲 𝗽𝗿𝗼𝘃𝗲 𝘆𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮 𝗿𝗼𝗯𝗼𝘁 𝘁𝗼 𝗴𝗲𝘁 𝗮𝗰𝗰𝗲𝘀𝘀."
        )
        try:
            await bot.send_message(user_chat_id or user.id, text, reply_markup=robot_keyboard(me.username, payload))
            await db.mark_request(chat.id, user.id, "awaiting_verification")
            await db.log_event("verification_sent", f"Verification sent: {chat.title or chat.id}", {"chat_id": chat.id, "user_id": user.id})
        except Exception as exc:
            # Fallback to immediate approval if verification DM fails to send
            await db.log_event(
                "verification_dm_failed_fallback",
                f"Verification DM failed, approving directly: {chat.title or chat.id}",
                {"chat_id": chat.id, "user_id": user.id, "error": str(exc)},
                "warning",
            )
            await approve_stored_request(
                bot,
                db,
                item_data,
                "join_request_verification_fallback",
                notify_user=True,
            )
        return

    await approve_stored_request(
        bot,
        db,
        item_data,
        "join_request_update",
        notify_user=True,
    )
