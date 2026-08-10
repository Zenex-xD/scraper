import logging
from pyrogram import enums
from config import LIVE_GROUP, CHARGED_GROUP, LOG_CHANNEL, FETCH_GROUP
from database.mongo_db import db

async def forward_card(app, card_data, source, chat_id, message_id, category, is_old=False):
    pan = card_data['pan']
    month = card_data['month']
    year = card_data['year']
    cvv = card_data['cvv']
    full = card_data['full']
    
    # Check if already forwarded
    if db.is_forwarded(chat_id, message_id):
        return
    
    # Save to DB
    card_id = db.save_card(pan, month, year, cvv, full, source, chat_id, message_id, category, is_old)
    if not card_id:
        return
    
    # Select channel
    if is_old:
        target_channel = FETCH_GROUP
        emoji = "📜 OLD"
    elif category == "APPROVED":
        target_channel = CHARGED_GROUP
        emoji = "✅ APPROVED"
    else:
        target_channel = LIVE_GROUP
        emoji = "🔴 LIVE"
    
    # Build message
    forward_text = f"""
{emoji} <b>CC DROPPED</b> {emoji}

<b>PAN:</b> <code>{pan}</code>
<b>Expiry:</b> {month}/{year}
<b>CVV:</b> <code>{cvv}</code>
<b>Full:</b> <code>{full}</code>

📡 <b>Source:</b> {source}
📋 <b>ID:</b> #{card_id}
<b>Category:</b> {category}
🕐 <b>Time:</b> {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    try:
        await app.send_message(
            chat_id=target_channel,
            text=forward_text,
            parse_mode=enums.ParseMode.HTML
        )
        db.mark_forwarded(card_id, target_channel)
        logging.info(f"📤 {pan[:6]}XXXX → {target_channel}")
        
        # Log to log channel
        await app.send_message(
            chat_id=LOG_CHANNEL,
            text=f"📤 Forwarded: {pan[:6]}XXXX | {category} | {source}",
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        logging.error(f"❌ Forward failed: {e}")
