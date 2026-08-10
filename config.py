# ========== config.py ==========

# Telegram API Credentials
API_ID = 123456               # Your API ID from my.telegram.org
API_HASH = "your_api_hash"    # Your API Hash
BOT_TOKEN = "your_bot_token"  # From @BotFather
USER_SESSION = "your_session_string"  # From Pyrogram session

# Group / Channel IDs or Usernames
LIVE_GROUP = -1001234567890    # Where live CCs are posted
CHARGED_GROUP = -1009876543210 # Where approved CCs go
LOG_CHANNEL = -1001111111111   # Log channel
FETCH_GROUP = -1002222222222   # Group to listen for live scrape

# Admin User IDs (list of integers)
ADMIN_IDS = [111111111, 222222222
             
APPROVED_KEYWORDS = [
    "✅", "APPROVED", "Card declined", "Response:", "RISK_DISALLOWED",
    "Info:", "Issuer:", "Country:", "Checked by", "BOT by",
    "VISA", "MASTERCARD", "DEBIT", "CREDIT", "GOLD", "PLATINUM",
    "BANK", "DECLINED", "ERROR", "PAYPAL", "STRIPE", "GATE",
    "ℹ️", "🏛️", "🌎", "STATUS", "GATEWAY", "AUTH", "CAPTURE"
]

# ========== SCRAPE SETTINGS ==========
SCRAPE_HISTORY = True
LIVE_SCRAPE_ACTIVE = False
