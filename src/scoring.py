from typing import List, Tuple, Dict, Any

def merge_intervals(intervals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Merges overlapping or adjacent character intervals.
    Input intervals are tuples of (start, end) where end is exclusive.
    """
    if not intervals:
        return []
    
    # Sort by start index
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    
    for curr in intervals[1:]:
        prev_start, prev_end = merged[-1]
        curr_start, curr_end = curr
        # If overlap or adjacent
        if curr_start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, curr_end))
        else:
            merged.append(curr)
            
    return merged

def map_intervals_to_original(
    norm_intervals: List[Tuple[int, int]], 
    index_map: List[int], 
    original_text: str
) -> List[Dict[str, Any]]:
    """
    Maps normalized intervals back to original text character offsets using the index_map.
    Returns list of dicts with start, end, and matched text.
    """
    results = []
    for start, end in norm_intervals:
        if start >= len(index_map):
            continue
        
        # Translate normalized indexes to original string offsets
        orig_start = index_map[start]
        # For the exclusive end index, map to the character after the last normalized character in range
        last_idx = min(end - 1, len(index_map) - 1)
        orig_end = index_map[last_idx] + 1

        results.append({
            "start": orig_start,
            "end": orig_end,
            "text": original_text[orig_start:orig_end]
        })
    return results

def calculate_coverage(merged_intervals: List[Tuple[int, int]], text_len: int) -> float:
    """
    Calculates the proportion of the text length covered by matched intervals.
    """
    if text_len == 0:
        return 0.0
    covered_chars = sum(end - start for start, end in merged_intervals)
    return min(1.0, covered_chars / text_len)

def calculate_blended_score(
    exact_cov: float, 
    winnow_overlap: float, 
    tfidf: float, 
    jaccard: float
) -> int:
    """
    Computes a blended 0-100 score representing the similarity.
    Weights:
      - Exact Match Coverage: 40%
      - Fingerprint Winnowing Overlap: 30%
      - TF-IDF Cosine Similarity: 20%
      - 4-gram Jaccard Similarity: 10%
    """
    score = (0.40 * exact_cov) + (0.30 * winnow_overlap) + (0.20 * tfidf) + (0.10 * jaccard)
    return int(min(100, max(0, score * 100)))
