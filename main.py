import asyncio
import logging
import signal
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait

import config
from config import (
    API_ID, API_HASH, BOT_TOKEN, USER_SESSION,
    LIVE_GROUP, CHARGED_GROUP, LOG_CHANNEL, FETCH_GROUP,
    APPROVED_KEYWORDS, SCRAPE_HISTORY, ADMIN_IDS
)
from core.extractor import extract_ccs, determine_category
from core.forwarder import forward_card
from database.mongo_db import db

# ========== LOGGING ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

# ========== CLIENTS ==========
user = Client(
    "user_session",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=USER_SESSION
)

bot = Client(
    "bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ========== ADMIN FILTER ==========
def admin_only(_, __, message):
    if not message.from_user:
        return False
    return message.from_user.id in ADMIN_IDS

admin_filter = filters.create(admin_only)

# ========== PROCESS MESSAGE ==========
async def process_message(message: Message, is_old: bool = False):
    try:
        if not message:
            return
        if not message.text:
            return
        if not message.chat:
            return

        cards = extract_ccs(message.text)
        if not cards:
            return

        source = (
            f"@{message.chat.username}"
            if message.chat.username
            else f"group_{message.chat.id}"
        )

        for card in cards:
            category = determine_category(message.text)
            # ✅ User scrape + forward karega
            await forward_card(
                user,
                card,
                source,
                message.chat.id,
                message.id,
                category,
                is_old
            )

    except FloodWait as e:
        logging.warning(f"⏳ FloodWait: {e.value}s")
        await asyncio.sleep(e.value)
    except Exception as e:
        logging.error(f"❌ process_message error: {e}")

# ========== SCRAPE HISTORY ==========
# ✅ Sirf /fetch button se chalega
async def scrape_all_history():
    logging.info("📜 SCRAPING ALL HISTORY STARTED...")

    total_scanned = 0

    try:
        async for dialog in user.get_dialogs():
            chat = dialog.chat

            if chat.type not in [
                enums.ChatType.GROUP,
                enums.ChatType.SUPERGROUP,
                enums.ChatType.CHANNEL
            ]:
                continue

            source = (
                f"@{chat.username}"
                if chat.username
                else f"group_{chat.id}"
            )
            logging.info(f"📜 Scraping: {source}")

            count = 0
            try:
                async for message in user.get_chat_history(chat.id):
                    try:
                        await process_message(message, is_old=True)
                        count += 1

                        if count % 50 == 0:
                            logging.info(
                                f"📊 Scanned {count} msgs in {source}"
                            )
                            await asyncio.sleep(1)

                    except FloodWait as e:
                        logging.warning(f"⏳ FloodWait: {e.value}s")
                        await asyncio.sleep(e.value)
                    except Exception as e:
                        logging.error(f"❌ Message error: {e}")
                        continue

            except FloodWait as e:
                logging.warning(f"⏳ FloodWait on history: {e.value}s")
                await asyncio.sleep(e.value)
            except Exception as e:
                logging.error(f"❌ Failed to scrape {source}: {e}")
                continue

            logging.info(f"✅ Done: {count} msgs from {source}")
            total_scanned += count
            await asyncio.sleep(2)

    except Exception as e:
        logging.error(f"❌ History scrape failed: {e}")

    logging.info(f"✅ TOTAL SCANNED: {total_scanned} messages")

# ========== LIVE SCRAPE ==========
# ✅ Sirf /scrape start karne ke baad naye messages
@user.on_message(filters.text)
async def live_handler(client: Client, message: Message):
    try:
        # ✅ Sirf tab forward karo jab LIVE_SCRAPE_ACTIVE = True
        if config.LIVE_SCRAPE_ACTIVE:
            await process_message(message, is_old=False)
    except Exception as e:
        logging.error(f"❌ live_handler error: {e}")

# ========== START COMMAND ==========
@bot.on_message(filters.command("start") & filters.private & admin_filter)
async def start_cmd(client: Client, message: Message):
    try:
        status = "🟢 ACTIVE" if config.LIVE_SCRAPE_ACTIVE else "🔴 INACTIVE"

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔥 START LIVE SCRAPE",
                    callback_data="scrape_start"
                )
            ],
            [
                InlineKeyboardButton(
                    "🛑 STOP LIVE SCRAPE",
                    callback_data="scrape_stop"
                )
            ],
            [
                InlineKeyboardButton(
                    "📜 FETCH OLD",
                    callback_data="fetch"
                )
            ],
            [
                InlineKeyboardButton(
                    "🛠 STATS",
                    callback_data="tools"
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 STATUS",
                    callback_data="status"
                )
            ]
        ])

        await message.reply_text(
            f"🤖 <b>CC SNIPER ULTIMATE</b>\n\n"
            f"┌ Status: <b>{status}</b>\n\n"
            f"🔥 START = Naye messages se CC lega\n"
            f"📜 FETCH OLD = Purane messages se CC lega\n\n"
            f"👇 Select karo:",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        logging.error(f"❌ start_cmd error: {e}")

# ========== CALLBACK HANDLER ==========
@bot.on_callback_query()
async def cb_handler(client: Client, query):
    try:
        # Admin check
        if query.from_user.id not in ADMIN_IDS:
            await query.answer("❌ Unauthorized!", show_alert=True)
            return

        data = query.data

        # ── START LIVE SCRAPE ──
        if data == "scrape_start":
            if config.LIVE_SCRAPE_ACTIVE:
                await query.answer("⚠️ Already Active!", show_alert=True)
                return
            config.LIVE_SCRAPE_ACTIVE = True
            await query.answer("✅ LIVE SCRAPING STARTED!")
            await query.message.reply_text(
                "🟢 <b>LIVE SCRAPING ACTIVE!</b>\n\n"
                "Ab se sirf NAYE messages ka CC forward hoga!\n"
                "Purane ke liye FETCH OLD use karo.",
                parse_mode=enums.ParseMode.HTML
            )

        # ── STOP LIVE SCRAPE ──
        elif data == "scrape_stop":
            if not config.LIVE_SCRAPE_ACTIVE:
                await query.answer("⚠️ Already Stopped!", show_alert=True)
                return
            config.LIVE_SCRAPE_ACTIVE = False
            await query.answer("🛑 LIVE SCRAPING STOPPED!")
            await query.message.reply_text(
                "🔴 <b>LIVE SCRAPING STOPPED</b>",
                parse_mode=enums.ParseMode.HTML
            )

        # ── FETCH OLD ──
        elif data == "fetch":
            await query.answer("📜 FETCH OLD STARTED!")
            msg = await query.message.reply_text(
                "📜 <b>Purane messages scan ho rahe hain...</b>\n"
                "Ye background me chalega!\n"
                "FETCH_GROUP me forward hoga!",
                parse_mode=enums.ParseMode.HTML
            )
            # ✅ Background me chalao
            asyncio.create_task(scrape_all_history())
            await msg.edit_text(
                "✅ <b>FETCH OLD RUNNING!</b>\n\n"
                "Purane CC FETCH_GROUP me aayenge!\n"
                "Live CC ke liye START LIVE SCRAPE karo!",
                parse_mode=enums.ParseMode.HTML
            )

        # ── TOOLS ──
        elif data == "tools":
            stats = db.get_stats() or {}
            today = db.get_today_stats() or {}
            text = (
                "🛠 <b>STATS</b>\n\n"
                "📊 <b>Overall:</b>\n"
                f"├ Total: <code>{stats.get('total', 0)}</code>\n"
                f"├ Approved: <code>{stats.get('approved', 0)}</code>\n"
                f"├ Live: <code>{stats.get('live', 0)}</code>\n"
                f"└ Old: <code>{stats.get('old', 0)}</code>\n\n"
                "📆 <b>Today:</b>\n"
                f"├ Forwarded: <code>{today.get('forwarded', 0)}</code>\n"
                f"└ Pending: <code>{today.get('pending', 0)}</code>"
            )
            await query.answer()
            await query.message.reply_text(
                text,
                parse_mode=enums.ParseMode.HTML
            )

        # ── STATUS ──
        elif data == "status":
            stats = db.get_stats() or {}
            status = "🟢 ACTIVE" if config.LIVE_SCRAPE_ACTIVE else "🔴 INACTIVE"
            await query.answer()
            await query.message.reply_text(
                f"📊 <b>STATUS</b>\n\n"
                f"├ Scraper: <b>{status}</b>\n"
                f"├ Total: <code>{stats.get('total', 0)}</code>\n"
                f"├ Approved: <code>{stats.get('approved', 0)}</code>\n"
                f"├ Live: <code>{stats.get('live', 0)}</code>\n"
                f"└ Old: <code>{stats.get('old', 0)}</code>",
                parse_mode=enums.ParseMode.HTML
            )

    except Exception as e:
        logging.error(f"❌ cb_handler error: {e}")
        try:
            await query.answer("❌ Error!", show_alert=True)
        except:
            pass

# ========== STATUS COMMAND ==========
@bot.on_message(
    filters.command("status") & filters.private & admin_filter
)
async def status_cmd(client: Client, message: Message):
    try:
        stats = db.get_stats() or {}
        status = "🟢 ACTIVE" if config.LIVE_SCRAPE_ACTIVE else "🔴 INACTIVE"
        await message.reply_text(
            f"📊 <b>STATUS</b>\n\n"
            f"├ Scraper: <b>{status}</b>\n"
            f"├ Total: <code>{stats.get('total', 0)}</code>\n"
            f"├ Approved: <code>{stats.get('approved', 0)}</code>\n"
            f"├ Live: <code>{stats.get('live', 0)}</code>\n"
            f"├ Old: <code>{stats.get('old', 0)}</code>\n"
            f"└ Today: <code>{stats.get('today', 0)}</code>",
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        logging.error(f"❌ status_cmd error: {e}")

# ========== SCAN TODAY ==========
@bot.on_message(
    filters.command("scan_today") & filters.private & admin_filter
)
async def scan_today_cmd(client: Client, message: Message):
    try:
        today = db.get_today_stats() or {}
        await message.reply_text(
            f"📆 <b>TODAY'S STATS</b>\n\n"
            f"├ Forwarded: <code>{today.get('forwarded', 0)}</code>\n"
            f"└ Pending: <code>{today.get('pending', 0)}</code>",
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        logging.error(f"❌ scan_today_cmd error: {e}")

# ========== RESCAN ==========
@bot.on_message(
    filters.command("rescan") & filters.private & admin_filter
)
async def rescan_cmd(client: Client, message: Message):
    try:
        msg = await message.reply_text(
            "🔄 <b>Checking skipped CCs...</b>",
            parse_mode=enums.ParseMode.HTML
        )
        skipped = db.get_skipped_cards() or []

        if not skipped:
            await msg.edit_text(
                "✅ <b>No skipped CCs found.</b>",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await msg.edit_text(
                f"⚠️ <b>Found {len(skipped)} skipped CCs</b>\n"
                "Processing...",
                parse_mode=enums.ParseMode.HTML
            )
            success = 0
            failed = 0

            for card_data in skipped:
                try:
                    await forward_card(
                        user,
                        card_data.get("card"),
                        card_data.get("source", "unknown"),
                        card_data.get("chat_id", 0),
                        card_data.get("message_id", 0),
                        card_data.get("category", "unknown"),
                        True
                    )
                    success += 1
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logging.error(f"❌ Rescan error: {e}")
                    failed += 1

            await msg.edit_text(
                f"✅ <b>RESCAN COMPLETE</b>\n\n"
                f"├ Success: <code>{success}</code>\n"
                f"└ Failed: <code>{failed}</code>",
                parse_mode=enums.ParseMode.HTML
            )
    except Exception as e:
        logging.error(f"❌ rescan_cmd error: {e}")

# ========== HELP ==========
@bot.on_message(
    filters.command("help") & filters.private & admin_filter
)
async def help_cmd(client: Client, message: Message):
    await message.reply_text(
        "📖 <b>COMMANDS</b>\n\n"
        "/start — Main menu\n"
        "/status — Scraper status\n"
        "/scan_today — Aaj ke stats\n"
        "/rescan — Skipped CCs retry\n"
        "/help — Ye message",
        parse_mode=enums.ParseMode.HTML
    )

# ========== MAIN ==========
async def main():
    logging.info("🔥 CC SNIPER STARTING...")

    # Start User
    try:
        await user.start()
        me = await user.get_me()
        logging.info(f"✅ User: {me.first_name} (@{me.username})")
    except Exception as e:
        logging.critical(f"❌ User FAILED: {e}")
        return

    # Start Bot
    try:
        await bot.start()
        bot_me = await bot.get_me()
        logging.info(f"✅ Bot: {bot_me.first_name} (@{bot_me.username})")
    except Exception as e:
        logging.critical(f"❌ Bot FAILED: {e}")
        await user.stop()
        return

    logging.info("━━━━━━━━━━━━━━━━━━━━━━━━")
    logging.info("✅ User = Scrape + Forward")
    logging.info("✅ Bot  = Sirf Control")
    logging.info("✅ /start se control karo")
    logging.info("━━━━━━━━━━━━━━━━━━━━━━━━")

    # Graceful Shutdown
    stop_event = asyncio.Event()
    loop = asyncio.get_event_loop()

    def shutdown():
        logging.info("🛑 Shutdown...")
        stop_event.set()

    try:
        loop.add_signal_handler(signal.SIGINT, shutdown)
        loop.add_signal_handler(signal.SIGTERM, shutdown)
    except NotImplementedError:
        pass

    await stop_event.wait()

    try:
        await user.stop()
        logging.info("✅ User stopped")
    except Exception as e:
        logging.error(f"❌ {e}")

    try:
        await bot.stop()
        logging.info("✅ Bot stopped")
    except Exception as e:
        logging.error(f"❌ {e}")

    logging.info("✅ DONE")

if __name__ == "__main__":
    asyncio.run(main())
