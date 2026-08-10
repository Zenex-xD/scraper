import re
from config import APPROVED_KEYWORDS

CC_PATTERNS = [
    r'(\d{13,19})\s*[\|\/\\\-]\s*(\d{1,2})\s*[\|\/\\\-]\s*(\d{2,4})\s*[\|\/\\\-]\s*(\d{3,4})',
    r'(\d{13,19})\s+(\d{1,2})\s+(\d{2,4})\s+(\d{3,4})',
    r'(\d{13,19})\s*,\s*(\d{1,2})\s*,\s*(\d{2,4})\s*,\s*(\d{3,4})',
    r'(\d{13,19})\s*\/\s*(\d{1,2})\s*\/\s*(\d{2,4})\s*\/\s*(\d{3,4})',
    r'(\d{13,19})\s*[\|\/]\s*(\d{1,2})\s*[\|\/]\s*(\d{2,4})\s*[\|\/]\s*(\d{3,4})',
]

def extract_ccs(text):
    if not text:
        return []
    cards = []
    for pattern in CC_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            groups = match.groups()
            if len(groups) == 4:
                pan = groups[0].strip()
                month = groups[1].strip().zfill(2)
                year = groups[2].strip()
                cvv = groups[3].strip()
                if not (1 <= int(month) <= 12):
                    continue
                if len(year) == 2:
                    year = "20" + year
                if len(year) != 4:
                    continue
                if not luhn_check(pan):
                    continue
                cards.append({
                    "pan": pan,
                    "month": month,
                    "year": year,
                    "cvv": cvv,
                    "full": f"{pan}|{month}|{year}|{cvv}"
                })
    return cards

def luhn_check(card):
    total = 0
    reverse = card[::-1]
    for i, digit in enumerate(reverse):
        n = int(digit)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0

def is_approved_message(text):
    if not text:
        return False
    text_upper = text.upper()
    for keyword in APPROVED_KEYWORDS:
        if keyword.upper() in text_upper:
            return True
    if re.search(r'RESPONSE:|INFO:|ISSUER:|COUNTRY:|CHECKED BY|BOT BY|STATUS:|GATEWAY:', text_upper):
        return True
    if re.search(r'VISA|MASTERCARD|AMEX|DISCOVER|DEBIT|CREDIT|GOLD|PLATINUM|TITANIUM', text_upper):
        return True
    return False

def determine_category(message_text):
    if is_approved_message(message_text):
        return "APPROVED"
    return "LIVE"
