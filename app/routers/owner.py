from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.keyboards import force_mode_keyboard, owner_health_keyboard, owner_panel_keyboard, subscriber_trick_keyboard
from app.services.formatters import owner_dashboard
from app.services.diagnostics import audit_connected_chats, owner_health_text
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
    await safe_answer(callback)
    await state.clear()
    settings = await db.settings()
    stats = await db.owner_stats()
    await safe_edit(callback.message, owner_dashboard(stats, settings), owner_panel_keyboard(settings))


@router.callback_query(F.data.startswith("owner:toggle:"))
async def owner_toggle(callback: CallbackQuery, db, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback)
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
    await safe_answer(callback)
    await safe_edit(callback.message, await owner_health_text(db), owner_health_keyboard())


@router.callback_query(F.data == "owner:audit_chats")
async def owner_audit_chats(callback: CallbackQuery, bot: Bot, db, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback)
    text = await audit_connected_chats(bot, db, callback.from_user.id)
    await db.log_event("owner_audit", "Connected chat audit completed", {"owner_id": callback.from_user.id})
    await safe_edit(callback.message, text, owner_health_keyboard())


@router.callback_query(F.data == "owner:force:add")
async def owner_force_add(callback: CallbackQuery, state: FSMContext, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback)
    await state.set_state(OwnerState.adding_force_chat)
    await safe_edit(
        callback.message,
        "➕ 𝗔𝗗𝗗 𝗙𝗢𝗥𝗖𝗘 𝗦𝗨𝗕𝗦𝗖𝗥𝗜𝗣𝗧𝗜𝗢𝗡 𝗖𝗛𝗔𝗧\n\n"
        "𝗦𝗲𝗻𝗱 𝗼𝗻𝗲 𝗰𝗵𝗮𝘁 𝗶𝗱𝗲𝗻𝘁𝗶𝘁𝘆 𝗻𝗼𝘄:\n"
        "• 𝗙𝗼𝗿𝘄𝗮𝗿𝗱 𝗮 𝗺𝗲𝘀𝘀𝗮𝗴𝗲 𝗳𝗿𝗼𝗺 𝘁𝗵𝗲 𝗰𝗵𝗮𝘁\n"
        "• 𝗦𝗲𝗻𝗱 @𝘂𝘀𝗲𝗿𝗻𝗮𝗺𝗲\n"
        "• 𝗦𝗲𝗻𝗱 𝗻𝘂𝗺𝗲𝗿𝗶𝗰 𝗰𝗵𝗮𝘁 𝗜𝗗\n"
        "• 𝗦𝗲𝗻𝗱 𝗮 𝗽𝘂𝗯𝗹𝗶𝗰 𝘁.𝗺𝗲 𝗹𝗶𝗻𝗸\n\n"
        "𝗔𝗳𝘁𝗲𝗿 𝗜 𝗿𝗲𝗮𝗱 𝘁𝗵𝗲 𝗰𝗵𝗮𝘁, 𝘆𝗼𝘂 𝘄𝗶𝗹𝗹 𝗰𝗵𝗼𝗼𝘀𝗲 𝗼𝗻𝗲 𝗺𝗼𝗱𝗲:\n\n"
        "𝗝𝗢𝗜𝗡 𝗠𝗢𝗗𝗘: 𝗨𝘀𝗲𝗿 𝗺𝘂𝘀𝘁 𝗷𝗼𝗶𝗻 𝘁𝗵𝗲 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 / 𝗴𝗿𝗼𝘂𝗽.\n"
        "𝗥𝗘𝗤𝗨𝗘𝗦𝗧 𝗠𝗢𝗗𝗘: 𝗨𝘀𝗲𝗿 𝗺𝘂𝘀𝘁 𝘀𝗲𝗻𝗱 𝗮 𝗷𝗼𝗶𝗻 𝗿𝗲𝗾𝘂𝗲𝘀𝘁.",
    )


