import uvicorn
import sys
import os

if __name__ == "__main__":
    # Add src to python path to resolve imports cleanly
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
    
    print("=" * 60)
    print("         OBSIDIAN PLAGIARISM ENGINE RUNNER")
    print("=" * 60)
    print("Host: http://127.0.0.1:8000")
    print("Use the web interface to index documents, test similarity,")
    print("and step through the KMP string-matching automaton simulator.")
    print("=" * 60)
    
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
