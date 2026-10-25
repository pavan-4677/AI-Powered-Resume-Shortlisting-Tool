/**
 * AI-Powered Resume Shortlisting Tool - Recruiter Client Application
 * Pure user-driven workflow: user enters Job Role & JD, uploads resumes, and scores.
 */

document.addEventListener("DOMContentLoaded", () => {
    // Application State
    const state = {
        activeJob: null,
        rankings: [],
        selectedFiles: [],
        selectedCandidate: null
    };

    // DOM Elements Cache
    const elements = {
        // Job Form Elements
        jobForm: document.getElementById("jobForm"),
        inputJobTitle: document.getElementById("inputJobTitle"),
        inputJobDesc: document.getElementById("inputJobDesc"),
        inputRequiredSkills: document.getElementById("inputRequiredSkills"),
        inputMinExp: document.getElementById("inputMinExp"),
        reanalyzeContainer: document.getElementById("reanalyzeContainer"),
        btnReanalyze: document.getElementById("btnReanalyze"),
        jobStatusBadge: document.getElementById("jobStatusBadge"),
        validationAlert: document.getElementById("validationAlert"),
        validationAlertText: document.getElementById("validationAlertText"),

        // Stats Counters
        statTotalResumes: document.getElementById("statTotalResumes"),
        statPendingReview: document.getElementById("statPendingReview"),
        statShortlisted: document.getElementById("statShortlisted"),
        statAvgScore: document.getElementById("statAvgScore"),

        // Upload Elements
        dropZone: document.getElementById("dropZone"),
        resumeFileInput: document.getElementById("resumeFileInput"),
        btnBrowseFiles: document.getElementById("btnBrowseFiles"),
        selectedFilesContainer: document.getElementById("selectedFilesContainer"),
        selectedFilesList: document.getElementById("selectedFilesList"),
        selectedFileCount: document.getElementById("selectedFileCount"),
        btnClearFiles: document.getElementById("btnClearFiles"),
        uploadProgressContainer: document.getElementById("uploadProgressContainer"),
        uploadProgressBar: document.getElementById("uploadProgressBar"),
        uploadProgressLabel: document.getElementById("uploadProgressLabel"),
        uploadProgressText: document.getElementById("uploadProgressText"),
        btnStartAnalyze: document.getElementById("btnStartAnalyze"),
        btnStartAnalyzeText: document.getElementById("btnStartAnalyzeText"),

        // Results & Table
        candidatesTableBody: document.getElementById("candidatesTableBody"),
        rankingCountBadge: document.getElementById("rankingCountBadge"),
        filterSearch: document.getElementById("filterSearch"),
        filterStatus: document.getElementById("filterStatus"),
        filterMinScore: document.getElementById("filterMinScore"),
        minScoreLabel: document.getElementById("minScoreLabel"),
        btnExportCSV: document.getElementById("btnExportCSV"),
        btnRefreshRankings: document.getElementById("btnRefreshRankings"),
        btnClearAll: document.getElementById("btnClearAll"),

        // Candidate Detail Modal
        candidateModal: new bootstrap.Modal(document.getElementById("candidateModal")),
        modalCandidateAvatar: document.getElementById("modalCandidateAvatar"),
        modalCandidateName: document.getElementById("modalCandidateName"),
        modalCandidateContact: document.getElementById("modalCandidateContact"),
        modalOverallScore: document.getElementById("modalOverallScore"),
        modalMatchBadge: document.getElementById("modalMatchBadge"),
        modalSkillScore: document.getElementById("modalSkillScore"),
        modalSkillCount: document.getElementById("modalSkillCount"),
        modalSemanticScore: document.getElementById("modalSemanticScore"),
        modalCosineRaw: document.getElementById("modalCosineRaw"),
        modalExpScore: document.getElementById("modalExpScore"),
        modalExpYears: document.getElementById("modalExpYears"),
        modalMatchReasonsList: document.getElementById("modalMatchReasonsList"),
        modalMatchedSkillsPills: document.getElementById("modalMatchedSkillsPills"),
        modalMissingSkillsPills: document.getElementById("modalMissingSkillsPills"),
        modalEducationList: document.getElementById("modalEducationList"),
        modalProjectsList: document.getElementById("modalProjectsList"),
        modalAllCandidateSkills: document.getElementById("modalAllCandidateSkills"),
        modalRawText: document.getElementById("modalRawText"),
        modalStatusSelect: document.getElementById("modalStatusSelect"),
        modalRecruiterNotes: document.getElementById("modalRecruiterNotes"),
        modalReviewedAt: document.getElementById("modalReviewedAt"),
        modalDownloadResumeBtn: document.getElementById("modalDownloadResumeBtn"),
        btnSaveRecruiterDecision: document.getElementById("btnSaveRecruiterDecision"),

        // Toast
        liveToast: document.getElementById("liveToast"),
        toastBody: document.getElementById("toastBody")
    };

    const toast = new bootstrap.Toast(elements.liveToast);

    // ==========================================
    // NOTIFICATION & VALIDATION HELPERS
    // ==========================================
    function showToast(message, type = "success") {
        elements.liveToast.className = `toast align-items-center text-white border-0 shadow bg-${type === 'error' ? 'danger' : type}`;
        elements.toastBody.textContent = message;
        toast.show();
    }

    function showValidationAlert(message) {
        elements.validationAlertText.textContent = message;
        elements.validationAlert.classList.remove("d-none");
        elements.validationAlert.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    function hideValidationAlert() {
        elements.validationAlert.classList.add("d-none");
        elements.validationAlertText.textContent = "";
    }

    // ==========================================
    // INITIALIZATION & STATE LOADING
    // ==========================================
    async function initApp() {
        setupEventListeners();
        await loadCurrentState();
    }

    async function loadCurrentState() {
        try {
            const res = await fetch("/api/rankings");
            const data = await res.json();

            if (data.success && data.has_job && data.job) {
                state.activeJob = data.job;
                state.rankings = data.rankings || [];

                // Populate Form with existing active job
                elements.inputJobTitle.value = data.job.title || "";
                elements.inputJobDesc.value = data.job.description || "";
                elements.inputRequiredSkills.value = (data.job.required_skills || []).join(", ");
                elements.inputMinExp.value = data.job.min_experience !== null ? data.job.min_experience : "";

                elements.jobStatusBadge.textContent = "Active Requirements";
                elements.reanalyzeContainer.classList.remove("d-none");

                updateStatsDisplay(data.stats);
                renderRankingsTable();
                elements.btnExportCSV.disabled = state.rankings.length === 0;
            } else {
                renderCleanEmptyState();
            }
        } catch (err) {
            console.error("Error loading application state:", err);
            renderCleanEmptyState();
        }
    }

    function renderCleanEmptyState() {
        state.activeJob = null;
        state.rankings = [];
        state.selectedFiles = [];

        elements.inputJobTitle.value = "";
        elements.inputJobDesc.value = "";
        elements.inputRequiredSkills.value = "";
        elements.inputMinExp.value = "";
        elements.reanalyzeContainer.classList.add("d-none");
        elements.jobStatusBadge.textContent = "New Analysis";

        elements.statTotalResumes.textContent = "0";
        elements.statPendingReview.textContent = "0";
        elements.statShortlisted.textContent = "0";
        elements.statAvgScore.textContent = "0%";

        elements.rankingCountBadge.textContent = "0";
        elements.btnExportCSV.disabled = true;

        elements.candidatesTableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-5 text-muted">
                    <i class="bi bi-file-earmark-text fs-1 d-block mb-2 text-slate-300"></i>
                    <h6 class="fw-semibold text-slate-700">No resumes uploaded yet.</h6>
                    <p class="small text-muted mb-0">Enter your job requirements on the left, upload candidate resumes, and click "Analyze Resumes".</p>
                </td>
            </tr>
        `;
    }

    function updateStatsDisplay(stats) {
        if (!stats) return;
        elements.statTotalResumes.textContent = stats.total_resumes || 0;
        elements.statPendingReview.textContent = stats.pending_review || 0;
        elements.statShortlisted.textContent = stats.shortlisted || 0;
        elements.statAvgScore.textContent = `${stats.avg_score || 0}%`;
    }

    // ==========================================
    // CANDIDATE RANKINGS RENDERING
    // ==========================================
    async function loadFilteredRankings() {
        if (!state.activeJob) return;

        try {
            const minScore = elements.filterMinScore.value;
            const search = encodeURIComponent(elements.filterSearch.value.trim());
            const status = encodeURIComponent(elements.filterStatus.value);

            const url = `/api/rankings?min_score=${minScore}&search=${search}&status=${status}`;
            const res = await fetch(url);
            const data = await res.json();

            if (data.success) {
                state.rankings = data.rankings || [];
                renderRankingsTable();
                updateStatsDisplay(data.stats);
            }
        } catch (err) {
            console.error("Error filtering rankings:", err);
        }
    }

    function renderRankingsTable() {
        if (!state.rankings || state.rankings.length === 0) {
            elements.candidatesTableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center py-5 text-muted">
                        <i class="bi bi-inbox fs-2 d-block mb-2 text-slate-300"></i>
                        <div>No candidates matching the current filter criteria.</div>
                    </td>
                </tr>
            `;
            elements.rankingCountBadge.textContent = "0";
            return;
        }

        elements.rankingCountBadge.textContent = state.rankings.length;
        elements.btnExportCSV.disabled = false;
        elements.candidatesTableBody.innerHTML = "";

        state.rankings.forEach((cand, idx) => {
            const rank = idx + 1;
            const tr = document.createElement("tr");

            // Rank Badge Class
            let rankClass = "rank-default";
            if (rank === 1) rankClass = "rank-top-1";
            else if (rank === 2) rankClass = "rank-top-2";
            else if (rank === 3) rankClass = "rank-top-3";

            // Score Badge Class & Indicator Tier
            let scoreClass = "score-badge-lower";
            let tierDotClass = "bg-danger";
            if (cand.overall_score >= 80) {
                scoreClass = "score-badge-strong";
                tierDotClass = "bg-success";
            } else if (cand.overall_score >= 60) {
                scoreClass = "score-badge-moderate";
                tierDotClass = "bg-warning";
            }

            // Status Badge styling
            let statusBadgeClass = "bg-secondary-subtle text-secondary";
            if (cand.status === "Shortlisted") statusBadgeClass = "bg-success-subtle text-success border border-success-subtle";
            else if (cand.status === "Interviewing") statusBadgeClass = "bg-primary-subtle text-primary border border-primary-subtle";
            else if (cand.status === "Rejected") statusBadgeClass = "bg-danger-subtle text-danger border border-danger-subtle";
            else if (cand.status === "Under Review") statusBadgeClass = "bg-warning-subtle text-warning border border-warning-subtle";

            // Skills pills
            const matchedHtml = (cand.matched_skills || []).slice(0, 3).map(s => 
                `<span class="skill-pill skill-pill-matched">${escapeHtml(s)}</span>`
            ).join(" ");
            const missingCount = (cand.missing_skills || []).length;
            const missingHtml = missingCount > 0 ? 
                `<span class="skill-pill skill-pill-missing">+${missingCount} missing</span>` : '';

            tr.innerHTML = `
                <td class="ps-3">
                    <span class="rank-circle ${rankClass}">${rank}</span>
                </td>
                <td>
                    <div class="d-flex align-items-center gap-2">
                        <div>
                            <div class="fw-bold text-slate-800 ${cand.display_name === 'Name Not Detected' ? 'fst-italic text-muted' : ''}">
                                ${escapeHtml(cand.display_name)}
                            </div>
                            <div class="small text-muted d-flex align-items-center gap-1">
                                <i class="bi bi-file-earmark-text text-primary"></i>
                                <span class="text-truncate" style="max-width: 220px;" title="${escapeHtml(cand.original_filename)}">${escapeHtml(cand.original_filename)}</span>
                            </div>
                        </div>
                    </div>
                </td>
                <td>
                    <div class="d-flex flex-column align-items-start">
                        <span class="score-badge ${scoreClass} mb-1">
                            <span class="tier-indicator-dot ${tierDotClass}"></span>${cand.overall_score}%
                        </span>
                        <div class="progress w-100" style="height: 4px;">
                            <div class="progress-bar ${cand.overall_score >= 80 ? 'bg-success' : (cand.overall_score >= 60 ? 'bg-warning' : 'bg-secondary')}" 
                                 role="progressbar" style="width: ${cand.overall_score}%"></div>
                        </div>
                        <span class="text-muted" style="font-size: 0.72rem;">${escapeHtml(cand.indicator_tier || 'Screening Score')}</span>
                    </div>
                </td>
                <td>
                    <div>
                        <div class="d-flex flex-wrap gap-1 align-items-center mb-1">
                            ${matchedHtml || '<span class="text-muted small">No direct match</span>'}
                            ${missingHtml}
                        </div>
                        <div class="small text-muted" style="font-size: 0.75rem;">
                            <i class="bi bi-briefcase me-1"></i>${escapeHtml(cand.experience_display)}
                        </div>
                    </div>
                </td>
                <td>
                    <select class="form-select form-select-sm border-0 ${statusBadgeClass} fw-semibold status-quick-change" data-app-id="${cand.application_id}">
                        <option value="Under Review" ${cand.status === 'Under Review' ? 'selected' : ''}>Under Review</option>
                        <option value="Shortlisted" ${cand.status === 'Shortlisted' ? 'selected' : ''}>Shortlisted</option>
                        <option value="Interviewing" ${cand.status === 'Interviewing' ? 'selected' : ''}>Interview Scheduled</option>
                        <option value="Rejected" ${cand.status === 'Rejected' ? 'selected' : ''}>Rejected</option>
                    </select>
                </td>
                <td class="text-end pe-3">
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-primary btn-sm btn-view-candidate" data-index="${idx}" title="View Evidence & Score Breakdown">
                            <i class="bi bi-eye"></i> View
                        </button>
                        <a href="/api/download/${encodeURIComponent(cand.filename)}" class="btn btn-outline-secondary btn-sm" title="Download Original Resume File">
                            <i class="bi bi-download"></i>
                        </a>
                    </div>
                </td>
            `;

            elements.candidatesTableBody.appendChild(tr);
        });

        // Quick status change listeners
        document.querySelectorAll(".status-quick-change").forEach(select => {
            select.addEventListener("change", async (e) => {
                const appId = e.target.getAttribute("data-app-id");
                const newStatus = e.target.value;
                await updateApplicationStatus(appId, newStatus);
            });
        });

        // Candidate detail modal trigger buttons
        document.querySelectorAll(".btn-view-candidate").forEach(btn => {
            btn.addEventListener("click", (e) => {
                const idx = parseInt(e.currentTarget.getAttribute("data-index"));
                openCandidateModal(state.rankings[idx]);
            });
        });
    }

    async function updateApplicationStatus(appId, status, notes = null) {
        try {
            const body = { status };
            if (notes !== null) body.notes = notes;

            const res = await fetch(`/api/application/${appId}/status`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body)
            });
            const data = await res.json();
            if (data.success) {
                showToast(`Candidate status updated to '${status}'.`, "success");
                await loadFilteredRankings();
            } else {
                showToast(data.error || "Failed to update status", "error");
            }
        } catch (err) {
            console.error("Error updating status:", err);
            showToast("Network error updating status", "error");
        }
    }

    // ==========================================
    // CANDIDATE ANALYSIS MODAL
    // ==========================================
    function openCandidateModal(cand) {
        state.selectedCandidate = cand;

        const initials = cand.display_name && cand.display_name !== "Name Not Detected" 
            ? cand.display_name.split(" ").map(w => w[0]).join("").substring(0, 2).toUpperCase() 
            : "CV";

        elements.modalCandidateAvatar.textContent = initials;
        elements.modalCandidateName.textContent = cand.display_name;
        elements.modalCandidateContact.textContent = `${cand.email || 'No email detected'} | File: ${cand.original_filename}`;

        // Scores
        elements.modalOverallScore.textContent = `${cand.overall_score}%`;
        elements.modalSkillScore.textContent = `${cand.skill_score}%`;
        elements.modalSemanticScore.textContent = `${cand.semantic_score}%`;
        elements.modalCosineRaw.textContent = `Raw TF-IDF Cosine: ${cand.raw_tfidf}%`;
        elements.modalExpScore.textContent = `${cand.experience_score}%`;
        elements.modalExpYears.textContent = cand.experience_label || cand.experience_display;

        const matchedCount = (cand.matched_skills || []).length;
        const totalReq = matchedCount + (cand.missing_skills || []).length;
        elements.modalSkillCount.textContent = `${matchedCount} of ${totalReq} required matched`;

        // Tier badge
        if (cand.overall_score >= 80) {
            elements.modalMatchBadge.className = "badge bg-success-subtle text-success border border-success-subtle";
            elements.modalMatchBadge.textContent = "Strong Match (80-100%)";
        } else if (cand.overall_score >= 60) {
            elements.modalMatchBadge.className = "badge bg-warning-subtle text-warning border border-warning-subtle";
            elements.modalMatchBadge.textContent = "Moderate Match (60-79%)";
        } else {
            elements.modalMatchBadge.className = "badge bg-secondary-subtle text-secondary border border-secondary-subtle";
            elements.modalMatchBadge.textContent = "Lower Match (<60%)";
        }

        // Supporting evidence reasons
        elements.modalMatchReasonsList.innerHTML = "";
        (cand.match_reasons || []).forEach(reason => {
            const li = document.createElement("li");
            li.className = "mb-1";
            li.textContent = reason;
            elements.modalMatchReasonsList.appendChild(li);
        });

        // Matched Skills
        elements.modalMatchedSkillsPills.innerHTML = "";
        if (cand.matched_skills && cand.matched_skills.length > 0) {
            cand.matched_skills.forEach(skill => {
                const span = document.createElement("span");
                span.className = "skill-pill skill-pill-matched";
                span.textContent = skill;
                elements.modalMatchedSkillsPills.appendChild(span);
            });
        } else {
            elements.modalMatchedSkillsPills.innerHTML = '<span class="text-muted small">No direct skill matches</span>';
        }

        // Missing Skills
        elements.modalMissingSkillsPills.innerHTML = "";
        if (cand.missing_skills && cand.missing_skills.length > 0) {
            cand.missing_skills.forEach(skill => {
                const span = document.createElement("span");
                span.className = "skill-pill skill-pill-missing";
                span.textContent = skill;
                elements.modalMissingSkillsPills.appendChild(span);
            });
        } else {
            elements.modalMissingSkillsPills.innerHTML = '<span class="text-success small fw-semibold">All required skills present!</span>';
        }

        // Education
        elements.modalEducationList.innerHTML = "";
        if (cand.education && cand.education.length > 0) {
            cand.education.forEach(edu => {
                const div = document.createElement("div");
                div.className = "mb-1";
                div.innerHTML = `<i class="bi bi-mortarboard me-1 text-primary"></i> ${escapeHtml(edu)}`;
                elements.modalEducationList.appendChild(div);
            });
        } else {
            elements.modalEducationList.innerHTML = '<span class="text-muted">No explicit degree detected in text.</span>';
        }

        // Projects
        elements.modalProjectsList.innerHTML = "";
        if (cand.projects && cand.projects.length > 0) {
            cand.projects.forEach(proj => {
                const div = document.createElement("div");
                div.className = "mb-2 pb-1 border-bottom border-light";
                div.innerHTML = `<i class="bi bi-arrow-right-short text-primary"></i> ${escapeHtml(proj)}`;
                elements.modalProjectsList.appendChild(div);
            });
        } else {
            elements.modalProjectsList.innerHTML = '<span class="text-muted">No explicit project bullets detected in text.</span>';
        }

        // All Skills
        elements.modalAllCandidateSkills.innerHTML = "";
        const allSkills = cand.candidate_skills || [];
        if (allSkills.length > 0) {
            allSkills.forEach(s => {
                const span = document.createElement("span");
                span.className = "skill-pill skill-pill-neutral";
                span.textContent = s;
                elements.modalAllCandidateSkills.appendChild(span);
            });
        } else {
            elements.modalAllCandidateSkills.innerHTML = '<span class="text-muted">No technical skills detected.</span>';
        }

        // Raw Text
        elements.modalRawText.textContent = cand.raw_text || "Resume text unavailable.";

        // Recruiter Action Form in modal
        elements.modalStatusSelect.value = cand.status || "Under Review";
        elements.modalRecruiterNotes.value = cand.recruiter_notes || "";
        elements.modalReviewedAt.textContent = cand.reviewed_at ? `Last reviewed: ${cand.reviewed_at}` : "Not yet reviewed";

        elements.modalDownloadResumeBtn.href = `/api/download/${encodeURIComponent(cand.filename)}`;
        elements.candidateModal.show();
    }

    elements.btnSaveRecruiterDecision.addEventListener("click", async () => {
        if (!state.selectedCandidate) return;
        const newStatus = elements.modalStatusSelect.value;
        const notes = elements.modalRecruiterNotes.value.trim();
        await updateApplicationStatus(state.selectedCandidate.application_id, newStatus, notes);
        elements.candidateModal.hide();
    });

    // ==========================================
    // WORKFLOW ACTIONS: ANALYZE & RE-ANALYZE
    // ==========================================
    function setupEventListeners() {
        // Dropzone & File Selection
        elements.btnBrowseFiles.addEventListener("click", () => elements.resumeFileInput.click());
        elements.dropZone.addEventListener("click", () => elements.resumeFileInput.click());

        elements.dropZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            elements.dropZone.classList.add("drag-over");
        });

        elements.dropZone.addEventListener("dragleave", () => {
            elements.dropZone.classList.remove("drag-over");
        });

        elements.dropZone.addEventListener("drop", (e) => {
            e.preventDefault();
            elements.dropZone.classList.remove("drag-over");
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                handleFileSelection(Array.from(e.dataTransfer.files));
            }
        });

        elements.resumeFileInput.addEventListener("change", (e) => {
            if (e.target.files && e.target.files.length > 0) {
                handleFileSelection(Array.from(e.target.files));
            }
        });

        elements.btnClearFiles.addEventListener("click", () => {
            state.selectedFiles = [];
            elements.selectedFilesContainer.classList.add("d-none");
            elements.resumeFileInput.value = "";
        });

        // Primary Action: Analyze Resumes Button
        elements.btnStartAnalyze.addEventListener("click", startAnalysisWorkflow);

        // Re-analyze existing resumes with updated JD
        elements.btnReanalyze.addEventListener("click", reanalyzeWorkflow);

        // Filter Controls
        elements.filterSearch.addEventListener("input", debounce(loadFilteredRankings, 250));
        elements.filterStatus.addEventListener("change", loadFilteredRankings);
        elements.filterMinScore.addEventListener("input", (e) => {
            elements.minScoreLabel.textContent = `${e.target.value}%`;
        });
        elements.filterMinScore.addEventListener("change", loadFilteredRankings);

        // Refresh Button
        elements.btnRefreshRankings.addEventListener("click", async () => {
            await loadFilteredRankings();
            showToast("Rankings refreshed.", "info");
        });

        // Export CSV
        elements.btnExportCSV.addEventListener("click", () => {
            window.location.href = "/api/export";
        });

        // Clear All Workspace
        elements.btnClearAll.addEventListener("click", async () => {
            if (!confirm("Are you sure you want to clear all uploaded resumes and job data? This will reset the workspace to a blank state.")) {
                return;
            }
            try {
                const res = await fetch("/api/clear", { method: "POST" });
                const data = await res.json();
                if (data.success) {
                    showToast("Workspace cleared. Ready for new analysis.", "info");
                    renderCleanEmptyState();
                }
            } catch (err) {
                console.error("Error clearing workspace:", err);
                showToast("Failed to clear workspace.", "error");
            }
        });
    }

    function handleFileSelection(files) {
        hideValidationAlert();
        const validExtensions = ["pdf", "docx"];
        const maxSizeBytes = 10 * 1024 * 1024; // 10 MB

        files.forEach(file => {
            const ext = file.name.split(".").pop().toLowerCase();
            if (!validExtensions.includes(ext)) {
                showToast(`Skipped '${file.name}': Only PDF and DOCX files are supported.`, "warning");
                return;
            }
            if (file.size > maxSizeBytes) {
                showToast(`Skipped '${file.name}': File exceeds 10MB maximum limit.`, "warning");
                return;
            }
            if (!state.selectedFiles.some(f => f.name === file.name && f.size === file.size)) {
                state.selectedFiles.push(file);
            }
        });

        if (state.selectedFiles.length > 0) {
            elements.selectedFilesContainer.classList.remove("d-none");
            renderSelectedFilesList();
        }
    }

    function renderSelectedFilesList() {
        elements.selectedFilesList.innerHTML = "";
        elements.selectedFileCount.textContent = `${state.selectedFiles.length} file(s) selected`;

        state.selectedFiles.forEach((file, index) => {
            const li = document.createElement("li");
            li.className = "list-group-item d-flex justify-content-between align-items-center py-2";
            const sizeKb = Math.round(file.size / 1024);
            li.innerHTML = `
                <div class="d-flex align-items-center gap-2 text-truncate">
                    <i class="bi ${file.name.endsWith('.pdf') ? 'bi-file-earmark-pdf text-danger' : 'bi-file-earmark-word text-primary'}"></i>
                    <span class="text-truncate">${escapeHtml(file.name)}</span>
                    <span class="text-muted small">(${sizeKb} KB)</span>
                </div>
                <button type="button" class="btn btn-link text-danger p-0 ms-2" onclick="removeSelectedFile(${index})">
                    <i class="bi bi-x"></i>
                </button>
            `;
            elements.selectedFilesList.appendChild(li);
        });
    }

    window.removeSelectedFile = function(index) {
        state.selectedFiles.splice(index, 1);
        if (state.selectedFiles.length === 0) {
            elements.selectedFilesContainer.classList.add("d-none");
            elements.resumeFileInput.value = "";
        } else {
            renderSelectedFilesList();
        }
    };

    // Primary Analysis Submission
    async function startAnalysisWorkflow() {
        hideValidationAlert();

        const jobTitle = elements.inputJobTitle.value.trim();
        const jobDesc = elements.inputJobDesc.value.trim();
        const reqSkills = elements.inputRequiredSkills.value.trim();
        const minExp = elements.inputMinExp.value.trim();

        // 1. Validate Job Role
        if (!jobTitle) {
            showValidationAlert("Please enter the Job Role / Job Title before analyzing.");
            elements.inputJobTitle.focus();
            return;
        }

        // 2. Validate Job Description
        if (!jobDesc) {
            showValidationAlert("Please provide the full Job Description (JD) to compare resumes against.");
            elements.inputJobDesc.focus();
            return;
        }

        // 3. Validate Resumes
        const hasExisting = state.rankings.length > 0;
        if (state.selectedFiles.length === 0 && !hasExisting) {
            showValidationAlert("Please upload at least one candidate resume (PDF or DOCX).");
            return;
        }

        // Start Execution UI
        elements.btnStartAnalyze.disabled = true;
        elements.btnStartAnalyzeText.textContent = "Analyzing Resumes...";
        elements.uploadProgressContainer.classList.remove("d-none");
        elements.uploadProgressBar.style.width = "25%";
        elements.uploadProgressLabel.textContent = "Uploading & extracting resume content...";
        elements.uploadProgressText.textContent = "25%";

        const formData = new FormData();
        formData.append("job_title", jobTitle);
        formData.append("job_description", jobDesc);
        formData.append("required_skills", reqSkills);
        formData.append("min_experience", minExp);

        state.selectedFiles.forEach(file => {
            formData.append("resumes", file);
        });

        try {
            elements.uploadProgressBar.style.width = "60%";
            elements.uploadProgressLabel.textContent = "Computing TF-IDF cosine similarity & skills matching...";
            elements.uploadProgressText.textContent = "60%";

            const res = await fetch("/api/analyze", {
                method: "POST",
                body: formData
            });

            elements.uploadProgressBar.style.width = "95%";
            elements.uploadProgressText.textContent = "95%";

            const data = await res.json();
            elements.uploadProgressBar.style.width = "100%";

            if (data.success) {
                state.activeJob = data.job;
                state.rankings = data.rankings || [];

                // Reset file selection
                state.selectedFiles = [];
                elements.selectedFilesContainer.classList.add("d-none");
                elements.resumeFileInput.value = "";

                // Update UI state
                elements.jobStatusBadge.textContent = "Active Requirements";
                elements.reanalyzeContainer.classList.remove("d-none");

                updateStatsDisplay(data.stats);
                renderRankingsTable();
                showToast(data.message, "success");

                if (data.file_errors && data.file_errors.length > 0) {
                    data.file_errors.forEach(err => {
                        showToast(`${err.filename}: ${err.error}`, "warning");
                    });
                }
            } else {
                showValidationAlert(data.error || "Analysis failed.");
                showToast(data.error || "Analysis failed.", "error");
            }
        } catch (err) {
            console.error("Analysis network error:", err);
            showToast("An error occurred during analysis.", "error");
        } finally {
            elements.btnStartAnalyze.disabled = false;
            elements.btnStartAnalyzeText.textContent = "Analyze Resumes";
            elements.uploadProgressContainer.classList.add("d-none");
            elements.uploadProgressBar.style.width = "0%";
        }
    }

    // Re-Analyze Existing Resumes with updated JD
    async function reanalyzeWorkflow() {
        hideValidationAlert();

        const jobTitle = elements.inputJobTitle.value.trim();
        const jobDesc = elements.inputJobDesc.value.trim();
        const reqSkills = elements.inputRequiredSkills.value.split(",").map(s => s.trim()).filter(Boolean);
        const minExp = elements.inputMinExp.value.trim();

        if (!jobTitle || !jobDesc) {
            showValidationAlert("Job Role and Job Description are required for re-analysis.");
            return;
        }

        elements.btnReanalyze.disabled = true;
        elements.btnReanalyze.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Re-scoring resumes against updated JD...';

        try {
            const res = await fetch("/api/reanalyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    job_title: jobTitle,
                    job_description: jobDesc,
                    required_skills: reqSkills,
                    min_experience: minExp ? parseFloat(minExp) : null
                })
            });

            const data = await res.json();
            if (data.success) {
                state.activeJob = data.job;
                state.rankings = data.rankings || [];
                updateStatsDisplay(data.stats);
                renderRankingsTable();
                showToast(data.message, "success");
            } else {
                showToast(data.error || "Re-analysis failed", "error");
            }
        } catch (err) {
            console.error("Re-analysis error:", err);
            showToast("Network error during re-analysis.", "error");
        } finally {
            elements.btnReanalyze.disabled = false;
            elements.btnReanalyze.innerHTML = '<i class="bi bi-arrow-repeat"></i> <span>Update Job Details & Re-Analyze Existing Resumes</span>';
        }
    }

    // ==========================================
    // UTILITY HELPERS
    // ==========================================
    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    function escapeHtml(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Launch Application
    initApp();
});
