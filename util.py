import re


def to_snake(before):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', before).lower()