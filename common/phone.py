import re


def normalize_phone(raw):
    """Format a North American phone number as (xxx) xxx-xxxx.

    Accepts any input with digits (spaces, dashes, parens, leading +1/1 all OK).
    Returns None for empty input. Raises ValueError if the digit count is
    not 10 (or 11 with a leading 1).
    """
    if not raw or not raw.strip():
        return None

    digits = re.sub(r'\D', '', raw)

    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]

    if len(digits) != 10:
        raise ValueError(
            f'Invalid phone number: "{raw}". '
            'Please enter a 10-digit North American phone number.'
        )

    return f'({digits[0:3]}) {digits[3:6]}-{digits[6:10]}'
