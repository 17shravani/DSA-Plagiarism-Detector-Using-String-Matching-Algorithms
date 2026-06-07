import math
from collections import Counter
from typing import Set, Dict

# Try importing sklearn, fallback to pure Python implementation if unavailable
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

def ngram_set(text: str, n: int = 4) -> Set[str]:
    """
    Creates a set of word n-grams from the normalized text.
    """
    toks = text.split()
    if len(toks) < n:
        return set()
    return {" ".join(toks[i : i + n]) for i in range(len(toks) - n + 1)}

def jaccard(a: Set[str], b: Set[str]) -> float:
    """
    Computes Jaccard Similarity between two sets.
    """
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

def tfidf_cosine(a: str, b: str) -> float:
    """
    Computes TF-IDF Cosine Similarity between two strings.
    Uses sklearn if available, else falls back to a pure-Python FNV/TF-IDF calculation.
    """
    if not a.strip() or not b.strip():
        return 0.0

    if SKLEARN_AVAILABLE:
        try:
            tf = TfidfVectorizer(min_df=1, ngram_range=(1, 2))
            M = tf.fit_transform([a, b])
            return float(cosine_similarity(M[0], M[1])[0, 0])
        except Exception:
            # Fall back if vectorization encounters unexpected issue
            pass

    # Pure Python TF-IDF Cosine Similarity
    toks_a = a.split()
    toks_b = b.split()
    
    tf_a = Counter(toks_a)
    tf_b = Counter(toks_b)
    
    vocab = set(tf_a.keys()) | set(tf_b.keys())
    
    # Document frequencies (in a corpus of these 2 docs)
    idf = {}
    for term in vocab:
        df = 0
        if term in tf_a:
            df += 1
        if term in tf_b:
            df += 1
        # Classic smooth IDF formula: ln( (1 + N) / (1 + df) ) + 1
        idf[term] = math.log((1.0 + 2.0) / (1.0 + df)) + 1.0

    # TF-IDF vectors
    vec_a = {term: tf_a[term] * idf[term] for term in tf_a}
    vec_b = {term: tf_b[term] * idf[term] for term in tf_b}

    dot_product = sum(vec_a[t] * vec_b.get(t, 0.0) for t in vec_a)
    norm_a = math.sqrt(sum(val ** 2 for val in vec_a.values()))
    norm_b = math.sqrt(sum(val ** 2 for val in vec_b.values()))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)
