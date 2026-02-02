import re
import phonenumbers
import logging

logger = logging.getLogger(__name__)

class DataCleaner:
    @staticmethod
    def normalize_phone(phone_str: str, country_code: str = "US") -> str:
        """
        Parses and formats phone number to E.164 or global format.
        Falls back to cleaning regex if parsing fails.
        """
        if not phone_str:
            return ""
            
        try:
            # removing some garbage that might confuse the parser if not strict
            # but phonenumbers is usually good.
            parsed = phonenumbers.parse(phone_str, country_code)
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        except Exception as e:
            pass
            
        # Fallback: simple digit extraction
        digits = re.sub(r'\D', '', phone_str)
        return digits

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Removes extra whitespace and newlines.
        """
        if not text:
            return ""
        return " ".join(text.split())
