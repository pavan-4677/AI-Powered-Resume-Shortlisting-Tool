import pytest
from parser import (
    extract_email, extract_phone, extract_name, 
    extract_skills, extract_experience_years, extract_education
)

SAMPLE_RESUME_TEXT = """
Sarah Jenkins
Email: sarah.jenkins@techmail.org
Phone: (555) 234-5678
Location: New York, NY

Summary:
Full stack developer with 5 years of experience building scalable web applications.

Skills:
Python, Flask, React, Docker, PostgreSQL, Git, JavaScript, CI/CD, AWS

Experience:
Senior Developer (2020 - Present)
- Architected REST APIs using Flask and Python.
- Containerized microservices using Docker.

Junior Developer (2018 - 2020)
- Built interactive frontend applications with React and JavaScript.

Education:
Bachelor of Technology in Computer Science (2018)
State University of New York
"""

def test_extract_email():
    email = extract_email(SAMPLE_RESUME_TEXT)
    assert email == "sarah.jenkins@techmail.org"

def test_extract_phone():
    phone = extract_phone(SAMPLE_RESUME_TEXT)
    assert "234" in phone and "5678" in phone

def test_extract_name_reliable():
    name = extract_name(SAMPLE_RESUME_TEXT)
    assert name == "Sarah Jenkins"

def test_extract_name_returns_empty_when_unreliable():
    unreliable_text = "Curriculum Vitae\nsoftware engineer\n555-123-4567\nSummary of skills\nPython, Docker"
    name = extract_name(unreliable_text)
    # Must NOT invent a fake candidate name
    assert name == ""

def test_extract_skills():
    skills = extract_skills(SAMPLE_RESUME_TEXT)
    assert "python" in skills
    assert "flask" in skills
    assert "react" in skills
    assert "docker" in skills
    assert "postgresql" in skills

def test_extract_experience_years():
    years = extract_experience_years(SAMPLE_RESUME_TEXT)
    assert years is not None
    assert years >= 4.0

def test_extract_education():
    education = extract_education(SAMPLE_RESUME_TEXT)
    assert len(education) > 0
    assert any("TECHNOLOGY" in edu or "B.TECH" in edu or "Bachelor" in edu for edu in education)
