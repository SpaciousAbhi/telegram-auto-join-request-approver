from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.keyboards import owner_panel_keyboard
from app.services.formatters import owner_dashboard
from app.services.telegram import safe_answer, safe_edit

router = Router()


class OwnerState(StatesGroup):
    adding_force_chat = State()
    broadcasting = State()


async def _is_owner(user_id: int, owner_id: int) -> bool:
    return user_id == owner_id


async def send_owner_panel(message: Message, db) -> None:
    settings = await db.settings()
    stats = await db.owner_stats()
    await message.answer(owner_dashboard(stats, settings), reply_markup=owner_panel_keyboard(settings))


@router.message(Command("owner"))
async def owner_command(message: Message, db, owner_id: int) -> None:
    if not await _is_owner(message.from_user.id, owner_id):
        return
    await send_owner_panel(message, db)


@router.callback_query(F.data == "owner:panel")
async def owner_panel(callback: CallbackQuery, db, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback)
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
    await safe_edit(callback.message, owner_dashboard(stats, settings), owner_panel_keyboard(settings))


@router.callback_query(F.data == "owner:force:add")
async def owner_force_add(callback: CallbackQuery, state: FSMContext, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback)
    await state.set_state(OwnerState.adding_force_chat)
    await safe_edit(
        callback.message,
        "➕ 𝗔𝗗𝗗 𝗙𝗢𝗥𝗖𝗘 𝗦𝗨𝗕𝗦𝗖𝗥𝗜𝗣𝗧𝗜𝗢𝗡 𝗖𝗛𝗔𝗧\n\n"
        "𝗙𝗼𝗿𝘄𝗮𝗿𝗱 𝗮 𝗺𝗲𝘀𝘀𝗮𝗴𝗲 𝗳𝗿𝗼𝗺 𝘁𝗵𝗲 𝗰𝗵𝗮𝘁, 𝗼𝗿 𝘀𝗲𝗻𝗱 𝗮 𝗽𝘂𝗯𝗹𝗶𝗰 @𝘂𝘀𝗲𝗿𝗻𝗮𝗺𝗲 / 𝗻𝘂𝗺𝗲𝗿𝗶𝗰 𝗰𝗵𝗮𝘁 𝗜𝗗 / 𝗶𝗻𝘃𝗶𝘁𝗲 𝗹𝗶𝗻𝗸.\n\n"
        "𝗔𝗱𝗱 ` request ` 𝗮𝘁 𝘁𝗵𝗲 𝗲𝗻𝗱 𝗳𝗼𝗿 𝗿𝗲𝗾𝘂𝗲𝘀𝘁-𝘁𝗼-𝗷𝗼𝗶𝗻 𝗺𝗼𝗱𝗲.",
    )


@router.message(OwnerState.adding_force_chat)
async def receive_force_chat(message: Message, state: FSMContext, bot: Bot, db, owner_id: int) -> None:
    if not await _is_owner(message.from_user.id, owner_id):
        return
    mode = "request" if (message.text or "").strip().lower().endswith(" request") else "join"
    target = None
    if message.forward_from_chat:
        target = message.forward_from_chat.id
    elif message.text:
        raw = message.text.strip().removesuffix(" request").strip()
        if raw.lstrip("-").isdigit():
            target = int(raw)
        elif raw.startswith("@"):
            target = raw
        elif "t.me/" in raw:
            target = raw.rstrip("/").split("/")[-1]
    if target is None:
        await message.answer("⚠️ 𝗖𝗢𝗨𝗟𝗗 𝗡𝗢𝗧 𝗥𝗘𝗔𝗗 𝗧𝗛𝗔𝗧 𝗖𝗛𝗔𝗧. 𝗧𝗥𝗬 𝗙𝗢𝗥𝗪𝗔𝗥𝗗𝗜𝗡𝗚 𝗔 𝗠𝗘𝗦𝗦𝗔𝗚𝗘.")
        return
    try:
        chat = await bot.get_chat(target)
        invite_link = chat.invite_link
        await db.add_force_chat(
            {
                "chat_id": chat.id,
                "title": chat.title or chat.full_name or str(chat.id),
                "type": chat.type,
                "username": chat.username,
                "invite_link": invite_link or (f"https://t.me/{chat.username}" if chat.username else None),
                "mode": mode,
                "added_by": owner_id,
            }
        )
        await state.clear()
        await message.answer(f"✅ 𝗙𝗢𝗥𝗖𝗘 𝗖𝗛𝗔𝗧 𝗔𝗗𝗗𝗘𝗗\n\n𝗡𝗔𝗠𝗘: {chat.title or chat.full_name}\n𝗠𝗢𝗗𝗘: {mode.upper()}")
    except Exception as exc:
        await message.answer(f"⚠️ 𝗙𝗢𝗥𝗖𝗘 𝗖𝗛𝗔𝗧 𝗘𝗥𝗥𝗢𝗥\n\n<code>{exc}</code>", parse_mode="HTML")


@router.callback_query(F.data == "owner:force:list")
async def owner_force_list(callback: CallbackQuery, db, owner_id: int) -> None:
    if not await _is_owner(callback.from_user.id, owner_id):
        return await safe_answer(callback, "Owner only", True)
    await safe_answer(callback)
    chats = await db.force_chats()
    if not chats:
        await safe_edit(callback.message, "📭 𝗡𝗢 𝗙𝗢𝗥𝗖𝗘 𝗖𝗛𝗔𝗧𝗦 𝗔𝗗𝗗𝗘𝗗.")
        return
    lines = ["📋 𝗙𝗢𝗥𝗖𝗘 𝗦𝗨𝗕𝗦𝗖𝗥𝗜𝗣𝗧𝗜𝗢𝗡 𝗖𝗛𝗔𝗧𝗦\n"]
    for item in chats:
        lines.append(f"• {item.get('title')} — {item.get('mode', 'join').upper()} — <code>{item['chat_id']}</code>")
        if item.get("last_error"):
            lines.append(f"  ⚠️ {item['last_error']}")
    await safe_edit(callback.message, "\n".join(lines), owner_panel_keyboard(await db.settings()))


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
