# ========== CONFIG.PY (NO LIMIT) ==========
import os

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SESSION_NAME = os.getenv("SESSION", "cc_sniper")

LIVE_GROUP = os.getenv("LIVE_GROUP", "")
CHARGED_GROUP = os.getenv("CHARGED_GROUP", "")
LOG_CHANNEL = os.getenv("LOG_CHANNEL", "")
FETCH_GROUP = os.getenv("FETCH_GROUP", "")

MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME = "cc_sniper"
COLLECTION_NAME = "cards"

APPROVED_KEYWORDS = [
    "✅", "APPROVED", "Card declined", "Response:", "RISK_DISALLOWED",
    "Info:", "Issuer:", "Country:", "Checked by", "BOT by",
    "VISA", "MASTERCARD", "DEBIT", "CREDIT", "GOLD", "PLATINUM",
    "BANK", "DECLINED", "ERROR", "PAYPAL", "STRIPE", "GATE",
    "ℹ️", "🏛️", "🌎", "STATUS", "GATEWAY", "AUTH", "CAPTURE"
]

SCRAPE_HISTORY = True
# HISTORY_LIMIT = HATAYA — AB UNLIMITED
