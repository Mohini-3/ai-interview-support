from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

import json
from io import BytesIO

from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for
from flask_sqlalchemy import SQLAlchemy
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
    education = db.Column(db.String(200), nullable=True)
    role = db.Column(db.String(200), nullable=False)
    skills = db.Column(db.String(400), nullable=False)


class Interview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidate.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
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
    interviews = Interview.query.order_by(Interview.created_at.desc()).all()
    question_bank = load_question_bank()
    return render_template(
        "dashboard.html",
        interviews=interviews,
        default_skills=sorted(question_bank.keys()),
    )


@app.route("/question-bank")
def question_bank():
    bank = load_question_bank()
    return render_template("question_bank.html", question_bank=bank)


@app.route("/question-bank", methods=["POST"])
def add_question_bank():
    skill = request.form.get("skill", "").strip()
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
    education = request.form.get("education", "").strip()
    role = request.form.get("role", "").strip()
    selected_skills = request.form.getlist("skills")
    custom_skills = request.form.get("custom_skills", "")
    assignment_score = request.form.get("assignment_score")
    assignment_remarks = request.form.get("assignment_remarks", "").strip()
    transcript = request.form.get("transcript", "").strip()

    if not name or not role:
        return redirect(url_for("dashboard"))

    candidate = Candidate(
        name=name,
        education=education,
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
    )
    db.session.add(interview)
    db.session.flush()

    selected_skills = normalize_skills(selected_skills, custom_skills)
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
    questions = Question.query.filter_by(interview_id=interview_id).all()
    notes = Note.query.filter_by(interview_id=interview_id).order_by(Note.timestamp.desc()).all()
    scores = Score.query.filter_by(interview_id=interview_id).all()
    return render_template(
        "interview.html",
        interview=interview,
        questions=questions,
        notes=notes,
        scores=scores,
    )


@app.route("/interviews/<int:interview_id>/summary")
def summary(interview_id: int):
    interview = Interview.query.get_or_404(interview_id)
    scores = Score.query.filter_by(interview_id=interview_id).all()
    notes = Note.query.filter_by(interview_id=interview_id).order_by(Note.timestamp.desc()).all()
    return render_template(
        "summary.html",
        interview=interview,
        scores=scores,
        notes=notes,
    )


@app.route("/api/interviews/<int:interview_id>/questions/<int:question_id>", methods=["POST"])
def update_question(interview_id: int, question_id: int):
    question = Question.query.filter_by(id=question_id, interview_id=interview_id).first_or_404()
    data = request.get_json(force=True)
    if "asked" in data:
        question.asked = bool(data["asked"])
    if "rating" in data and data["rating"] is not None:
        question.rating = int(data["rating"])
    db.session.commit()
    return jsonify({"status": "ok"})


@app.route("/api/interviews/<int:interview_id>/notes", methods=["POST"])
def add_note(interview_id: int):
    data = request.get_json(force=True)
    note = Note(
        interview_id=interview_id,
        skill=data.get("skill", "General"),
        tag=data.get("tag", "Strength"),
        text=data.get("text", "").strip(),
    )
    if not note.text:
        return jsonify({"status": "empty"}), 400
    db.session.add(note)
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
    interview.summary = request.form.get("summary", "").strip()
    interview.recommendation = request.form.get("recommendation", "").strip()
    interview.recommendation_reason = request.form.get("recommendation_reason", "").strip()
    db.session.commit()
    return redirect(url_for("summary", interview_id=interview_id))


@app.route("/interviews/<int:interview_id>/export")
def export_interview(interview_id: int):
    interview = Interview.query.get_or_404(interview_id)
    candidate = interview.candidate
    questions = Question.query.filter_by(interview_id=interview_id).all()
    notes = Note.query.filter_by(interview_id=interview_id).all()
    scores = Score.query.filter_by(interview_id=interview_id).all()

    payload = {
        "candidate": {
            "name": candidate.name,
            "education": candidate.education,
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
    write_line(f"Education: {candidate.education or 'N/A'}")
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

    write_line("Questions:", bold=True)
    for question in questions:
        status = "Asked" if question.asked else "Skipped"
        rating = question.rating if question.rating is not None else "N/A"
        write_line(f"- {question.skill}: {question.text} ({status}, Rating: {rating})")
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
