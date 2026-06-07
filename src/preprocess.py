import re
import unicodedata
from typing import Tuple, List

def normalize(text: str) -> Tuple[str, List[int]]:
    """
    Normalizes the input text for comparison:
    1. Lowercases the text.
    2. Strips punctuation and non-alphanumeric characters (except spaces).
    3. Collapses multiple spaces/newlines into a single space.
    4. Maps every character in the normalized text to its original index in the raw text.

    Returns:
        normalized_str: Cleaned lowercase string with single-spaced words.
        index_map: List where index_map[i] is the character index in the original text
                   corresponding to normalized_str[i].
    """
    if not text:
        return "", []

    out = []
    idx_map = []

    # Step 1: Normalize unicode characters and filter alphanumeric/space
    for i, ch in enumerate(text):
        # Normalize Unicode character to standard form
        ch_norm = unicodedata.normalize("NFKC", ch)
        ch_lower = ch_norm.lower()

        if ch_lower.isalnum():
            out.append(ch_lower)
            idx_map.append(i)
        elif ch_lower.isspace() or ch == '\n' or ch == '\r' or ch == '\t':
            # Append a single space if the output doesn't already end with one
            if out and out[-1] != " ":
                out.append(" ")
                idx_map.append(i)

    # Strip trailing space if any
    while out and out[-1] == " ":
        out.pop()
        idx_map.pop()

    # Strip leading space if any
    while out and out[0] == " ":
        out.pop(0)
        idx_map.pop(0)

    normalized_str = "".join(out)
    return normalized_str, idx_map
