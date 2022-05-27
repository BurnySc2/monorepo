import re
from typing import Dict

from loguru import logger


def mass_replacer(text: str, replace_dict: Dict[str, str]) -> str:
    # Source: https://stackoverflow.com/a/6117124
    # In case there is escape characters in k, it will not work without "re.escape"
    replace_dict = {re.escape(k): v for k, v in replace_dict.items()}
    pattern = re.compile('|'.join(replace_dict.keys()))
    new_text = pattern.sub(lambda m: replace_dict[re.escape(m.group(0))], text)
    return new_text


def main():
    text = 'my text cond\nition1 condition2'
    replace_dict = {'cond\nition1': 'loves', 'condition2': 'fun'}
    new_text = mass_replacer(text, replace_dict)
    logger.info(f'Mass replaced\n"{text}"\nto\n{new_text}')


if __name__ == '__main__':
    main()
