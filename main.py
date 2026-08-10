import asyncio
import logging
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from config import (
    API_ID, API_HASH, BOT_TOKEN, USER_SESSION,
    LIVE_GROUP, CHARGED_GROUP, LOG_CHANNEL, FETCH_GROUP,
    APPROVED_KEYWORDS, SCRAPE_HISTORY, LIVE_SCRAPE_ACTIVE
)
from core.extractor import extract_ccs, determine_category
from core.forwarder import forward_card
from database.mongo_db import db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ========== CLIENTS ==========
user = Client("user_session", api_id=API_ID, api_hash=API_HASH, session_string=USER_SESSION)
bot = Client("bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ========== PROCESS MESSAGE ==========
async def process_message(message, is_old=False):
    if not message or not message.text:
        return
    
    cards = extract_ccs(message.text)
    if not cards:
        return
    
    source = f"@{message.chat.username}" if message.chat.username else f"group_{message.chat.id}"
    
    for card in cards:
        category = determine_category(message.text)
        await forward_card(
            user, card, source, message.chat.id, message.id, category, is_old
        )

# ========== SCRAPE HISTORY ==========
async def scrape_all_history():
    logging.info("📜 SCRAPING ALL HISTORY...")
    
    if not user.is_connected:
        await user.start()
    
    total_scanned = 0
    try:
        async for dialog in user.get_dialogs():
            chat = dialog.chat
            if chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL]:
                source = f"@{chat.username}" if chat.username else f"group_{chat.id}"
                logging.info(f"📜 Scraping: {source}")
                
                count = 0
                async for message in user.get_chat_history(chat.id):
                    await process_message(message, is_old=True)
                    count += 1
                    if count % 100 == 0:
                        logging.info(f"📊 Scanned {count} messages in {source}")
                        await asyncio.sleep(0.3)
                
                logging.info(f"✅ Done: {count} messages from {source}")
                total_scanned += count
                
    except Exception as e:
        logging.error(f"❌ History scrape failed: {e}")
    
    logging.info(f"✅ TOTAL SCANNED: {total_scanned} messages")

# ========== LIVE SCRAPE ==========
@user.on_message(filters.text & ~filters.bot)
async def live_handler(client, message):
    if LIVE_SCRAPE_ACTIVE:
        await process_message(message, is_old=False)

# ========== BOT COMMANDS ==========
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
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
        "👉 SCRAPE button dabao — live start hoga.",
        reply_markup=keyboard,
        parse_mode=enums.ParseMode.HTML
    )

@bot.on_callback_query()
async def cb_handler(client, query):
    global LIVE_SCRAPE_ACTIVE
    data = query.data
    
    if data == "scrape_start":
        LIVE_SCRAPE_ACTIVE = True
        await query.answer("✅ LIVE SCRAPING STARTED!")
        await query.message.reply_text("🟢 LIVE SCRAPING ACTIVE — har group se CC lega.")
    
    elif data == "tools":
        stats = db.get_stats()
        today = db.get_today_stats()
        text = f"""
🛠 <b>TOOLS MENU</b>
📊 Total: {stats['total']}
├ Approved: {stats['approved']}
├ Live: {stats['live']}
└ Old: {stats['old']}
📆 Today: {today['forwarded']} forwarded, {today['pending']} pending
"""
        await query.message.reply_text(text)
    
    elif data == "fetch":
        await query.answer("📜 OLD SCRAPE STARTED!")
        msg = await query.message.reply_text("📜 Scraping old messages...")
        await scrape_all_history()
        await msg.edit_text("✅ OLD SCRAPE COMPLETE!")

@bot.on_message(filters.command("status") & filters.private)
async def status_cmd(client, message):
    stats = db.get_stats()
    await message.reply_text(
        f"📊 <b>STATUS</b>\n\n"
        f"Total: {stats['total']}\n"
        f"Approved: {stats['approved']}\n"
        f"Live: {stats['live']}\n"
        f"Old: {stats['old']}\n"
        f"Today: {stats['today']}",
        parse_mode=enums.ParseMode.HTML
    )

@bot.on_message(filters.command("scan_today") & filters.private)
async def scan_today_cmd(client, message):
    today = db.get_today_stats()
    await message.reply_text(
        f"📆 <b>TODAY</b>\n\n"
        f"Forwarded: {today['forwarded']}\n"
        f"Pending: {today['pending']}",
        parse_mode=enums.ParseMode.HTML
    )

@bot.on_message(filters.command("rescan") & filters.private)
async def rescan_cmd(client, message):
    await message.reply_text("🔄 Checking skipped CCs...")
    skipped = db.get_skipped_cards()
    if not skipped:
        await message.reply_text("✅ No skipped CCs found.")
    else:
        await message.reply_text(f"✅ Found {len(skipped)} skipped CCs.")

# ========== MAIN ==========
async def main():
    logging.info("🔥 CC SNIPER ULTIMATE STARTING...")
    
    await user.start()
    logging.info("✅ User account started!")
    
    await bot.start()
    logging.info("✅ Bot account started!")
    
    if SCRAPE_HISTORY:
        logging.info("📜 SCRAPING HISTORY ONCE...")
        await scrape_all_history()
        logging.info("✅ HISTORY SCRAPE COMPLETE")
    
    logging.info("🤖 Bot is LIVE! Commands available via bot.")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
