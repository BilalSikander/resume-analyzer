import os
import re
from typing import List, Dict

import spacy
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = None
    print("⚠️ spaCy model 'en_core_web_sm' not found. Run: python -m spacy download en_core_web_sm")

SKILL_KEYWORDS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "sql", "nosql", "mongodb", "postgresql", "mysql", "redis",
    "fastapi", "flask", "django", "streamlit", "react", "node.js", "express",
    "docker", "kubernetes", "aws", "azure", "gcp", "terraform",
    "machine learning", "deep learning", "nlp", "computer vision",
    "pytorch", "tensorflow", "scikit-learn", "pandas", "numpy",
    "llm", "openai", "langchain", "rag", "prompt engineering",
    "git", "github", "ci/cd", "jenkins", "github actions",
    "agile", "scrum", "jira", "rest api", "graphql", "microservices",
]

# --- Pydantic Schema for Gemini Structured Output ---
class MatchedSkill(BaseModel):
    skill: str = Field(description="Skill from the job description")
    evidence: str = Field(description="Exact quote from the resume showing this skill")

class MissingSkill(BaseModel):
    skill: str = Field(description="Skill required by the job description but absent from the resume")
    importance: str = Field(description="critical | important | nice-to-have")

class AnalysisResult(BaseModel):
    match_score: int = Field(ge=0, le=100, description="Overall match score from 0 to 100")
    score_justification: str = Field(description="1-2 sentence explanation of the score")
    matched_skills: List[MatchedSkill] = Field(description="Skills found in both resume and JD")
    missing_skills: List[MissingSkill] = Field(description="Skills required by JD but missing from resume")
    strengths: List[str] = Field(description="Specific strengths of this candidate for this role")
    red_flags: List[str] = Field(description="Potential concerns, e.g., missing certifications")
    tailored_suggestions: List[str] = Field(description="Specific, actionable advice for the candidate")

def extract_skills_rule_based(text: str) -> List[str]:
    text_lower = text.lower()
    found = set()
    for skill in SKILL_KEYWORDS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.add(skill)
    return sorted(found)

def build_prompt(resume_text: str, job_description: str) -> str:
    return f"""You are an expert technical recruiter and hiring manager.
Analyze the RESUME against the JOB DESCRIPTION below.

Your job is to produce an evidence-based gap report. Be specific and quote
actual text from the resume as evidence. Do not invent skills or experience.

=== JOB DESCRIPTION ===
{job_description}

=== RESUME ===
{resume_text}

Rules:
- match_score must reflect actual overlap, not optimism.
- Only list matched_skills you can back with a quote from the resume.
- missing_skills must come from the JD, not from your own assumptions.
- If the resume is completely unrelated, score below 20.
"""

def analyze_with_llm(resume_text: str, job_description: str) -> Dict:
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key or api_key.startswith("your-"):
        # FALLBACK: Rule-based only
        resume_skills = set(extract_skills_rule_based(resume_text))
        jd_skills = set(extract_skills_rule_based(job_description))
        matched = resume_skills & jd_skills
        missing = jd_skills - resume_skills
        score = int((len(matched) / len(jd_skills) * 100)) if jd_skills else 0

        return {
            "match_score": score,
            "score_justification": "Rule-based score (no LLM API key configured).",
            "matched_skills": [{"skill": s, "evidence": "Found in resume (keyword match)."} for s in matched],
            "missing_skills": [{"skill": s, "importance": "important"} for s in missing],
            "strengths": [f"Demonstrates experience with {s}" for s in list(matched)[:5]],
            "red_flags": ["LLM analysis disabled — no API key configured."],
            "tailored_suggestions": [f"Consider highlighting or learning: {s}" for s in list(missing)[:5]],
        }

    # PRIMARY: Gemini LLM analysis
    try:
        client = genai.Client(api_key=api_key)
        prompt = build_prompt(resume_text, job_description)

        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AnalysisResult,
                temperature=0.2,
            ),
        )

        # Gemini returns the structured data in response.parsed
        return response.parsed.model_dump()

    except Exception as e:
        print(f"❌ Gemini API Error: {str(e)}")
        raise Exception(f"AI Service Error: {str(e)}")