import random
import string


def endorsement_code(length=6) -> str:
    """random_number_to_string"""
    charset = string.ascii_uppercase + string.digits
    base = len(charset)  # 36 possible characters
    max_number = base ** length
    num = random.randint(0, max_number)
    result = []
    for _ in range(length):
        result.append(charset[num % base])
        num //= base
    return ''.join(reversed(result))  # Reverse to get correct ord
