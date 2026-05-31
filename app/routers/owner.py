from __future__ import annotations

from html import escape

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.keyboards import force_mode_keyboard, owner_health_keyboard, owner_panel_keyboard, subscriber_trick_keyboard
from app.services.diagnostics import audit_connected_chats, owner_health_text
from app.services.formatters import owner_dashboard
from app.services.telegram import safe_answer, safe_edit

router = Router()


class OwnerState(StatesGroup):
    adding_force_chat = State()
    choosing_force_mode = State()
    adding_subscriber_chat = State()
    setting_subscriber_message = State()
    broadcasting = State()


async def _is_owner(user_id: int, owner_id: int) -> bool:
    return user_id == owner_id


def _chat_name(chat: dict) -> str:
    return escape(str(chat.get("title") or chat.get("chat_id") or "Unknown"))


def _button_title(chat: dict, limit: int = 34) -> str:
    title = str(chat.get("title") or chat.get("chat_id") or "Untitled").strip()
    if len(title) <= limit:
        return title
    return f"{title[: limit - 1]}…"


def _could_not_read_chat_text(error: Exception | None = None) -> str:
    text = (
        "⚠️ <b>COULD NOT READ THAT CHAT</b>\n\n"
        "Forward a message from the chat, send @username, send the numeric chat ID, or send a public t.me link."
    )
    if error:
        text += f"\n\n<code>{escape(str(error))}</code>"
    return text


def _force_add_prompt() -> str:
    return (
        "➕ <b>ADD FORCE SUBSCRIPTION CHAT</b>\n\n"
        "Send one chat identity now:\n"
        "• Forward a message from the chat\n"
        "• Send @username\n"
        "• Send numeric chat ID\n"
        "• Send a public t.me link\n\n"
        "<b>Join Mode</b>: user must already be a member.\n"
        "<b>Request Mode</b>: user must send a join request."
    )


def _subscriber_add_prompt() -> str:
    return (
        "➕ <b>ADD SUBSCRIBER CHANNEL</b>\n\n"
        "Forward a message, send @username, send chat ID, or send a public t.me link."
    )


async def send_owner_panel(message: Message, db) -> None:
    settings = await db.settings()
    stats = await db.owner_stats()
    await message.answer(owner_dashboard(stats, settings), reply_markup=owner_panel_keyboard(settings))


async def _resolve_chat_from_message(message: Message, bot: Bot) -> dict | None:
    target = None
    if message.forward_from_chat:
        target = message.forward_from_chat.id
    elif message.text:
        raw = message.text.strip()
        if raw.lstrip("-").isdigit():
            target = int(raw)
        elif raw.startswith("@"):
            target = raw
        elif "t.me/" in raw:
            target = raw.rstrip("/").split("/")[-1]
            if target.startswith("+"):
                return None
    if target is None:
        return None
    chat = await bot.get_chat(target)
    return {
        "chat_id": chat.id,
        "title": chat.title or chat.full_name or str(chat.id),
        "type": chat.type,
        "username": chat.username,
        "invite_link": chat.invite_link or (f"https://t.me/{chat.username}" if chat.username else None),
    }


@router.message(Command("owner"))
async def owner_command(message: Message, db, owner_id: int) -> None:
    if not await _is_owner(message.from_user.id, owner_id):
        return
    await send_owner_panel(message, db)


@router.callback_query(F.data == "owner:panel")
async def owner_panel(callback: CallbackQuery, state: FSMContext, db, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback, "Opening owner panel...")
    await state.clear()
    settings = await db.settings()
    stats = await db.owner_stats()
    await safe_edit(callback.message, owner_dashboard(stats, settings), owner_panel_keyboard(settings))


