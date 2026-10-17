import streamlit as st
import requests
RENDER_API_URL = "https://resume-analyzer-api-7e26.onrender.com/"
st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="wide", initial_sidebar_state="collapsed")

# --- Custom CSS (Teal & Emerald Theme) ---
st.markdown("""
<style>
    .stApp { background-color: #F8FAFC; }
    .hero-title { font-size: 3rem; font-weight: 800; color: #0F172A; margin-bottom: 0rem; line-height: 1.2; }
    .hero-subtitle { font-size: 1.2rem; color: #475569; margin-bottom: 2rem; }
    [data-testid="stFileUploader"] { border: 2px dashed #14B8A6; border-radius: 12px; padding: 20px; background-color: #F0FDFA; }
    .stButton>button {
        background-color: #0F766E; color: white; border-radius: 8px; padding: 0.6rem 2rem;
        font-weight: 600; width: 100%; transition: all 0.3s ease;
    }
    .stButton>button:hover { background-color: #0D9488; border-color: #0D9488; transform: translateY(-2px); }
    .score-card {
        background-color: #FFFFFF; padding: 2rem; border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); text-align: center; border-top: 4px solid #10B981;
    }
    .score-number { font-size: 4rem; font-weight: 800; color: #0F172A; margin: 0; }
    .score-label { font-size: 1rem; color: #64748B; text-transform: uppercase; letter-spacing: 1px; }
    .evidence-card {
        background-color: #FFFFFF; padding: 1rem; border-radius: 8px; border-left: 4px solid #10B981;
        margin-bottom: 0.8rem; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    .evidence-skill { font-weight: 700; color: #0F172A; font-size: 1.05rem; margin-bottom: 0.2rem; }
    .evidence-quote { color: #475569; font-style: italic; font-size: 0.95rem; }
</style>
""", unsafe_allow_html=True)

# --- Layout: Hero Section ---
st.markdown('<div class="hero-title">Beat the ATS.<br>Land the Interview.</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">Upload your resume and paste the job description. Our AI analyzes the gap and gives you an evidence-based score.</div>', unsafe_allow_html=True)

# --- Layout: Split Screen ---
col1, col2 = st.columns([1, 1.2], gap="large")

# ================= LEFT COLUMN: INPUTS =================
with col1:
    st.markdown("### 1. Upload Resume")
    uploaded_file = st.file_uploader("Drop your resume here (PDF only)", type=["pdf"], label_visibility="collapsed")
    if uploaded_file:
        st.success(f"✅ Uploaded: {uploaded_file.name}")

    st.markdown("### 2. Paste Job Description")
    job_description = st.text_area(
        "Paste the full JD here...", height=250, 
        placeholder="We are looking for a Python Developer with experience in NLP, FastAPI...",
        label_visibility="collapsed"
    )
    
    analyze_btn = st.button("Analyze Match & Generate Report 🚀")

# ================= RIGHT COLUMN: RESULTS =================
with col2:
    if not analyze_btn:
        st.markdown("""
            <div style="background-color: #FFFFFF; padding: 3rem; border-radius: 16px; text-align: center; border: 1px dashed #CBD5E1;">
                <img src="https://cdn-icons-png.flaticon.com/512/3125/3125720.png" width="80" style="opacity: 0.5; margin-bottom: 1rem;">
                <h3 style="color: #64748B;">Your AI Report will appear here</h3>
                <p style="color: #94A3B8; font-size: 0.9rem;">Upload a resume, paste a JD, and click Analyze.</p>
            </div>
        """, unsafe_allow_html=True)

    if analyze_btn:
        if not uploaded_file or not job_description.strip():
            st.error("⚠️ Please upload a PDF resume and paste a job description first.")
        else:
            # 1. Parsing Resume
            with st.spinner("Extracting text from PDF..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    parse_res = requests.post(f"{RENDER_API_URL}/parse-resume", files=files)
                    if parse_res.status_code != 200:
                        st.error(f"Parsing Error: {parse_res.json().get('detail')}")
                        st.stop()
                    resume_text = parse_res.json()["resume_text"]
                except Exception as e:
                    st.error(f"Connection failed: {e}")
                    st.stop()

            # 2. Analyzing Match
            with st.spinner("AI is comparing your skills..."):
                try:
                    payload = {"resume_text": resume_text, "job_description": job_description}
                    analysis_res = requests.post(f"{RENDER_API_URL}/analyze-match", json=payload)
                    
                    # Catch backend errors (like API Key issues)
                    if analysis_res.status_code != 200:
                        error_detail = analysis_res.json().get("detail", "Unknown error")
                        st.error(f"Backend Error: {error_detail}")
                        st.stop()
                        
                    result = analysis_res.json()
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
                    st.stop()

            # 3. Displaying Results
            st.markdown(f"""
                <div class="score-card">
                    <p class="score-label">Overall Match Score</p>
                    <h1 class="score-number">{result['match_score']}<span style="font-size: 1.5rem; color: #94A3B8;">/100</span></h1>
                    <p style="color: #475569; margin-top: 0.5rem; font-size: 0.95rem;">{result['score_justification']}</p>
                </div>
                <br>
            """, unsafe_allow_html=True)

            tab1, tab2, tab3 = st.tabs(["✅ Matched Skills", "❌ Missing Skills", "💡 AI Suggestions"])

            with tab1:
                if result['matched_skills']:
                    for skill in result['matched_skills']:
                        st.markdown(f"""
                            <div class="evidence-card">
                                <div class="evidence-skill">✔ {skill['skill'].title()}</div>
                                <div class="evidence-quote">"{skill['evidence']}"</div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No matching skills found.")

                st.markdown("### Core Strengths")
                for strength in result['strengths']:
                    st.write(f"🌟 {strength}")

            with tab2:
                st.markdown("The job description requires these skills, but they were not found in your resume:")
                missing_html = ""
                for skill in result['missing_skills']:
                    color = "#FEE2E2" if skill['importance'] == 'critical' else "#FEF3C7"
                    text_color = "#991B1B" if skill['importance'] == 'critical' else "#92400E"
                    missing_html += f'<span style="background-color: {color}; color: {text_color}; padding: 6px 14px; border-radius: 16px; font-size: 0.9rem; font-weight: 600; display: inline-block; margin: 4px;">{skill["skill"].title()} ({skill["importance"]})</span>'
                st.markdown(missing_html, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                if result['red_flags']:
                    st.markdown("### 🚩 Red Flags / Areas of Concern")
                    for flag in result['red_flags']:
                        st.warning(flag)

            with tab3:
                st.markdown("### Tailored Action Plan")
                st.write("Here is exactly what you should change or highlight to tailor your resume for this specific role:")
                for suggestion in result['tailored_suggestions']:
                    st.info(f"💡 {suggestion}")