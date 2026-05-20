from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.types import ChatJoinRequest, ChatMemberUpdated

from app.i18n import t
from app.keyboards import chat_manage_keyboard, robot_keyboard
from app.services.formatters import connected_chat_report
from app.services.telegram import approve_join_request, inspect_bot_permissions

router = Router()


@router.my_chat_member()
async def bot_membership_changed(event: ChatMemberUpdated, bot: Bot, db) -> None:
    chat = event.chat
    user = event.from_user
    me = await bot.get_me()
    if event.new_chat_member.status in {"left", "kicked"}:
        await db.mark_chat_inactive(chat.id, "Bot removed from chat")
        return
    if event.new_chat_member.status not in {"administrator", "member"}:
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
    settings = await db.settings()
    chat = request.chat
    user = request.from_user
    invite = request.invite_link.invite_link if request.invite_link else None
    await db.add_pending_request(chat, user, invite)
    if await db.db.force_chats.find_one({"chat_id": chat.id, "active": True, "mode": "request"}):
        await db.mark_join_request_sent(user.id, chat.id)
    if settings.get("verification_enabled"):
        me = await bot.get_me()
        payload = f"verify_{chat.id}_{user.id}"
        text = (
            f"𝗛𝗲𝗹𝗹𝗼, 𝘆𝗼𝘂 𝗿𝗲𝗾𝘂𝗲𝘀𝘁𝗲𝗱 𝘁𝗼 𝗷𝗼𝗶𝗻 {chat.title}. "
            "𝗣𝗹𝗲𝗮𝘀𝗲 𝗽𝗿𝗼𝘃𝗲 𝘆𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮 𝗿𝗼𝗯𝗼𝘁 𝘁𝗼 𝗴𝗲𝘁 𝗮𝗰𝗰𝗲𝘀𝘀."
        )
        try:
            await bot.send_message(user.id, text, reply_markup=robot_keyboard(me.username, payload))
        except Exception as exc:
            await db.mark_request(chat.id, user.id, "verification_dm_failed", str(exc))
        return
    ok, error = await approve_join_request(bot, chat.id, user.id)
    await db.mark_request(chat.id, user.id, "approved" if ok else "failed", error)
    await db.record_approval(chat.id, ok)
