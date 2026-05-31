from __future__ import annotations

from html import escape
from typing import Any

from aiogram import Bot

from app.bold import bold
from app.services.telegram import inspect_bot_permissions


def _mark(ok: bool) -> str:
    return "✅" if ok else "⚠️"


def _toggle(value: object) -> str:
    return "ON" if value else "OFF"


async def owner_health_text(db: Any) -> str:
    stats = await db.owner_stats()
    settings = await db.settings()
    recent = await db.recent_events(limit=6)
    lines = [
        f"🧠 {bold('SYSTEM HEALTH')}",
        "",
        f"🛡 {bold('READINESS')}",
        f"{_mark(stats['active_chats'] > 0)} {bold('Active Chats')}: {stats['active_chats']} / {stats['connected_chats']}",
        f"{_mark(settings.get('bulk_approval_enabled'))} {bold('Bulk Approval')}: {_toggle(settings.get('bulk_approval_enabled'))}",
        f"{_mark(True)} {bold('Verification')}: {_toggle(settings.get('verification_enabled'))}",
        f"{_mark(True)} {bold('Force Sub')}: {_toggle(settings.get('force_subscription_enabled'))}",
        "",
        f"📦 {bold('QUEUE')}",
        f"{bold('Open Request States')}: {stats.get('open_requests', 0)}",
        f"{bold('Retry Queue')}: {stats.get('retrying_requests', 0)}",
        f"{bold('Notification Failures')}: {stats.get('notification_failures', 0)}",
        f"{bold('Join Requests Seen')}: {stats.get('join_requests', 0)}",
        f"{bold('Active Bulk Jobs')}: {stats['active_bulk_jobs']}",
        "",
        f"⚠️ {bold('SIGNALS')}",
        f"{bold('Warnings')}: {stats.get('warnings', 0)}",
        f"{bold('Errors')}: {stats.get('errors', 0)}",
        "",
        f"🧾 {bold('RECENT EVENTS')}",
    ]
    if not recent:
        lines.append("No events recorded yet.")
    for event in recent:
        title = escape(str(event.get("title", event.get("kind", "event"))))
        lines.append(f"• {event.get('severity', 'info').upper()} - {title}")
    return "\n".join(lines)


async def audit_connected_chats(bot: Bot, db: Any, owner_id: int) -> str:
    chats = await db.chats_for_owner(owner_id)
    if not chats:
        return f"📭 {bold('NO CHATS TO AUDIT')}\n\nAdd the bot to a channel or group first."
    me = await bot.get_me()
    ok_count = warning_count = 0
    lines = [f"🧪 {bold('CONNECTED CHAT AUDIT')}", ""]
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
        title = escape(str(chat.get("title", chat["chat_id"])))
        lines.append(f"{_mark(active)} {title} - {escape(str(report.status))}")
        if report.missing:
            lines.append(f"   Missing: {escape(', '.join(report.missing))}")
    lines.append("")
    lines.append(f"{bold('Ready')}: {ok_count}")
    lines.append(f"{bold('Needs Fix')}: {warning_count}")
    return "\n".join(lines)
