from __future__ import annotations

from typing import Any

from aiogram import Bot

from app.services.telegram import inspect_bot_permissions


def _mark(ok: bool) -> str:
    return "✅" if ok else "⚠️"


async def owner_health_text(db: Any) -> str:
    stats = await db.owner_stats()
    settings = await db.settings()
    recent = await db.recent_events(limit=6)
    lines = [
        "🧠 𝗦𝗬𝗦𝗧𝗘𝗠 𝗛𝗘𝗔𝗟𝗧𝗛",
        "",
        f"{_mark(stats['active_chats'] > 0)} 𝗔𝗖𝗧𝗜𝗩𝗘 𝗖𝗛𝗔𝗧𝗦: {stats['active_chats']} / {stats['connected_chats']}",
        f"{_mark(settings.get('bulk_approval_enabled'))} 𝗕𝗨𝗟𝗞 𝗔𝗣𝗣𝗥𝗢𝗩𝗔𝗟: {'𝗢𝗡' if settings.get('bulk_approval_enabled') else '𝗢𝗙𝗙'}",
        f"{_mark(True)} 𝗩𝗘𝗥𝗜𝗙𝗜𝗖𝗔𝗧𝗜𝗢𝗡: {'𝗢𝗡' if settings.get('verification_enabled') else '𝗢𝗙𝗙'}",
        f"{_mark(True)} 𝗙𝗢𝗥𝗖𝗘 𝗦𝗨𝗕: {'𝗢𝗡' if settings.get('force_subscription_enabled') else '𝗢𝗙𝗙'}",
        "",
        f"𝗝𝗢𝗜𝗡 𝗥𝗘𝗤𝗨𝗘𝗦𝗧𝗦 𝗦𝗘𝗘𝗡: {stats.get('join_requests', 0)}",
        f"𝗔𝗖𝗧𝗜𝗩𝗘 𝗕𝗨𝗟𝗞 𝗝𝗢𝗕𝗦: {stats['active_bulk_jobs']}",
        f"𝗪𝗔𝗥𝗡𝗜𝗡𝗚𝗦: {stats.get('warnings', 0)}",
        f"𝗘𝗥𝗥𝗢𝗥𝗦: {stats.get('errors', 0)}",
        "",
        "𝗥𝗘𝗖𝗘𝗡𝗧 𝗘𝗩𝗘𝗡𝗧𝗦:",
    ]
    lines.insert(8, f"NOTIFICATION FAILURES: {stats.get('notification_failures', 0)}")
    lines.insert(8, f"RETRY QUEUE: {stats.get('retrying_requests', 0)}")
    lines.insert(8, f"OPEN REQUEST STATES: {stats.get('open_requests', 0)}")
    if not recent:
        lines.append("• 𝗡𝗼 𝗲𝘃𝗲𝗻𝘁𝘀 𝗿𝗲𝗰𝗼𝗿𝗱𝗲𝗱 𝘆𝗲𝘁.")
    for event in recent:
        lines.append(f"• {event.get('severity', 'info').upper()} — {event.get('title', event.get('kind'))}")
    return "\n".join(lines)


async def audit_connected_chats(bot: Bot, db: Any, owner_id: int) -> str:
    chats = await db.chats_for_owner(owner_id)
    if not chats:
        return "📭 𝗡𝗢 𝗖𝗛𝗔𝗧𝗦 𝗧𝗢 𝗔𝗨𝗗𝗜𝗧."
    me = await bot.get_me()
    ok_count = warning_count = 0
    lines = ["🧪 𝗖𝗢𝗡𝗡𝗘𝗖𝗧𝗘𝗗 𝗖𝗛𝗔𝗧 𝗔𝗨𝗗𝗜𝗧", ""]
    for chat in chats[:30]:
        report = await inspect_bot_permissions(bot, chat["chat_id"], me.id)
        active = report.ok and not chat.get("removed_by_owner")
        await db.upsert_connected_chat(
            {
                **chat,
                "bot_is_admin": report.is_admin,
                "permissions_ok": report.ok,
                "missing_permissions": report.missing,
                "permission_status": report.status,
                "active": active,
                "last_error": None if report.ok else f"Missing permissions: {', '.join(report.missing) or report.status}",
            }
        )
        if active:
            ok_count += 1
        else:
            warning_count += 1
        lines.append(f"{_mark(active)} {chat.get('title', chat['chat_id'])} — {report.status}")
        if report.missing:
            lines.append(f"   𝗠𝗶𝘀𝘀𝗶𝗻𝗴: {', '.join(report.missing)}")
    lines.append("")
    lines.append(f"𝗥𝗘𝗔𝗗𝗬: {ok_count}")
    lines.append(f"𝗡𝗘𝗘𝗗𝗦 𝗙𝗜𝗫: {warning_count}")
    return "\n".join(lines)
