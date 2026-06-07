import random
from typing import List, Set, Dict, Any
import numpy as np

# Try importing mmh3, fallback to a robust pure-Python hash if not available.
try:
    import mmh3
except ImportError:
    class PurePythonMmh3:
        @staticmethod
        def hash(key: str, seed: int, signed: bool = False) -> int:
            # High-quality 32-bit FNV-1a mix hash
            h = (2166136261 ^ seed) & 0xFFFFFFFF
            for char in key:
                h = h ^ ord(char)
                h = (h * 16777619) & 0xFFFFFFFF
            return h
    mmh3 = PurePythonMmh3

class MinHasher:
    def __init__(self, n: int = 100, seed: int = 42):
        self.n = n
        # Deterministically generate seeds for hash functions
        random.seed(seed)
        self.seeds = [random.randint(1, (1 << 31) - 1) for _ in range(n)]

    def signature(self, tokens: Set[str]) -> np.ndarray:
        """
        Computes the MinHash signature of a set of tokens.
        If tokens is empty, returns a signature of maximum values.
        """
        sig = []
        for s in self.seeds:
            if not tokens:
                m = (1 << 32) - 1
            else:
                m = min(mmh3.hash(t, s, signed=False) for t in tokens)
            sig.append(m)
        return np.array(sig, dtype=np.uint32)

class LSH:
    def __init__(self, bands: int = 20, rows: int = 5):
        """
        Locality Sensitive Hashing (LSH) for quick candidate retrieval.
        n = bands * rows (signature size must match bands * rows).
        """
        self.bands = bands
        self.rows = rows
        # Index tables: list of dicts, one for each band.
        # Each dict maps band_hash -> list of doc_ids
        self.tables: List[Dict[bytes, List[str]]] = [{} for _ in range(bands)]

    def add(self, doc_id: str, sig: np.ndarray):
        """
        Splits signature into bands and indexes the document.
        """
        for b in range(self.bands):
            band_sig = sig[b * self.rows : (b + 1) * self.rows].tobytes()
            self.tables[b].setdefault(band_sig, []).append(doc_id)

    def query(self, sig: np.ndarray) -> List[str]:
        """
        Queries LSH tables for documents that share at least one band signature.
        """
        candidates = set()
        for b in range(self.bands):
            band_sig = sig[b * self.rows : (b + 1) * self.rows].tobytes()
            matches = self.tables[b].get(band_sig, [])
            candidates.update(matches)
        return list(candidates)

    def clear(self):
        """
        Resets the index tables.
        """
        self.tables = [{} for _ in range(self.bands)]
