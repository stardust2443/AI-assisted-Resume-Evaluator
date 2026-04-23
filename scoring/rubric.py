"""
scoring/rubric.py — Scoring engine: builds prompts, calls LLM, enforces explainability.
Uses llm.client — provider-agnostic.

Design principles:
- Prompt injects raw resume text so the LLM can pull verbatim quotes
- total_score from LLM is IGNORED — recomputed deterministically by validator
- Temperature = 0.0 for scoring (consistency-critical)
"""

import logging
from textwrap import dedent

from llm.client import complete_json
from config import settings, RUBRIC_WEIGHTS
from data_models import ParsedResume, JDRequirements, RubricEvaluation, EvidenceScore

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt Construction
# ---------------------------------------------------------------------------

# Max chars of raw resume text to include — avoids bloating output with huge resumes
_MAX_RESUME_TEXT_CHARS = 3500


def build_scoring_prompt(resume: ParsedResume, jd: JDRequirements) -> str:
    """
    Build the user-turn scoring prompt.
    Raw resume text is capped at _MAX_RESUME_TEXT_CHARS to prevent output token overflow.
    Reasoning is instructed to be 1-2 sentences; quotes limited to 2 per section.
    """
    skills_list = ", ".join(resume.skills) if resume.skills else "none listed"
    required_skills = ", ".join(jd.required_skills) if jd.required_skills else "not specified"
    preferred_skills = ", ".join(jd.preferred_skills) if jd.preferred_skills else "not specified"

    experience_summary = "\n".join(
        f"- {e.title} at {e.company} ({e.start_date or '?'} to {e.end_date or 'Present'})"
        for e in resume.work_experience
    ) or "No experience listed"

    responsibilities = "\n".join(
        f"- {r}" for r in jd.key_responsibilities
    ) or "Not specified"

    return dedent(f"""
        ## JOB DESCRIPTION REQUIREMENTS
        Role: {jd.role_title} ({jd.seniority_level or 'unspecified seniority'})
        Required Skills: {required_skills}
        Preferred Skills: {preferred_skills}
        Min Experience: {jd.min_years_experience or 'not specified'} years
        Key Responsibilities:
        {responsibilities}

        ## CANDIDATE PROFILE SUMMARY
        Name: {resume.candidate_name}
        Skills: {skills_list}
        Experience:
        {experience_summary}
        Certifications: {', '.join(resume.certifications) or 'none'}
        Awards: {', '.join(resume.awards_and_achievements) or 'none'}
        Projects: {', '.join(p.name for p in resume.projects) or 'none'}

        ## RESUME TEXT (for verbatim quotes — first {_MAX_RESUME_TEXT_CHARS} chars)
        ---
        {resume.raw_text[:_MAX_RESUME_TEXT_CHARS]}
        ---

        ## SCORING INSTRUCTIONS
        Score the candidate on EXACTLY these 4 sections.
        Rules (CRITICAL — follow precisely to avoid token overflow):
        1. reasoning: MAXIMUM 2 sentences. Be direct and specific.
        2. evidence_quotes: MAXIMUM 2 short quotes per section (each under 120 chars).
        3. If no quote exists for a point, award 0 for that section.
        4. Do NOT reward keyword stuffing — check for real depth and measurable impact.
        5. Do NOT award points for job titles without supporting responsibilities.

        Rubric max points:
        - skill_match: {RUBRIC_WEIGHTS['skill_match']} points
        - experience_depth: {RUBRIC_WEIGHTS['experience_depth']} points
        - role_alignment: {RUBRIC_WEIGHTS['role_alignment']} points
        - additional_strengths: {RUBRIC_WEIGHTS['additional_strengths']} points

        Return ONLY this JSON (no markdown, no extra text):
        {{
          "skill_match": {{"score": <int 0-{RUBRIC_WEIGHTS['skill_match']}>, "reasoning": "<max 2 sentences>", "evidence_quotes": ["<short quote>", "<short quote>"]}},
          "experience_depth": {{"score": <int 0-{RUBRIC_WEIGHTS['experience_depth']}>, "reasoning": "<max 2 sentences>", "evidence_quotes": ["<short quote>", "<short quote>"]}},
          "role_alignment": {{"score": <int 0-{RUBRIC_WEIGHTS['role_alignment']}>, "reasoning": "<max 2 sentences>", "evidence_quotes": ["<short quote>", "<short quote>"]}},
          "additional_strengths": {{"score": <int 0-{RUBRIC_WEIGHTS['additional_strengths']}>, "reasoning": "<max 2 sentences>", "evidence_quotes": ["<short quote>", "<short quote>"]}},
          "total_score": <int>
        }}
    """).strip()


_SCORING_SYSTEM = dedent("""\
    You are a rigorous, unbiased resume evaluator.
    You evaluate candidates against job descriptions using a strict evidence-based rubric.
    Every point you award MUST be backed by a direct, verbatim quote from the resume text.
    You never guess, hallucinate, or infer skills that are not explicitly stated.
    You never reward keyword stuffing or inflated job titles without supporting evidence.
    Return ONLY valid JSON. No markdown, no explanations outside JSON.
""")


# ---------------------------------------------------------------------------
# Scoring Entry Point
# ---------------------------------------------------------------------------

def score_candidate(resume: ParsedResume, jd: JDRequirements) -> RubricEvaluation:
    """
    Call the LLM to score the candidate against the JD.
    The returned total_score is a placeholder — validator will recompute it.
    """
    prompt = build_scoring_prompt(resume, jd)
    logger.info("Scoring '%s' for '%s'", resume.candidate_name, jd.role_title)

    data = complete_json(
        system=_SCORING_SYSTEM,
        user=prompt,
        max_tokens=settings.llm.max_tokens_score,
        temperature=0.0,
    )

    def parse_section(key: str) -> EvidenceScore:
        section = data.get(key, {})
        return EvidenceScore(
            score=int(section.get("score", 0)),
            reasoning=section.get("reasoning", "No reasoning provided"),
            evidence_quotes=section.get("evidence_quotes", []),
        )

    return RubricEvaluation(
        skill_match=parse_section("skill_match"),
        experience_depth=parse_section("experience_depth"),
        role_alignment=parse_section("role_alignment"),
        additional_strengths=parse_section("additional_strengths"),
        total_score=int(data.get("total_score", 0)),  # placeholder — recomputed by validator
    )