@router.message(OwnerState.adding_force_chat)
async def receive_force_chat(message: Message, state: FSMContext, bot: Bot, owner_id: int) -> None:
    if not await _is_owner(message.from_user.id, owner_id):
        return
    try:
        chat_data = await _resolve_chat_from_message(message, bot)
    except Exception as exc:
        await message.answer(f"⚠️ 𝗖𝗢𝗨𝗟𝗗 𝗡𝗢𝗧 𝗥𝗘𝗔𝗗 𝗧𝗛𝗔𝗧 𝗖𝗛𝗔𝗧.\n\n<code>{exc}</code>\n\n𝗧𝗿𝘆 𝗳𝗼𝗿𝘄𝗮𝗿𝗱𝗶𝗻𝗴 𝗮 𝗺𝗲𝘀𝘀𝗮𝗴𝗲 𝗳𝗿𝗼𝗺 𝘁𝗵𝗲 𝗰𝗵𝗮𝘁.", parse_mode="HTML")
        return
    if not chat_data:
        await message.answer("⚠️ 𝗖𝗢𝗨𝗟𝗗 𝗡𝗢𝗧 𝗥𝗘𝗔𝗗 𝗧𝗛𝗔𝗧 𝗖𝗛𝗔𝗧.\n\n𝗙𝗼𝗿 𝗽𝗿𝗶𝘃𝗮𝘁𝗲 𝗶𝗻𝘃𝗶𝘁𝗲 𝗹𝗶𝗻𝗸𝘀, 𝗳𝗼𝗿𝘄𝗮𝗿𝗱 𝗮 𝗺𝗲𝘀𝘀𝗮𝗴𝗲 𝗳𝗿𝗼𝗺 𝘁𝗵𝗲 𝗰𝗵𝗮𝘁 𝗼𝗿 𝘀𝗲𝗻𝗱 𝘁𝗵𝗲 𝗻𝘂𝗺𝗲𝗿𝗶𝗰 𝗜𝗗.")
        return
    await state.update_data(force_chat=chat_data)
    await state.set_state(OwnerState.choosing_force_mode)
    await message.answer(
        f"✅ 𝗖𝗛𝗔𝗧 𝗙𝗢𝗨𝗡𝗗\n\n𝗡𝗔𝗠𝗘: {chat_data['title']}\n𝗜𝗗: <code>{chat_data['chat_id']}</code>\n\n𝗦𝗲𝗹𝗲𝗰𝘁 𝗙𝗼𝗿𝗰𝗲 𝗦𝘂𝗯𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻 𝗠𝗼𝗱𝗲 𝗳𝗼𝗿 𝘁𝗵𝗶𝘀 𝗰𝗵𝗮𝘁.",
        reply_markup=force_mode_keyboard(chat_data["chat_id"]),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("owner:force:mode:"))
async def choose_force_mode(callback: CallbackQuery, state: FSMContext, bot: Bot, db, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback)
    mode = callback.data.rsplit(":", 1)[1]
    data = await state.get_data()
    chat_data = data.get("force_chat")
    if not chat_data:
        await safe_edit(callback.message, "⚠️ 𝗦𝗘𝗦𝗦𝗜𝗢𝗡 𝗘𝗫𝗣𝗜𝗥𝗘𝗗. 𝗣𝗹𝗲𝗮𝘀𝗲 𝘀𝘁𝗮𝗿𝘁 𝗮𝗱𝗱𝗶𝗻𝗴 𝘁𝗵𝗲 𝗳𝗼𝗿𝗰𝗲 𝗰𝗵𝗮𝘁 𝗮𝗴𝗮𝗶𝗻.", owner_panel_keyboard(await db.settings()))
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
    warning = f"\n\n⚠️ {last_error}\n𝗔𝗱𝗱 𝘁𝗵𝗲 𝗯𝗼𝘁 𝘁𝗼 𝘁𝗵𝗶𝘀 𝗰𝗵𝗮𝘁 𝘀𝗼 𝗖𝗵𝗲𝗰𝗸 𝗔𝗰𝗰𝗲𝘀𝘀 𝗰𝗮𝗻 𝘄𝗼𝗿𝗸." if last_error else ""
    await safe_edit(callback.message, f"✅ 𝗙𝗢𝗥𝗖𝗘 𝗖𝗛𝗔𝗧 𝗔𝗗𝗗𝗘𝗗\n\n𝗡𝗔𝗠𝗘: {chat_data['title']}\n𝗠𝗢𝗗𝗘: {mode.upper()}{warning}", owner_panel_keyboard(await db.settings()))


