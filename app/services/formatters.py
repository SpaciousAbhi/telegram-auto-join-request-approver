from __future__ import annotations

from app.bold import bold


def connected_chat_report(chat: dict) -> str:
    username = f"@{chat['username']}" if chat.get("username") else "𝗡/𝗔"
    perms = "✅ 𝗔𝗖𝗧𝗜𝗩𝗘" if chat.get("permissions_ok") else "⚠️ 𝗠𝗜𝗦𝗦𝗜𝗡𝗚"
    active = "✅ 𝗢𝗡" if chat.get("active") else "⛔ 𝗢𝗙𝗙"
    member_count = chat.get("member_count", "𝗨𝗡𝗞𝗡𝗢𝗪𝗡")
    ready_line = (
        "✅ 𝗧𝗵𝗶𝘀 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 / 𝗴𝗿𝗼𝘂𝗽 𝗶𝘀 𝗻𝗼𝘄 𝗰𝗼𝗻𝗻𝗲𝗰𝘁𝗲𝗱. "
        "𝗥𝗲𝗾𝘂𝗶𝗿𝗲𝗱 𝗽𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻𝘀 𝗮𝗿𝗲 𝗮𝗰𝘁𝗶𝘃𝗲, 𝗮𝗻𝗱 𝗮𝗹𝗹 𝗻𝗲𝘄 𝗷𝗼𝗶𝗻 𝗿𝗲𝗾𝘂𝗲𝘀𝘁𝘀 𝘄𝗶𝗹𝗹 𝗯𝗲 𝗵𝗮𝗻𝗱𝗹𝗲𝗱 𝗮𝘂𝘁𝗼𝗺𝗮𝘁𝗶𝗰𝗮𝗹𝗹𝘆."
        if chat.get("permissions_ok")
        else "⚠️ 𝗧𝗵𝗶𝘀 𝗰𝗵𝗮𝘁 𝗶𝘀 𝘀𝗮𝘃𝗲𝗱, 𝗯𝘂𝘁 𝗿𝗲𝗾𝘂𝗶𝗿𝗲𝗱 𝗮𝗱𝗺𝗶𝗻 𝗽𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻𝘀 𝗮𝗿𝗲 𝗺𝗶𝘀𝘀𝗶𝗻𝗴. 𝗡𝗲𝘄 𝗷𝗼𝗶𝗻 𝗿𝗲𝗾𝘂𝗲𝘀𝘁𝘀 𝗰𝗮𝗻𝗻𝗼𝘁 𝗯𝗲 𝗮𝗽𝗽𝗿𝗼𝘃𝗲𝗱 𝘂𝗻𝘁𝗶𝗹 𝘁𝗵𝗶𝘀 𝗶𝘀 𝗳𝗶𝘅𝗲𝗱."
    )
    return (
        "✅ 𝗖𝗛𝗔𝗧 𝗖𝗢𝗡𝗡𝗘𝗖𝗧𝗘𝗗\n\n"
        f"{ready_line}\n\n"
        f"𝗡𝗔𝗠𝗘: {chat.get('title', 'Unknown')}\n"
        f"𝗧𝗬𝗣𝗘: {bold(str(chat.get('type', 'unknown')).upper())}\n"
        f"𝗖𝗛𝗔𝗧 𝗜𝗗: <code>{chat.get('chat_id')}</code>\n"
        f"𝗨𝗦𝗘𝗥𝗡𝗔𝗠𝗘: {username}\n"
        f"𝗕𝗢𝗧 𝗔𝗗𝗠𝗜𝗡: {'✅ 𝗬𝗘𝗦' if chat.get('bot_is_admin') else '❌ 𝗡𝗢'}\n"
        f"𝗥𝗘𝗤𝗨𝗜𝗥𝗘𝗗 𝗣𝗘𝗥𝗠𝗜𝗦𝗦𝗜𝗢𝗡𝗦: {perms}\n"
        f"𝗠𝗘𝗠𝗕𝗘𝗥𝗦: {member_count}\n"
        f"𝗔𝗨𝗧𝗢 𝗔𝗣𝗣𝗥𝗢𝗩𝗘: {active}\n"
        "𝗛𝗔𝗡𝗗𝗟𝗜𝗡𝗚: 𝗜𝗻𝘀𝘁𝗮𝗻𝘁 𝗮𝗽𝗽𝗿𝗼𝘃𝗮𝗹 𝗼𝗿 𝗼𝘄𝗻𝗲𝗿-𝗰𝗼𝗻𝘁𝗿𝗼𝗹𝗹𝗲𝗱 𝘃𝗲𝗿𝗶𝗳𝗶𝗰𝗮𝘁𝗶𝗼𝗻\n"
        f"𝗧𝗢𝗧𝗔𝗟 𝗔𝗣𝗣𝗥𝗢𝗩𝗘𝗗: {chat.get('total_approved', 0)}\n"
        f"𝗙𝗔𝗜𝗟𝗘𝗗: {chat.get('failed_approvals', 0)}"
    )


