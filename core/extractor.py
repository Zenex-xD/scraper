# ========== core/extractor.py ==========
import re
import logging

# CC Pattern: 16 digits | exp month | exp year | cvv
CC_PATTERN = re.compile(
    r'\b(\d{15,16})[|/:,\s](\d{1,2})[|/:,\s](\d{2,4})[|/:,\s](\d{3,4})\b'
)

LIVE_KEYWORDS = [
    "charged", "approved", "live", "hit", "success",
    "✅", "charge", "captured", "auth"
]

DEAD_KEYWORDS = [
    "dead", "declined", "failed", "invalid",
    "❌", "error", "insufficient"
]

def extract_ccs(text: str) -> list:
    """Extract all CC numbers from text."""
    try:
        if not text:
            return []

        cards = []
        matches = CC_PATTERN.findall(text)

        for match in matches:
            number, month, year, cvv = match

            # Normalize year
            if len(year) == 2:
                year = f"20{year}"

            # Basic validation
            if not _luhn_check(number):
                logging.debug(f"Failed Luhn: {number}")
                continue

            month_int = int(month)
            if not (1 <= month_int <= 12):
                continue

            card = f"{number}|{month}|{year}|{cvv}"
            cards.append(card)

        return list(set(cards))  # Remove duplicates

    except Exception as e:
        logging.error(f"❌ extract_ccs error: {e}")
        return []

def determine_category(text: str) -> str:
    """Determine if card is live, dead, or unknown."""
    try:
        if not text:
            return "unknown"

        text_lower = text.lower()

        for keyword in LIVE_KEYWORDS:
            if keyword.lower() in text_lower:
                return "live"

        for keyword in DEAD_KEYWORDS:
            if keyword.lower() in text_lower:
                return "dead"

        return "unknown"

    except Exception as e:
        logging.error(f"❌ determine_category error: {e}")
        return "unknown"

def _luhn_check(card_number: str) -> bool:
    """Validate card number using Luhn algorithm."""
    try:
        digits = [int(d) for d in card_number]
        digits.reverse()
        total = 0

        for i, digit in enumerate(digits):
            if i % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            total += digit

        return total % 10 == 0

    except Exception:
        return False
