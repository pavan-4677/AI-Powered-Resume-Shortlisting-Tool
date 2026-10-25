import sqlite3
import json
import os
from config import Config

def get_db_connection():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        department TEXT DEFAULT '',
        min_experience REAL DEFAULT NULL,
        required_skills TEXT NOT NULL,
        description TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT DEFAULT '',
        email TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        experience_years REAL DEFAULT NULL,
        skills TEXT DEFAULT '[]',
        education TEXT DEFAULT '[]',
        projects TEXT DEFAULT '[]',
        raw_text TEXT DEFAULT '',
        filename TEXT NOT NULL,
        original_filename TEXT NOT NULL,
        file_type TEXT DEFAULT '',
        file_size INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS job_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        candidate_id INTEGER NOT NULL,
        overall_score REAL NOT NULL,
        indicator_tier TEXT DEFAULT 'Lower Match',
        semantic_score REAL NOT NULL,
        raw_tfidf REAL NOT NULL,
        skill_score REAL NOT NULL,
        experience_score REAL NOT NULL,
        experience_label TEXT DEFAULT '',
        qualification_score REAL NOT NULL,
        matched_skills TEXT DEFAULT '[]',
        missing_skills TEXT DEFAULT '[]',
        match_reasons TEXT DEFAULT '[]',
        status TEXT DEFAULT 'Under Review',
        recruiter_notes TEXT DEFAULT '',
        reviewed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE,
        FOREIGN KEY (candidate_id) REFERENCES candidates (id) ON DELETE CASCADE,
        UNIQUE(job_id, candidate_id)
    )
    """)
    
    conn.commit()
    conn.close()

def clear_all_data():
    """Wipes all jobs, candidates, evaluations, and uploads to provide an empty state."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM job_applications")
    cursor.execute("DELETE FROM candidates")
    cursor.execute("DELETE FROM jobs")
    conn.commit()
    conn.close()
    
    # Clean uploaded files
    if os.path.exists(Config.UPLOAD_FOLDER):
        for f in os.listdir(Config.UPLOAD_FOLDER):
            fpath = os.path.join(Config.UPLOAD_FOLDER, f)
            if os.path.isfile(fpath):
                try:
                    os.remove(fpath)
                except Exception:
                    pass

def get_latest_job():
    """Gets the most recently created or updated job description."""
    conn = get_db_connection()
    job = conn.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    if not job:
        return None
    d = dict(job)
    try:
        d["required_skills"] = json.loads(d["required_skills"])
    except Exception:
        d["required_skills"] = [s.strip() for s in d["required_skills"].split(",") if s.strip()]
    return d

def get_job_by_id(job_id):
    conn = get_db_connection()
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    if not job:
        return None
    d = dict(job)
    try:
        d["required_skills"] = json.loads(d["required_skills"])
    except Exception:
        d["required_skills"] = [s.strip() for s in d["required_skills"].split(",") if s.strip()]
    return d

