from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from parser import extract_text_from_pdf
from analyzer import analyze_with_llm, extract_skills_rule_based
from models import AnalyzeRequest, AnalysisResult, ParseResponse

app = FastAPI(
    title="AI Resume Analyzer & Job Matcher",
    description="Evidence-based gap analysis between a resume and a job description.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Resume Analyzer API is running 🚀"}

@app.post("/parse-resume", response_model=ParseResponse)
async def parse_resume(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    try:
        pdf_bytes = await file.read()
        text = extract_text_from_pdf(pdf_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {e}")
    if not text:
        raise HTTPException(status_code=422, detail="No text could be extracted from the PDF.")
    return ParseResponse(resume_text=text, word_count=len(text.split()))

@app.post("/analyze-match", response_model=AnalysisResult)
async def analyze_match(payload: AnalyzeRequest):
    if not payload.resume_text.strip() or not payload.job_description.strip():
        raise HTTPException(status_code=400, detail="Both resume and job description are required.")
    try:
        result = analyze_with_llm(payload.resume_text, payload.job_description)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return result

@app.post("/extract-skills")
async def extract_skills(payload: AnalyzeRequest):
    return {
        "resume_skills": extract_skills_rule_based(payload.resume_text),
        "jd_skills": extract_skills_rule_based(payload.job_description),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)