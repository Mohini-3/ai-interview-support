# AI-Assisted Technical Interview Companion

## 1) Overview
A web-based interview companion that helps interviewers run consistent technical interviews, capture structured notes, score skills, and generate standardized interview summaries with a hire recommendation. The MVP includes a lightweight Python API with SQLite storage and is containerized with Docker for consistent setup.

## 2) Goals
- Standardize questions and scoring per role/skill.
- Reduce interviewer cognitive load during live interviews.
- Produce clear, editable summaries with evidence-based rationale.
- Minimize bias with structured inputs and rubric-based scoring.

## 3) Non-Goals (Out of Scope)
- Automated candidate rejection or autonomous decisions.
- Personality/emotion/voice/video analysis.
- Multi-user collaboration (MVP).
- ATS integrations (MVP).

## 4) User Personas
- Interviewer: conducts interviews, records feedback, and generates summaries.

## 5) MVP User Journey
1. Pre-Interview Setup
   - Select role and skill set.
   - Load a standard question bank.
   - Capture candidate profile.
2. Live Interview
   - Ask questions (mark asked/skipped).
   - Rate answers (1–5).
   - Add structured notes with tags and optional timestamps.
3. Post-Interview
   - Review and adjust skill scores.
   - Generate summary + recommendation.
   - Edit output and export.

## 6) Functional Requirements
### 6.1 Interview Question Prompting
- Skill-based question lists.
- Mark questions as asked or skipped.
- Rate answer per question (1–5).

### 6.2 Live Note-Taking
- Notes are tagged by skill.
- Quick tags: Strength, Weakness, Red Flag.
- Optional timestamps.

### 6.3 Skill-Wise Scoring
- Score per skill (1–5).
- Visual table or chart.

### 6.4 AI-Assisted Summary
- 4–6 bullet points covering strengths, weaknesses, and overall impression.
- Hire recommendation: Hire / No Hire / Borderline.
- 1–2 sentence justification.
- Must be editable before finalization.

## 7) Inputs
- Candidate profile: name, education, role, skills.
- Assignment score and remarks.
- Selected interview questions.
- Interviewer notes.
- Skill ratings.
- Optional transcript (text input or paste).

## 8) Outputs
- Interview summary.
- Skill-wise scores.
- Hire recommendation.
- Editable feedback.
- Export format: PDF or JSON (MVP can start with JSON).

## 8.1 Storage & Deployment (MVP)
- Backend: Python Flask API.
- Database: SQLite (file-based) with SQLAlchemy ORM.
- Frontend: HTML, CSS, JavaScript (vanilla).
- Containerization: Docker (single container for MVP).

## 9) Scoring Rubric (Recommended)
- 1: Poor/no understanding
- 2: Limited/basic
- 3: Competent
- 4: Strong
- 5: Exceptional

## 10) Data Model (Minimal)
### Candidate
- id
- name
- education
- role
- skills[]

### Interview
- id
- candidateId
- date
- questions[]
- notes[]
- scores[]
- summary
- recommendation

### Question
- id
- skill
- text
- asked
- rating

### Note
- id
- skill
- tag (Strength/Weakness/RedFlag)
- text
- timestamp?

### Score
- skill
- value
- comment?

## 11) Summary Generation Logic
### Rule-Based Fallback (Deterministic)
- Identify top 2 strengths (highest scores + Strength tags).
- Identify top 1–2 weaknesses (lowest scores + Weakness/Red Flag tags).
- Use assignment remarks if provided.
- Produce 4–6 bullets from evidence.

### LLM Prompt Skeleton (Optional)
- Input: candidate profile, scores, notes, question ratings, assignment results.
- Output: 4–6 bullets, hire recommendation, 1–2 sentence rationale.
- Constraints: avoid sensitive attributes, cite evidence from notes/ratings.

## 12) UX Requirements
- Live interview screen optimized for speed.
- Keyboard shortcuts for tagging and rating (optional in MVP).
- Split view: question list + notes panel + score widget.
- Summary page with edit-in-place.

## 13) Accessibility & Privacy
- Clear consent if transcripts are used.
- Local-only mode optional for MVP.
- Do not store sensitive attributes.

## 13.1 Data Retention (SQLite)
- SQLite file stored on the host or container volume.
- Exported reports stored on disk and explicitly initiated by the interviewer.

## 14) Acceptance Criteria
- All interviews can be completed end-to-end.
- Summary and recommendation generated in <2 minutes.
- 100% of interviews have scores + summary.

## 15) Suggested Screens
1. Interviewer Dashboard
   - Create new interview
   - Past interviews list
2. Live Interview Screen
   - Question list + rating
   - Notes panel with tags
   - Skill score widget
3. Summary & Results
   - Generated summary (editable)
   - Recommendation (editable)
   - Export options

## 16) User Stories (MVP)
- As an interviewer, I can select a role and skills to load a question set.
- As an interviewer, I can mark questions asked/skipped and rate answers.
- As an interviewer, I can add tagged notes during the interview.
- As an interviewer, I can score each skill after the interview.
- As an interviewer, I can generate a summary and recommendation and edit it.
- As an interviewer, I can export a final interview report.

## 17) Future Enhancements
- Role templates + rubric customization
- Multi-interviewer merge and conflict resolution
- ATS export
- Analytics dashboard (score distributions, question usage)
- Move SQLite to managed database for multi-user deployment
- Multi-container deployment with API + UI separation
