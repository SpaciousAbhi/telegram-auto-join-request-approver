# Telegram Auto Join Request Acceptor / Approver Bot

Premium multilingual Telegram bot for automatically approving join requests in channels, groups, and supergroups. It includes a clean user flow, owner-only control panel, force subscription, hidden verification, stored pending-request bulk approval, broadcast tools, MongoDB storage, and Heroku deployment support.

## Main Features

- Bold branded Unicode UI across menus, buttons, reports, warnings, and owner screens.
- Force Subscription before normal `/start`, with only missing required chats shown.
- Language screen after Force Subscription: English, Hindi, Hinglish, Urdu.
- Hindi uses Devanagari script and Urdu uses natural Urdu script for the main user flow.
- Add-to-channel and add-to-group buttons using Telegram admin invite URLs with `can_invite_users`.
- Automatic live join-request approval.
- Owner-only hidden verification flow using “✅ 𝗜’𝗠 𝗡𝗢𝗧 𝗔 𝗥𝗢𝗕𝗢𝗧”.
- Verification flow is separate from Force Subscription and never shows Force Subscription.
- Subscriber Adding Trick after successful verification, managed separately from Force Subscription.
- Connected chat report after the bot is added.
- My Channels / Groups management panel.
- Stored pending-request bulk approval with progress and pause/resume/stop controls.
- Owner panel with global toggles, stats, Force Subscription chat management, and broadcast.
- System Health dashboard with recent event logs and connected-chat audit.
- Startup default admin-rights setup for the Telegram add-bot flow.
- Heroku-ready `Procfile`, `runtime.txt`, `.env.example`, and minimal required config.

## Required Config Vars

Only these values are required:

```env
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
OWNER_ID=YOUR_OWNER_ID_HERE
MONGO_DB_URI=YOUR_MONGODB_DATABASE_URL_HERE
```

All other operational controls are stored in MongoDB and managed inside the owner panel.

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` with your real `BOT_TOKEN`, `OWNER_ID`, and `MONGO_DB_URI`, then run:

```bash
python -m app.main
```

## Heroku Deployment

1. Create a Heroku app.
2. Add these Config Vars in Heroku:
   - `BOT_TOKEN`
   - `OWNER_ID`
   - `MONGO_DB_URI`
3. Deploy the repository to Heroku.
4. Scale the worker dyno:

```bash
heroku ps:scale worker=1 -a YOUR_HEROKU_APP_NAME
```

The bot uses long polling through a worker dyno. No web dyno or public webhook URL is required.

## Owner Setup

Open the bot and send:

```text
/owner
```

From the owner panel you can:

- Turn Force Subscription ON/OFF.
- Turn hidden verification ON/OFF.
- Manage Subscriber Adding Trick ON/OFF, optional/required mode, channels, and message text.
- Turn bulk approval ON/OFF.
- Add Force Subscription chats.
- View Force Subscription errors.
- Audit connected chats and inspect recent approval, verification, force-check, and bulk events.
- Broadcast copied/forwarded/text/media messages to registered users.

## Telegram Permission Requirements

For approval to work, the bot must be added as admin to the target channel/group with the permission Telegram exposes as `can_invite_users`. This is the permission required by Bot API `approveChatJoinRequest`.

## Important Bot API Boundary

Telegram Bot API can approve a join request when the bot knows the requesting user ID, and the bot receives new `chat_join_request` updates while it is admin. The Bot API does not expose a full endpoint to enumerate every historical pending join request that existed before the bot received updates. Therefore, this project’s bulk approval processes stored pending requests observed by the bot. Unknown historical requests require Telegram-side manual handling or an additional MTProto/user-account workflow, which is intentionally not included because this project requires only `BOT_TOKEN`, `OWNER_ID`, and `MONGO_DB_URI`.

## Validation

```bash
python -m compileall app
python -m pytest -q
```
