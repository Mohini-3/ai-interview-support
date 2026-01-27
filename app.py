from __future__ import annotations

from datetime import datetime
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import json
from io import BytesIO

from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from fpdf import FPDF

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "interviews.db"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH.as_posix()}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy(app)


class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    branch = db.Column(db.String(200), nullable=False)
    degree = db.Column(db.String(200), nullable=False)
    year = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(200), nullable=False)
    skills = db.Column(db.String(400), nullable=False)


class Interview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidate.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ended_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="ongoing", nullable=False)
    assignment_score = db.Column(db.Integer, nullable=True)
    assignment_remarks = db.Column(db.Text, nullable=True)
    transcript = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    recommendation = db.Column(db.String(50), nullable=True)
    recommendation_reason = db.Column(db.Text, nullable=True)

    candidate = db.relationship("Candidate", backref=db.backref("interviews", lazy=True))


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey("interview.id"), nullable=False)
    skill = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    asked = db.Column(db.Boolean, default=False, nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    note = db.Column(db.Text, nullable=True)


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey("interview.id"), nullable=False)
    skill = db.Column(db.String(100), nullable=False)
    tag = db.Column(db.String(50), nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey("interview.id"), nullable=False)
    skill = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)


QUESTION_BANK_PATH = BASE_DIR / "question_bank.json"

DEFAULT_QUESTION_BANK = {
    "Python": [
        "Explain list vs tuple and when to use each.",
        "What is a Python generator and why use it?",
        "How does Python handle memory management?",
    ],
    "DSA": [
        "Explain time complexity for common sorting algorithms.",
        "How would you detect a cycle in a linked list?",
        "Describe the difference between stack and queue.",
    ],
    "Web": [
        "Explain the difference between HTTP and HTTPS.",
        "What is REST and how do you design a RESTful API?",
        "Describe the role of a CDN in web apps.",
    ],
    "ML": [
        "What is overfitting and how do you reduce it?",
        "Explain precision vs recall.",
        "What is a confusion matrix used for?",
    ],
    "Communication": [
        "Describe a complex project to a non-technical stakeholder.",
        "How do you handle feedback on your work?",
    ],
}

DEFAULT_ROLES = [
    "Backend Engineer",
    "Frontend Engineer",
    "Full Stack Engineer",
    "Data Engineer",
    "Data Scientist",
    "ML Engineer",
    "DevOps Engineer",
    "QA Engineer",
]

DEFAULT_BRANCHES = [
    "Computer Science",
    "Information Technology",
    "Electronics",
    "Electrical",
    "Mechanical",
    "Civil",
    "Other",
]

DEFAULT_DEGREES = [
    "B.Tech",
    "B.E",
    "B.Sc",
    "M.Tech",
    "M.Sc",
    "MBA",
    "Other",
]

DEFAULT_YEARS = [
    "1st Year",
    "2nd Year",
    "3rd Year",
    "4th Year",
    "Graduate",
]


