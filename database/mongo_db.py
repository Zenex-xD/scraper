from pymongo import MongoClient
from datetime import datetime
import logging
from config import MONGO_URI, DB_NAME, COLLECTION_NAME

class Database:
    def __init__(self):
        try:
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            self.db = self.client[DB_NAME]
            self.collection = self.db[COLLECTION_NAME]
            # Create index for duplicate check
            self.collection.create_index([("chat_id", 1), ("message_id", 1)], unique=True)
            logging.info("✅ MongoDB connected")
        except Exception as e:
            logging.error(f"❌ MongoDB connection failed: {e}")
            self.client = None
            self.db = None
            self.collection = None

    def save_card(self, pan, month, year, cvv, full, source, chat_id, message_id, category, is_old=False):
        if not self.collection:
            return None
        try:
            doc = {
                "pan": pan,
                "month": month,
                "year": year,
                "cvv": cvv,
                "full": full,
                "bin": pan[:6],
                "source": source,
                "chat_id": chat_id,
                "message_id": message_id,
                "category": category,
                "is_old": is_old,
                "forwarded": False,
                "forwarded_to": None,
                "timestamp": datetime.now().isoformat()
            }
            result = self.collection.insert_one(doc)
            return result.inserted_id
        except Exception as e:
            logging.error(f"Save error: {e}")
            return None

    def mark_forwarded(self, card_id, channel):
        if not self.collection:
            return
        try:
            self.collection.update_one(
                {"_id": card_id},
                {"$set": {"forwarded": True, "forwarded_to": channel}}
            )
        except Exception as e:
            logging.error(f"Mark forward error: {e}")

    def is_forwarded(self, chat_id, message_id):
        if not self.collection:
            return False
        try:
            result = self.collection.find_one({"chat_id": chat_id, "message_id": message_id})
            return result is not None
        except:
            return False

    def get_stats(self):
        if not self.collection:
            return {"total": 0, "approved": 0, "live": 0, "old": 0, "today": 0}
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            total = self.collection.count_documents({})
            approved = self.collection.count_documents({"category": "APPROVED"})
            live = self.collection.count_documents({"category": "LIVE"})
            old = self.collection.count_documents({"is_old": True})
            today_count = self.collection.count_documents({"timestamp": {"$regex": f"^{today}"}})
            return {
                "total": total,
                "approved": approved,
                "live": live,
                "old": old,
                "today": today_count
            }
        except:
            return {"total": 0, "approved": 0, "live": 0, "old": 0, "today": 0}

    def get_today_stats(self):
        if not self.collection:
            return {"forwarded": 0, "pending": 0}
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            forwarded = self.collection.count_documents({
                "timestamp": {"$regex": f"^{today}"},
                "forwarded": True
            })
            pending = self.collection.count_documents({
                "timestamp": {"$regex": f"^{today}"},
                "forwarded": False
            })
            return {"forwarded": forwarded, "pending": pending}
        except:
            return {"forwarded": 0, "pending": 0}

    def get_skipped_cards(self):
        """Cards that were extracted but not forwarded (missing category)"""
        if not self.collection:
            return []
        try:
            return list(self.collection.find({"forwarded": False, "category": {"$exists": True}}).limit(10))
        except:
            return []

db = Database()
