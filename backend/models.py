from pydantic import BaseModel, Field
from typing import List

class AnalyzeRequest(BaseModel):
    resume_text: str = Field(..., description="Raw text extracted from the resume")
    job_description: str = Field(..., description="The full job description text")

class MatchedSkill(BaseModel):
    skill: str
    evidence: str = Field(..., description="Exact quote or context from the resume")

class MissingSkill(BaseModel):
    skill: str
    importance: str = Field(..., description="critical | important | nice-to-have")

class AnalysisResult(BaseModel):
    match_score: int = Field(..., ge=0, le=100)
    score_justification: str
    matched_skills: List[MatchedSkill]
    missing_skills: List[MissingSkill]
    strengths: List[str]
    red_flags: List[str]
    tailored_suggestions: List[str]

class ParseResponse(BaseModel):
    resume_text: str
    word_count: int