def save_job(title, description, required_skills, min_experience, job_id=None):
    """Inserts or updates a user-provided job description."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    skills_json = json.dumps(required_skills if isinstance(required_skills, list) else [s.strip() for s in required_skills.split(",") if s.strip()])
    min_exp_val = float(min_experience) if min_experience is not None and str(min_experience).strip() != "" else None
    
    if job_id:
        cursor.execute("""
            UPDATE jobs SET
                title = ?, description = ?, required_skills = ?, min_experience = ?
            WHERE id = ?
        """, (title, description, skills_json, min_exp_val, job_id))
        target_id = job_id
    else:
        cursor.execute("""
            INSERT INTO jobs (title, description, required_skills, min_experience)
            VALUES (?, ?, ?, ?)
        """, (title, description, skills_json, min_exp_val))
        target_id = cursor.lastrowid
        
    conn.commit()
    conn.close()
    return target_id

def insert_or_update_candidate(candidate_data):
    """Saves candidate data without fabricating information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    original_fname = candidate_data.get("original_filename", "").strip()
    email = candidate_data.get("email", "").strip()
    
    # Check if candidate already exists by original_filename or email
    existing = None
    if original_fname:
        existing = cursor.execute("SELECT id FROM candidates WHERE original_filename = ?", (original_fname,)).fetchone()
    if not existing and email:
        existing = cursor.execute("SELECT id FROM candidates WHERE email = ?", (email,)).fetchone()
        
    exp_val = candidate_data.get("experience_years")
    if exp_val is not None:
        try:
            exp_val = float(exp_val)
        except (ValueError, TypeError):
            exp_val = None
            
    if existing:
        candidate_id = existing[0]
        cursor.execute("""
            UPDATE candidates SET
                name = ?, email = ?, phone = ?, experience_years = ?,
                skills = ?, education = ?, projects = ?, raw_text = ?,
                filename = ?, file_type = ?, file_size = ?
            WHERE id = ?
        """, (
            candidate_data.get("name", "").strip(),
            email,
            candidate_data.get("phone", "").strip(),
            exp_val,
            json.dumps(candidate_data.get("skills", [])),
            json.dumps(candidate_data.get("education", [])),
            json.dumps(candidate_data.get("projects", [])),
            candidate_data.get("raw_text", ""),
            candidate_data.get("filename", ""),
            candidate_data.get("file_type", ""),
            int(candidate_data.get("file_size") or 0),
            candidate_id
        ))
        conn.commit()
        conn.close()
        return candidate_id
        
    cursor.execute("""
        INSERT INTO candidates (
            name, email, phone, experience_years,
            skills, education, projects, raw_text,
            filename, original_filename, file_type, file_size
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        candidate_data.get("name", "").strip(),
        email,
        candidate_data.get("phone", "").strip(),
        exp_val,
        json.dumps(candidate_data.get("skills", [])),
        json.dumps(candidate_data.get("education", [])),
        json.dumps(candidate_data.get("projects", [])),
        candidate_data.get("raw_text", ""),
        candidate_data.get("filename", ""),
        original_fname,
        candidate_data.get("file_type", ""),
        int(candidate_data.get("file_size") or 0)
    ))
    candidate_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return candidate_id

def save_application_match(job_id, candidate_id, match_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO job_applications (
            job_id, candidate_id, overall_score, indicator_tier,
            semantic_score, raw_tfidf, skill_score, experience_score,
            experience_label, qualification_score, matched_skills,
            missing_skills, match_reasons, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(job_id, candidate_id) DO UPDATE SET
            overall_score = excluded.overall_score,
            indicator_tier = excluded.indicator_tier,
            semantic_score = excluded.semantic_score,
            raw_tfidf = excluded.raw_tfidf,
            skill_score = excluded.skill_score,
            experience_score = excluded.experience_score,
            experience_label = excluded.experience_label,
            qualification_score = excluded.qualification_score,
            matched_skills = excluded.matched_skills,
            missing_skills = excluded.missing_skills,
            match_reasons = excluded.match_reasons,
            status = excluded.status
    """, (
        job_id,
        candidate_id,
        round(match_data.get("overall_score", 0), 1),
        match_data.get("indicator_tier", "Lower Match"),
        round(match_data.get("semantic_score", 0), 1),
        round(match_data.get("raw_tfidf", 0), 1),
        round(match_data.get("skill_score", 0), 1),
        round(match_data.get("experience_score", 0), 1),
        match_data.get("experience_label", ""),
        round(match_data.get("qualification_score", 0), 1),
        json.dumps(match_data.get("matched_skills", [])),
        json.dumps(match_data.get("missing_skills", [])),
        json.dumps(match_data.get("evidence_reasons", [])),
        match_data.get("status", "Under Review")
    ))
    conn.commit()
    conn.close()

