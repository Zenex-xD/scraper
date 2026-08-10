# ========== database/mongo_db.py ==========
import logging
from datetime import datetime, date
from pymongo import MongoClient, errors
from pymongo.collection import Collection

MONGO_URI = "mongodb://localhost:27017"  # Change to your MongoDB URI
DB_NAME = "cc_sniper"

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.cards: Collection = None
        self.skipped: Collection = None
        self._connect()

    def _connect(self):
        """Connect to MongoDB."""
        try:
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            self.client.server_info()  # Test connection
            self.db = self.client[DB_NAME]
            self.cards = self.db["cards"]
            self.skipped = self.db["skipped"]

            # Indexes
            self.cards.create_index("card", unique=True)
            self.skipped.create_index("card")

            logging.info("✅ MongoDB connected!")

        except errors.ServerSelectionTimeoutError:
            logging.critical("❌ MongoDB connection FAILED!")
            raise

    def is_duplicate(self, card: str) -> bool:
        """Check if card already exists."""
        try:
            return self.cards.find_one({"card": card}) is not None
        except Exception as e:
            logging.error(f"❌ is_duplicate error: {e}")
            return False

    def save_card(
        self,
        card: str,
        source: str,
        chat_id: int,
        message_id: int,
        category: str,
        is_old: bool
    ):
        """Save card to database."""
        try:
            self.cards.update_one(
                {"card": card},
                {"$setOnInsert": {
                    "card": card,
                    "source": source,
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "category": category,
                    "is_old": is_old,
                    "forwarded": True,
                    "date": datetime.utcnow(),
                    "date_str": str(date.today())
                }},
                upsert=True
            )
        except errors.DuplicateKeyError:
            logging.debug(f"⏭️ Duplicate card: {card}")
        except Exception as e:
            logging.error(f"❌ save_card error: {e}")

    def save_skipped(
        self,
        card: str,
        source: str,
        chat_id: int,
        message_id: int,
        category: str
    ):
        """Save skipped card."""
        try:
            self.skipped.insert_one({
                "card": card,
                "source": source,
                "chat_id": chat_id,
                "message_id": message_id,
                "category": category,
                "date": datetime.utcnow()
            })
        except Exception as e:
            logging.error(f"❌ save_skipped error: {e}")

    def get_stats(self) -> dict:
        """Get overall statistics."""
        try:
            total = self.cards.count_documents({})
            approved = self.cards.count_documents({"category": "live"})
            live = self.cards.count_documents({"is_old": False})
            old = self.cards.count_documents({"is_old": True})
            today_count = self.cards.count_documents(
                {"date_str": str(date.today())}
            )
            return {
                "total": total,
                "approved": approved,
                "live": live,
                "old": old,
                "today": today_count
            }
        except Exception as e:
            logging.error(f"❌ get_stats error: {e}")
            return {
                "total": 0,
                "approved": 0,
                "live": 0,
                "old": 0,
                "today": 0
            }

    def get_today_stats(self) -> dict:
        """Get today's statistics."""
        try:
            today_str = str(date.today())
            forwarded = self.cards.count_documents({"date_str": today_str})
            pending = self.skipped.count_documents({"date": {
                "$gte": datetime.utcnow().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            }})
            return {
                "forwarded": forwarded,
                "pending": pending
            }
        except Exception as e:
            logging.error(f"❌ get_today_stats error: {e}")
            return {"forwarded": 0, "pending": 0}

    def get_skipped_cards(self) -> list:
        """Get all skipped cards."""
        try:
            return list(self.skipped.find({}, {"_id": 0}))
        except Exception as e:
            logging.error(f"❌ get_skipped_cards error: {e}")
            return []

# Singleton instance
db = Database()
