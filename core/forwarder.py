import logging
import asyncio
from pyrogram import Client, enums
from pyrogram.errors import FloodWait, ChatWriteForbidden, PeerIdInvalid

import config
from database.mongo_db import db

async def forward_card(
    client: Client,
    card: str,
    source: str,
    chat_id: int,
    message_id: int,
    category: str,
    is_old: bool
):
    try:
        if not card:
            logging.warning("⚠️ Empty card received, skipping")
            return

        if db.is_duplicate(card):
            logging.debug(f"⏭️ Duplicate skipped: {card}")
            return

        db.save_card(
            card=card,
            source=source,
            chat_id=chat_id,
            message_id=message_id,
            category=category,
            is_old=is_old
        )

        card_parts = card.split("|")
        if len(card_parts) != 4:
            logging.warning(f"⚠️ Invalid card format: {card}")
            return

        number, month, year, cvv = card_parts

        label = "📜 OLD" if is_old else "🔴 LIVE"
        cat_emoji = {
            "live": "✅",
            "dead": "❌",
            "unknown": "❓"
        }.get(category, "❓")

        text = (
            f"{label} | {cat_emoji} <b>{category.upper()}</b>\n\n"
            f"💳 <code>{number}|{month}|{year}|{cvv}</code>\n"
            f"📌 Source: {source}\n"
            f"🏷️ Category: <b>{category}</b>"
        )

        target = (
            config.LIVE_GROUP
            if category == "live"
            else config.CHARGED_GROUP
        )

        await _safe_send(client, target, text)
        await _safe_send(
            client,
            config.LOG_CHANNEL,
            f"📝 LOGGED\n{text}"
        )

        logging.info(f"✅ Forwarded [{category}]: {card} from {source}")

    except Exception as e:
        logging.error(f"❌ forward_card error: {e}")
        try:
            db.save_skipped(card, source, chat_id, message_id, category)
        except Exception as db_err:
            logging.error(f"❌ Failed to save skipped: {db_err}")

async def _safe_send(
    client: Client,
    chat_id,
    text: str,
    retries: int = 3
):
    for attempt in range(retries):
        try:
            await client.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=enums.ParseMode.HTML
            )
            return

        except FloodWait as e:
            logging.warning(f"⏳ FloodWait {e.value}s (attempt {attempt+1})")
            await asyncio.sleep(e.value)

        except ChatWriteForbidden:
            logging.error(f"❌ Cannot write to {chat_id}")
            return

        except PeerIdInvalid:
            logging.error(f"❌ Invalid peer: {chat_id}")
            return

        except Exception as e:
            logging.error(f"❌ Send error (attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                await asyncio.sleep(2)

    logging.error(f"❌ Failed after {retries} attempts")
