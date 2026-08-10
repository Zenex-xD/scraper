import asyncio
import logging
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from config import (
    API_ID, API_HASH, BOT_TOKEN, USER_SESSION,
    LIVE_GROUP, CHARGED_GROUP, LOG_CHANNEL, FETCH_GROUP,
    MONGO_URI, APPROVED_KEYWORDS, SCRAPE_HISTORY, LIVE_SCRAPE_ACTIVE
)
from core.extractor import extract_ccs, determine_category
from core.forwarder import forward_card
from database.mongo_db import db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ========== USER ACCOUNT (Scrape + Forward — Direct String Session) ==========
user_app = Client(
    "user_session",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=USER_SESSION,  # Direct string session — no file
    parse_mode=enums.ParseMode.HTML
)

# ========== BOT ACCOUNT (Commands + Status Only) ==========
bot_app = Client(
    "bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    parse_mode=enums.ParseMode.HTML
)

# ========== PROCESS MESSAGE ==========
async def process_message(message: Message, is_old=False):
    if not message.text:
        return
    
    chat = message.chat
    source = f"@{chat.username}" if chat.username else f"group_{chat.id}"
    message_text = message.text
    
    cards = extract_ccs(message_text)
    if not cards:
        return
    
    logging.info(f"🔍 Found {len(cards)} CCs in {source}")
    
    for card in cards:
        category = determine_category(message_text)
        await forward_card(
            app=user_app,
            card_data=card,
            source=source,
            chat_id=message.chat.id,
            message_id=message.id,
            category=category,
            is_old=is_old
        )

# ========== SCRAPE HISTORY ==========
async def scrape_all_history():
    logging.info("📜 SCRAPING ALL HISTORY...")
    count_total = 0
    try:
        async for dialog in user_app.get_dialogs():
            chat = dialog.chat
            if chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL]:
                source = f"@{chat.username}" if chat.username else f"group_{chat.id}"
                logging.info(f"📜 Scraping: {source}")
                count = 0
                async for message in user_app.get_chat_history(chat.id):
                    await process_message(message, is_old=True)
                    count += 1
                    if count % 100 == 0:
                        logging.info(f"📊 Scanned {count} messages")
                        await asyncio.sleep(0.3)
                logging.info(f"✅ Done: {count} messages from {source}")
                count_total += count
    except Exception as e:
        logging.error(f"❌ History scrape failed: {e}")
    logging.info(f"✅ TOTAL: {count_total} messages scanned")

# ========== LIVE SCRAPE ==========
@user_app.on_message(filters.text & ~filters.bot)
async def live_scrape_handler(client, message: Message):
    if not LIVE_SCRAPE_ACTIVE:
        return
    await process_message(message, is_old=False)

# ========== BOT COMMANDS ==========
@bot_app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 SCRAPE", callback_data="scrape_start")],
        [InlineKeyboardButton("🛠 TOOLS", callback_data="tools")],
        [InlineKeyboardButton("📜 OLD SCRAPE", callback_data="fetch")]
    ])
    status = "🟢 ACTIVE" if LIVE_SCRAPE_ACTIVE else "🔴 INACTIVE"
    await message.reply_text(
        f"🤖 <b>CC SNIPER ULTIMATE</b>\n\n"
        f"Status: {status}\n\n"
        "📌 LIVE CC → @live_group\n"
        "📌 APPROVED CC → @charged_group\n"
        "📌 OLD SCRAPE → @fetch_group\n"
        "📌 LOGS → @log_channel\n\n"
        "👉 SCRAPE button dabao — tab live start hoga.",
        reply_markup=keyboard,
        parse_mode=enums.ParseMode.HTML
    )

@bot_app.on_callback_query()
async def button_callback(client, callback_query):
    global LIVE_SCRAPE_ACTIVE
    data = callback_query.data
    
    if data == "scrape_start":
        LIVE_SCRAPE_ACTIVE = True
        await callback_query.answer("✅ LIVE SCRAPING STARTED!")
        await callback_query.message.reply_text(
            "🟢 <b>LIVE SCRAPING ACTIVE</b>\n\n"
            "User account ab har group/channel se CC uthayega.\n"
            "Jab tak bot running hai, kaam karega."
        )
    
    elif data == "tools":
        stats = db.get_stats()
        today_stats = db.get_today_stats()
        text = f"""
🛠 <b>TOOLS MENU</b>

📊 <b>OVERALL STATS</b>
├ Total: {stats['total']}
├ Approved: {stats['approved']}
├ Live: {stats['live']}
└ Old Scrape: {stats['old']}

📆 <b>TODAY</b>
├ Forwarded: {today_stats['forwarded']}
└ Pending: {today_stats['pending']}

<b>Commands:</b>
/scan_today - Today's forwards
/status - Overall stats
/rescan - Check skipped CCs
"""
        await callback_query.message.reply_text(text)
    
    elif data == "fetch":
        await callback_query.answer("📜 OLD SCRAPE STARTED!")
        msg = await callback_query.message.reply_text("📜 Scraping old messages from all groups...")
        await scrape_all_history()
        await msg.edit_text("✅ OLD SCRAPE COMPLETE! Sab purani CC forward ho gayi.")

@bot_app.on_message(filters.command("scan_today") & filters.private)
async def scan_today(client, message):
    stats = db.get_today_stats()
    await message.reply_text(
        f"📆 <b>TODAY'S FORWARDS</b>\n\n"
        f"✅ Forwarded: {stats['forwarded']}\n"
        f"⏳ Pending: {stats['pending']}"
    )

@bot_app.on_message(filters.command("status") & filters.private)
async def status_command(client, message):
    stats = db.get_stats()
    await message.reply_text(
        f"📊 <b>OVERALL STATUS</b>\n\n"
        f"Total: {stats['total']}\n"
        f"Approved: {stats['approved']}\n"
        f"Live: {stats['live']}\n"
        f"Old Scrape: {stats['old']}\n"
        f"Today: {stats['today']}"
    )

@bot_app.on_message(filters.command("rescan") & filters.private)
async def rescan_command(client, message):
    await message.reply_text("🔄 Checking for skipped CCs...")
    skipped = db.get_skipped_cards()
    if not skipped:
        await message.reply_text("✅ No skipped CCs found. Sab forward ho gaye.")
        return
    await message.reply_text(f"✅ Found {len(skipped)} skipped CCs.")

# ========== MAIN ==========
async def main():
    logging.info("🔥 CC SNIPER ULTIMATE STARTING...")
    
    await user_app.start()
    logging.info("✅ User account started!")
    
    await bot_app.start()
    logging.info("✅ Bot account started!")
    
    if SCRAPE_HISTORY:
        logging.info("📜 SCRAPING HISTORY ONCE...")
        await scrape_all_history()
        logging.info("✅ HISTORY SCRAPE COMPLETE")
    
    logging.info("🤖 Bot is LIVE! Commands available via bot.")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