@router.callback_query(F.data.startswith("owner:toggle:"))
async def owner_toggle(callback: CallbackQuery, db, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback, "Updating setting...")
    key = callback.data.rsplit(":", 1)[1]
    settings = await db.settings()
    await db.set_setting(key, not bool(settings.get(key)))
    settings = await db.settings()
    stats = await db.owner_stats()
    if key.startswith("subscriber_trick"):
        await safe_edit(callback.message, subscriber_trick_text(settings, await db.subscriber_trick_chats()), subscriber_trick_keyboard(settings))
    else:
        await safe_edit(callback.message, owner_dashboard(stats, settings), owner_panel_keyboard(settings))


@router.callback_query(F.data == "owner:health")
async def owner_health(callback: CallbackQuery, db, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback, "Loading system health...")
    await safe_edit(callback.message, await owner_health_text(db), owner_health_keyboard())


@router.callback_query(F.data == "owner:audit_chats")
async def owner_audit_chats(callback: CallbackQuery, bot: Bot, db, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback, "Running chat audit...")
    text = await audit_connected_chats(bot, db, callback.from_user.id)
    await db.log_event("owner_audit", "Connected chat audit completed", {"owner_id": callback.from_user.id})
    await safe_edit(callback.message, text, owner_health_keyboard())


@router.callback_query(F.data == "owner:force:add")
async def owner_force_add(callback: CallbackQuery, state: FSMContext, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback, "Ready to add force chat...")
    await state.set_state(OwnerState.adding_force_chat)
    await safe_edit(callback.message, _force_add_prompt())


@router.message(OwnerState.adding_force_chat)
async def receive_force_chat(message: Message, state: FSMContext, bot: Bot, owner_id: int) -> None:
    if not await _is_owner(message.from_user.id, owner_id):
        return
    try:
        chat_data = await _resolve_chat_from_message(message, bot)
    except Exception as exc:
        await message.answer(_could_not_read_chat_text(exc), parse_mode="HTML")
        return
    if not chat_data:
        await message.answer(_could_not_read_chat_text(), parse_mode="HTML")
        return
    await state.update_data(force_chat=chat_data)
    await state.set_state(OwnerState.choosing_force_mode)
    await message.answer(
        f"✅ <b>CHAT FOUND</b>\n\n"
        f"<b>Name</b>: {_chat_name(chat_data)}\n"
        f"<b>ID</b>: <code>{chat_data['chat_id']}</code>\n\n"
        "Select how this chat should be used for force subscription.",
        reply_markup=force_mode_keyboard(chat_data["chat_id"]),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("owner:force:mode:"))
async def choose_force_mode(callback: CallbackQuery, state: FSMContext, bot: Bot, db, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback, "Saving force mode...")
    mode = callback.data.rsplit(":", 1)[1]
    data = await state.get_data()
    chat_data = data.get("force_chat")
    if not chat_data:
        await safe_edit(callback.message, "⚠️ <b>SESSION EXPIRED</b>\n\nStart adding the force chat again.", owner_panel_keyboard(await db.settings()))
        return
    last_error = None
    try:
        me = await bot.get_me()
        await bot.get_chat_member(chat_data["chat_id"], me.id)
    except Exception as exc:
        last_error = f"Bot cannot check this chat yet: {exc}"
    await db.add_force_chat({**chat_data, "mode": mode, "added_by": owner_id, "last_error": last_error})
    await db.log_event(
        "force_chat_added",
        f"Force chat added: {chat_data['title']}",
        {"chat_id": chat_data["chat_id"], "mode": mode, "last_error": last_error},
        "warning" if last_error else "info",
    )
    await state.clear()
    warning = ""
    if last_error:
        warning = f"\n\n⚠️ {escape(last_error)}\nAdd the bot to this chat so Check Access can verify users cleanly."
    await safe_edit(
        callback.message,
        f"✅ <b>FORCE CHAT ADDED</b>\n\n<b>Name</b>: {_chat_name(chat_data)}\n<b>Mode</b>: {mode.upper()}{warning}",
        owner_panel_keyboard(await db.settings()),
    )


