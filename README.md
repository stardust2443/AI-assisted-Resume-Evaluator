# AI-Assisted Resume Evaluator

> **Evidence-based resume scoring powered by Gemini 2.5 Flash — every point awarded is backed by a verbatim quote from the resume.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render-46E3B7?style=for-the-badge)](https://ai-assisted-resume-evaluator.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)

---

## What it does

Upload a resume (PDF/DOCX/TXT) and a job description — get back a structured evaluation with:

| Output | Detail |
|---|---|
| **Score /100** | Rubric: Skills 25 · Experience 35 · Role Alignment 30 · Strengths 10 |
| **Evidence quotes** | Every sub-score backed by exact text from the resume |
| **SWOT analysis** | Strengths, Weaknesses, Opportunities, Threats |
| **Improvement tips** | Specific, actionable suggestions |
| **Batch compare** | Rank multiple candidates with percentile scores |

### Anti-gaming design
- Quote verification: scores without verbatim evidence are zeroed out
- Deterministic total: recomputed in code, never trusted from the LLM
- Keyword-stuffing detection built into the scoring prompt

---

## Architecture

```
Frontend (React + Vite)          Backend (FastAPI + Python)
────────────────────             ──────────────────────────
Upload page (Single/Compare)  →  POST /evaluate
Results page (Score + SWOT)   ←  JSON report
Compare page (Leaderboard)    →  POST /compare

                    LLM Layer (Gemini 2.5 Flash)
                    ────────────────────────────
                    parser/resume_parser.py   ← structured extraction
                    parser/jd_parser.py       ← requirements extraction
                    scoring/rubric.py         ← evidence-based scoring
                    scoring/validator.py      ← quote verification
                    reporting/report_generator.py ← SWOT + suggestions
```

---

## Running locally

```bash
# 1. Clone
git clone https://github.com/stardust2443/AI-assisted-Resume-Evaluator.git
cd AI-assisted-Resume-Evaluator

# 2. Install backend deps
pip install -r requirements.txt

# 3. Set your Gemini API key (get one free at aistudio.google.com)
echo "GEMINI_API_KEY=your_key_here" > .env

# 4. Build frontend
cd frontend && npm install && npm run build && cd ..

# 5. Start
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
# Open http://localhost:8000
```

---

## Tech stack

| Layer | Tech |
|---|---|
| LLM | Google Gemini 2.5 Flash (JSON mode) |
| Backend | FastAPI, Pydantic, pdfplumber, python-docx |
| Frontend | React 18, Vite, React Router |
| Hosting | Render.com (auto-deploy from GitHub) |

---

## Scoring rubric

```
Skill Match          25 pts  — exact match of required + preferred skills
Experience Depth     35 pts  — years, seniority, measurable impact
Role Alignment       30 pts  — responsibilities vs JD requirements  
Additional Strengths 10 pts  — projects, certifications, achievements
─────────────────────────────
Total               100 pts
```

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | ✅ | Get free at [aistudio.google.com](https://aistudio.google.com) |

**Never commit your `.env` file.** Set the key in Render dashboard → Environment.
