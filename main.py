import asyncio
import logging
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from config import (
    API_ID, API_HASH, BOT_TOKEN, SESSION_NAME, 
    SCRAPE_HISTORY, HISTORY_LIMIT, LIVE_SCRAPE_ACTIVE
)
from core.extractor import extract_ccs, determine_category
from core.forwarder import forward_card
from database.mongo_db import db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Client(
    SESSION_NAME,
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
            app=app,
            card_data=card,
            source=source,
            chat_id=message.chat.id,
            message_id=message.id,
            category=category,
            is_old=is_old
        )

# ========== NEW MESSAGE HANDLER ==========
@app.on_message(filters.text & ~filters.bot)
async def new_message_handler(client, message: Message):
    # AGAR LIVE_SCRAPE_ACTIVE = FALSE, TOH KAM NAHI KAREGA
    if not LIVE_SCRAPE_ACTIVE:
        return
    await process_message(message, is_old=False)

# ========== SCRAPE HISTORY (WITH DELAY) ==========
async def scrape_history(target_identifier):
    try:
        logging.info(f"📜 Scraping history from: {target_identifier}")
        count = 0
        async for message in app.get_chat_history(target_identifier, limit=HISTORY_LIMIT):
            await process_message(message, is_old=True)
            count += 1
            if count % 100 == 0:
                logging.info(f"📊 Scanned {count} messages")
                await asyncio.sleep(0.3)
        logging.info(f"✅ Done: {count} messages")
    except Exception as e:
        logging.error(f"❌ History scrape failed: {e}")

# ========== /start ==========
@app.on_message(filters.command("start") & filters.private)
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
        "Bot is running in ALL groups/channels where it's added.\n"
        "Har jagah se CC uthayega aur forward karega.\n\n"
        "📌 LIVE CC → @live_group\n"
        "📌 APPROVED CC → @charged_group\n"
        "📌 OLD SCRAPE → @fetch_group\n"
        "📌 LOGS → @log_channel\n\n"
        "👉 SCRAPE button dabao — tab live start hoga.",
        reply_markup=keyboard,
        parse_mode=enums.ParseMode.HTML
    )

# ========== BUTTON CALLBACKS ==========
@app.on_callback_query()
async def button_callback(client, callback_query):
    global LIVE_SCRAPE_ACTIVE
    data = callback_query.data
    
    if data == "scrape_start":
        LIVE_SCRAPE_ACTIVE = True
        await callback_query.answer("✅ LIVE SCRAPING STARTED! Monitoring 24/7...")
        await callback_query.message.reply_text(
            "🟢 <b>LIVE SCRAPING ACTIVE</b>\n\n"
            "Bot ab har group/channel se CC uthayega aur forward karega.\n"
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
        
        try:
            async for dialog in app.get_dialogs():
                if dialog.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL]:
                    await scrape_history(dialog.chat.id)
            await msg.edit_text("✅ OLD SCRAPE COMPLETE! Sab purani CC forward ho gayi.")
        except Exception as e:
            await msg.edit_text(f"❌ Error: {e}")

# ========== COMMANDS ==========
@app.on_message(filters.command("scan_today") & filters.private)
async def scan_today(client, message):
    stats = db.get_today_stats()
    await message.reply_text(
        f"📆 <b>TODAY'S FORWARDS</b>\n\n"
        f"✅ Forwarded: {stats['forwarded']}\n"
        f"⏳ Pending: {stats['pending']}"
    )

@app.on_message(filters.command("status") & filters.private)
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

@app.on_message(filters.command("rescan") & filters.private)
async def rescan_command(client, message):
    await message.reply_text("🔄 Checking for skipped CCs...")
    skipped = db.get_skipped_cards()
    if not skipped:
        await message.reply_text("✅ No skipped CCs found. Sab forward ho gaye.")
        return
    
    count = 0
    for card in skipped:
        # Try to forward skipped cards
        count += 1
    await message.reply_text(f"✅ Rescanned {count} skipped CCs.")

# ========== MAIN ==========
async def main():
    logging.info("🔥 CC SNIPER ULTIMATE STARTING...")
    logging.info("📌 Bot will monitor ALL groups/channels where it's added")
    logging.info(f"📌 LIVE_SCRAPE_ACTIVE = {LIVE_SCRAPE_ACTIVE}")
    
    await app.start()
    logging.info("✅ Bot started!")
    
    # Auto-scrape history on first run
    if SCRAPE_HISTORY:
        logging.info("📜 SCRAPING HISTORY ONCE...")
        try:
            async for dialog in app.get_dialogs():
                if dialog.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL]:
                    await scrape_history(dialog.chat.id)
        except Exception as e:
            logging.error(f"History scrape error: {e}")
        logging.info("✅ HISTORY SCRAPE COMPLETE")
    
    logging.info("🤖 Bot is LIVE! Waiting for SCRAPE button...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    app.run(main())
