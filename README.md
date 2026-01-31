# AI-Assisted Technical Interview Companion

A web-based interview companion that standardizes question flow, structured notes, skill scoring, and summary generation for technical interviews.

This README consolidates the product spec, architecture, requirements, test coverage, and roadmap from:
- [PRODUCT_SPEC.md](PRODUCT_SPEC.md)
- [SRS.md](SRS.md)
- [architecture.md](architecture.md)
- [project_plan.md](project_plan.md)
- [tests.md](tests.md)
- [what-next.md](what-next.md)
- [llm.md](llm.md)

## Overview
The app helps interviewers run consistent technical interviews, capture structured evidence, and generate standardized summaries with a hire recommendation. It is built with Flask, SQLite, and SQLAlchemy, with a lightweight HTML/CSS/JS frontend.

## Goals
- Standardize questions and scoring per role/skill.
- Reduce interviewer cognitive load during live interviews.
- Produce clear, editable summaries with evidence-based rationale.
- Minimize bias with structured inputs and rubric-based scoring.

## Non-goals
- Automated candidate rejection or autonomous decisions.
- Personality/emotion/voice/video analysis.
- Multi-user collaboration (MVP).
- ATS integrations (MVP).

## Core features
- Candidate profile capture with validation and duplicate prevention.
- Role/skill-based question bank with grouping and navigation.
- Live interview flow with question ratings and tagged notes.
- Skill-wise scoring (1–5) with visual indicators.
- Summary generation with rule-based fallback and optional LLM.
- Editable summary, recommendation, and justification.
- Export interview report as JSON and PDF.

## Architecture (high level)
- UI: Dashboard, Live Interview, Summary & Results
- API: Flask routes + SQLAlchemy ORM
- Data: SQLite database + JSON/PDF exports
- Summary: rule-based fallback + LLM adapter

Refer to [architecture.md](architecture.md) for diagrams and detailed flows.

## Project layout
- app.py: Flask entrypoint
- app/: application package (routes, models, services)
- app/templates/: HTML templates
- app/static/: CSS styles
- question_bank.json: default question bank
- interviews.db: SQLite database (auto-generated)
- Dockerfile: container build

## User journey
1. Pre-interview setup
	- Select role and skill set
	- Load standard question bank
	- Capture candidate profile
2. Live interview
	- Ask questions and rate answers (1–5)
	- Add tagged notes (Strength, Weakness, Red Flag)
	- Update skill scores
3. Post-interview
	- Generate summary + recommendation
	- Edit summary and justification
	- Export JSON/PDF report

## Functional requirements (summary)
From [SRS.md](SRS.md):
- Candidate details must validate required fields and email format.
- Branch/department is a controlled input from predefined values.
- Duplicate candidate emails are prevented.
- Live interview session supports start, timer, and explicit end.
- Questions are grouped by skill and include notes per asked question.
- Notes allow existing skills and an other option for custom skills.
- Summary is available only after completion and includes asked questions only.
- Recent interviews support filtering by role/recommendation and sorting by skill level.

## Data model (minimal)
From [PRODUCT_SPEC.md](PRODUCT_SPEC.md):
- Candidate: name, email, branch, degree, year, role, skills
- Interview: status, created/ended timestamps, assignment results, transcript, summary, recommendation
- Question: skill, text, asked, rating, note
- Note: skill, tag, text, timestamp
- Score: skill, value

## Summary generation
Two-stage approach:
1) Rule-based fallback (deterministic):
	- Highlights top strengths and weaknesses from scores and notes
	- Adds assignment remarks if present
	- Produces 4–6 evidence-based bullets
2) LLM (optional):
	- Uses structured prompt and JSON parsing
	- Output is editable

## LLM integration (OpenRouter)
This project is configured for OpenRouter. See [llm.md](llm.md) for full setup.

Required environment variables in .env:
- LLM_ENABLED=true
- OPENROUTER_API_KEY=your_key_here
- OPENROUTER_MODEL=openai/gpt-4o-mini
- OPENROUTER_TIMEOUT=30
- OPENROUTER_SITE_URL=https://your-domain-or-localhost
- OPENROUTER_APP_NAME=Interview Companion

## Local setup
1) Create a virtual environment
2) Install dependencies from requirements.txt
3) Configure .env
4) Run app.py and open the dashboard URL printed in the console

## Docker
The Dockerfile provides a single-container setup with SQLite persistence. Mount a volume if you want to persist interviews.db outside the container.

## Testing
Automated tests are defined in [tests.md](tests.md) and implemented in tests/test_app.py. Run tests with:
- python -m pytest

Coverage highlights:
- Candidate creation validation and duplicate prevention
- Interview completion + summary generation
- Notes and asked questions persistence
- Filters and sorting in the dashboard
- PDF export for asked questions

## Roadmap
From [what-next.md](what-next.md):
- v0.1.0: controlled inputs, live timer, grouped questions, asked question notes, filtering and sorting, summary rules
- v0.1.1: custom role only on other selection, question bank counts
- LLM: improve parsing and handle provider limits

## Future enhancements
From [PRODUCT_SPEC.md](PRODUCT_SPEC.md):
- Role templates and rubric customization
- Multi-interviewer support
- ATS export
- Analytics dashboard
- Managed DB for multi-user deployments

## References
- [PRODUCT_SPEC.md](PRODUCT_SPEC.md)
- [SRS.md](SRS.md)
- [architecture.md](architecture.md)
- [project_plan.md](project_plan.md)
- [tests.md](tests.md)
- [what-next.md](what-next.md)
- [llm.md](llm.md)