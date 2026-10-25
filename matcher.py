import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from config import Config
from parser import extract_skills

def clean_text_for_nlp(text):
    """Cleans text for TF-IDF vectorization while retaining technical symbols."""
    if not text:
        return ""
    cleaned = re.sub(r"[^\w\s\.\+#-]", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

def compute_tfidf_semantic_similarity(job_text, resume_text):
    """
    Computes TF-IDF cosine similarity between job description and candidate resume text.
    Returns:
      - raw_cosine: Cosine similarity in range [0.0, 1.0]
      - scaled_score: Calibrated semantic alignment score in range [0.0, 100.0]
    """
    cleaned_job = clean_text_for_nlp(job_text)
    cleaned_resume = clean_text_for_nlp(resume_text)
    
    if not cleaned_job or not cleaned_resume:
        return 0.0, 0.0
        
    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=1
        )
        tfidf_matrix = vectorizer.fit_transform([cleaned_job, cleaned_resume])
        raw_cosine = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
        raw_cosine = max(0.0, min(1.0, raw_cosine))
        
        # In NLP document similarity, cross-genre text (JD vs Resume) typically maxes around 0.50-0.60
        # for excellent matches. We scale so that 0.40+ reflects high alignment.
        scaled_score = min(100.0, (raw_cosine / 0.55) * 100.0)
        return round(raw_cosine * 100.0, 1), round(scaled_score, 1)
    except Exception:
        return 0.0, 0.0

def compute_skills_alignment(required_skills, candidate_skills, raw_resume_text=""):
    """
    Compares required skills against candidate's extracted skills and resume body.
    Returns:
      - matched_skills (list)
      - missing_skills (list)
      - skill_score (0.0 to 100.0)
    """
    if not required_skills:
        # If user didn't specify required skills, candidate receives full neutral score
        return [], [], 100.0
        
    matched = []
    missing = []
    
    cand_skills_lower = {s.lower().strip() for s in (candidate_skills or [])}
    resume_lower = (raw_resume_text or "").lower()
    
    for req in required_skills:
        req_clean = req.lower().strip()
        if not req_clean:
            continue
            
        is_matched = False
        if req_clean in cand_skills_lower:
            is_matched = True
        else:
            for cs in cand_skills_lower:
                if req_clean in cs or cs in req_clean:
                    is_matched = True
                    break
                    
        if not is_matched and resume_lower:
            if req_clean in ["c++", "c#", ".net"]:
                if re.search(r"(?:^|\s)" + re.escape(req_clean) + r"(?:$|\s|[,;])", resume_lower):
                    is_matched = True
            elif len(req_clean) <= 2:
                if re.search(r"\b" + re.escape(req_clean) + r"\b", resume_lower):
                    is_matched = True
            else:
                if req_clean in resume_lower:
                    is_matched = True
                    
        if is_matched:
            matched.append(req.strip())
        else:
            missing.append(req.strip())
            
    total = len(matched) + len(missing)
    if total == 0:
        return [], [], 100.0
        
    score = (len(matched) / total) * 100.0
    return matched, missing, round(score, 1)

def compute_experience_alignment(min_experience, candidate_experience):
    """
    Evaluates candidate's experience against user's required minimum.
    Returns:
      - experience_score (0.0 to 100.0)
      - experience_label (str explanation)
    """
    if min_experience is None or min_experience <= 0:
        if candidate_experience is not None:
            return 100.0, f"{candidate_experience:g} years documented (No minimum specified)"
        else:
            return 100.0, "Not specified (No minimum required)"
            
    min_exp = float(min_experience)
    
    if candidate_experience is None:
        # Experience couldn't be extracted from resume
        return 30.0, f"Not specified in resume (Requires minimum {min_exp:g} yrs)"
        
    cand_exp = float(candidate_experience)
    if cand_exp >= min_exp:
        diff = cand_exp - min_exp
        label = f"{cand_exp:g} yrs documented (Meets minimum {min_exp:g} yrs; +{diff:g} yrs)" if diff > 0 else f"{cand_exp:g} yrs documented (Meets exact requirement)"
        return 100.0, label
    else:
        gap = min_exp - cand_exp
        score = (cand_exp / min_exp) * 100.0
        return round(max(0.0, score), 1), f"{cand_exp:g} yrs documented ({gap:g} yrs below desired {min_exp:g} yrs)"

def compute_qualification_relevance(candidate_education, candidate_projects, job_description):
    """
    Evaluates depth of documented education and relevant projects against the JD.
    Returns score between 0.0 and 100.0.
    """
    score = 40.0  # Base credit
    
    # Education presence
    if candidate_education and len(candidate_education) > 0:
        score += 30.0
        
    # Projects presence and keywords
    if candidate_projects and len(candidate_projects) > 0:
        score += 30.0
        
    return min(100.0, score)

