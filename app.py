import os
import io
import csv
import uuid
import json
from flask import (
    Flask, render_template, request, jsonify, 
    send_from_directory, Response
)
from werkzeug.utils import secure_filename

from config import Config
from database import (
    init_db, clear_all_data, get_latest_job, get_job_by_id,
    save_job, insert_or_update_candidate, save_application_match,
    get_job_rankings, get_dashboard_stats, update_application_status,
    get_db_connection
)
from parser import parse_resume
from matcher import evaluate_resume

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Initialize database schema
init_db()

def allowed_file(filename):
    """Check if file extension is an allowed document type."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route("/")
def index():
    """Serves the main recruiter dashboard."""
    return render_template("index.html")

# ----------------- RECRUITER WORKFLOW ENDPOINTS ----------------- #

@app.route("/api/active-job", methods=["GET"])
def get_active_job():
    """Returns the user's active job description, or null if empty."""
    try:
        job = get_latest_job()
        return jsonify({"success": True, "job": job})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/analyze", methods=["POST"])
def analyze_resumes():
    """
    Main Workflow Endpoint:
    1. Receives user-provided Job Title, Job Description, Required Skills, Min Experience.
    2. Receives uploaded resumes (PDF / DOCX).
    3. Validates inputs.
    4. Extracts text and real candidate entities (no fake data).
    5. Evaluates each resume against the user's actual JD using TF-IDF & weighted matching.
    6. Returns candidates ranked in descending score order.
    """
    try:
        job_title = request.form.get("job_title", "").strip()
        job_description = request.form.get("job_description", "").strip()
        required_skills_str = request.form.get("required_skills", "").strip()
        min_experience_str = request.form.get("min_experience", "").strip()
        
        # 1. Validate Job Details
        if not job_title:
            return jsonify({
                "success": False, 
                "error": "Validation Error: Please enter the Job Role / Job Title."
            }), 400
            
        if not job_description:
            return jsonify({
                "success": False, 
                "error": "Validation Error: Please provide the full Job Description (JD)."
            }), 400
            
        required_skills = [s.strip() for s in required_skills_str.split(",") if s.strip()]
        min_experience = float(min_experience_str) if min_experience_str else None
        
        # 2. Check for Resumes
        uploaded_files = request.files.getlist("resumes")
        has_new_files = uploaded_files and len(uploaded_files) > 0 and uploaded_files[0].filename != ""
        
        # Check if existing candidates exist in DB
        conn = get_db_connection()
        existing_candidate_count = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
        conn.close()
        
        if not has_new_files and existing_candidate_count == 0:
            return jsonify({
                "success": False,
                "error": "Validation Error: Please upload at least one candidate resume (PDF or DOCX)."
            }), 400
            
        # 3. Save or update the active job
        existing_job = get_latest_job()
        job_id = save_job(
            title=job_title,
            description=job_description,
            required_skills=required_skills,
            min_experience=min_experience,
            job_id=existing_job["id"] if existing_job else None
        )
        current_job = get_job_by_id(job_id)
        
        # 4. Process new uploaded files
        file_errors = []
        newly_processed = 0
        
        if has_new_files:
            for file in uploaded_files:
                original_filename = file.filename
                if not original_filename:
                    continue
                    
                if not allowed_file(original_filename):
                    file_errors.append({
                        "filename": original_filename,
                        "error": "Unsupported file format. Please upload .pdf or .docx only."
                    })
                    continue
                    
                safe_base = secure_filename(original_filename)
                unique_name = f"{uuid.uuid4().hex[:8]}_{safe_base}"
                saved_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
                
                try:
                    file.save(saved_path)
                    candidate_profile = parse_resume(saved_path, original_filename)
                    candidate_profile["filename"] = unique_name
                    insert_or_update_candidate(candidate_profile)
                    newly_processed += 1
                except Exception as e:
                    if os.path.exists(saved_path):
                        try:
                            os.remove(saved_path)
                        except Exception:
                            pass
                    file_errors.append({
                        "filename": original_filename,
                        "error": f"Extraction error: {str(e)}"
                    })
                    
        # 5. Evaluate all candidates against the user's current job description
        conn = get_db_connection()
        candidates = conn.execute("SELECT * FROM candidates").fetchall()
        conn.close()
        
        for cand_row in candidates:
            cand = dict(cand_row)
            try:
                cand["skills"] = json.loads(cand["skills"] or "[]")
                cand["education"] = json.loads(cand["education"] or "[]")
                cand["projects"] = json.loads(cand["projects"] or "[]")
            except Exception:
                cand["skills"] = []
                cand["education"] = []
                cand["projects"] = []
                
            eval_result = evaluate_resume(current_job, cand)
            save_application_match(job_id, cand["id"], eval_result)
            
        # 6. Retrieve ranked candidates in descending order
        rankings = get_job_rankings(job_id)
        stats = get_dashboard_stats(job_id)
        
        return jsonify({
            "success": True,
            "message": f"Successfully analyzed {len(rankings)} candidate resume(s).",
            "job": current_job,
            "rankings": rankings,
            "stats": stats,
            "file_errors": file_errors
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/reanalyze", methods=["POST"])
def reanalyze_candidates():
    """Re-analyzes all currently uploaded resumes when the user modifies the JD or requirements."""
    try:
        data = request.get_json() or {}
        job_title = data.get("job_title", "").strip()
        job_description = data.get("job_description", "").strip()
        required_skills = data.get("required_skills", [])
        min_experience = data.get("min_experience")
        
        if not job_title or not job_description:
            return jsonify({
                "success": False, 
                "error": "Validation Error: Job Title and Job Description are required."
            }), 400
            
        existing_job = get_latest_job()
        job_id = save_job(
            title=job_title,
            description=job_description,
            required_skills=required_skills,
            min_experience=min_experience,
            job_id=existing_job["id"] if existing_job else None
        )
        current_job = get_job_by_id(job_id)
        
        conn = get_db_connection()
        candidates = conn.execute("SELECT * FROM candidates").fetchall()
        conn.close()
        
        if not candidates:
            return jsonify({
                "success": False,
                "error": "No resumes currently uploaded. Please upload candidate resumes first."
            }), 400
            
        for cand_row in candidates:
            cand = dict(cand_row)
            try:
                cand["skills"] = json.loads(cand["skills"] or "[]")
                cand["education"] = json.loads(cand["education"] or "[]")
                cand["projects"] = json.loads(cand["projects"] or "[]")
            except Exception:
                cand["skills"] = []
                cand["education"] = []
                cand["projects"] = []
                
            eval_result = evaluate_resume(current_job, cand)
            save_application_match(job_id, cand["id"], eval_result)
            
        rankings = get_job_rankings(job_id)
        stats = get_dashboard_stats(job_id)
        
        return jsonify({
            "success": True,
            "message": "Resumes re-analyzed against updated Job Description.",
            "job": current_job,
            "rankings": rankings,
            "stats": stats
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/rankings", methods=["GET"])
def fetch_rankings():
    """Returns candidate rankings for active job with live search and score filters."""
    try:
        job = get_latest_job()
        if not job:
            return jsonify({
                "success": True,
                "has_job": False,
                "rankings": [],
                "stats": {"total_resumes": 0, "pending_review": 0, "shortlisted": 0, "avg_score": 0}
            })
            
        min_score = float(request.args.get("min_score", 0))
        search = request.args.get("search", "").strip()
        status = request.args.get("status", "").strip()
        
        rankings = get_job_rankings(job["id"], min_score, search, status)
        stats = get_dashboard_stats(job["id"])
        
        return jsonify({
            "success": True,
            "has_job": True,
            "job": job,
            "rankings": rankings,
            "stats": stats
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/application/<int:app_id>/status", methods=["POST"])
def update_status(app_id):
    """Updates candidate status or notes."""
    try:
        data = request.get_json() or {}
        new_status = data.get("status", "Under Review")
        notes = data.get("notes")
        update_application_status(app_id, new_status, notes)
        return jsonify({"success": True, "message": "Candidate status updated."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/clear", methods=["POST"])
def reset_workspace():
    """Wipes all uploaded resumes and job descriptions to provide a completely blank state."""
    try:
        clear_all_data()
        return jsonify({
            "success": True, 
            "message": "All uploaded resumes and analysis data cleared successfully."
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/export", methods=["GET"])
def export_csv():
    """Exports candidate shortlisting results as CSV."""
    try:
        job = get_latest_job()
        if not job:
            return jsonify({"success": False, "error": "No job analysis found to export."}), 400
            
        rankings = get_job_rankings(job["id"])
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            "Rank",
            "Candidate Name",
            "Resume Filename",
            "Overall Match Score (%)",
            "Match Tier",
            "Matched Skills",
            "Missing Skills",
            "Relevant Experience",
            "Semantic Relevance (%)",
            "Review Status",
            "Recruiter Notes"
        ])
        
        for idx, cand in enumerate(rankings, 1):
            writer.writerow([
                idx,
                cand.get("display_name", "Name Not Detected"),
                cand.get("original_filename", ""),
                f"{cand.get('overall_score', 0)}%",
                cand.get("indicator_tier", "Lower Match"),
                ", ".join(cand.get("matched_skills", [])),
                ", ".join(cand.get("missing_skills", [])),
                cand.get("experience_display", "Not specified"),
                f"{cand.get('semantic_score', 0)}%",
                cand.get("status", "Under Review"),
                cand.get("recruiter_notes", "")
            ])
            
        csv_content = output.getvalue()
        output.close()
        
        safe_title = secure_filename(job["title"].replace(" ", "_"))
        return Response(
            csv_content,
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=Candidate_Rankings_{safe_title}.csv"
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/download/<filename>", methods=["GET"])
def download_resume(filename):
    """Safely serves uploaded resume files for recruiter review."""
    safe_name = secure_filename(filename)
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        safe_name,
        as_attachment=True
    )

@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Returns dashboard statistics (0 if empty)."""
    try:
        job = get_latest_job()
        jid = job["id"] if job else None
        stats = get_dashboard_stats(jid)
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
