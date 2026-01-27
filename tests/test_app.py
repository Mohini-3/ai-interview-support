from __future__ import annotations

import json

from app.constants import DEFAULT_BRANCHES, DEFAULT_DEGREES, DEFAULT_ROLES, DEFAULT_YEARS
from app.extensions import db
from app.models import Interview, Note, Question, Score
from tests.conftest import extract_interview_id


def _valid_payload(**overrides):
    payload = {
        "name": "Asha Rao",
        "email": "asha@example.com",
        "branch": DEFAULT_BRANCHES[0],
        "degree": DEFAULT_DEGREES[0],
        "year": DEFAULT_YEARS[0],
        "role": DEFAULT_ROLES[0],
        "skills": ["Python"],
    }
    payload.update(overrides)
    return payload


def test_dashboard_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Interviewer Dashboard" in response.data


def test_create_interview_missing_fields_redirects(client):
    response = client.post("/interviews", data={"name": "Asha"})
    assert response.status_code == 302
    assert "error=missing" in response.headers["Location"]


def test_create_interview_duplicate_email(client):
    payload = _valid_payload()
    first = client.post("/interviews", data=payload)
    assert first.status_code == 302

    duplicate = client.post("/interviews", data=payload)
    assert duplicate.status_code == 302
    assert "error=duplicate" in duplicate.headers["Location"]


def test_summary_blocked_until_completed(client):
    response = client.post("/interviews", data=_valid_payload())
    interview_id = extract_interview_id(response.headers["Location"])

    summary = client.get(f"/interviews/{interview_id}/summary")
    assert summary.status_code == 200
    assert b"Summary is available only after the interview is completed" in summary.data


def test_end_interview_and_generate_summary(client, app):
    response = client.post("/interviews", data=_valid_payload())
    interview_id = extract_interview_id(response.headers["Location"])

    end_response = client.post(f"/interviews/{interview_id}/end")
    assert end_response.status_code == 302

    generate = client.post(f"/api/interviews/{interview_id}/generate_summary")
    assert generate.status_code == 200
    data = json.loads(generate.data)
    assert "recommendation" in data

    with app.app_context():
        interview = db.session.get(Interview, interview_id)
        assert interview.status == "completed"


def test_pdf_export_asked_questions_only(client, app):
    response = client.post("/interviews", data=_valid_payload())
    interview_id = extract_interview_id(response.headers["Location"])

    with app.app_context():
        question = Question.query.filter_by(interview_id=interview_id).first()
        assert question is not None
        question.asked = True
        question.note = "Good explanation."
        db.session.commit()

    client.post(f"/interviews/{interview_id}/end")
    pdf_response = client.get(f"/interviews/{interview_id}/export/pdf")
    assert pdf_response.status_code == 200
    assert pdf_response.mimetype == "application/pdf"


def test_update_question_marks_asked_and_note(client, app):
    response = client.post("/interviews", data=_valid_payload())
    interview_id = extract_interview_id(response.headers["Location"])

    with app.app_context():
        question = Question.query.filter_by(interview_id=interview_id).first()
        assert question is not None
        question_id = question.id

    update = client.post(
        f"/api/interviews/{interview_id}/questions/{question_id}",
        data=json.dumps({"asked": True, "rating": 4, "note": "Solid answer"}),
        content_type="application/json",
    )
    assert update.status_code == 200

    with app.app_context():
        updated = db.session.get(Question, question_id)
        assert updated.asked is True
        assert updated.rating == 4
        assert updated.note == "Solid answer"


def test_add_note_with_other_skill(client, app):
    response = client.post("/interviews", data=_valid_payload())
    interview_id = extract_interview_id(response.headers["Location"])

    note_response = client.post(
        f"/api/interviews/{interview_id}/notes",
        data=json.dumps({
            "skill": "other",
            "custom_skill": "Problem Solving",
            "tag": "Strength",
            "text": "Great reasoning",
        }),
        content_type="application/json",
    )
    assert note_response.status_code == 200

    with app.app_context():
        note = Note.query.filter_by(interview_id=interview_id).first()
        assert note is not None
        assert note.skill == "Problem Solving"


def test_update_score(client, app):
    response = client.post("/interviews", data=_valid_payload())
    interview_id = extract_interview_id(response.headers["Location"])

    score_response = client.post(
        f"/api/interviews/{interview_id}/scores",
        data=json.dumps({"skill": "Python", "value": 5}),
        content_type="application/json",
    )
    assert score_response.status_code == 200

    with app.app_context():
        score = Score.query.filter_by(interview_id=interview_id, skill="Python").first()
        assert score is not None
        assert score.value == 5


def test_filters_by_role_and_recommendation(client, app):
    response = client.post("/interviews", data=_valid_payload())
    interview_id = extract_interview_id(response.headers["Location"])

    client.post(f"/interviews/{interview_id}/end")
    client.post(f"/api/interviews/{interview_id}/generate_summary")

    with app.app_context():
        interview = db.session.get(Interview, interview_id)
        assert interview is not None
        role = interview.candidate.role
        recommendation = interview.recommendation

    filtered = client.get(f"/?role={role}&recommendation={recommendation}")
    assert filtered.status_code == 200
    assert role.encode() in filtered.data


def test_summary_shows_only_asked_questions(client, app):
    response = client.post("/interviews", data=_valid_payload())
    interview_id = extract_interview_id(response.headers["Location"])

    with app.app_context():
        questions = Question.query.filter_by(interview_id=interview_id).all()
        assert len(questions) >= 1
        questions[0].asked = True
        questions[0].note = "Good" 
        if len(questions) > 1:
            questions[1].asked = False
        db.session.commit()

    client.post(f"/interviews/{interview_id}/end")
    summary = client.get(f"/interviews/{interview_id}/summary")
    assert summary.status_code == 200
    assert b"Asked Questions" in summary.data
