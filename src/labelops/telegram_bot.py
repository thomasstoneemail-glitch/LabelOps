from __future__ import annotations

import logging
import re
from pathlib import Path

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from labelops.config import AppConfig, load_config
from labelops.storage import (
    load_chat_defaults,
    save_chat_defaults,
    write_ingestion_message,
)

CLIENT_LINE_PATTERN = re.compile(r"^client_\d{2}$", re.IGNORECASE)


def _is_allowlisted(update: Update, config: AppConfig) -> bool:
    chat_id = update.effective_chat.id if update.effective_chat else None
    if chat_id in config.telegram.allowlisted_chat_ids:
        return True

    username = update.effective_user.username if update.effective_user else None
    if username:
        normalized = username.lstrip("@").lower()
        return normalized in config.telegram.allowlisted_usernames

    return False


def _get_default_client(chat_id: int, config: AppConfig, defaults: dict[str, str]) -> str:
    return defaults.get(str(chat_id), config.telegram.default_client_id)


def _resolve_client_id(message_text: str, default_client_id: str) -> str:
    for line in message_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if CLIENT_LINE_PATTERN.match(stripped):
            return stripped.lower()
        break
    return default_client_id


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config: AppConfig = context.bot_data["config"]
    await update.message.reply_text(
        "✅ Bot online\n"
        f"Default client: {config.telegram.default_client_id}\n"
        f"Clients: {', '.join(config.telegram.clients) or 'none'}"
    )


async def clients_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config: AppConfig = context.bot_data["config"]
    await update.message.reply_text(
        "Available clients: " + (", ".join(config.telegram.clients) or "none")
    )


async def setclient_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config: AppConfig = context.bot_data["config"]
    defaults_path: Path = context.bot_data["chat_defaults_path"]
    defaults = load_chat_defaults(defaults_path)

    if not context.args:
        await update.message.reply_text("Usage: /setclient client_XX")
        return

    client_id = context.args[0].strip().lower()
    if client_id not in config.telegram.clients:
        await update.message.reply_text(
            f"Unknown client '{client_id}'. Use /clients to list available clients."
        )
        return

    chat_id = update.effective_chat.id
    defaults[str(chat_id)] = client_id
    save_chat_defaults(defaults_path, defaults)
    await update.message.reply_text(
        f"Default client set to {client_id} for this chat."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Commands:\n"
        "/status - bot health and available clients\n"
        "/clients - list client IDs\n"
        "/setclient client_XX - set chat default\n"
        "/chatid - show chat ID"
    )


async def chatid_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id if update.effective_chat else "unknown"
    await update.message.reply_text(f"Chat ID: {chat_id}")


async def ingest_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config: AppConfig = context.bot_data["config"]
    base_dir: Path = context.bot_data["base_dir"]
    defaults_path: Path = context.bot_data["chat_defaults_path"]

    if not update.message or not update.message.text:
        return

    if not _is_allowlisted(update, config):
        logging.info(
            "Ignored message from non-allowlisted chat_id=%s",
            update.effective_chat.id if update.effective_chat else "unknown",
        )
        return

    defaults = load_chat_defaults(defaults_path)
    chat_id = update.effective_chat.id
    default_client = _get_default_client(chat_id, config, defaults)
    client_id = _resolve_client_id(update.message.text, default_client)

    await update.message.chat.send_action(ChatAction.TYPING)
    result = write_ingestion_message(base_dir, client_id, update.message.text)

    logging.info(
        "Ingested telegram message chat_id=%s client_id=%s filename=%s length=%s ts=%s",
        chat_id,
        result.client_id,
        result.filename,
        result.message_length,
        result.timestamp,
    )


def build_application(config_path: Path) -> Application:
    config = load_config(config_path)
    application = Application.builder().token(config.telegram.token).build()

    application.bot_data["config"] = config
    application.bot_data["base_dir"] = config_path.parent
    application.bot_data["chat_defaults_path"] = config.telegram.chat_defaults_path

    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("clients", clients_command))
    application.add_handler(CommandHandler("setclient", setclient_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("chatid", chatid_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ingest_message))

    return application


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    config_path = Path("clients.yaml")
    app = build_application(config_path)
    app.run_polling()


if __name__ == "__main__":
    main()
