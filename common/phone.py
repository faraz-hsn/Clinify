import re


def normalize_phone(raw):
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

    return digits


def format_phone(value):
    if not value:
        return ''
    digits = re.sub(r'\D', '', str(value))
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]
    if len(digits) != 10:
        return str(value)
    return f'({digits[0:3]}) {digits[3:6]}-{digits[6:10]}'
