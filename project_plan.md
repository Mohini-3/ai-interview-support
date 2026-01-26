# Project Plan (MVP)

## 1) Milestones
### M1: Discovery & Spec (Day 1)
- Finalize scope and user stories
- Lock down data model and UX flows

### M2: UI Skeleton (Day 1–2)
- Dashboard layout
- Live interview screen layout
- Summary screen layout

### M3: Core Functionality (Day 2–3)
- Question prompting and rating
- Notes with tags
- Skill scoring
- Flask API endpoints (CRUD for interviews, notes, scores)
- SQLite persistence via SQLAlchemy

### M4: Summary Generation (Day 3)
- Rule-based summary
- Recommendation logic
- Editable output

### M5: Export & Polish (Day 4)
- Export JSON / PDF
- UI polish + accessibility
- Bug fixes
- Dockerfile + container run validation

## 2) Task Breakdown
### Frontend
- Create base layout and navigation (HTML/CSS/JS)
- Implement QuestionList and rating controls
- Implement NotePanel with tags
- Implement SkillScoreTable
- Implement SummaryEditor

### Data & State
- Define data models
- Implement Flask API layer
- Store interview session in SQLite via SQLAlchemy
- Add export function

### DevOps
- Create Dockerfile
- Add docker-compose for local run (optional)
- Document run instructions

### Summary Logic
- Rule-based summarizer
- Recommendation thresholds

## 3) Deliverables
- Functional MVP web app
- Product spec
- Architecture overview
- Demo-ready flow

## 4) Risks & Mitigations
- Time constraints → focus on MVP, skip auth
- Inconsistent scoring → enforce rubric in UI
- Summary quality → deterministic fallback
- Local DB loss → use Docker volume for SQLite

## 5) Testing Checklist
- Create interview session
- Add notes and scores
- Generate summary
- Export report