@router.callback_query(F.data == "owner:force:list")
async def owner_force_list(callback: CallbackQuery, db, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback, "Opening force chats...")
    chats = await db.force_chats()
    if not chats:
        await safe_edit(callback.message, "📭 <b>NO FORCE CHATS ADDED</b>", owner_panel_keyboard(await db.settings()))
        return
    lines = ["📋 <b>FORCE SUBSCRIPTION CHATS</b>", ""]
    keyboard = []
    for item in chats:
        lines.append(f"• {_chat_name(item)} - {escape(str(item.get('mode', 'join')).upper())} - <code>{item['chat_id']}</code>")
        keyboard.append([InlineKeyboardButton(text=f"🗑 Remove • {_button_title(item)}", callback_data=f"owner:force:remove:{item['chat_id']}")])
        if item.get("last_error"):
            lines.append(f"  ⚠️ {escape(str(item['last_error']))}")
    keyboard.append([InlineKeyboardButton(text="⬅️ Back", callback_data="owner:panel")])
    await safe_edit(callback.message, "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=keyboard))


@router.callback_query(F.data.startswith("owner:force:remove:"))
async def remove_force_chat(callback: CallbackQuery, db, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback, "Removing force chat...")
    chat_id = int(callback.data.rsplit(":", 1)[1])
    await db.remove_force_chat(chat_id)
    await safe_edit(callback.message, "✅ <b>FORCE CHAT REMOVED</b>", owner_panel_keyboard(await db.settings()))


def subscriber_trick_text(settings: dict, chats: list[dict]) -> str:
    mode = "Required" if settings.get("subscriber_trick_required") else "Optional"
    status = "ON" if settings.get("subscriber_trick_enabled") else "OFF"
    message = escape(str(settings.get("subscriber_trick_message") or "No message set yet."))
    return (
        "👑 <b>SUBSCRIBER TRICK</b>\n\n"
        "Shown only after a user's join request is approved. Keep this message short and action-focused.\n\n"
        f"<b>Status</b>: {status}\n"
        f"<b>Mode</b>: {mode}\n"
        f"<b>Channels</b>: {len(chats)}\n\n"
        f"<b>Message</b>:\n{message}"
    )


@router.callback_query(F.data == "owner:sub:panel")
async def subscriber_panel(callback: CallbackQuery, db, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback, "Opening subscriber tools...")
    settings = await db.settings()
    await safe_edit(callback.message, subscriber_trick_text(settings, await db.subscriber_trick_chats()), subscriber_trick_keyboard(settings))


@router.callback_query(F.data == "owner:sub:add")
async def subscriber_add(callback: CallbackQuery, state: FSMContext, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback, "Ready to add channel...")
    await state.set_state(OwnerState.adding_subscriber_chat)
    await safe_edit(callback.message, _subscriber_add_prompt())


@router.message(OwnerState.adding_subscriber_chat)
async def receive_subscriber_chat(message: Message, state: FSMContext, bot: Bot, db, owner_id: int) -> None:
    if not await _is_owner(message.from_user.id, owner_id):
        return
    try:
        chat_data = await _resolve_chat_from_message(message, bot)
    except Exception as exc:
        await message.answer(_could_not_read_chat_text(exc), parse_mode="HTML")
        return
    if not chat_data:
        await message.answer(_could_not_read_chat_text(), parse_mode="HTML")
        return
    await db.add_subscriber_trick_chat({**chat_data, "added_by": owner_id})
    await state.clear()
    await message.answer(
        f"✅ <b>SUBSCRIBER CHANNEL ADDED</b>\n\n<b>Name</b>: {_chat_name(chat_data)}",
        reply_markup=subscriber_trick_keyboard(await db.settings()),
    )


@router.callback_query(F.data == "owner:sub:list")
async def subscriber_list(callback: CallbackQuery, db, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback, "Opening channel list...")
    chats = await db.subscriber_trick_chats()
    if not chats:
        await safe_edit(callback.message, "📭 <b>NO SUBSCRIBER CHANNELS ADDED</b>", subscriber_trick_keyboard(await db.settings()))
        return
    lines = ["📋 <b>SUBSCRIBER CHANNELS</b>", ""]
    keyboard = []
    for item in chats:
        lines.append(f"• {_chat_name(item)} - <code>{item['chat_id']}</code>")
        keyboard.append([InlineKeyboardButton(text=f"🗑 Remove • {_button_title(item)}", callback_data=f"owner:sub:remove:{item['chat_id']}")])
    keyboard.append([InlineKeyboardButton(text="⬅️ Back", callback_data="owner:sub:panel")])
    await safe_edit(callback.message, "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=keyboard))


@router.callback_query(F.data.startswith("owner:sub:remove:"))
async def subscriber_remove(callback: CallbackQuery, db, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback, "Removing channel...")
    chat_id = int(callback.data.rsplit(":", 1)[1])
    await db.remove_subscriber_trick_chat(chat_id)
    await safe_edit(callback.message, "✅ <b>SUBSCRIBER CHANNEL REMOVED</b>", subscriber_trick_keyboard(await db.settings()))


@router.callback_query(F.data == "owner:sub:message")
async def subscriber_message(callback: CallbackQuery, state: FSMContext, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback, "Waiting for new message...")
    await state.set_state(OwnerState.setting_subscriber_message)
    await safe_edit(callback.message, "✏️ <b>SEND THE NEW SUBSCRIBER MESSAGE</b>\n\nThis message is shown after approval.")


@router.message(OwnerState.setting_subscriber_message)
async def receive_subscriber_message(message: Message, state: FSMContext, db, owner_id: int) -> None:
    if not await _is_owner(message.from_user.id, owner_id):
        return
    await db.set_setting("subscriber_trick_message", message.html_text or message.text or "")
    await state.clear()
    await message.answer("✅ <b>SUBSCRIBER MESSAGE UPDATED</b>", reply_markup=subscriber_trick_keyboard(await db.settings()))


@router.callback_query(F.data == "owner:broadcast")
async def owner_broadcast(callback: CallbackQuery, state: FSMContext, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback, "Ready to broadcast...")
    await state.set_state(OwnerState.broadcasting)
    await safe_edit(callback.message, "📣 <b>SEND OR FORWARD THE BROADCAST MESSAGE</b>\n\nIt will be copied to active bot users.")


@router.message(OwnerState.broadcasting)
async def receive_broadcast(message: Message, state: FSMContext, bot: Bot, db, owner_id: int) -> None:
    if not await _is_owner(message.from_user.id, owner_id):
        return
    users = await db.db.users.find({"banned": {"$ne": True}}, {"user_id": 1}).to_list(length=None)
    total = len(users)
    sent = failed = blocked = 0
    progress = await message.answer(f"📣 <b>BROADCAST STARTED</b>\n\n<b>Total</b>: {total}\n<b>Sent</b>: 0")
    for index, user in enumerate(users, start=1):
        try:
            await message.copy_to(user["user_id"])
            sent += 1
        except Exception as exc:
            failed += 1
            if "bot was blocked" in str(exc).lower():
                blocked += 1
        if index == 1 or index % 25 == 0 or index == total:
            await progress.edit_text(
                f"📣 <b>BROADCAST RUNNING</b>\n\n"
                f"<b>Total</b>: {total}\n"
                f"<b>Sent</b>: {sent}\n"
                f"<b>Failed</b>: {failed}\n"
                f"<b>Blocked</b>: {blocked}\n"
                f"<b>Remaining</b>: {total - index}"
            )
    await state.clear()
    await progress.edit_text(
        f"✅ <b>BROADCAST COMPLETE</b>\n\n"
        f"<b>Total</b>: {total}\n"
        f"<b>Sent</b>: {sent}\n"
        f"<b>Failed</b>: {failed}\n"
        f"<b>Blocked</b>: {blocked}"
    )
