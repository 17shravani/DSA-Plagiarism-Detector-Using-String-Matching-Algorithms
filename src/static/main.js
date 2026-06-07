document.addEventListener("DOMContentLoaded", () => {
    // Application state
    let analysisResult = null;
    let currentTrace = [];
    let currentTraceStep = 0;
    let consultationInterval = null;

    // Helper to escape HTML and prevent XSS
    function escapeHtml(text) {
        if (!text) return "";
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // ================= 1. TAB ROUTING =================
    const navButtons = document.querySelectorAll(".nav-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            navButtons.forEach(b => b.classList.remove("active"));
            tabContents.forEach(t => t.classList.remove("active"));

            btn.classList.add("active");
            const target = btn.getAttribute("data-target");
            document.getElementById(target).classList.add("active");
        });
    });

    // ================= 2. LIVE CHARACTER COUNTERS =================
    const submissionArea = document.getElementById("submission-text");
    const wordCountSpan = document.getElementById("word-count");
    const charCountSpan = document.getElementById("char-count");

    function updateCounts() {
        const text = submissionArea.value;
        charCountSpan.textContent = text.length;
        const words = text.trim().split(/\s+/).filter(w => w.length > 0);
        wordCountSpan.textContent = words.length;
    }

    submissionArea.addEventListener("input", updateCounts);

    // Sample Loader
    document.getElementById("sample-btn").addEventListener("click", () => {
        submissionArea.value = 
            "Data structures and algorithms form the foundation of computer science. " +
            "The Knuth-Morris-Pratt (KMP) algorithm is a highly efficient linear-time " +
            "pattern matching procedure. It optimizes string search processes by pre-computing " +
            "a longest prefix suffix table. This prevents repeating character checks on sections " +
            "already known to match, resolving performance degradation associated with " +
            "naive quadratic time search methods. Let's make sure it checks everything.";
        updateCounts();
    });

    document.getElementById("clear-btn").addEventListener("click", () => {
        submissionArea.value = "";
        updateCounts();
    });

    // ================= 3. CORPUS MANAGER =================
    const indexedDocsBody = document.getElementById("indexed-docs-body");
    const addDocForm = document.getElementById("add-doc-form");

    async function loadCorpusList() {
        try {
            const res = await fetch("/corpus");
            const data = await res.json();
            indexedDocsBody.innerHTML = "";
            
            data.documents.forEach(docId => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td><strong>${escapeHtml(docId)}</strong></td>
                    <td><span class="key-badge">LSH-Bucket</span></td>
                    <td><span class="status-indicator"><span class="pulse-dot green"></span> Ready</span></td>
                `;
                indexedDocsBody.appendChild(tr);
            });
        } catch (err) {
            console.error("Error loading corpus list", err);
        }
    }

    addDocForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const docId = document.getElementById("doc-id-input").value.trim();
        const text = document.getElementById("doc-text-input").value;

        if (!docId || !text) return;

        try {
            const res = await fetch("/index", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ doc_id: docId, text: text })
            });
            const data = await res.json();
            if (data.status === "indexed") {
                alert(`Document '${docId}' indexed to LSH successfully!`);
                addDocForm.reset();
                loadCorpusList();
            }
        } catch (err) {
            alert("Error indexing document. Check console logs.");
            console.error(err);
        }
    });

    // ================= 4. PLAGIARISM ANALYSIS PIPELINE =================
    const analyzeBtn = document.getElementById("analyze-btn");
    const overallPercentage = document.getElementById("score-percentage");
    const progressCircle = document.getElementById("score-progress");
    const comparisonWorkspace = document.getElementById("comparison-workspace");
    const candidateSelect = document.getElementById("candidate-select");

    // Metrics progress UI elements
    const metricExactVal = document.getElementById("metric-exact-val");
    const metricExactBar = document.getElementById("metric-exact-bar");
    const metricWinnowVal = document.getElementById("metric-winnow-val");
    const metricWinnowBar = document.getElementById("metric-winnow-bar");
    const metricTfidfVal = document.getElementById("metric-tfidf-val");
    const metricTfidfBar = document.getElementById("metric-tfidf-bar");
    const metricJaccardVal = document.getElementById("metric-jaccard-val");
    const metricJaccardBar = document.getElementById("metric-jaccard-bar");

    analyzeBtn.addEventListener("click", async () => {
        const text = submissionArea.value.trim();
        if (!text) {
            alert("Please input document text before running analysis.");
            return;
        }

        analyzeBtn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Analyzing String Arrays...`;
        analyzeBtn.disabled = true;

        try {
            const res = await fetch("/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: text, top_k: 5 })
            });
            analysisResult = await res.json();
            
            updateOverviewDashboard(analysisResult);
            populateCandidateSelect(analysisResult.candidates);
            
            if (analysisResult.candidates.length > 0) {
                comparisonWorkspace.classList.remove("hidden");
                // Render details of top candidate match
                renderMatchComparison(analysisResult.candidates[0], text);
                document.getElementById("trigger-consultation").disabled = false;
            } else {
                comparisonWorkspace.classList.add("hidden");
                document.getElementById("trigger-consultation").disabled = true;
            }
        } catch (err) {
            alert("Analysis failed. Refer to server logs.");
            console.error(err);
        } finally {
            analyzeBtn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Compare Submission`;
            analyzeBtn.disabled = false;
        }
    });

    function updateOverviewDashboard(result) {
        const score = result.overall;
        overallPercentage.textContent = `${score}%`;

        // Circumference perimeter calculation = 440
        const perimeter = 440;
        const offset = perimeter - (score / 100) * perimeter;
        progressCircle.style.strokeDashoffset = offset;

        // Visual alert status
        if (score < 15) {
            progressCircle.style.stroke = "var(--green)";
            overallPercentage.style.color = "var(--green)";
        } else if (score < 50) {
            progressCircle.style.stroke = "var(--yellow)";
            overallPercentage.style.color = "var(--yellow)";
        } else {
            progressCircle.style.stroke = "var(--red)";
            overallPercentage.style.color = "var(--red)";
        }
    }

    function populateCandidateSelect(candidates) {
        candidateSelect.innerHTML = "";
        if (candidates.length === 0) {
            const opt = document.createElement("option");
            opt.textContent = "No Match Found";
            candidateSelect.appendChild(opt);
            return;
        }

        candidates.forEach(cand => {
            const opt = document.createElement("option");
            opt.value = cand.doc_id;
            opt.textContent = `${cand.doc_id} (Match: ${cand.score}%)`;
            candidateSelect.appendChild(opt);
        });
    }

    candidateSelect.addEventListener("change", () => {
        const docId = candidateSelect.value;
        const selectedCand = analysisResult.candidates.find(c => c.doc_id === docId);
        if (selectedCand) {
            renderMatchComparison(selectedCand, submissionArea.value);
        }
    });

    // ================= 5. COMPARISON & HIGHLIGHT RENDERER =================
    function buildHighlightedText(originalText, highlights) {
        if (!highlights || highlights.length === 0) return escapeHtml(originalText);

        // Sort highlights by starting offset ascending
        let sorted = [...highlights].sort((a, b) => a.start - b.start);

        let result = "";
        let lastIdx = 0;

        sorted.forEach(hl => {
            if (hl.start < lastIdx) {
                // Skip nested ranges to prevent malformed nested HTML tags
                return;
            }
            result += escapeHtml(originalText.slice(lastIdx, hl.start));
            result += `<span class="hl-exact" title="Matched exact string subsequence">${escapeHtml(originalText.slice(hl.start, hl.end))}</span>`;
            lastIdx = hl.end;
        });

        result += escapeHtml(originalText.slice(lastIdx));
        return result;
    }

    async function renderMatchComparison(candidate, originalSubmission) {
        document.getElementById("matched-source-id").textContent = candidate.doc_id;

        // Render matching candidate scores to slider board
        const m = candidate.metrics;
        metricExactVal.textContent = `${Math.round(m.exact_coverage * 100)}%`;
        metricExactBar.style.width = `${m.exact_coverage * 100}%`;

        metricWinnowVal.textContent = `${Math.round(m.winnow_overlap * 100)}%`;
        metricWinnowBar.style.width = `${m.winnow_overlap * 100}%`;

        metricTfidfVal.textContent = `${Math.round(m.tfidf * 100)}%`;
        metricTfidfBar.style.width = `${m.tfidf * 100}%`;

        metricJaccardVal.textContent = `${Math.round(m.jaccard * 100)}%`;
        metricJaccardBar.style.width = `${m.jaccard * 100}%`;

        // Render submission side matches
        const subPane = document.getElementById("submission-highlight-pane");
        subPane.innerHTML = buildHighlightedText(originalSubmission, candidate.submission_highlights);

        // Fetch reference source body from corpus
        try {
            const res = await fetch(`/document/${encodeURIComponent(candidate.doc_id)}`);
            const docData = await res.json();
            const refPane = document.getElementById("reference-highlight-pane");
            refPane.innerHTML = buildHighlightedText(docData.text, candidate.reference_highlights);
        } catch (err) {
            console.error("Error retrieving reference doc details for rendering comparison", err);
        }
    }

    // ================= 6. KMP LPS SIMULATOR =================
    const startSimBtn = document.getElementById("start-sim-btn");
    const prevSimBtn = document.getElementById("prev-sim-btn");
    const nextSimBtn = document.getElementById("next-sim-btn");
    const simPatternInput = document.getElementById("sim-pattern");

    const simCharsRow = document.getElementById("sim-chars-row");
    const simLpsRow = document.getElementById("sim-lps-row");
    
    const simStepIdx = document.getElementById("sim-step-idx");
    const simPointerI = document.getElementById("sim-pointer-i");
    const simPointerLen = document.getElementById("sim-pointer-len");
    const simComparison = document.getElementById("sim-comparison");
    const simActionDesc = document.getElementById("sim-action-desc");

    startSimBtn.addEventListener("click", async () => {
        const pattern = simPatternInput.value.trim();
        if (!pattern) return;

        try {
            const res = await fetch("/simulate-algorithm", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ pattern: pattern })
            });
            const data = await res.json();
            currentTrace = data.trace;
            currentTraceStep = 0;

            prevSimBtn.disabled = true;
            nextSimBtn.disabled = false;

            renderSimulatorStep();
        } catch (err) {
            console.error(err);
        }
    });

    function renderSimulatorStep() {
        if (!currentTrace || currentTrace.length === 0) return;
        const stepData = currentTrace[currentTraceStep];
        const pattern = simPatternInput.value.trim();

        // Update statistics
        simStepIdx.textContent = `${currentTraceStep + 1} / ${currentTrace.length}`;
        simPointerI.textContent = stepData.i;
        simPointerLen.textContent = stepData.length;
        simComparison.textContent = stepData.comparison;
        simActionDesc.textContent = stepData.action;

        // Render Character Blocks
        simCharsRow.innerHTML = "";
        for (let idx = 0; idx < pattern.length; idx++) {
            const box = document.createElement("div");
            box.className = "sim-box sim-box-char";
            box.textContent = pattern[idx];
            
            // Add label index hint
            const label = document.createElement("span");
            label.className = "label-hint";
            label.textContent = idx;
            box.appendChild(label);

            // Highlighting based on execution indices
            if (idx === stepData.i) {
                box.classList.add("highlight-i");
            }
            if (idx === stepData.length && currentTraceStep > 0 && idx < stepData.i) {
                box.classList.add("highlight-len");
            }
            if (stepData.matched && (idx === stepData.i || idx === stepData.length - 1)) {
                box.classList.add("highlight-match");
            }

            simCharsRow.appendChild(box);
        }

        // Render LPS Array Boxes
        simLpsRow.innerHTML = "";
        stepData.lps.forEach((val, idx) => {
            const box = document.createElement("div");
            box.className = "sim-box sim-box-lps";
            box.textContent = val;
            
            const label = document.createElement("span");
            label.className = "label-hint";
            label.textContent = `LPS[${idx}]`;
            box.appendChild(label);

            if (idx === stepData.i && currentTraceStep > 0) {
                box.classList.add("highlight-i");
            }

            simLpsRow.appendChild(box);
        });

        // Set nav controls
        prevSimBtn.disabled = currentTraceStep === 0;
        nextSimBtn.disabled = currentTraceStep === currentTrace.length - 1;
    }

    prevSimBtn.addEventListener("click", () => {
        if (currentTraceStep > 0) {
            currentTraceStep--;
            renderSimulatorStep();
        }
    });

    nextSimBtn.addEventListener("click", () => {
        if (currentTraceStep < currentTrace.length - 1) {
            currentTraceStep++;
            renderSimulatorStep();
        }
    });

    // ================= 7. MULTI-AGENT CONSULTATION LOG SIMULATION =================
    const triggerBtn = document.getElementById("trigger-consultation");
    const chatLog = document.getElementById("agents-chat-log");

    triggerBtn.addEventListener("click", () => {
        if (!analysisResult || analysisResult.candidates.length === 0) return;
        const candidate = analysisResult.candidates.find(c => c.doc_id === candidateSelect.value);
        if (!candidate) return;

        triggerBtn.disabled = true;
        chatLog.innerHTML = "";

        // Simulated Agent dialogue payload based on match score metrics
        const dialogue = [
            {
                agent: "Risk Detection Agent",
                class: "risk",
                icon: "fa-user-secret",
                msg: `Initiating manuscript scan on submission against source: '${candidate.doc_id}'. ` +
                     `Exact match overlap coverage computed at ${Math.round(candidate.metrics.exact_coverage * 100)}%. ` +
                     `Structural 4-gram Jaccard index stands at ${Math.round(candidate.metrics.jaccard * 100)}%. ` +
                     `Checking document structure: No zero-width characters or Cyrillic homoglyph replacements detected. This represents clean, verbatim text copying.`
            },
            {
                agent: "Optimization Agent",
                class: "optimization",
                icon: "fa-gears",
                msg: `Analyzing engine parameters. Winnowing was configured at shingle-size $k=5$, guarantee-threshold $t=9$. ` +
                     `The fingerprint match overlap of ${Math.round(candidate.metrics.winnow_overlap * 100)}% confirms high structural similarity. ` +
                     `Retrieval was completed under 4ms using LSH. Standard $O(N)$ pair-wise checks bypassed. Recommendation: Maintain row parameter $r=5$ for robust candidate bucketing.`
            },
            {
                agent: "Decision Agent",
                class: "decision",
                icon: "fa-gavel",
                msg: `Blended Plagiarism likelihood is ${candidate.score}%. Given the verbatim overlap of core KMP explanations, ` +
                     `this represents a severe infraction (Similarity Threshold exceeded). ` +
                     `Action Recommendation: Reject manuscript submission or request complete paraphrase rewriting, since the matching sequences are identical to '${candidate.doc_id}'.`
            }
        ];

        let index = 0;
        
        function postNextMessage() {
            if (index >= dialogue.length) {
                triggerBtn.disabled = false;
                return;
            }

            const item = dialogue[index];
            const msgRow = document.createElement("div");
            msgRow.className = `chat-msg agent-msg-${item.class}`;
            msgRow.innerHTML = `
                <div class="agent-avatar avatar-${item.class}"><i class="fa-solid ${item.icon}"></i></div>
                <div class="chat-bubble">
                    <div class="chat-bubble-header bubble-${item.class}">
                        <i class="fa-solid ${item.icon}"></i> ${item.agent}
                    </div>
                    <div class="chat-bubble-text">${escapeHtml(item.msg)}</div>
                </div>
            `;
            chatLog.appendChild(msgRow);
            chatLog.scrollTop = chatLog.scrollHeight;

            index++;
            setTimeout(postNextMessage, 1500);
        }

        postNextMessage();
    });

    // Populate initial views
    loadCorpusList();
    
    // Auto-trigger simulator initialization
    simPatternInput.dispatchEvent(new Event("input"));
    startSimBtn.click();
});
