# ========== config.py ==========
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def get_int(key: str, default=None):
    """Safely get integer from env."""
    val = os.getenv(key, default)
    try:
        return int(val)
    except (TypeError, ValueError):
        return default

def get_bool(key: str, default=False) -> bool:
    """Safely get boolean from env."""
    val = os.getenv(key, str(default)).lower()
    return val in ("true", "1", "yes", "on")

def get_list(key: str, default="") -> list:
    """Safely get list from env (comma separated)."""
    val = os.getenv(key, default)
    if not val:
        return []
    return [item.strip() for item in val.split(",") if item.strip()]

def get_int_list(key: str, default="") -> list:
    """Safely get integer list from env (comma separated)."""
    items = get_list(key, default)
    result = []
    for item in items:
        try:
            result.append(int(item))
        except ValueError:
            pass
    return result

# ========== TELEGRAM CREDENTIALS ==========
API_ID = get_int("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_SESSION = os.getenv("USER_SESSION")

# ========== GROUPS / CHANNELS ==========
LIVE_GROUP = get_int("LIVE_GROUP")
CHARGED_GROUP = get_int("CHARGED_GROUP")
LOG_CHANNEL = get_int("LOG_CHANNEL")
FETCH_GROUP = get_int("FETCH_GROUP")

# ========== ADMIN IDS ==========
ADMIN_IDS = get_int_list("ADMIN_IDS")

# ========== KEYWORDS =========
APPROVED_KEYWORDS = get_list(
    "APPROVED_KEYWORDS",
    "✅,APPROVED,Card declined,Response:,RISK_DISALLOWED,Info:,Issuer:,Country:,Checked by,BOT by,VISA,MASTERCARD,DEBIT,CREDIT,GOLD,PLATINUM,BANK,DECLINED,ERROR,PAYPAL,STRIPE,GATE,ℹ️,🏛️,🌎,STATUS,GATEWAY,AUTH,CAPTURE"
)
# ========== MONGO DB ==========
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "cc_sniper")

# ========== SCRAPER SETTINGS ==========
SCRAPE_HISTORY = get_bool("SCRAPE_HISTORY", False)
LIVE_SCRAPE_ACTIVE = get_bool("LIVE_SCRAPE_ACTIVE", False)

# ========== VALIDATION ==========
def validate_config():
    """Validate all required config values."""
    errors = []

    if not API_ID:
        errors.append("❌ API_ID is missing!")

    if not API_HASH:
        errors.append("❌ API_HASH is missing!")

    if not BOT_TOKEN:
        errors.append("❌ BOT_TOKEN is missing!")

    if not USER_SESSION:
        errors.append("❌ USER_SESSION is missing!")

    if not LIVE_GROUP:
        errors.append("❌ LIVE_GROUP is missing!")

    if not CHARGED_GROUP:
        errors.append("❌ CHARGED_GROUP is missing!")

    if not LOG_CHANNEL:
        errors.append("❌ LOG_CHANNEL is missing!")

    if not FETCH_GROUP:
        errors.append("❌ FETCH_GROUP is missing!")

    if not ADMIN_IDS:
        errors.append("❌ ADMIN_IDS is missing!")

    if not MONGO_URI:
        errors.append("❌ MONGO_URI is missing!")

    if errors:
        print("\n".join(errors))
        print("\n⚠️  Fix above errors in .env file!")
        raise SystemExit(1)
    else:
        print("✅ Config validated successfully!")

# Run validation on import
validate_config()
             


# ========== SCRAPE SETTINGS ==========
SCRAPE_HISTORY = True
LIVE_SCRAPE_ACTIVE = False
