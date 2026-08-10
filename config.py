import os

# ========== BOT ACCOUNT (Commands + Status) ==========
BOT_TOKEN = os.getenv("BOT_TOKEN", "")  # Bot token for commands only

# ========== USER ACCOUNT (Scrape + Forward) ==========
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
USER_SESSION = os.getenv("USER_SESSION", "user_session")  # User session for scraping

# ========== FORWARD CHANNELS ==========
LIVE_GROUP = os.getenv("LIVE_GROUP", "")
CHARGED_GROUP = os.getenv("CHARGED_GROUP", "")
LOG_CHANNEL = os.getenv("LOG_CHANNEL", "")
FETCH_GROUP = os.getenv("FETCH_GROUP", "")

# ========== MONGODB ==========
MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME = "cc_sniper"
COLLECTION_NAME = "cards"

# ========== KEYWORDS FOR APPROVED ==========
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
