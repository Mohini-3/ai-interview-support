# Architecture

## 1) Overview
A lightweight, web-based application optimized for live interview usage. MVP targets a single interviewer on a single device with a Flask API, SQLite storage, and SQLAlchemy ORM. The frontend is HTML/CSS/JS and the system is containerized with Docker for consistent setup and portability.

## 2) High-Level Diagram (Logical)
- UI (Dashboard, Live Interview, Summary)
- API (Flask service)
- Data Layer (SQLite + SQLAlchemy + export)
- Optional AI Summary Service (stubbed or local rules)

## 3) Frontend Architecture
- Pages
  - Dashboard
  - Live Interview
  - Summary & Results
- UI Modules
  - QuestionList
  - NotePanel
  - SkillScoreTable
  - SummaryEditor
  - ExportPanel
- State Model
  - Candidate
  - Interview
  - Questions
  - Notes
  - Scores

## 4) Data Flow
1. Load role template → question list
2. Capture candidate profile → create interview session (API + SQLite)
3. During interview: update question states, add notes, update scores (API + SQLite)
4. Post-interview: generate summary (rules or AI)
5. Export report (API)

## 5) Storage Strategy (MVP)
- SQLite database (file-based)
- Export JSON (optionally PDF)
- Docker volume for persistence

## 6) Summary Generation
- Rule-based fallback (deterministic)
- Optional LLM adapter interface (future)

## 7) Security & Privacy
- No PII beyond interview data
- No external upload by default
- Explicit consent for transcript text

## 8) Scalability & Future
- Replace SQLite with managed DB for multi-user deployment
- Multi-interviewer support
- Audit trail and rubric customization
- Separate UI and API containers

## 9) Diagrams (Mermaid)

### 9.1 System Context
```mermaid
flowchart LR
  Interviewer[Interviewer] -->|Uses| WebApp[Interview Companion Web App]
  WebApp -->|Calls| API[Python API]
  API -->|Stores| SQLite[(SQLite DB)]
  WebApp -->|Exports| Report[JSON/PDF Report]
  API -->|Optional| AIService[AI Summary Service]
```

### 9.2 Container/Component View
```mermaid
flowchart TB
  subgraph UI[Web UI]
    Dashboard
    LiveInterview[Live Interview Screen]
    Summary[Summary & Results]
  end

  subgraph API[Python API]
    Endpoints[REST Endpoints]
    SummaryService[Summary Service]
  end

  subgraph State[State/Store]
    SessionState[Interview Session State]
    Templates[Question Templates]
  end

  subgraph Data[Data Layer]
    SQLite[(SQLite DB)]
    Exporter[Export Service]
  end

  subgraph AI[Summary Engine]
    Rules[Rule-Based Summarizer]
    Adapter[LLM Adapter Optional]
  end

  UI --> API
  API --> State
  State --> Data
  Summary --> API
  API --> AI
  AI --> State
  Exporter --> Report[JSON/PDF]
```

### 9.3 User Flow
```mermaid
flowchart LR
  Start([Start]) --> Setup[Pre-Interview Setup]
  Setup --> Live[Live Interview]
  Live --> Review[Post-Interview Review]
  Review --> Summary[Generate Summary]
  Summary --> Edit[Edit Output]
  Edit --> Export[Export Report]
  Export --> End([End])
```

### 9.4 Use Case Diagram
```mermaid
flowchart TB
  Interviewer((Interviewer))

  UC1[Create Interview Session]
  UC2[Select Role & Skills]
  UC3[Ask Questions & Rate]
  UC4[Take Tagged Notes]
  UC5[Score Skills]
  UC6[Generate Summary]
  UC7[Edit Summary]
  UC8[Export Report]

  Interviewer --> UC1
  Interviewer --> UC2
  Interviewer --> UC3
  Interviewer --> UC4
  Interviewer --> UC5
  Interviewer --> UC6
  Interviewer --> UC7
  Interviewer --> UC8
```

### 9.5 Sequence Diagram: Live Interview
```mermaid
sequenceDiagram
  participant I as Interviewer
  participant UI as Web UI
  participant API as Python API
  participant DB as SQLite DB

  I->>UI: Select role & skills
  UI->>API: Load question set
  API->>UI: Questions ready
  I->>UI: Mark asked / rate answer
  UI->>API: Update question rating
  API->>DB: Persist rating
  I->>UI: Add tagged note
  UI->>API: Save note
  API->>DB: Persist note
```

### 9.6 Sequence Diagram: Summary Generation
```mermaid
sequenceDiagram
  participant I as Interviewer
  participant UI as Web UI
  participant API as Python API
  participant DB as SQLite DB
  participant R as Rule-Based Summarizer
  participant A as LLM Adapter Optional

  I->>UI: Generate summary
  UI->>API: Request summary
  API->>DB: Fetch scores + notes + ratings
  API->>R: Build draft summary
  alt LLM enabled
    R->>A: Send structured prompt
    A->>R: Return refined summary
  end
  R->>API: Summary + recommendation
  API->>UI: Summary + recommendation
  I->>UI: Edit summary
  UI->>API: Save final summary
  API->>DB: Persist summary
```

### 9.7 Data Model (ER)
```mermaid
erDiagram
  CANDIDATE ||--o{ INTERVIEW : has
  INTERVIEW ||--o{ QUESTION : includes
  INTERVIEW ||--o{ NOTE : includes
  INTERVIEW ||--o{ SCORE : includes

  CANDIDATE {
    string id
    string name
    string education
    string role
  }
  INTERVIEW {
    string id
    date date
    string summary
    string recommendation
  }
  QUESTION {
    string id
    string skill
    string text
    boolean asked
    int rating
  }
  NOTE {
    string id
    string skill
    string tag
    string text
    datetime timestamp
  }
  SCORE {
    string skill
    int value
    string comment
  }
```
