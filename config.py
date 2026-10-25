import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "ai-resume-shortlisting-secure-key-2026")
    DATABASE_PATH = os.path.join(BASE_DIR, "resume_tool.db")
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB maximum file size limit
    ALLOWED_EXTENSIONS = {"pdf", "docx"}
    
    # Transparent AI Scoring Weights (Normalized to 1.0)
    # - 35% Semantic Relevance (TF-IDF Cosine Similarity with User's JD)
    # - 35% Required Skills Match (Specific User-Entered Skills or Extracted Technical Terms)
    # - 15% Relevant Experience (Alignment with User-Specified Minimum Years)
    # - 15% Education, Projects & Responsibility Depth
    WEIGHT_SEMANTIC = 0.35
    WEIGHT_SKILLS = 0.35
    WEIGHT_EXPERIENCE = 0.15
    WEIGHT_QUALIFICATIONS = 0.15