@router.callback_query(F.data == "owner:force:list")
async def owner_force_list(callback: CallbackQuery, db, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback)
    chats = await db.force_chats()
    if not chats:
        await safe_edit(callback.message, "📭 𝗡𝗢 𝗙𝗢𝗥𝗖𝗘 𝗖𝗛𝗔𝗧𝗦 𝗔𝗗𝗗𝗘𝗗.", owner_panel_keyboard(await db.settings()))
        return
    lines = ["📋 𝗙𝗢𝗥𝗖𝗘 𝗦𝗨𝗕𝗦𝗖𝗥𝗜𝗣𝗧𝗜𝗢𝗡 𝗖𝗛𝗔𝗧𝗦\n"]
    keyboard = []
    for item in chats:
        lines.append(f"• {item.get('title')} — {item.get('mode', 'join').upper()} — <code>{item['chat_id']}</code>")
        keyboard.append([InlineKeyboardButton(text=f"🗑 𝗥𝗘𝗠𝗢𝗩𝗘 • {item.get('title')}", callback_data=f"owner:force:remove:{item['chat_id']}")])
        if item.get("last_error"):
            lines.append(f"  ⚠️ {item['last_error']}")
    keyboard.append([InlineKeyboardButton(text="⬅️ 𝗕𝗔𝗖𝗞", callback_data="owner:panel")])
    await safe_edit(callback.message, "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=keyboard))


@router.callback_query(F.data.startswith("owner:force:remove:"))
async def remove_force_chat(callback: CallbackQuery, db, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback)
    chat_id = int(callback.data.rsplit(":", 1)[1])
    await db.remove_force_chat(chat_id)
    await safe_edit(callback.message, "✅ 𝗙𝗢𝗥𝗖𝗘 𝗖𝗛𝗔𝗧 𝗥𝗘𝗠𝗢𝗩𝗘𝗗.", owner_panel_keyboard(await db.settings()))


def subscriber_trick_text(settings: dict, chats: list[dict]) -> str:
    mode = "𝗥𝗘𝗤𝗨𝗜𝗥𝗘𝗗" if settings.get("subscriber_trick_required") else "𝗢𝗣𝗧𝗜𝗢𝗡𝗔𝗟"
    status = "𝗢𝗡" if settings.get("subscriber_trick_enabled") else "𝗢𝗙𝗙"
    return (
        "👑 𝗦𝗨𝗕𝗦𝗖𝗥𝗜𝗕𝗘𝗥 𝗔𝗗𝗗𝗜𝗡𝗚 𝗧𝗥𝗜𝗖𝗞\n\n"
        "𝗧𝗵𝗶𝘀 𝗶𝘀 𝘀𝗲𝗽𝗮𝗿𝗮𝘁𝗲 𝗳𝗿𝗼𝗺 𝗙𝗼𝗿𝗰𝗲 𝗦𝘂𝗯𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻. 𝗜𝘁 𝗼𝗻𝗹𝘆 𝗮𝗽𝗽𝗲𝗮𝗿𝘀 𝗮𝗳𝘁𝗲𝗿 𝗮 𝗷𝗼𝗶𝗻𝗶𝗻𝗴 𝘂𝘀𝗲𝗿 𝘃𝗲𝗿𝗶𝗳𝗶𝗲𝘀 𝗮𝗻𝗱 𝘁𝗵𝗲𝗶𝗿 𝗿𝗲𝗾𝘂𝗲𝘀𝘁 𝗶𝘀 𝗮𝗰𝗰𝗲𝗽𝘁𝗲𝗱.\n\n"
        f"𝗦𝗧𝗔𝗧𝗨𝗦: {status}\n"
        f"𝗠𝗢𝗗𝗘: {mode}\n"
        f"𝗖𝗛𝗔𝗡𝗡𝗘𝗟𝗦: {len(chats)}\n\n"
        f"𝗠𝗘𝗦𝗦𝗔𝗚𝗘:\n{settings.get('subscriber_trick_message')}"
    )


@router.callback_query(F.data == "owner:sub:panel")
async def subscriber_panel(callback: CallbackQuery, db, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback)
    settings = await db.settings()
    await safe_edit(callback.message, subscriber_trick_text(settings, await db.subscriber_trick_chats()), subscriber_trick_keyboard(settings))


@router.callback_query(F.data == "owner:sub:add")
async def subscriber_add(callback: CallbackQuery, state: FSMContext, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback)
    await state.set_state(OwnerState.adding_subscriber_chat)
    await safe_edit(callback.message, "➕ 𝗔𝗗𝗗 𝗦𝗨𝗕𝗦𝗖𝗥𝗜𝗕𝗘𝗥 𝗧𝗥𝗜𝗖𝗞 𝗖𝗛𝗔𝗡𝗡𝗘𝗟\n\n𝗙𝗼𝗿𝘄𝗮𝗿𝗱 𝗮 𝗺𝗲𝘀𝘀𝗮𝗴𝗲, 𝘀𝗲𝗻𝗱 @𝘂𝘀𝗲𝗿𝗻𝗮𝗺𝗲, 𝗰𝗵𝗮𝘁 𝗜𝗗, 𝗼𝗿 𝗽𝘂𝗯𝗹𝗶𝗰 𝘁.𝗺𝗲 𝗹𝗶𝗻𝗸.")


@router.message(OwnerState.adding_subscriber_chat)
async def receive_subscriber_chat(message: Message, state: FSMContext, bot: Bot, db, owner_id: int) -> None:
    if not await _is_owner(message.from_user.id, owner_id):
        return
    try:
        chat_data = await _resolve_chat_from_message(message, bot)
    except Exception as exc:
        await message.answer(f"⚠️ 𝗖𝗢𝗨𝗟𝗗 𝗡𝗢𝗧 𝗥𝗘𝗔𝗗 𝗧𝗛𝗔𝗧 𝗖𝗛𝗔𝗧.\n\n<code>{exc}</code>", parse_mode="HTML")
        return
    if not chat_data:
        await message.answer("⚠️ 𝗖𝗢𝗨𝗟𝗗 𝗡𝗢𝗧 𝗥𝗘𝗔𝗗 𝗧𝗛𝗔𝗧 𝗖𝗛𝗔𝗧. 𝗧𝗿𝘆 𝗳𝗼𝗿𝘄𝗮𝗿𝗱𝗶𝗻𝗴 𝗮 𝗺𝗲𝘀𝘀𝗮𝗴𝗲.")
        return
    await db.add_subscriber_trick_chat({**chat_data, "added_by": owner_id})
    await state.clear()
    await message.answer(f"✅ 𝗦𝗨𝗕𝗦𝗖𝗥𝗜𝗕𝗘𝗥 𝗧𝗥𝗜𝗖𝗞 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗔𝗗𝗗𝗘𝗗\n\n𝗡𝗔𝗠𝗘: {chat_data['title']}", reply_markup=subscriber_trick_keyboard(await db.settings()))


@router.callback_query(F.data == "owner:sub:list")
async def subscriber_list(callback: CallbackQuery, db, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback)
    chats = await db.subscriber_trick_chats()
    if not chats:
        await safe_edit(callback.message, "📭 𝗡𝗢 𝗦𝗨𝗕𝗦𝗖𝗥𝗜𝗕𝗘𝗥 𝗧𝗥𝗜𝗖𝗞 𝗖𝗛𝗔𝗡𝗡𝗘𝗟𝗦 𝗔𝗗𝗗𝗘𝗗.", subscriber_trick_keyboard(await db.settings()))
        return
    lines = ["📋 𝗦𝗨𝗕𝗦𝗖𝗥𝗜𝗕𝗘𝗥 𝗧𝗥𝗜𝗖𝗞 𝗖𝗛𝗔𝗡𝗡𝗘𝗟𝗦\n"]
    keyboard = []
    for item in chats:
        lines.append(f"• {item.get('title')} — <code>{item['chat_id']}</code>")
        keyboard.append([InlineKeyboardButton(text=f"🗑 𝗥𝗘𝗠𝗢𝗩𝗘 • {item.get('title')}", callback_data=f"owner:sub:remove:{item['chat_id']}")])
    keyboard.append([InlineKeyboardButton(text="⬅️ 𝗕𝗔𝗖𝗞", callback_data="owner:sub:panel")])
    await safe_edit(callback.message, "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=keyboard))


@router.callback_query(F.data.startswith("owner:sub:remove:"))
async def subscriber_remove(callback: CallbackQuery, db, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback)
    chat_id = int(callback.data.rsplit(":", 1)[1])
    await db.remove_subscriber_trick_chat(chat_id)
    await safe_edit(callback.message, "✅ 𝗦𝗨𝗕𝗦𝗖𝗥𝗜𝗕𝗘𝗥 𝗧𝗥𝗜𝗖𝗞 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗥𝗘𝗠𝗢𝗩𝗘𝗗.", subscriber_trick_keyboard(await db.settings()))


@router.callback_query(F.data == "owner:sub:message")
async def subscriber_message(callback: CallbackQuery, state: FSMContext, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback)
    await state.set_state(OwnerState.setting_subscriber_message)
    await safe_edit(callback.message, "✏️ 𝗦𝗘𝗡𝗗 𝗧𝗛𝗘 𝗡𝗘𝗪 𝗦𝗨𝗕𝗦𝗖𝗥𝗜𝗕𝗘𝗥 𝗧𝗥𝗜𝗖𝗞 𝗠𝗘𝗦𝗦𝗔𝗚𝗘.")


@router.message(OwnerState.setting_subscriber_message)
async def receive_subscriber_message(message: Message, state: FSMContext, db, owner_id: int) -> None:
    if not await _is_owner(message.from_user.id, owner_id):
        return
    await db.set_setting("subscriber_trick_message", message.html_text or message.text or "")
    await state.clear()
    await message.answer("✅ 𝗦𝗨𝗕𝗦𝗖𝗥𝗜𝗕𝗘𝗥 𝗧𝗥𝗜𝗖𝗞 𝗠𝗘𝗦𝗦𝗔𝗚𝗘 𝗨𝗣𝗗𝗔𝗧𝗘𝗗.", reply_markup=subscriber_trick_keyboard(await db.settings()))


@router.callback_query(F.data == "owner:broadcast")
async def owner_broadcast(callback: CallbackQuery, state: FSMContext, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback)
    await state.set_state(OwnerState.broadcasting)
    await safe_edit(callback.message, "📣 𝗦𝗘𝗡𝗗 𝗢𝗥 𝗙𝗢𝗥𝗪𝗔𝗥𝗗 𝗧𝗛𝗘 𝗠𝗘𝗦𝗦𝗔𝗚𝗘 𝗬𝗢𝗨 𝗪𝗔𝗡𝗧 𝗧𝗢 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧.")


@router.message(OwnerState.broadcasting)
async def receive_broadcast(message: Message, state: FSMContext, bot: Bot, db, owner_id: int) -> None:
    if not await _is_owner(message.from_user.id, owner_id):
        return
    users = await db.db.users.find({"banned": {"$ne": True}}, {"user_id": 1}).to_list(length=None)
    total = len(users)
    sent = failed = blocked = 0
    progress = await message.answer(f"📣 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧 𝗦𝗧𝗔𝗥𝗧𝗘𝗗\n\n𝗧𝗢𝗧𝗔𝗟: {total}\n𝗦𝗘𝗡𝗧: 0")
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
                f"📣 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧 𝗥𝗨𝗡𝗡𝗜𝗡𝗚\n\n𝗧𝗢𝗧𝗔𝗟: {total}\n𝗦𝗘𝗡𝗧: {sent}\n𝗙𝗔𝗜𝗟𝗘𝗗: {failed}\n𝗕𝗟𝗢𝗖𝗞𝗘𝗗: {blocked}\n𝗥𝗘𝗠𝗔𝗜𝗡𝗜𝗡𝗚: {total - index}"
            )
    await state.clear()
    await progress.edit_text(f"✅ 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘\n\n𝗧𝗢𝗧𝗔𝗟: {total}\n𝗦𝗘𝗡𝗧: {sent}\n𝗙𝗔𝗜𝗟𝗘𝗗: {failed}\n𝗕𝗟𝗢𝗖𝗞𝗘𝗗: {blocked}")
