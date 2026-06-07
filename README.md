# Obsidian Plagiarism Engine - String Matching & DSA Analytics

An enterprise-grade, high-performance plagiarism detection pipeline combining classic string-matching algorithms, locality-sensitive hashing, and vector space similarity models. Designed with a custom glassmorphism dark-themed dashboard, real-time automaton simulators, and an interactive multi-agent integrity review panel.

---

## 📖 Project Overview & Technical Architecture

Plagiarism detectors prevent intellectual property theft, guarantee academic honesty, and verify freelance content originality. Modern commercial search tools must run sub-linear candidate lookups across billions of pages. To accomplish this, this system utilizes a multi-tiered pipeline:

1. **Text Normalization**: Unicode NFKC translation, case folding, and non-alphanumeric strip mapping.
2. **Global Candidate Search (MinHash + LSH)**: Maps documents into buckets to isolate candidates in $O(1)$ time, bypassing $O(N)$ pair comparisons.
3. **Fuzzy Overlap Fingerprinting (Winnowing)**: Shingles words ($k=5$) and selects windows of min-hashes to catch structural reordering.
4. **Exact Substring Matching (KMP & Rabin-Karp)**: Multi-window rolling hashes ($w=35$) locate verbatim copying.
5. **Statistical / Semantic Sim (TF-IDF & Jaccard)**: Calculates vocabulary similarities to flag heavily paraphrased passages.

```
Manuscript Submission
         │
         ▼
 ┌───────────────┐
 │ Normalization │ ───► Position Map (Clean -> Raw char offsets)
 └───────────────┘
         │
         ▼
 ┌───────────────┐
 │ MinHash + LSH │ ───► Candidate Isolation in O(1)
 └───────────────┘
         │
         ▼
 ┌────────────────────────────────────────────────────────┐
 │   Multi-Algorithm Exact & Structural Comparison        │
 ├───────────────────┬───────────────────┬────────────────┤
 │    Rabin-Karp     │     Winnowing     │  TF-IDF/Jacc   │
 │   (Substrings)    │  (Fingerprints)   │  (Vocabulary)  │
 └───────────────────┴───────────────────┴────────────────┘
         │
         ▼
 ┌───────────────┐
 │ Blended Score │ ───► Weighted Matrix Percentage (0 - 100%)
 └───────────────┘
         │
         ▼
 ┌────────────────────────────────────────────────────────┐
 │                   Evidence Reporting                   │
 ├────────────────────────────────────────────────────────┤
 │  • Side-by-Side Highlighted Comparison Panel            │
 │  • Real-Time Automaton Execution Trace Simulator       │
 │  • Multi-Agent Academic Integrity Consultation Dialog   │
 └────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack & Algorithms

* **Language**: Python 3.8+ (Modular, zero dependencies fallback architecture)
* **Framework**: FastAPI (Web Engine), Uvicorn (ASGI Application Server)
* **Design Engine**: Vanilla HTML5, CSS3 Custom Theme (Slate-Obsidian), and pure Javascript ES6
* **Key DSA Concepts**:
  * **Knuth-Morris-Pratt (KMP)**: Linear $O(N+M)$ search pattern locating. LPS pre-computation table.
  * **Rabin-Karp Rolling Hash**: Multi-window substring matching via polynomial modular arithmetic.
  * **Winnowing (Fingerprinting)**: Position-guaranteed local hash selection.
  * **Locality-Sensitive Hashing (LSH)**: Approximate Nearest Neighbor (ANN) search buckets using Jaccard approximations.

---

## 📂 Folder Structure

```
Plagiarism-Detector-String-Matching/
│
├── documents/          # Offline testing corpus & target files
├── src/                # Backend API service and algorithmic library
│   ├── app.py          # FastAPI application server paths
│   ├── exact.py        # KMP & Rabin-Karp string matching algorithms
│   ├── lsh.py          # MinHash and LSH indexing classes
│   ├── preprocess.py   # Text normalizer and character index mapper
│   ├── scoring.py      # Highlight coordinate merge & score blending
│   ├── similarity.py   # Jaccard and TF-IDF Cosine similarity metrics
│   ├── winnow.py       # K-shingler and winnowing fingerprinter
│   └── static/         # Frontend web application assets
│       ├── index.html  # Dashboard workspace page
│       ├── style.css   # Dark-theme premium responsive layout
│       └── main.js     # User interaction and simulation controller
│
├── outputs/            # Saved analysis report logs
├── images/             # Screenshot assets for showcase portfolio
├── reports/            # Exported plagiarised validation sheets
├── docs/               # Advanced algorithm design notes
├── requirements.txt    # Standard system requirements list
├── .gitignore          # Cache and workspace exclude rules
└── main.py             # Main entry point runner script
```

---

## 🚀 Installation & How to Run

### 1. Prerequisites & Environment Setup
Clone the repository and install the standard dependencies:
```bash
# Clone the project repository
git clone https://github.com/yourusername/Plagiarism-Detector-String-Matching.git
cd Plagiarism-Detector-String-Matching

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Booting the Application
Execute the primary runner to start the server:
```bash
python main.py
```
Open your web browser and navigate to: **`http://127.0.0.1:8000`**

---

## 🧠 Interview Preparation Q&A

### Q1: Explain your plagiarism detection project.
**Answer**: I built a multi-tiered plagiarism detection engine using Python and FastAPI that compares a submitted manuscript against an indexed corpus. It uses Locality Sensitive Hashing (LSH) with MinHash signatures to query candidate matches in sub-linear time, winnowing to fingerprint local k-shingles, Rabin-Karp rolling hashes to isolate exact substring spans, and KMP pattern matching for automaton validation. Results are served on a glassmorphism frontend dashboard with side-by-side highlighting, a step-by-step KMP LPS visualizer, and a simulated multi-agent integrity review panel.

### Q2: What is the benefit of using an index map in the pre-processing phase?
**Answer**: Text normalization strips spaces, lowercase shifts, and removes punctuation. If a match is found in the cleaned text, the index offsets will not align with the student's original raw document. By returning a character index map that matches every normalized character index back to its corresponding index in the raw text, we can precisely highlight plagiarized spans in the raw view.

### Q3: Why combine KMP, Rabin-Karp, and Winnowing instead of just using Cosine Similarity?
**Answer**: Cosine similarity evaluates bag-of-words or vector representations, which can easily miss structural copying if words are rearranged. Rabin-Karp and KMP identify verbatim substring copies. Winnowing handles minor changes (like synonyms or small word additions) by mapping local fingerprints. Combining them covers the entire spectrum of copy-paste, near-duplicate, and structural plagiarism.
