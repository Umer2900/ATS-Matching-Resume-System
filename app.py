import streamlit as st
import zipfile
import io
import re
import PyPDF2
import pandas as pd
import time

# ---------------------------
# SKILL DATABASE
# ---------------------------
SKILLS_DB = [
    # Programming Languages
    "python", "java", "c++", "c", "c#", "javascript", "typescript", "go", "rust", "kotlin", "swift", "php", "ruby",

    # Web Development
    "html", "css", "bootstrap", "tailwind", "react", "angular", "vue", "node.js", "express.js", "next.js",

    # Databases
    "sql", "mysql", "postgresql", "mongodb", "oracle", "sqlite", "redis", "cassandra",

    # Data Science / Analytics
    "data analysis", "data visualization", "data mining", "pandas", "numpy", "scipy", "matplotlib", "seaborn",
    "power bi", "tableau", "excel", "statistics", "hypothesis testing",

    # Machine Learning / AI
    "machine learning", "deep learning", "nlp", "computer vision", "tensorflow", "keras", "pytorch",
    "scikit-learn", "xgboost", "lightgbm", "model deployment", "feature engineering",

    # Big Data
    "hadoop", "spark", "pyspark", "hive", "kafka",

    # Cloud Technologies
    "aws", "azure", "google cloud", "gcp", "cloud computing", "lambda", "ec2", "s3",

    # DevOps / Tools
    "docker", "kubernetes", "jenkins", "git", "github", "gitlab", "ci/cd",

    # Cyber Security
    "network security", "ethical hacking", "penetration testing", "cryptography", "firewalls", "vulnerability assessment",

    # Software Engineering Concepts
    "data structures", "algorithms", "object oriented programming", "oop", "system design",
    "design patterns", "api development", "rest api", "microservices",

    # Mobile Development
    "android", "ios", "flutter", "react native",

    # Testing
    "unit testing", "integration testing", "selenium", "pytest",

    # Soft Skills (important for ATS too)
    "communication", "teamwork", "problem solving", "leadership", "time management"
]

# ---------------------------
# JOB ROLE MAPPING (NEW)
# ---------------------------

ROLE_MAP = {

    "Data Analyst": [
        "excel", "sql", "power bi", "tableau", "data analysis",
        "statistics", "data visualization"
    ],

    "Data Scientist": [
        "python", "machine learning", "deep learning", "pandas",
        "numpy", "scikit-learn", "tensorflow", "nlp"
    ],

    "Web Developer": [
        "html", "css", "javascript", "react", "node.js",
        "express.js", "bootstrap", "tailwind"
    ],

    "Software Engineer": [
        "java", "c++", "python", "data structures",
        "algorithms", "oop", "system design"
    ],

    "Frontend Developer": [
        "html", "css", "javascript", "react", "angular",
        "vue", "tailwind", "bootstrap"
    ],

    "Backend Developer": [
        "node.js", "express.js", "python", "java",
        "sql", "mongodb", "api development", "microservices"
    ],

    "Full Stack Developer": [
        "html", "css", "javascript", "react", "node.js",
        "express.js", "mongodb", "sql"
    ],

    "DevOps Engineer": [
        "docker", "kubernetes", "jenkins", "aws",
        "azure", "ci/cd", "linux", "git"
    ],

    "Cloud Engineer": [
        "aws", "azure", "google cloud", "cloud computing",
        "lambda", "ec2", "s3"
    ],

    "Cyber Security Analyst": [
        "network security", "ethical hacking",
        "penetration testing", "cryptography",
        "vulnerability assessment"
    ],

    "Machine Learning Engineer": [
        "python", "machine learning", "deep learning",
        "tensorflow", "pytorch", "model deployment"
    ],

    "Business Analyst": [
        "excel", "sql", "data analysis",
        "communication", "problem solving"
    ]
}

# ---------------------------
# HELPERS
# ---------------------------
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.lower()

def extract_text_from_txt(file):
    return file.read().decode("utf-8").lower()

def extract_skills(text):
    found = []
    for skill in SKILLS_DB:
        if re.search(rf"\b{re.escape(skill)}\b", text):
            found.append(skill)
    return list(set(found))

def calculate_scores(jd_skills, resume_skills):
    if not jd_skills:
        return 0, 0
    matched = list(set(jd_skills) & set(resume_skills))
    score_percent = (len(matched) / len(jd_skills)) * 100
    score_10 = score_percent / 10
    return round(score_percent, 1), round(score_10, 1), matched

def get_missing_skills(jd_skills, resume_skills):
    return list(set(jd_skills) - set(resume_skills))

# ---------------------------
# NEW: ROLE SUGGESTION
# ---------------------------
def suggest_roles(skills):
    roles = []
    for role, req_skills in ROLE_MAP.items():
        match = len(set(skills) & set(req_skills))
        if match >= 2:
            roles.append(role)
    return roles if roles else ["General Role"]

