import logging

from casefy import kebabcase
from unidecode import unidecode

log_file = "audit.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ],
    force=True  # This will reset the root logger's handlers and apply the new configuration
)

logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


def unicode_to_ascii(text):
    """
    Convert unicode text to ASCII, replacing special characters.
    """

    if text is None:
        return None

    # Replacing 'ë' with 'e' and return the ASCII text
    return unidecode(text).replace("ë", "e")


def kebab_case(s):
    return kebabcase(s)


def unique_strings(lst):
    # Use a set to remove duplicates, then convert back to a list
    return list(dict.fromkeys(lst))


def printred(text):
    red = "\033[91m"
    reset = "\033[0m"
    logger.debug("Printing text in red: %s", text)
    print(f"{red}{text}{reset}")


def printyellow(text):
    yellow = "\033[93m"
    reset = "\033[0m"
    logger.debug("Printing text in yellow: %s", text)
    print(f"{yellow}{text}{reset}")
