# AI-Powered Resume Shortlisting Tool (TalentAI)

A full-stack recruiter dashboard for screening and shortlisting candidate resumes against actual, user-provided job descriptions using local NLP (TF-IDF and Cosine Similarity), skill taxonomy matching, and transparent criteria alignment.

---

## 🎯 Key Features & Design

1. **User-Driven Requirements (Zero Demo Data)**:
   - Starts with a clean, empty workspace.
   - Enter your own **Job Role / Title**, **Full Job Description (JD)**, optional **Required Skills**, and optional **Minimum Experience**.
   - Analyzes strictly the job requirements you enter—no predefined roles or hardcoded scores.

2. **Multi-Format Resume Upload**:
   - Accepts multiple candidate resumes in **PDF** (`.pdf`) and **Word** (`.docx`) formats.
   - File validation: format validation, size limit (<10MB), and safe sanitized filenames with collision prevention.
   - Robust error handling for unreadable or scanned documents.

3. **Truthful Extraction (No Fabricated Data)**:
   - Candidate names are shown only if reliably extracted from document headers; otherwise marked as `"Name Not Detected"` alongside the original resume filename.
   - Relevant experience extracted in years, or marked as `"Not specified"`.
   - Extracts contact details, education, detected technical skills, and projects.

4. **Transparent, Explainable AI Match Scoring**:
   - **Semantic Relevance (35%)**: TF-IDF vectorization with unigrams and bigrams, calculating cosine similarity between the job description and the resume text.
   - **Required Skills Match (35%)**: Direct matching of required technical skills against candidate skills and text.
   - **Relevant Experience (15%)**: Alignment between candidate's documented experience years and your specified minimum.
   - **Education & Projects (15%)**: Evaluation of relevant academic background and project depth.
   - **Transparent Evidence**: Every candidate card includes a breakdown of matched skills, missing skills, and detailed bullet-point explanations.
   - **Score Guidelines**:
     - `80% – 100%`: **Strong Match** (Emerald)
     - `60% – 79%`: **Moderate Match** (Amber/Blue)
     - `Below 60%`: **Lower Match** (Slate/Red)

5. **Re-Analysis & Dynamic Updates**:
   - Update the Job Title, Description, or Required Skills at any time and click **"Update Job Details & Re-Analyze"** to instantly re-score all existing resumes against the new criteria.
   - Filter candidates in real-time by search query, review status, or minimum score slider.
   - Update recruiter review decisions (`Shortlisted`, `Under Review`, `Interview Scheduled`, `Rejected`) and internal recruiter notes.

6. **Export & Workspace Management**:
   - Download ranked candidate shortlists with match breakdowns as standard **CSV**.
   - One-click **"Clear Workspace"** button to delete uploaded resumes and reset to a completely blank slate.

7. **Privacy & Fairness Guarantees**:
   - **100% Local Processing**: No personal data or resumes are sent to external third-party cloud services or paid APIs.
   - **Ethical AI**: Protected personal characteristics (age, gender, religion, caste, nationality, photographs) are strictly excluded from scoring.
   - **Human-in-the-Loop**: Scores are advisory screening guidelines to support human recruiters, not automated hiring or rejection decisions.

---

## 🛠️ Technology Stack

- **Backend**: Python 3 (Flask)
- **NLP & AI Engine**: Scikit-learn (`TfidfVectorizer`, `cosine_similarity`), NumPy, SciPy
- **Document Parsing**: `pypdf` (PDF extraction), `python-docx` (DOCX extraction)
- **Database**: SQLite (local embedded storage)
- **Frontend**: HTML5, Vanilla CSS, JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons
- **Testing**: `pytest`

---

## 💻 Windows Setup & Installation

### Prerequisites
- Python 3.10+ installed on Windows (ensure `python` is added to your Windows PATH).

### 1. Clone or Open Project Folder
Open PowerShell or Command Prompt in the project directory:
```powershell
cd "c:\Users\pavan\OneDrive\Desktop\project Ai Resume"
```

### 2. Activate Existing Virtual Environment (or create one)
```powershell
# If virtual environment is already present:
.\venv\Scripts\Activate.ps1

# (Or if creating fresh):
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
```

---

## 🚀 Running the Application

To start the Flask development server:
```powershell
.\venv\Scripts\python app.py
```

Once started, open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 📋 How to Upload Your Own Job Description & Resumes

1. **Step 1: Enter Job Requirements**
   - Type your **Job Role / Title** (e.g., `Senior Python Backend Engineer`, `Frontend React Developer`).
   - Paste your full **Job Description (JD)** into the textarea.
   - *(Optional)* Add comma-separated **Required Skills** (e.g., `Python, Flask, Docker, PostgreSQL`).
   - *(Optional)* Enter the **Minimum Experience** in years (e.g., `3.0`).

2. **Step 2: Upload Resumes**
   - Click **"Browse Files"** or drag and drop your candidate resumes (`.pdf` or `.docx`) into the upload dropzone.

3. **Step 3: Analyze Resumes**
   - Click the blue **"Analyze Resumes"** button.
   - The tool will extract candidate text, run the TF-IDF cosine comparison and skills match, and present ranked candidates in descending score order.

4. **Step 4: Review and Inspect**
   - Click **"View"** on any candidate to inspect their detailed AI breakdown:
     - See exact matched skills (green badges) and missing skills (red badges).
     - Read the supporting evidence explaining the score.
     - View extracted education and project sections.
     - Download the candidate's original resume file.
     - Update their review status or leave recruiter notes.

5. **Step 5: Tweak Criteria or Export**
   - Modify the Job Description or Required Skills and click **"Update Job Details & Re-Analyze"** to immediately re-score all resumes against the new requirements.
   - Click **"Export CSV"** to download the shortlisted candidate table.
   - Click **"Clear Workspace"** when you are ready to start a completely new job search.

---

## 🧪 Running the Automated Test Suite

To run all 18 automated unit and integration tests:
```powershell
.\venv\Scripts\python -m pytest -v
```

All tests verify:
- Safe document parsing (PDF and DOCX)
- Accurate entity extraction without fake names
- TF-IDF semantic cosine similarity calculations
- Skills and experience scoring logic
- Sensitivity to different job descriptions and resume texts
- Clean initial empty states and input validation
- Workspace clearing and CSV export