# ---------------------------
# MAIN FUNCTION
# ---------------------------
def screen_resumes(zip_bytes, job_description):
    start_time = time.time()
    results = []
    filtered_files = []

    jd_skills = extract_skills(job_description.lower())

    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zip_ref:
        files = [f for f in zip_ref.namelist() if f.endswith((".pdf", ".txt"))]

        progress = st.progress(0)

        for i, file_name in enumerate(files):
            with zip_ref.open(file_name) as f:
                try:
                    file_bytes = f.read()
                    file_obj = io.BytesIO(file_bytes)

                    text = extract_text_from_pdf(file_obj) if file_name.endswith(".pdf") else extract_text_from_txt(file_obj)

                    resume_skills = extract_skills(text)

                    score_percent, score_10, matched = calculate_scores(jd_skills, resume_skills)
                    missing = get_missing_skills(jd_skills, resume_skills)

                    roles = suggest_roles(resume_skills)

                    status = "Passed" if score_10 >= 7 else "Rejected"

                    results.append({
                        "File": file_name,
                        "ATS %": f"{score_percent}%",
                        "Score (/10)": f"{score_10}",
                        "Status": status,
                        "Matched Skills": ", ".join(matched) if matched else "None",
                        "Missing Skills": ", ".join(missing) if missing else "None",
                        "Suggested Roles": ", ".join(roles)
                    })

                    if status == "Passed":
                        filtered_files.append((file_name, file_bytes, score_percent))

                except:
                    results.append({
                        "File": file_name,
                        "ATS %": "Error",
                        "Score (/10)": "-",
                        "Status": "Failed",
                        "Matched Skills": "-",
                        "Missing Skills": "-",
                        "Suggested Roles": "-"
                    })

            progress.progress((i + 1) / len(files))

    # ---------------------------
    # TOP 5 RESUMES (NEW)
    # ---------------------------
    top5 = sorted(filtered_files, key=lambda x: x[2], reverse=True)[:5]

    # Create ZIP
    output_zip = io.BytesIO()
    with zipfile.ZipFile(output_zip, "w") as out_zip:
        for name, data, _ in top5:
            out_zip.writestr(name, data)
    output_zip.seek(0)

    st.caption(f"⏱ Completed in {round(time.time() - start_time, 2)} sec")

    return results, output_zip, top5


# ---------------------------
# CORPORATE DASHBOARD UI 💼
# ---------------------------
st.set_page_config(layout="wide")

st.markdown("""
<style>
/* Background */
body {
    background-color: #f5f7fa;
    color: #1f2937;
}

/* Header */
h1 {
    color: #1e3a8a;
    font-weight: 700;
}

h2, h3 {
    color: #111827;
}

/* Inputs */
textarea, input {
    background-color: white !important;
    color: #111827 !important;
    border: 1px solid #d1d5db !important;
    border-radius: 8px !important;
}

/* Buttons */
.stButton>button {
    background-color: #1e40af;
    color: white;
    font-weight: 600;
    border-radius: 8px;
    padding: 10px;
    transition: 0.2s;
}
.stButton>button:hover {
    background-color: #1e3a8a;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    background-color: white;
    border-radius: 10px;
    border: 1px solid #e5e7eb;
}

/* Progress bar */
.stProgress > div > div > div {
    background-color: #2563eb;
}

/* Alerts */
.stAlert {
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# HEADER
# ---------------------------
st.markdown("""
<h1 style='text-align:center;'>Smart Resume Screening Dashboard</h1>
<p style='text-align:center; font-size:16px; color:#6b7280;'>
Efficient Candidate Screening • ATS-Based Matching • Recruiter Friendly
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ---------------------------
# STEP 1
# ---------------------------
st.subheader("📄 Step 1: Enter Job Description")

job_description = st.text_area(
    "Paste Job Description",
    height=180,
    placeholder="Enter job description with required skills..."
)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------
# STEP 2
# ---------------------------
st.subheader("📂 Step 2: Upload Resume ZIP")

zip_file = st.file_uploader(
    "Upload ZIP File",
    type=["zip"]
)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------
# STEP 3
# ---------------------------
if st.button("Start Screening", use_container_width=True):

    if not job_description.strip():
        st.error("Please enter Job Description")
    elif not zip_file:
        st.error("Please upload ZIP file")
    else:
        with st.spinner("Processing resumes..."):
            results, output_zip, top5 = screen_resumes(zip_file.read(), job_description)

        st.success("Screening Completed Successfully")

        # ---------------------------
        # RESULTS
        # ---------------------------
        st.markdown("---")
        st.subheader("📊 Screening Results")

        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)

        # ---------------------------
        # STATS
        # ---------------------------
        total = len(df)
        passed = df[df["Status"] == "Passed"].shape[0]
        rejected = df[df["Status"] == "Rejected"].shape[0]

        st.info(f"Total Candidates: {total} | Passed: {passed} | Rejected: {rejected}")

        # ---------------------------
        # TOP 5
        # ---------------------------
        st.markdown("---")
        st.subheader("🏆 Top Candidates")

        if top5:
            for i, (name, _, score) in enumerate(top5, 1):
                st.success(f"{i}. {name} — {round(score,1)}% Match")
        else:
            st.warning("No strong candidates found.")

        # ---------------------------
        # DOWNLOAD
        # ---------------------------
        if top5:
            st.download_button(
                "Download Top Candidates",
                data=output_zip,
                file_name="top_candidates.zip",
                mime="application/zip",
                use_container_width=True
            )