def owner_dashboard(stats: dict, settings: dict) -> str:
    return (
        "👑 𝗢𝗪𝗡𝗘𝗥 𝗖𝗢𝗡𝗧𝗥𝗢𝗟 𝗣𝗔𝗡𝗘𝗟\n\n"
        f"𝗧𝗢𝗧𝗔𝗟 𝗨𝗦𝗘𝗥𝗦: {stats['users']}\n"
        f"𝗥𝗘𝗚𝗜𝗦𝗧𝗘𝗥𝗘𝗗: {stats['registered']}\n"
        f"𝗩𝗘𝗥𝗜𝗙𝗜𝗘𝗗: {stats['verified']}\n"
        f"𝗖𝗢𝗡𝗡𝗘𝗖𝗧𝗘𝗗 𝗖𝗛𝗔𝗧𝗦: {stats['connected_chats']}\n"
        f"𝗔𝗖𝗧𝗜𝗩𝗘 𝗖𝗛𝗔𝗧𝗦: {stats['active_chats']}\n"
        f"𝗧𝗢𝗗𝗔𝗬 𝗔𝗣𝗣𝗥𝗢𝗩𝗔𝗟𝗦: {stats['today_approvals']}\n"
        f"𝗔𝗖𝗧𝗜𝗩𝗘 𝗕𝗨𝗟𝗞 𝗝𝗢𝗕𝗦: {stats['active_bulk_jobs']}\n"
        f"𝗙𝗔𝗜𝗟𝗘𝗗 𝗝𝗢𝗕𝗦: {stats['failed_jobs']}\n"
        f"𝗙𝗢𝗥𝗖𝗘 𝗖𝗛𝗔𝗧𝗦: {stats['force_chats']}\n\n"
        f"𝗦𝗨𝗕𝗦𝗖𝗥𝗜𝗕𝗘𝗥 𝗧𝗥𝗜𝗖𝗞 𝗖𝗛𝗔𝗧𝗦: {stats.get('subscriber_trick_chats', 0)}\n\n"
        f"𝗩𝗘𝗥𝗜𝗙𝗜𝗖𝗔𝗧𝗜𝗢𝗡: {'𝗢𝗡' if settings.get('verification_enabled') else '𝗢𝗙𝗙'}\n"
        f"𝗙𝗢𝗥𝗖𝗘 𝗦𝗨𝗕𝗦𝗖𝗥𝗜𝗣𝗧𝗜𝗢𝗡: {'𝗢𝗡' if settings.get('force_subscription_enabled') else '𝗢𝗙𝗙'}\n"
        f"𝗦𝗨𝗕𝗦𝗖𝗥𝗜𝗕𝗘𝗥 𝗧𝗥𝗜𝗖𝗞: {'𝗢𝗡' if settings.get('subscriber_trick_enabled') else '𝗢𝗙𝗙'}\n"
        f"𝗕𝗨𝗟𝗞 𝗔𝗣𝗣𝗥𝗢𝗩𝗔𝗟: {'𝗢𝗡' if settings.get('bulk_approval_enabled') else '𝗢𝗙𝗙'}\n"
        f"𝗦𝗣𝗘𝗘𝗗 𝗟𝗜𝗠𝗜𝗧: {settings.get('approval_speed_per_minute')} / 𝗠𝗜𝗡"
    )


def bulk_status(job: dict) -> str:
    total = max(int(job.get("total", 0)), 1)
    done = int(job.get("approved", 0)) + int(job.get("failed", 0)) + int(job.get("skipped", 0))
    percent = min(100, round(done * 100 / total, 2))
    remaining = max(0, int(job.get("total", 0)) - done)
    return (
        "⚡ 𝗕𝗨𝗟𝗞 𝗔𝗣𝗣𝗥𝗢𝗩𝗔𝗟 𝗦𝗧𝗔𝗧𝗨𝗦\n\n"
        f"𝗦𝗧𝗔𝗧𝗨𝗦: {bold(str(job.get('status', 'unknown')).upper())}\n"
        f"𝗧𝗢𝗧𝗔𝗟: {job.get('total', 0)}\n"
        f"𝗔𝗣𝗣𝗥𝗢𝗩𝗘𝗗: {job.get('approved', 0)}\n"
        f"𝗙𝗔𝗜𝗟𝗘𝗗: {job.get('failed', 0)}\n"
        f"𝗦𝗞𝗜𝗣𝗣𝗘𝗗: {job.get('skipped', 0)}\n"
        f"𝗥𝗘𝗠𝗔𝗜𝗡𝗜𝗡𝗚: {remaining}\n"
        f"𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗜𝗢𝗡: {percent}%"
    )
