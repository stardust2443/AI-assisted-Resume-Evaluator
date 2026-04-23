"""
reporting/report_generator.py — SWOT analysis + improvement suggestions via LLM.
Uses llm.client — provider-agnostic.
"""

import logging
from textwrap import dedent

from llm.client import complete_json
from config import settings
from data_models import (
    ParsedResume,
    JDRequirements,
    RubricEvaluation,
    SWOTAnalysis,
    CandidateReport,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SWOT Analysis
# ---------------------------------------------------------------------------

def _build_swot_prompt(
    resume: ParsedResume, jd: JDRequirements, evaluation: RubricEvaluation
) -> str:
    return dedent(f"""
        You are evaluating {resume.candidate_name} for the role of {jd.role_title}.

        VALIDATED SCORES:
        - Skill Match: {evaluation.skill_match.score}/25 — {evaluation.skill_match.reasoning}
        - Experience Depth: {evaluation.experience_depth.score}/35 — {evaluation.experience_depth.reasoning}
        - Role Alignment: {evaluation.role_alignment.score}/30 — {evaluation.role_alignment.reasoning}
        - Additional Strengths: {evaluation.additional_strengths.score}/10 — {evaluation.additional_strengths.reasoning}
        - Total: {evaluation.total_score}/100

        JD Required Skills: {', '.join(jd.required_skills) or 'not specified'}
        JD Preferred Skills: {', '.join(jd.preferred_skills) or 'not specified'}
        Candidate Skills: {', '.join(resume.skills) or 'none listed'}

        Produce a SWOT analysis for this candidate relative to this specific JD.
        Be specific and evidence-based. No generic advice.

        Return ONLY valid JSON:
        {{
          "strengths": ["<specific strength>"],
          "weaknesses": ["<specific gap vs JD>"],
          "opportunities": ["<potential if hired>"],
          "threats": ["<risk for employer>"]
        }}

        Rules:
        - Each point must be specific to this candidate and this JD (not generic).
        - weaknesses must reference actual JD requirements missing from the resume.
        - Aim for 2-4 items per category.
    """).strip()


def generate_swot(
    resume: ParsedResume, jd: JDRequirements, evaluation: RubricEvaluation
) -> SWOTAnalysis:
    logger.info("Generating SWOT for '%s'", resume.candidate_name)

    data = complete_json(
        system=(
            "You are a sharp talent assessor. You produce specific, evidence-backed "
            "SWOT analyses based on validated resume evaluation data."
        ),
        user=_build_swot_prompt(resume, jd, evaluation),
        max_tokens=settings.llm.max_tokens_report,
        temperature=0.2,
    )

    return SWOTAnalysis(
        strengths=data.get("strengths", []),
        weaknesses=data.get("weaknesses", []),
        opportunities=data.get("opportunities", []),
        threats=data.get("threats", []),
    )


# ---------------------------------------------------------------------------
# Improvement Suggestions
# ---------------------------------------------------------------------------

def _build_suggestions_prompt(
    resume: ParsedResume, jd: JDRequirements, evaluation: RubricEvaluation
) -> str:
    missing_required = [s for s in jd.required_skills if s not in resume.skills]

    return dedent(f"""
        Candidate: {resume.candidate_name}
        Role applied for: {jd.role_title}
        Total score: {evaluation.total_score}/100

        Skills required by JD but NOT found in resume:
        {', '.join(missing_required) if missing_required else 'None — candidate appears to have all required skills'}

        Score breakdown:
        - Skill Match: {evaluation.skill_match.score}/25
        - Experience Depth: {evaluation.experience_depth.score}/35
        - Role Alignment: {evaluation.role_alignment.score}/30
        - Additional Strengths: {evaluation.additional_strengths.score}/10

        Lowest-scoring sections with reasoning:
        {_lowest_sections(evaluation)}

        Generate 4-6 specific, actionable improvement suggestions for this candidate
        to strengthen their profile for this specific role.
        Focus on the biggest gaps first. Do NOT give generic resume advice.

        Return ONLY valid JSON:
        {{
          "suggestions": ["<actionable suggestion>"]
        }}
    """).strip()


def _lowest_sections(evaluation: RubricEvaluation) -> str:
    sections = [
        ("skill_match", evaluation.skill_match),
        ("experience_depth", evaluation.experience_depth),
        ("role_alignment", evaluation.role_alignment),
        ("additional_strengths", evaluation.additional_strengths),
    ]
    sorted_sections = sorted(sections, key=lambda x: x[1].score)
    return "\n".join(
        f"- {name}: {s.score} pts — {s.reasoning}" for name, s in sorted_sections[:2]
    )


def generate_suggestions(
    resume: ParsedResume, jd: JDRequirements, evaluation: RubricEvaluation
) -> list[str]:
    logger.info("Generating suggestions for '%s'", resume.candidate_name)

    data = complete_json(
        system=(
            "You are a career coach specializing in helping candidates close specific "
            "skill and experience gaps for target roles. Be concrete and actionable."
        ),
        user=_build_suggestions_prompt(resume, jd, evaluation),
        max_tokens=settings.llm.max_tokens_report,
        temperature=0.2,
    )

    return data.get("suggestions", [])


# ---------------------------------------------------------------------------
# Full Report Assembly
# ---------------------------------------------------------------------------

def generate_report(
    resume: ParsedResume,
    jd: JDRequirements,
    evaluation: RubricEvaluation,
) -> CandidateReport:
    """Assemble the full CandidateReport from validated evaluation data."""
    swot = generate_swot(resume, jd, evaluation)
    suggestions = generate_suggestions(resume, jd, evaluation)

    return CandidateReport(
        candidate_name=resume.candidate_name,
        evaluation=evaluation,
        swot=swot,
        suggestions_for_improvement=suggestions,
    )