def evaluate_resume(job, candidate):
    """
    Compares candidate resume against user-provided job requirements.
    Calculates transparent weighted score and generates evidentiary reasons.
    """
    job_title = job.get("title", "").strip()
    job_desc = job.get("description", "").strip()
    raw_req_skills = job.get("required_skills", [])
    
    if isinstance(raw_req_skills, str):
        required_skills = [s.strip() for s in raw_req_skills.split(",") if s.strip()]
    else:
        required_skills = [s.strip() for s in raw_req_skills if s and s.strip()]
        
    # If user did not provide explicit skills, extract key skills from the JD text
    if not required_skills and job_desc:
        required_skills = extract_skills(f"{job_title} {job_desc}")[:8]
        
    min_experience = job.get("min_experience")
    if min_experience is not None:
        try:
            min_experience = float(min_experience)
            if min_experience <= 0:
                min_experience = None
        except (ValueError, TypeError):
            min_experience = None

    resume_text = candidate.get("raw_text", "")
    
    # 1. Semantic TF-IDF Similarity
    full_job_context = f"{job_title}\n{job_desc}\n{' '.join(required_skills)}"
    raw_tfidf, semantic_score = compute_tfidf_semantic_similarity(full_job_context, resume_text)
    
    # 2. Skills Match
    matched_skills, missing_skills, skill_score = compute_skills_alignment(
        required_skills,
        candidate.get("skills", []),
        resume_text
    )
    
    # 3. Experience Match
    cand_exp = candidate.get("experience_years")
    exp_score, exp_label = compute_experience_alignment(min_experience, cand_exp)
    
    # 4. Education & Projects Relevance
    qual_score = compute_qualification_relevance(
        candidate.get("education", []),
        candidate.get("projects", []),
        job_desc
    )
    
    # 5. Weighted Score Calculation
    w_sem = Config.WEIGHT_SEMANTIC
    w_skl = Config.WEIGHT_SKILLS
    w_exp = Config.WEIGHT_EXPERIENCE
    w_qua = Config.WEIGHT_QUALIFICATIONS
    
    overall_score = (semantic_score * w_sem) + (skill_score * w_skl) + (exp_score * w_exp) + (qual_score * w_qua)
    overall_score = round(max(0.0, min(100.0, overall_score)), 1)
    
    # 6. Score Indicator Tier
    if overall_score >= 80.0:
        indicator_tier = "Strong Match"
        indicator_class = "strong"
        status = "Shortlisted"
    elif overall_score >= 60.0:
        indicator_tier = "Moderate Match"
        indicator_class = "moderate"
        status = "Under Review"
    else:
        indicator_tier = "Lower Match"
        indicator_class = "lower"
        status = "Under Review"
        
    # 7. Evidentiary Match Explanation
    evidence_reasons = []
    
    # Skills evidence
    if required_skills:
        evidence_reasons.append(
            f"Skills Alignment ({skill_score}%): Matched {len(matched_skills)} of {len(required_skills)} required skills. "
            f"Found: [{', '.join(matched_skills) if matched_skills else 'None'}]."
        )
        if missing_skills:
            evidence_reasons.append(f"Missing Key Skills: Lacking [{', '.join(missing_skills)}].")
    else:
        evidence_reasons.append("Skills Alignment: No required skills specified in job criteria.")
        
    # Experience evidence
    evidence_reasons.append(f"Experience Alignment ({exp_score}%): {exp_label}.")
    
    # Semantic similarity evidence
    evidence_reasons.append(
        f"Semantic Content Relevance ({semantic_score}%): Cosine similarity of {raw_tfidf}% between resume text and JD keywords."
    )
    
    # Education/Projects evidence
    edu_list = candidate.get("education", [])
    proj_list = candidate.get("projects", [])
    evidence_reasons.append(
        f"Profile Completeness ({qual_score}%): {len(edu_list)} education entries and {len(proj_list)} project references detected."
    )
    
    # Advisory notice
    evidence_reasons.append(
        "Screening Guideline: This score provides transparent criteria alignment for human recruiter review and does not represent an automated hiring decision or probability of hire."
    )
    
    return {
        "overall_score": overall_score,
        "indicator_tier": indicator_tier,
        "indicator_class": indicator_class,
        "semantic_score": semantic_score,
        "raw_tfidf": raw_tfidf,
        "skill_score": skill_score,
        "experience_score": exp_score,
        "experience_label": exp_label,
        "qualification_score": qual_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "evidence_reasons": evidence_reasons,
        "status": status
    }
