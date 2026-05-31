from __future__ import annotations

from html import escape

from app.bold import bold


def _value(value: object, fallback: str = "Not set") -> str:
    if value is None or value == "":
        return fallback
    return escape(str(value))


def _enabled(value: object) -> str:
    return "ON" if value else "OFF"


def connected_chat_report(chat: dict) -> str:
    title = _value(chat.get("title"), "Unknown")
    username = f"@{_value(chat['username'])}" if chat.get("username") else "Not set"
    chat_type = bold(str(chat.get("type", "unknown")).upper())
    permission_line = "✅ Ready" if chat.get("permissions_ok") else "⚠️ Needs admin rights"
    active_line = "✅ ON" if chat.get("active") else "⛔ OFF"
    admin_line = "✅ Yes" if chat.get("bot_is_admin") else "❌ No"
    member_count = _value(chat.get("member_count"), "Unknown")

    if chat.get("permissions_ok"):
        guidance = "New join requests in this chat are ready for automatic approval."
    else:
        missing = ", ".join(chat.get("missing_permissions") or []) or chat.get("permission_status") or "required rights"
        guidance = f"Fix bot admin permissions before new requests can be approved. Missing: {escape(str(missing))}."

    return (
        f"✅ {bold('CHAT CONNECTED')}\n\n"
        f"{guidance}\n\n"
        f"📌 {bold('CHAT')}\n"
        f"{bold('Name')}: {title}\n"
        f"{bold('Type')}: {chat_type}\n"
        f"{bold('ID')}: <code>{chat.get('chat_id')}</code>\n"
        f"{bold('Username')}: {username}\n\n"
        f"🛡 {bold('STATUS')}\n"
        f"{bold('Bot Admin')}: {admin_line}\n"
        f"{bold('Permissions')}: {permission_line}\n"
        f"{bold('Auto Approve')}: {active_line}\n"
        f"{bold('Members')}: {member_count}\n\n"
        f"📈 {bold('RESULTS')}\n"
        f"{bold('Approved')}: {chat.get('total_approved', 0)}\n"
        f"{bold('Failed')}: {chat.get('failed_approvals', 0)}"
    )


def owner_dashboard(stats: dict, settings: dict) -> str:
    return (
        f"👑 {bold('OWNER CONTROL PANEL')}\n\n"
        f"📊 {bold('LIVE SNAPSHOT')}\n"
        f"{bold('Users')}: {stats['users']}\n"
        f"{bold('Registered')}: {stats['registered']}\n"
        f"{bold('Verified')}: {stats['verified']}\n"
        f"{bold('Connected Chats')}: {stats['connected_chats']}\n"
        f"{bold('Active Chats')}: {stats['active_chats']}\n"
        f"{bold('Approved Today')}: {stats['today_approvals']}\n\n"
        f"⚙️ {bold('AUTOMATION')}\n"
        f"{bold('Verification')}: {_enabled(settings.get('verification_enabled'))}\n"
        f"{bold('Force Subscription')}: {_enabled(settings.get('force_subscription_enabled'))}\n"
        f"{bold('Subscriber Trick')}: {_enabled(settings.get('subscriber_trick_enabled'))}\n"
        f"{bold('Bulk Approval')}: {_enabled(settings.get('bulk_approval_enabled'))}\n"
        f"{bold('Speed Limit')}: {settings.get('approval_speed_per_minute')} / min\n\n"
        f"🧭 {bold('OPERATIONS')}\n"
        f"{bold('Active Bulk Jobs')}: {stats['active_bulk_jobs']}\n"
        f"{bold('Failed Jobs')}: {stats['failed_jobs']}\n"
        f"{bold('Force Chats')}: {stats['force_chats']}\n"
        f"{bold('Subscriber Chats')}: {stats.get('subscriber_trick_chats', 0)}"
    )


def bulk_status(job: dict) -> str:
    total = max(int(job.get("total", 0)), 1)
    approved = int(job.get("approved", 0))
    failed = int(job.get("failed", 0))
    skipped = int(job.get("skipped", 0))
    done = approved + failed + skipped
    percent = min(100, round(done * 100 / total, 2))
    remaining = max(0, int(job.get("total", 0)) - done)
    status = bold(str(job.get("status", "unknown")).upper())
    last_error = job.get("last_error")

    text = (
        f"⚡ {bold('BULK APPROVAL STATUS')}\n\n"
        f"{bold('Status')}: {status}\n"
        f"{bold('Progress')}: {percent}%\n\n"
        f"📦 {bold('QUEUE')}\n"
        f"{bold('Total')}: {job.get('total', 0)}\n"
        f"{bold('Approved')}: {approved}\n"
        f"{bold('Failed')}: {failed}\n"
        f"{bold('Skipped')}: {skipped}\n"
        f"{bold('Remaining')}: {remaining}"
    )
    if last_error:
        text += f"\n\n⚠️ {bold('Last Error')}: {escape(str(last_error))}"
    return text
