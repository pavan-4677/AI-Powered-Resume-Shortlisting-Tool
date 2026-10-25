import pytest
import json
import io
import os
from app import app
from database import init_db, clear_all_data

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        clear_all_data()
        init_db()
        yield client
        clear_all_data()

def test_index_route(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"AI-Powered Resume Shortlisting" in res.data or b"TalentAI" in res.data

def test_empty_initial_state(client):
    res = client.get("/api/rankings")
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["success"] is True
    assert data["has_job"] is False
    assert len(data["rankings"]) == 0
    assert data["stats"]["total_resumes"] == 0

def test_analyze_validation_missing_fields(client):
    # Missing job title
    res1 = client.post("/api/analyze", data={"job_description": "Some JD"})
    assert res1.status_code == 400
    data1 = json.loads(res1.data)
    assert "Job Role" in data1["error"]

    # Missing job description
    res2 = client.post("/api/analyze", data={"job_title": "Software Engineer"})
    assert res2.status_code == 400
    data2 = json.loads(res2.data)
    assert "Job Description" in data2["error"]

    # Missing resumes when no existing resumes exist
    res3 = client.post("/api/analyze", data={
        "job_title": "Software Engineer",
        "job_description": "Build python web applications."
    })
    assert res3.status_code == 400
    data3 = json.loads(res3.data)
    assert "resume" in data3["error"].lower()

def test_analyze_and_rank_resumes(client):
    # Create sample in-memory test PDF using reportlab
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Alex Morgan", styles['Heading1']),
        Paragraph("Email: alex.morgan@example.com | Phone: 555-123-4567", styles['Normal']),
        Paragraph("Python backend developer with 4 years experience in Flask, Docker, and PostgreSQL.", styles['Normal']),
        Paragraph("Skills: Python, Flask, Docker, PostgreSQL, REST API, Git", styles['Normal']),
        Paragraph("Education: Bachelor of Technology in Computer Science", styles['Normal']),
        Paragraph("Projects: Built microservices using Flask and Docker containerization", styles['Normal'])
    ]
    doc.build(story)
    pdf_buffer.seek(0)

    data = {
        "job_title": "Python Backend Engineer",
        "job_description": "Looking for a Python Backend Engineer with hands-on experience in Flask, Docker, and PostgreSQL.",
        "required_skills": "Python, Flask, Docker, PostgreSQL",
        "min_experience": "3.0",
        "resumes": (pdf_buffer, "Alex_Resume.pdf")
    }

    res = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    assert res.status_code == 200
    resp_data = json.loads(res.data)
    assert resp_data["success"] is True
    assert len(resp_data["rankings"]) == 1

    candidate = resp_data["rankings"][0]
    assert candidate["display_name"] == "Alex Morgan"
    assert candidate["overall_score"] >= 70.0
    assert "Python" in candidate["matched_skills"]
    assert "Flask" in candidate["matched_skills"]
    assert "Docker" in candidate["matched_skills"]
    assert len(candidate["match_reasons"]) > 0

def test_reanalyze_workflow(client):
    # First submit an initial analysis
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Morgan Reed", styles['Heading1']),
        Paragraph("Email: morgan.reed@example.com", styles['Normal']),
        Paragraph("Skills: React, TypeScript, JavaScript, CSS, HTML", styles['Normal']),
        Paragraph("Summary: 3 years experience building React frontend interfaces.", styles['Normal'])
    ]
    doc.build(story)
    pdf_buffer.seek(0)

    client.post("/api/analyze", data={
        "job_title": "Frontend Engineer",
        "job_description": "Build web user interfaces using React, TypeScript, and CSS.",
        "required_skills": "React, TypeScript, CSS",
        "min_experience": "2.0",
        "resumes": (pdf_buffer, "Morgan_Resume.pdf")
    }, content_type="multipart/form-data")

    # Score should be high for frontend job
    res1 = client.get("/api/rankings")
    score1 = json.loads(res1.data)["rankings"][0]["overall_score"]
    assert score1 >= 65.0

    # Now re-analyze candidate against a completely different role: Cloud Architect
    reanalyze_payload = {
        "job_title": "Cloud Infrastructure Architect",
        "job_description": "Manage multi-cluster Kubernetes on AWS with Terraform and Linux.",
        "required_skills": ["AWS", "Kubernetes", "Terraform", "Linux"],
        "min_experience": 5.0
    }
    res2 = client.post("/api/reanalyze", json=reanalyze_payload)
    assert res2.status_code == 200
    score2 = json.loads(res2.data)["rankings"][0]["overall_score"]

    # Score should drop significantly because candidate has 0 cloud skills
    assert score2 < score1
    assert score2 < 50.0

def test_clear_workspace(client):
    # Post a job & resume
    pdf_buffer = io.BytesIO(b"%PDF-1.4 empty fake pdf")
    client.post("/api/analyze", data={
        "job_title": "Test Job",
        "job_description": "Some description",
        "resumes": (pdf_buffer, "test.pdf")
    }, content_type="multipart/form-data")

    # Clear workspace
    res = client.post("/api/clear")
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["success"] is True

    # Verify clean empty state
    res_rank = client.get("/api/rankings")
    rank_data = json.loads(res_rank.data)
    assert rank_data["has_job"] is False
    assert len(rank_data["rankings"]) == 0
