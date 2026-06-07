from collections import defaultdict
import hashlib
from typing import List, Tuple, Dict, Generator

def shingle_tokens(text: str, k=5) -> Generator[Tuple[int, str], None, None]:
    """
    Splits normalized text into word shingles of size k.
    Yields (char_index_in_normalized_text, shingle_string).
    """
    words = text.split()
    if len(words) < k:
        return

    # Pre-calculate the starting character index for each word
    word_starts = []
    curr_idx = 0
    for w in words:
        start = text.find(w, curr_idx)
        word_starts.append(start)
        curr_idx = start + len(w)

    for i in range(len(words) - k + 1):
        shingle_words = words[i:i+k]
        shingle_str = " ".join(shingle_words)
        char_pos = word_starts[i]
        yield char_pos, shingle_str

def hash_shingle(s: str) -> int:
    """
    Hash a shingle using blake2b, truncated to a 64-bit integer.
    """
    return int(hashlib.blake2b(s.encode(), digest_size=8).hexdigest(), 16)

def winnow_fingerprints(text: str, k=5, t=9) -> List[Tuple[int, int]]:
    """
    Winnowing algorithm.
    Selects a subset of shingle hashes within a sliding window of size w = t - k + 1.
    Returns a list of (start_char_idx, fingerprint_hash).
    """
    w = max(1, t - k + 1)
    shingles = list(shingle_tokens(text, k))
    if not shingles:
        return []

    hashes = [(pos, hash_shingle(sh)) for pos, sh in shingles]
    mins = []
    last_min = None

    # Sliding window over shingle hashes
    for i in range(len(hashes) - w + 1):
        window = hashes[i:i+w]
        # In case of tie, choose the rightmost minimum value
        # by sorting with key: (hash_value, -position)
        mpos, mval = min(window, key=lambda x: (x[1], -x[0]))
        if (mpos, mval) != last_min:
            mins.append((mpos, mval))
            last_min = (mpos, mval)

    return mins

def build_fingerprint_index(texts: Dict[str, str], k=5, t=9) -> Dict[int, List[Tuple[str, int]]]:
    """
    Builds an inverted index of fingerprints.
    Returns a dictionary of:
    { fingerprint_hash: [(doc_id, normalized_char_pos), ...] }
    """
    inv = defaultdict(list)
    for doc_id, txt in texts.items():
        fps = winnow_fingerprints(txt, k=k, t=t)
        for pos, h in fps:
            inv[h].append((doc_id, pos))
    return dict(inv)
