import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from preprocess import normalize
from exact import compute_lps_trace, rabin_karp_windows
from winnow import winnow_fingerprints, build_fingerprint_index
from lsh import MinHasher, LSH
from similarity import ngram_set, jaccard, tfidf_cosine
from scoring import merge_intervals, map_intervals_to_original, calculate_coverage, calculate_blended_score

app = FastAPI(title="Obsidian Plagiarism Engine", version="2.0.0")

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory database
CORPUS: Dict[str, str] = {}           # doc_id -> original_text
NORM_CORPUS: Dict[str, str] = {}      # doc_id -> normalized_text
INDEX_MAPS: Dict[str, List[int]] = {} # doc_id -> character index map

# MinHash & LSH setup
SIGNATURE_SIZE = 100
BANDS = 20
ROWS = 5
minhasher = MinHasher(n=SIGNATURE_SIZE)
lsh_index = LSH(bands=BANDS, rows=ROWS)

# Winnowing setup
K_SHINGLE = 5
T_GUARANTEE = 9

class DocRequest(BaseModel):
    doc_id: str
    text: str

class AnalyzeRequest(BaseModel):
    text: str
    top_k: Optional[int] = 5

class SimulateRequest(BaseModel):
    pattern: str

@app.post("/index")
def index_document(req: DocRequest):
    """
    Cleans, normalizes, and indexes a reference document into the corpus.
    Updates MinHash + LSH and Winnowing fingerprinter.
    """
    if not req.doc_id or not req.text.strip():
        raise HTTPException(status_code=400, detail="doc_id and non-empty text are required.")

    # Save to corpus
    CORPUS[req.doc_id] = req.text
    norm_txt, idx_map = normalize(req.text)
    NORM_CORPUS[req.doc_id] = norm_txt
    INDEX_MAPS[req.doc_id] = idx_map

    # Update MinHash + LSH index
    tokens = set(norm_txt.split())
    sig = minhasher.signature(tokens)
    lsh_index.add(req.doc_id, sig)

    return {"status": "indexed", "doc_id": req.doc_id, "normalized_length": len(norm_txt)}

@app.get("/corpus")
def list_corpus():
    """
    Lists all document IDs currently in the database.
    """
    return {"documents": list(CORPUS.keys())}

@app.get("/document/{doc_id}")
def get_document(doc_id: str):
    """
    Retrieves original raw document text by ID.
    """
    if doc_id not in CORPUS:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"doc_id": doc_id, "text": CORPUS[doc_id]}

