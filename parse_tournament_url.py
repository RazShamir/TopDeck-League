"""
Parse tournament URLs and IDs to extract tournament_id and encoded_id
"""

import re
import sys

def parse_tournament_url(url_or_id):
    """
    Parse tournament URL or ID to extract tournament_id.

    Supported formats:
    - https://mtgarena.appspot.com/#t4651297216135168
    - https://mtgarena.appspot.com/#tournament4651297216135168
    - mtgarena.appspot.com/#t4651297216135168
    - #t4651297216135168
    - t4651297216135168
    - 4651297216135168

    Returns:
        tuple: (tournament_id, None) - encoded_id must still be provided separately
    """
    # Remove any whitespace
    url_or_id = url_or_id.strip()

    # Pattern to match tournament ID in various formats
    patterns = [
        r'#t(\d+)',                          # #t4651297216135168
        r'#tournament(\d+)',                 # #tournament4651297216135168
        r't(\d+)',                           # t4651297216135168
        r'tournament(\d+)',                  # tournament4651297216135168
        r'^(\d+)$',                          # 4651297216135168
    ]

    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1), None

    # If no match, assume it's already just the ID
    return url_or_id, None

def test_parser():
    """Test the parser with various inputs"""
    test_cases = [
        "https://mtgarena.appspot.com/#t4651297216135168",
        "https://mtgarena.appspot.com/#tournament4651297216135168",
        "mtgarena.appspot.com/#t4651297216135168",
        "#t4651297216135168",
        "t4651297216135168",
        "4651297216135168",
    ]

    print("Testing URL parser:")
    for test in test_cases:
        tid, _ = parse_tournament_url(test)
        print(f"  {test:50s} → {tid}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        tid, _ = parse_tournament_url(sys.argv[1])
        print(tid)
    else:
        test_parser()
