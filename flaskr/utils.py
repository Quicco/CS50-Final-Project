import phonenumbers
import re
from phonenumbers import NumberParseException

# Constants
LOCATIONS = ["Lisbon", "Sintra", "Porto"]
CLASS_TYPES = ["PowerUp", "Bootcamp"]


# Validate the phone number and standardize the format
def validate_phone_num(contact_info):
    REGION = "PT"

    if re.search("[a-zA-Z]", contact_info):
        return False

    try:
        phone_number = phonenumbers.parse(contact_info, REGION)

        if not phonenumbers.is_possible_number(phone_number):
            return False

        if not phonenumbers.is_valid_number(phone_number):
            return False

        formatted_number = phonenumbers.format_number(
            phone_number, phonenumbers.PhoneNumberFormat.NATIONAL
        )

        return formatted_number
    except NumberParseException as e:
        return False