def load_question_bank() -> dict[str, list[str]]:
    if QUESTION_BANK_PATH.exists():
        try:
            return json.loads(QUESTION_BANK_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return DEFAULT_QUESTION_BANK
    QUESTION_BANK_PATH.write_text(
        json.dumps(DEFAULT_QUESTION_BANK, indent=2),
        encoding="utf-8",
    )
    return DEFAULT_QUESTION_BANK


def save_question_bank(bank: dict[str, list[str]]) -> None:
    QUESTION_BANK_PATH.write_text(
        json.dumps(bank, indent=2),
        encoding="utf-8",
    )


@app.before_request
def ensure_db():
    db.create_all()
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
        migrate_sqlite_schema()


def _get_table_columns(table_name: str) -> set[str]:
    result = db.session.execute(text(f"PRAGMA table_info({table_name})"))
    return {row[1] for row in result}


def migrate_sqlite_schema() -> None:
    migrations = {
        "candidate": {
            "email": "ALTER TABLE candidate ADD COLUMN email VARCHAR(200)",
            "branch": "ALTER TABLE candidate ADD COLUMN branch VARCHAR(200)",
            "degree": "ALTER TABLE candidate ADD COLUMN degree VARCHAR(200)",
            "year": "ALTER TABLE candidate ADD COLUMN year VARCHAR(50)",
        },
        "interview": {
            "ended_at": "ALTER TABLE interview ADD COLUMN ended_at DATETIME",
            "status": "ALTER TABLE interview ADD COLUMN status VARCHAR(20)",
        },
        "question": {
            "note": "ALTER TABLE question ADD COLUMN note TEXT",
        },
    }

    for table, columns in migrations.items():
        existing = _get_table_columns(table)
        for column, statement in columns.items():
            if column not in existing:
                db.session.execute(text(statement))

    if "email" in _get_table_columns("candidate"):
        db.session.execute(text("UPDATE candidate SET email = COALESCE(email, '')"))
    if "branch" in _get_table_columns("candidate"):
        db.session.execute(text("UPDATE candidate SET branch = COALESCE(branch, 'Other')"))
    if "degree" in _get_table_columns("candidate"):
        db.session.execute(text("UPDATE candidate SET degree = COALESCE(degree, 'B.Tech')"))
    if "year" in _get_table_columns("candidate"):
        db.session.execute(text("UPDATE candidate SET year = COALESCE(year, 'Graduate')"))
    if "status" in _get_table_columns("interview"):
        db.session.execute(text("UPDATE interview SET status = COALESCE(status, 'completed')"))
    db.session.commit()


def parse_skills(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [skill.strip() for skill in raw.split(",") if skill.strip()]


def normalize_skills(selected: Iterable[str], custom_raw: str | None) -> list[str]:
    skills = [skill.strip() for skill in selected if skill.strip()]
    skills.extend(parse_skills(custom_raw))
    unique = []
    seen = set()
    for skill in skills:
        if skill.lower() in seen:
            continue
        seen.add(skill.lower())
        unique.append(skill)
    return unique


def is_valid_email(email: str) -> bool:
    if not email or "@" not in email:
        return False
    local, _, domain = email.partition("@")
    return bool(local) and "." in domain


def build_question_set(skills: Iterable[str]) -> list[dict]:
    question_bank = load_question_bank()
    questions = []
    for skill in skills:
        for text in question_bank.get(skill, []):
            questions.append({"skill": skill, "text": text})
    return questions


def aggregate_scores(interview_id: int) -> dict[str, int]:
    scores = Score.query.filter_by(interview_id=interview_id).all()
    return {score.skill: score.value for score in scores}


def average_skill_scores(interviews: list[Interview]) -> dict[int, float]:
    if not interviews:
        return {}
    interview_ids = [interview.id for interview in interviews]
    scores = Score.query.filter(Score.interview_id.in_(interview_ids)).all()
    totals: dict[int, int] = defaultdict(int)
    counts: dict[int, int] = defaultdict(int)
    for score in scores:
        totals[score.interview_id] += score.value
        counts[score.interview_id] += 1
    averages: dict[int, float] = {}
    for interview_id in interview_ids:
        if counts.get(interview_id):
            averages[interview_id] = totals[interview_id] / counts[interview_id]
    return averages


def build_summary(interview: Interview) -> tuple[list[str], str, str]:
    scores = Score.query.filter_by(interview_id=interview.id).all()
    notes = Note.query.filter_by(interview_id=interview.id).order_by(Note.timestamp).all()

    strengths = [note.text for note in notes if note.tag == "Strength"]
    weaknesses = [note.text for note in notes if note.tag in {"Weakness", "Red Flag"}]

    scored = sorted(scores, key=lambda s: s.value, reverse=True)
    top_scores = [s for s in scored if s.value >= 4][:2]
    low_scores = [s for s in scored if s.value <= 2][:2]

    bullets: list[str] = []
    for item in top_scores:
        bullets.append(f"Strong {item.skill} performance (score {item.value}/5).")
    if strengths:
        bullets.append(f"Strength noted: {strengths[0]}")

    for item in low_scores:
        bullets.append(f"Needs improvement in {item.skill} (score {item.value}/5).")
    if weaknesses:
        bullets.append(f"Concern: {weaknesses[0]}")

    if interview.assignment_score is not None:
        bullets.append(
            f"Assignment score: {interview.assignment_score}/100. {interview.assignment_remarks or ''}".strip()
        )

    if interview.transcript:
        bullets.append("Interview transcript provided for review.")

    if not bullets:
        bullets.append("No significant strengths or weaknesses recorded. Add notes and scores to refine.")

    avg_score = None
    if scores:
        avg_score = sum(score.value for score in scores) / len(scores)

    recommendation = "Borderline"
    if avg_score is not None:
        if avg_score >= 4:
            recommendation = "Hire"
        elif avg_score <= 2.5:
            recommendation = "No Hire"
    reason = "Recommendation based on skill scores and evidence from notes."
    if avg_score is not None:
        reason = f"Average score: {avg_score:.1f}/5. Recommendation considers strengths, weaknesses, and interview notes."

    return bullets[:6], recommendation, reason


@app.route("/")
def dashboard():
    role_filter = request.args.get("role", "").strip()
    recommendation_filter = request.args.get("recommendation", "").strip()
    sort_filter = request.args.get("sort", "").strip()

    interviews = Interview.query.order_by(Interview.created_at.desc()).all()
    if role_filter:
        interviews = [i for i in interviews if i.candidate.role == role_filter]

    if recommendation_filter:
        if recommendation_filter == "Unrated":
            interviews = [i for i in interviews if not i.recommendation]
        else:
            interviews = [i for i in interviews if i.recommendation == recommendation_filter]

    skill_scores = average_skill_scores(interviews)
    if sort_filter == "skill_desc":
        interviews = sorted(
            interviews,
            key=lambda i: skill_scores.get(i.id, 0),
            reverse=True,
        )

    ongoing_interviews = [i for i in interviews if i.status != "completed"]
    completed_interviews = [i for i in interviews if i.status == "completed"]
    question_bank = load_question_bank()
    return render_template(
        "dashboard.html",
        ongoing_interviews=ongoing_interviews,
        completed_interviews=completed_interviews,
        skill_scores=skill_scores,
        default_skills=sorted(question_bank.keys()),
        role_filter=role_filter,
        recommendation_filter=recommendation_filter,
        sort_filter=sort_filter,
        default_roles=DEFAULT_ROLES,
        default_branches=DEFAULT_BRANCHES,
        default_degrees=DEFAULT_DEGREES,
        default_years=DEFAULT_YEARS,
        error=request.args.get("error", ""),
    )


@app.route("/question-bank")
def question_bank():
    bank = load_question_bank()
    return render_template("question_bank.html", question_bank=bank)


@app.route("/question-bank", methods=["POST"])
def add_question_bank():
    skill_existing = request.form.get("skill_existing", "").strip()
    skill_new = request.form.get("skill_new", "").strip()
    skill = (skill_new or skill_existing).strip()
    questions_raw = request.form.get("questions", "").strip()
    if not skill or not questions_raw:
        return redirect(url_for("question_bank"))

    new_questions = [line.strip() for line in questions_raw.split("\n") if line.strip()]
    bank = load_question_bank()
    bank.setdefault(skill, [])
    bank[skill].extend(new_questions)
    bank[skill] = list(dict.fromkeys(bank[skill]))
    save_question_bank(bank)
    return redirect(url_for("question_bank"))


@app.route("/question-bank/<string:skill>/delete", methods=["POST"])
def delete_question_bank_skill(skill: str):
    bank = load_question_bank()
    if skill in bank:
        del bank[skill]
        save_question_bank(bank)
    return redirect(url_for("question_bank"))


@app.route("/interviews", methods=["POST"])
def create_interview():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    branch = request.form.get("branch", "").strip()
    degree = request.form.get("degree", "").strip()
    year = request.form.get("year", "").strip()
    role = request.form.get("role", "").strip()
    custom_role = request.form.get("custom_role", "").strip()
    selected_skills = request.form.getlist("skills")
    custom_skills = request.form.get("custom_skills", "")
    assignment_score = request.form.get("assignment_score")
    assignment_remarks = request.form.get("assignment_remarks", "").strip()
    transcript = request.form.get("transcript", "").strip()

    if role == "other":
        role = custom_role

    if not name or not email or not role or not branch or not degree or not year:
        return redirect(url_for("dashboard", error="missing"))

    if not is_valid_email(email):
        return redirect(url_for("dashboard", error="invalid_email"))

    if branch not in DEFAULT_BRANCHES:
        return redirect(url_for("dashboard", error="invalid_branch"))
    if degree not in DEFAULT_DEGREES:
        return redirect(url_for("dashboard", error="invalid_degree"))
    if year not in DEFAULT_YEARS:
        return redirect(url_for("dashboard", error="invalid_year"))

    if Candidate.query.filter_by(email=email).first():
        return redirect(url_for("dashboard", error="duplicate"))

    candidate = Candidate(
        name=name,
        email=email,
        branch=branch,
        degree=degree,
        year=year,
        role=role,
        skills=",".join(normalize_skills(selected_skills, custom_skills)),
    )
    db.session.add(candidate)
    db.session.flush()

    interview = Interview(
        candidate_id=candidate.id,
        assignment_score=int(assignment_score) if assignment_score else None,
        assignment_remarks=assignment_remarks or None,
        transcript=transcript or None,
        status="ongoing",
    )
    db.session.add(interview)
    db.session.flush()

    selected_skills = normalize_skills(selected_skills, custom_skills)
    if selected_skills:
        bank = load_question_bank()
        updated = False
        for skill in selected_skills:
            if skill not in bank:
                bank[skill] = []
                updated = True
        if updated:
            save_question_bank(bank)
    for question in build_question_set(selected_skills):
        db.session.add(
            Question(
                interview_id=interview.id,
                skill=question["skill"],
                text=question["text"],
            )
        )

    for skill in selected_skills:
        db.session.add(Score(interview_id=interview.id, skill=skill, value=3))

    db.session.commit()

    return redirect(url_for("live_interview", interview_id=interview.id))


@app.route("/interviews/<int:interview_id>/live")
def live_interview(interview_id: int):
    interview = Interview.query.get_or_404(interview_id)
    questions = Question.query.filter_by(interview_id=interview_id).order_by(Question.skill, Question.id).all()
    grouped_questions: dict[str, list[Question]] = defaultdict(list)
    for question in questions:
        grouped_questions[question.skill].append(question)
    notes = Note.query.filter_by(interview_id=interview_id).order_by(Note.timestamp.desc()).all()
    scores = Score.query.filter_by(interview_id=interview_id).all()
    question_bank = load_question_bank()
    note_skills = sorted({"General", *question_bank.keys(), *[score.skill for score in scores]})
    return render_template(
        "interview.html",
        interview=interview,
        grouped_questions=grouped_questions,
        notes=notes,
        scores=scores,
        note_skills=note_skills,
    )


@app.route("/interviews/<int:interview_id>/summary")
def summary(interview_id: int):
    interview = Interview.query.get_or_404(interview_id)
    if interview.status != "completed":
        return render_template(
            "summary.html",
            interview=interview,
            scores=[],
            asked_questions=[],
            blocked=True,
        )

    scores = Score.query.filter_by(interview_id=interview_id).all()
    asked_questions = Question.query.filter_by(interview_id=interview_id, asked=True).all()
    return render_template(
        "summary.html",
        interview=interview,
        scores=scores,
        asked_questions=asked_questions,
        blocked=False,
    )


@app.route("/api/interviews/<int:interview_id>/questions/<int:question_id>", methods=["POST"])
def update_question(interview_id: int, question_id: int):
    interview = Interview.query.get_or_404(interview_id)
    if interview.status == "completed":
        return jsonify({"status": "locked"}), 400
    question = Question.query.filter_by(id=question_id, interview_id=interview_id).first_or_404()
    data = request.get_json(force=True)
    if "asked" in data:
        question.asked = bool(data["asked"])
    if "rating" in data and data["rating"] is not None:
        question.rating = int(data["rating"])
    if "note" in data:
        note_value = str(data["note"]).strip()
        question.note = note_value or None
    db.session.commit()
    return jsonify({"status": "ok"})


@app.route("/api/interviews/<int:interview_id>/notes", methods=["POST"])
def add_note(interview_id: int):
    interview = Interview.query.get_or_404(interview_id)
    if interview.status == "completed":
        return jsonify({"status": "locked"}), 400
    data = request.get_json(force=True)
    skill = data.get("skill", "General")
    if skill == "other":
        skill = data.get("custom_skill", "").strip() or "General"
    note = Note(
        interview_id=interview_id,
        skill=skill,
        tag=data.get("tag", "Strength"),
        text=data.get("text", "").strip(),
    )
    if not note.text:
        return jsonify({"status": "empty"}), 400
    db.session.add(note)
    bank = load_question_bank()
    if skill and skill not in bank:
        bank[skill] = []
        save_question_bank(bank)
    db.session.commit()
    return jsonify({
        "status": "ok",
        "note": {
            "id": note.id,
            "skill": note.skill,
            "tag": note.tag,
            "text": note.text,
            "timestamp": note.timestamp.isoformat(),
        },
    })


@app.route("/api/interviews/<int:interview_id>/scores", methods=["POST"])
def update_score(interview_id: int):
    interview = Interview.query.get_or_404(interview_id)
    if interview.status == "completed":
        return jsonify({"status": "locked"}), 400
    data = request.get_json(force=True)
    skill = data.get("skill")
    value = int(data.get("value", 0))
    if not skill or value <= 0:
        return jsonify({"status": "invalid"}), 400
    score = Score.query.filter_by(interview_id=interview_id, skill=skill).first()
    if not score:
        score = Score(interview_id=interview_id, skill=skill, value=value)
        db.session.add(score)
    else:
        score.value = value
    db.session.commit()
    return jsonify({"status": "ok"})


@app.route("/api/interviews/<int:interview_id>/generate_summary", methods=["POST"])
def generate_summary(interview_id: int):
    interview = Interview.query.get_or_404(interview_id)
    if interview.status != "completed":
        return jsonify({"status": "blocked"}), 400
    bullets, recommendation, reason = build_summary(interview)
    interview.summary = "\n".join(f"- {bullet}" for bullet in bullets)
    interview.recommendation = recommendation
    interview.recommendation_reason = reason
    db.session.commit()
    return jsonify({
        "summary": interview.summary,
        "recommendation": recommendation,
        "reason": reason,
    })


@app.route("/interviews/<int:interview_id>/summary", methods=["POST"])
def save_summary(interview_id: int):
    interview = Interview.query.get_or_404(interview_id)
    if interview.status != "completed":
        return redirect(url_for("summary", interview_id=interview_id))
    interview.summary = request.form.get("summary", "").strip()
    interview.recommendation = request.form.get("recommendation", "").strip()
    interview.recommendation_reason = request.form.get("recommendation_reason", "").strip()
    db.session.commit()
    return redirect(url_for("summary", interview_id=interview_id))


@app.route("/interviews/<int:interview_id>/end", methods=["POST"])
def end_interview(interview_id: int):
    interview = Interview.query.get_or_404(interview_id)
    if interview.status != "completed":
        interview.status = "completed"
        interview.ended_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for("live_interview", interview_id=interview_id))


@app.route("/interviews/<int:interview_id>/export")
def export_interview(interview_id: int):
    interview = Interview.query.get_or_404(interview_id)
    candidate = interview.candidate
    questions = Question.query.filter_by(interview_id=interview_id).all()
    asked_questions = [question for question in questions if question.asked]
    notes = Note.query.filter_by(interview_id=interview_id).all()
    scores = Score.query.filter_by(interview_id=interview_id).all()

    payload = {
        "candidate": {
            "name": candidate.name,
            "email": candidate.email,
            "branch": candidate.branch,
            "degree": candidate.degree,
            "year": candidate.year,
            "role": candidate.role,
            "skills": parse_skills(candidate.skills),
        },
        "interview": {
            "id": interview.id,
            "created_at": interview.created_at.isoformat(),
            "assignment_score": interview.assignment_score,
            "assignment_remarks": interview.assignment_remarks,
            "transcript": interview.transcript,
            "summary": interview.summary,
            "recommendation": interview.recommendation,
            "recommendation_reason": interview.recommendation_reason,
        },
        "questions": [
            {
                "skill": q.skill,
                "text": q.text,
                "asked": q.asked,
                "rating": q.rating,
            }
            for q in questions
        ],
        "notes": [
            {
                "skill": n.skill,
                "tag": n.tag,
                "text": n.text,
                "timestamp": n.timestamp.isoformat(),
            }
            for n in notes
        ],
        "scores": [
            {"skill": s.skill, "value": s.value, "comment": s.comment}
            for s in scores
        ],
    }

    export_path = BASE_DIR / f"interview_{interview_id}.json"
    export_path.write_text(
        jsonify(payload).get_data(as_text=True),
        encoding="utf-8",
    )
    return send_file(export_path, as_attachment=True)


@app.route("/interviews/<int:interview_id>/export/pdf")
def export_interview_pdf(interview_id: int):
    interview = Interview.query.get_or_404(interview_id)
    candidate = interview.candidate
    questions = Question.query.filter_by(interview_id=interview_id).all()
    asked_questions = [question for question in questions if question.asked]
    notes = Note.query.filter_by(interview_id=interview_id).all()
    scores = Score.query.filter_by(interview_id=interview_id).all()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    def write_line(text: str, bold: bool = False):
        pdf.set_font("Helvetica", style="B" if bold else "", size=12)
        pdf.multi_cell(0, 8, text)

    write_line("Interview Report", bold=True)
    write_line(f"Candidate: {candidate.name}")
    write_line(f"Email: {candidate.email}")
    write_line(f"Branch: {candidate.branch}")
    write_line(f"Degree: {candidate.degree}")
    write_line(f"Year: {candidate.year}")
    write_line(f"Role: {candidate.role}")
    write_line(f"Skills: {candidate.skills}")
    write_line("")

    write_line("Assignment Results:", bold=True)
    write_line(f"Score: {interview.assignment_score if interview.assignment_score is not None else 'N/A'}")
    write_line(f"Remarks: {interview.assignment_remarks or 'N/A'}")
    write_line("")

    write_line("Skill Scores:", bold=True)
    for score in scores:
        write_line(f"- {score.skill}: {score.value}/5")
    write_line("")

    write_line("Notes:", bold=True)
    for note in notes:
        write_line(f"- [{note.tag}] {note.skill}: {note.text}")
    write_line("")

    write_line("Asked Questions:", bold=True)
    if asked_questions:
        for question in asked_questions:
            rating = question.rating if question.rating is not None else "N/A"
            note = question.note or ""
            suffix = f" Rating: {rating}" if rating != "N/A" else ""
            note_text = f" Note: {note}" if note else ""
            write_line(f"- {question.skill}: {question.text}.{suffix}{note_text}")
    else:
        write_line("No asked questions recorded.")
    write_line("")

    write_line("Summary:", bold=True)
    summary_text = interview.summary or "N/A"
    for line in summary_text.split("\n"):
        write_line(line)
    write_line("")

    write_line("Recommendation:", bold=True)
    write_line(f"Decision: {interview.recommendation or 'N/A'}")
    write_line(f"Justification: {interview.recommendation_reason or 'N/A'}")

    buffer = BytesIO(pdf.output(dest="S").encode("latin-1"))
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"interview_{interview_id}.pdf",
        mimetype="application/pdf",
    )


if __name__ == "__main__":
    app.run(debug=True)
