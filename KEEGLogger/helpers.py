def safe_cast(val, to_type, default=None):
    try:
        return to_type(val)
    except (ValueError, TypeError):
        return default

def print_dashes(dashes = 40, rows = 1):
    dashText = ''
    for i in range(dashes): dashText += '-'
    for i in range(rows):
        print(dashText)

