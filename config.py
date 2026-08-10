import os

# ========== TELEGRAM API ==========
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SESSION_NAME = os.getenv("SESSION", "cc_sniper")

# ========== FORWARD CHANNELS ==========
LIVE_GROUP = os.getenv("LIVE_GROUP", "")          # Raw CCs
CHARGED_GROUP = os.getenv("CHARGED_GROUP", "")    # Approved CCs
LOG_CHANNEL = os.getenv("LOG_CHANNEL", "")        # Logs
FETCH_GROUP = os.getenv("FETCH_GROUP", "")        # Old scrape

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
# HISTORY_LIMIT = 5000   # <-- HATAYA — AB UNLIMITED

# ========== LIVE SCRAPE FLAG ==========
LIVE_SCRAPE_ACTIVE = False   # Default OFF — SCRAPE button se ON hoga
