import pytest
from matcher import (
    compute_tfidf_semantic_similarity, compute_skills_alignment,
    compute_experience_alignment, evaluate_resume
)

def test_compute_tfidf_similarity():
    job_text = (
        "Senior Python backend engineer with Flask and Docker skills. "
        "Responsible for building scalable REST APIs, microservices, and database models."
    )
    resume_matching = (
        "Experienced Python backend engineer specializing in Flask microservices and Docker containerization. "
        "Developed scalable REST APIs and automated deployment pipelines."
    )
    resume_different = "Executive chef with extensive culinary experience in restaurant kitchen operations and pastry."

    raw_match, score_match = compute_tfidf_semantic_similarity(job_text, resume_matching)
    raw_diff, score_diff = compute_tfidf_semantic_similarity(job_text, resume_different)

    assert score_match > 30.0
    assert score_match > score_diff
    assert score_diff == 0.0

def test_compute_skills_alignment():
    required = ["Python", "Flask", "Docker", "PostgreSQL", "React"]
    candidate = ["python", "flask", "docker", "git", "linux"]
    raw_text = "Experienced in Python, Flask, Docker, and PostgreSQL databases."

    matched, missing, score = compute_skills_alignment(required, candidate, raw_text)
    assert "Python" in matched
    assert "Flask" in matched
    assert "Docker" in matched
    assert "PostgreSQL" in matched
    assert "React" in missing
    assert score == 80.0

def test_compute_experience_alignment():
    # Meets requirement
    score, label = compute_experience_alignment(3.0, 5.0)
    assert score == 100.0
    assert "Meets" in label

    # Below requirement
    score_below, label_below = compute_experience_alignment(4.0, 2.0)
    assert score_below == 50.0
    assert "below" in label_below

    # Not specified
    score_unspecified, label_unspec = compute_experience_alignment(3.0, None)
    assert score_unspecified < 50.0
    assert "Not specified" in label_unspec

def test_different_resumes_receive_different_scores():
    job = {
        "title": "Senior Python & AI Engineer",
        "description": "Develop scalable Python backend microservices, REST APIs, and ML models using Flask and Docker.",
        "required_skills": ["Python", "Flask", "Docker", "Machine Learning"],
        "min_experience": 3.0
    }
    
    strong_candidate = {
        "name": "Alex Tech",
        "skills": ["python", "flask", "docker", "machine learning", "git"],
        "experience_years": 4.5,
        "education": ["B.Tech in Computer Science"],
        "projects": ["Built AI matching platform in Python with Flask"],
        "raw_text": "Senior Python engineer with 4.5 years experience in Flask, Docker, and Machine Learning."
    }
    
    weak_candidate = {
        "name": "Jordan Art",
        "skills": ["html", "css"],
        "experience_years": 0.5,
        "education": ["Graphic Design Diploma"],
        "projects": ["Portfolio landing page"],
        "raw_text": "Entry level graphic designer with HTML and CSS styling experience."
    }

    eval_strong = evaluate_resume(job, strong_candidate)
    eval_weak = evaluate_resume(job, weak_candidate)

    # Strong candidate should have high score
    assert eval_strong["overall_score"] >= 75.0
    assert eval_strong["indicator_tier"] in ["Strong Match", "Moderate Match"]

    # Weak candidate should have low score
    assert eval_weak["overall_score"] < 50.0
    assert eval_weak["indicator_tier"] == "Lower Match"

    # Score differentiation is clear
    assert eval_strong["overall_score"] > eval_weak["overall_score"] + 30.0

def test_changing_jd_changes_analysis():
    candidate = {
        "name": "Taylor Swiftly",
        "skills": ["react", "javascript", "typescript", "html", "css", "redux"],
        "experience_years": 3.0,
        "education": ["B.S. in Software Engineering"],
        "projects": ["Interactive React web applications"],
        "raw_text": "Frontend developer specializing in React, TypeScript, and modern JavaScript UI design."
    }

    frontend_job = {
        "title": "Frontend React Developer",
        "description": "Build modern responsive web applications using React, TypeScript, HTML, CSS, and Redux.",
        "required_skills": ["React", "TypeScript", "JavaScript", "HTML", "CSS"],
        "min_experience": 2.0
    }

    devops_job = {
        "title": "DevOps & Cloud Engineer",
        "description": "Manage Kubernetes clusters, AWS cloud infrastructure, Terraform scripts, and Linux servers.",
        "required_skills": ["Kubernetes", "AWS", "Terraform", "Linux", "Docker"],
        "min_experience": 4.0
    }

    eval_frontend = evaluate_resume(frontend_job, candidate)
    eval_devops = evaluate_resume(devops_job, candidate)

    # Candidate should match Frontend job very well, and DevOps job poorly
    assert eval_frontend["overall_score"] > 75.0
    assert eval_devops["overall_score"] < 45.0
    assert eval_frontend["overall_score"] > eval_devops["overall_score"] + 35.0
