import re
from typing import Tuple, Optional

def parse_title_and_year(input_str: str) -> Tuple[str, Optional[int]]:
    """
    Splits "The Matrix (1999)" into ("The Matrix", 1999).
    Returns (Title, None) if no year is found.
    Regex is extremely fast, so no tqdm needed here.
    """
    if not input_str: return "", None
    
    # Regex to find (YYYY) at the very end of the string
    # Matches: "Movie Title (1999)" -> Group 1: "Movie Title", Group 2: "1999"
    match = re.search(r'(.*?)\s*\((\d{4})\)$', str(input_str))
    
    if match:
        title = match.group(1).strip()
        year = int(match.group(2))
        return title, year
    
    # No year found, return clean original string
    return input_str.strip(), None