def get_job_rankings(job_id, min_score=0, search="", status_filter=""):
    conn = get_db_connection()
    query = """
        SELECT 
            ja.id as application_id,
            ja.job_id,
            ja.candidate_id,
            ja.overall_score,
            ja.indicator_tier,
            ja.semantic_score,
            ja.raw_tfidf,
            ja.skill_score,
            ja.experience_score,
            ja.experience_label,
            ja.qualification_score,
            ja.matched_skills,
            ja.missing_skills,
            ja.match_reasons,
            ja.status,
            ja.recruiter_notes,
            ja.reviewed_at,
            c.name,
            c.email,
            c.phone,
            c.experience_years,
            c.skills as candidate_skills,
            c.education,
            c.projects,
            c.filename,
            c.original_filename,
            c.file_type,
            c.file_size
        FROM job_applications ja
        JOIN candidates c ON ja.candidate_id = c.id
        WHERE ja.job_id = ?
    """
    params = [job_id]
    
    if min_score > 0:
        query += " AND ja.overall_score >= ?"
        params.append(min_score)
        
    query += " ORDER BY ja.overall_score DESC, ja.skill_score DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    
    results = []
    for r in rows:
        d = dict(r)
        d["matched_skills"] = json.loads(d["matched_skills"] or "[]")
        d["missing_skills"] = json.loads(d["missing_skills"] or "[]")
        d["match_reasons"] = json.loads(d["match_reasons"] or "[]")
        d["candidate_skills"] = json.loads(d["candidate_skills"] or "[]")
        d["education"] = json.loads(d["education"] or "[]")
        d["projects"] = json.loads(d["projects"] or "[]")
        
        # Candidate name display: only if reliably extracted
        raw_name = (d.get("name") or "").strip()
        d["display_name"] = raw_name if raw_name else "Name Not Detected"
        
        # Relevant experience label
        if d.get("experience_years") is not None:
            d["experience_display"] = f"{d['experience_years']:g} years"
        else:
            d["experience_display"] = "Not specified"
            
        # Filters
        if search:
            s_low = search.lower()
            name_hit = s_low in (d["display_name"]).lower()
            file_hit = s_low in (d["original_filename"] or "").lower()
            skill_hit = any(s_low in sk.lower() for sk in d["matched_skills"])
            if not (name_hit or file_hit or skill_hit):
                continue
                
        if status_filter and status_filter.lower() != "all":
            if d["status"].lower() != status_filter.lower():
                continue
                
        results.append(d)
        
    return results

def get_dashboard_stats(job_id=None):
    conn = get_db_connection()
    if job_id:
        total = conn.execute("SELECT COUNT(*) FROM job_applications WHERE job_id = ?", (job_id,)).fetchone()[0]
        shortlisted = conn.execute("SELECT COUNT(*) FROM job_applications WHERE job_id = ? AND status = 'Shortlisted'", (job_id,)).fetchone()[0]
        under_review = conn.execute("SELECT COUNT(*) FROM job_applications WHERE job_id = ? AND status = 'Under Review'", (job_id,)).fetchone()[0]
        avg_score = conn.execute("SELECT COALESCE(AVG(overall_score), 0) FROM job_applications WHERE job_id = ?", (job_id,)).fetchone()[0]
    else:
        total = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
        shortlisted = conn.execute("SELECT COUNT(*) FROM job_applications WHERE status = 'Shortlisted'").fetchone()[0]
        under_review = conn.execute("SELECT COUNT(*) FROM job_applications WHERE status = 'Under Review'").fetchone()[0]
        avg_score = conn.execute("SELECT COALESCE(AVG(overall_score), 0) FROM job_applications").fetchone()[0]
    conn.close()
    
    return {
        "total_resumes": total,
        "pending_review": under_review,
        "shortlisted": shortlisted,
        "avg_score": round(avg_score, 1)
    }

def update_application_status(app_id, status, notes=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if notes is not None:
        cursor.execute("""
            UPDATE job_applications
            SET status = ?, recruiter_notes = ?, reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, notes, app_id))
    else:
        cursor.execute("""
            UPDATE job_applications
            SET status = ?, reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, app_id))
    conn.commit()
    conn.close()
