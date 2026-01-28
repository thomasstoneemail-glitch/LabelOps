# LabelOps

## Telegram ingestion

### BotFather setup
1. In Telegram, open `@BotFather`.
2. Run `/newbot` and follow prompts to create a bot.
3. Copy the token and place it in `clients.yaml` (`telegram.token`).
4. (Optional for group usage) Run `/setprivacy` and disable privacy mode for the bot so it can read group messages.

### Configure allowlist
Edit `clients.yaml`:
- `telegram.allowlisted_chat_ids` list of allowed chat IDs.
- `telegram.allowlisted_usernames` (optional) allowed usernames (without `@`).
- `telegram.default_client_id` and `telegram.clients` determine routing.

### Obtain chat IDs
Use the built-in `/chatid` command after starting the bot, or temporarily enable logging and read the chat ID from the logs when a message is received.

### Run the bot
```bash
pip install -r requirements.txt
python -m labelops.telegram_bot
```

### Routing rules
- If the first non-empty line of a message matches `client_XX`, the message routes to that client.
- Otherwise the chat default (from `/setclient`) or `telegram.default_client_id` is used.

Messages are written atomically to:
```
Clients/<client_id>/IN_TXT/telegram_<UTC_TIMESTAMP>.txt
```

### Commands
- `/status` - bot health and available clients
- `/clients` - list client IDs
- `/setclient client_XX` - set chat-scoped default client
- `/chatid` - show chat ID
- `/help` - usage

## Click & Drop
- `labelops.clickdrop.export_tracking_report` writes tracking exports to:
  `Clients/<client_id>/TRACKING_OUT/tracking_<date>_<batch_id>.csv`
- Missing tracking numbers are exported as `PENDING`.
- `labelops.clickdrop.write_clickdrop_import_xlsx` writes import files with **no header row** (row 1 is data).
