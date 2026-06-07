from typing import List, Tuple, Dict, Any

def compute_lps(pat: str) -> List[int]:
    """
    Computes the Longest Prefix Suffix (LPS) array for KMP string matching.
    LPS[i] stores the length of the longest proper prefix of pat[0...i]
    that is also a suffix of pat[0...i].
    """
    m = len(pat)
    lps = [0] * m
    length = 0  # Length of the previous longest prefix suffix
    i = 1

    while i < m:
        if pat[i] == pat[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1
    return lps

def compute_lps_trace(pat: str) -> List[Dict[str, Any]]:
    """
    Trace the step-by-step execution of the LPS array calculation.
    Useful for the frontend virtual simulator.
    """
    m = len(pat)
    lps = [0] * m
    trace = []
    length = 0
    i = 1

    # Record the initial state
    trace.append({
        "step": 0,
        "i": 0,
        "length": 0,
        "lps": list(lps),
        "comparison": "Initialization",
        "action": "Initialize LPS array with zeros.",
        "matched": None
    })

    step = 1
    while i < m:
        char_i = pat[i]
        char_len = pat[length]
        comp_str = f"pat[{i}] ('{char_i}') == pat[{length}] ('{char_len}')"
        
        if pat[i] == pat[length]:
            length += 1
            lps[i] = length
            trace.append({
                "step": step,
                "i": i,
                "length": length,
                "lps": list(lps),
                "comparison": comp_str,
                "action": f"Match! Set lps[{i}] = {length}. Move to next character.",
                "matched": True
            })
            i += 1
        else:
            if length != 0:
                old_length = length
                length = lps[length - 1]
                trace.append({
                    "step": step,
                    "i": i,
                    "length": length,
                    "lps": list(lps),
                    "comparison": comp_str,
                    "action": f"Mismatch! Fall back: length = lps[{old_length}-1] = {length}.",
                    "matched": False
                })
            else:
                lps[i] = 0
                trace.append({
                    "step": step,
                    "i": i,
                    "length": 0,
                    "lps": list(lps),
                    "comparison": comp_str,
                    "action": f"Mismatch & length is 0. Set lps[{i}] = 0. Move to next character.",
                    "matched": False
                })
                i += 1
        step += 1
    return trace

def kmp_search(text: str, pat: str) -> List[int]:
    """
    Searches for all occurrences of pattern 'pat' in 'text' using the
    Knuth-Morris-Pratt algorithm. Returns a list of start indices.
    """
    n = len(text)
    m = len(pat)
    if m == 0 or n < m:
        return []

    lps = compute_lps(pat)
    res = []
    i = 0  # index for text
    j = 0  # index for pat

    while i < n:
        if pat[j] == text[i]:
            i += 1
            j += 1

        if j == m:
            res.append(i - j)
            j = lps[j - 1]
        elif i < n and pat[j] != text[i]:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1
    return res

def rabin_karp_search(text: str, pat: str, base=256, mod=10**9+7) -> List[int]:
    """
    Rabin-Karp single pattern matching using rolling hash.
    Returns a list of start indices.
    """
    n = len(text)
    m = len(pat)
    if m == 0 or n < m:
        return []

    res = []
    h = 0  # hash value for pattern
    t = 0  # hash value for text sliding window
    h_multiplier = pow(base, m - 1, mod)

    # Calculate the hash value of pattern and first window of text
    for i in range(m):
        h = (base * h + ord(pat[i])) % mod
        t = (base * t + ord(text[i])) % mod

    # Slide the pattern over text one by one
    for i in range(n - m + 1):
        if h == t:
            # Check characters one by one for confirmation (resolve collisions)
            if text[i:i+m] == pat:
                res.append(i)

        if i < n - m:
            t = (base * (t - ord(text[i]) * h_multiplier) + ord(text[i+m])) % mod
            # Make sure hash is positive
            if t < 0:
                t = t + mod
    return res

def rabin_karp_windows(text: str, ref: str, w=30, base=256, mod=10**9+7) -> List[Tuple[int, int]]:
    """
    Rabin-Karp multi-window/substring matching.
    Slides a window of length 'w' across both documents to find matching exact substrings.
    Returns a list of (start_in_text, start_in_ref).
    """
    if len(text) < w or len(ref) < w:
        return []

    # Calculate hash multiplier for the window size w
    h_multiplier = pow(base, w - 1, mod)

    # Hash table storing all window hashes of the reference document
    # hash -> list of start indices in ref
    ref_hashes = {}
    hr = 0
    # First window of reference
    for i in range(w):
        hr = (hr * base + ord(ref[i])) % mod
    ref_hashes.setdefault(hr, []).append(0)

    # Rolling hash for the rest of reference
    for i in range(w, len(ref)):
        hr = (base * (hr - ord(ref[i - w]) * h_multiplier) + ord(ref[i])) % mod
        if hr < 0:
            hr += mod
        ref_hashes.setdefault(hr, []).append(i - w + 1)

    # Compare with submission (text) windows
    ht = 0
    # First window of text
    for i in range(w):
        ht = (ht * base + ord(text[i])) % mod

    out = []
    
    # Check the first window
    if ht in ref_hashes:
        for ref_start in ref_hashes[ht]:
            if text[0:w] == ref[ref_start:ref_start+w]:
                out.append((0, ref_start))

    # Rolling hash for the rest of text
    for i in range(w, len(text)):
        ht = (base * (ht - ord(text[i - w]) * h_multiplier) + ord(text[i])) % mod
        if ht < 0:
            ht += mod
        
        if ht in ref_hashes:
            text_start = i - w + 1
            for ref_start in ref_hashes[ht]:
                # Confirm character match to avoid collisions
                if text[text_start:text_start+w] == ref[ref_start:ref_start+w]:
                    out.append((text_start, ref_start))
                    
    return out