@app.post("/analyze")
def analyze_submission(req: AnalyzeRequest):
    """
    Analyses a raw text submission against the corpus:
    1. Normalizes the submission.
    2. Runs LSH to query candidates.
    3. Runs windowed Rabin-Karp & Winnowing to check overlaps.
    4. Computes semantic TF-IDF Cosine & Jaccard overlaps.
    5. Returns matches, highlights, and blended plagiarism scores.
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Submission text cannot be empty.")

    sub_norm, sub_idx_map = normalize(req.text)
    sub_tokens = set(sub_norm.split())

    # Get MinHash signature and query LSH for candidates
    sig = minhasher.signature(sub_tokens)
    candidates = lsh_index.query(sig)

    # Fallback to all documents in the corpus if LSH has no overlap (dense inspection)
    if not candidates:
        candidates = list(CORPUS.keys())

    results = []

    # Window size for Rabin-Karp substring matches
    w_size = 35 

    # Generate winnowing fingerprints for the query submission
    sub_fps = winnow_fingerprints(sub_norm, k=K_SHINGLE, t=T_GUARANTEE)
    sub_fp_set = {h for _, h in sub_fps}

    for did in candidates:
        ref_raw = CORPUS[did]
        ref_norm = NORM_CORPUS[did]
        ref_idx_map = INDEX_MAPS[did]

        # 1. Exact Rabin-Karp Window Matching
        rk_matches = rabin_karp_windows(sub_norm, ref_norm, w=w_size)
        
        # Merge overlaps in the submission (query text)
        sub_norm_intervals = []
        ref_norm_intervals = []
        for s_idx, r_idx in rk_matches:
            sub_norm_intervals.append((s_idx, s_idx + w_size))
            ref_norm_intervals.append((r_idx, r_idx + w_size))

        merged_sub_intervals = merge_intervals(sub_norm_intervals)
        merged_ref_intervals = merge_intervals(ref_norm_intervals)

        # Highlight coordinates in original texts
        submission_highlights = map_intervals_to_original(merged_sub_intervals, sub_idx_map, req.text)
        reference_highlights = map_intervals_to_original(merged_ref_intervals, ref_idx_map, ref_raw)

        # Exact Match Coverage
        exact_coverage = calculate_coverage(merged_sub_intervals, len(sub_norm))

        # 2. Winnowing fingerprint overlap ratio (Jaccard of winnowed hashes)
        ref_fps = winnow_fingerprints(ref_norm, k=K_SHINGLE, t=T_GUARANTEE)
        ref_fp_set = {h for _, h in ref_fps}
        
        intersection_fp = sub_fp_set.intersection(ref_fp_set)
        union_fp = sub_fp_set.union(ref_fp_set)
        winnow_overlap = len(intersection_fp) / max(1, len(union_fp))

        # 3. N-gram Jaccard Overlap (structural)
        sub_ngrams = ngram_set(sub_norm, n=4)
        ref_ngrams = ngram_set(ref_norm, n=4)
        jaccard_score = jaccard(sub_ngrams, ref_ngrams)

        # 4. TF-IDF Cosine Similarity
        cosine_sim = tfidf_cosine(sub_norm, ref_norm)

        # 5. Blended Score
        blended = calculate_blended_score(exact_coverage, winnow_overlap, cosine_sim, jaccard_score)

        results.append({
            "doc_id": did,
            "score": blended,
            "metrics": {
                "exact_coverage": float(round(exact_coverage, 3)),
                "winnow_overlap": float(round(winnow_overlap, 3)),
                "tfidf": float(round(cosine_sim, 3)),
                "jaccard": float(round(jaccard_score, 3))
            },
            "submission_highlights": submission_highlights,
            "reference_highlights": reference_highlights,
            "snippet": ref_raw[:200] + "..." if len(ref_raw) > 200 else ref_raw
        })

    # Sort candidates by similarity score in descending order
    results.sort(key=lambda x: -x["score"])

    # Slice to top_k
    top_candidates = results[:req.top_k]
    
    # Calculate overall plagiarism percentage based on the top match
    overall_score = top_candidates[0]["score"] if top_candidates else 0

    return {
        "overall": overall_score,
        "candidates": top_candidates
    }

@app.post("/simulate-algorithm")
def simulate_kmp(req: SimulateRequest):
    """
    Simulates KMP LPS array construction on the pattern provided.
    """
    if not req.pattern.strip():
        raise HTTPException(status_code=400, detail="Pattern cannot be empty.")
    trace = compute_lps_trace(req.pattern)
    return {"trace": trace}

# Static file serving paths
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    """Serves the dashboard home page."""
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse("Frontend static files not found. Check installation guide.")

@app.get("/style.css")
def serve_css():
    return FileResponse(os.path.join(STATIC_DIR, "style.css"), media_type="text/css")

@app.get("/main.js")
def serve_js():
    return FileResponse(os.path.join(STATIC_DIR, "main.js"), media_type="application/javascript")

def populate_sample_data():
    """
    Injects realistic test documents for university and edtech workloads.
    """
    docs = {
        "dsa_thesis_original": (
            "Data structures and algorithms form the foundation of computer science. "
            "The Knuth-Morris-Pratt (KMP) algorithm is a highly efficient linear-time "
            "pattern matching procedure. It optimizes string search processes by pre-computing "
            "a longest prefix suffix table. This prevents repeating character checks on sections "
            "already known to match, resolving performance degradation associated with "
            "naive quadratic time search methods."
        ),
        "dsa_thesis_plagiarized": (
            "An academic paper states that data structures and algorithms form the foundation "
            "of computer science. The Knuth-Morris-Pratt (KMP) algorithm is a highly efficient "
            "linear-time pattern matching procedure. It optimizes string search processes by "
            "pre-computing a longest prefix suffix table. This prevents repeating character checks, "
            "avoiding the performance issues of naive quadratic search."
        ),
        "cybersecurity_notes": (
            "Network security protocols authenticate connections to protect critical data. "
            "By deploying symmetric and asymmetric encryption systems alongside firewalls, "
            "enterprises defend their infrastructure against unauthorized database operations."
        )
    }
    for did, text in docs.items():
        # Clean & normalise
        norm_txt, idx_map = normalize(text)
        CORPUS[did] = text
        NORM_CORPUS[did] = norm_txt
        INDEX_MAPS[did] = idx_map
        # Index in LSH
        tokens = set(norm_txt.split())
        sig = minhasher.signature(tokens)
        lsh_index.add(did, sig)

# Auto populate sample data at startup
populate_sample_data()
