
import json
import os
from datetime import date, timedelta

from openai import OpenAI

from app.models import (
    Student,
    Instalment,
    AttendanceRecord,
    TestScore,
)


def collect_student_signals(db, student):
    today = date.today()

    instalments = (
        db.query(Instalment)
        .filter(Instalment.student_id == student.id)
        .all()
    )

    missed_instalments = []

    for item in instalments:
        remaining = float(item.amount or 0) - float(item.paid_amount or 0)

        if item.due_date < today and remaining > 0:
            missed_instalments.append({
                "due_date": item.due_date.isoformat(),
                "outstanding_amount": round(remaining, 2),
                "days_overdue": (today - item.due_date).days,
            })

    attendance_records = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.student_id == student.id,
            AttendanceRecord.attendance_date >= today - timedelta(days=60),
            AttendanceRecord.attendance_date <= today,
        )
        .order_by(AttendanceRecord.attendance_date.asc())
        .all()
    )

    recent_attendance = [
        item for item in attendance_records
        if item.attendance_date >= today - timedelta(days=30)
    ]

    previous_attendance = [
        item for item in attendance_records
        if today - timedelta(days=60) <= item.attendance_date < today - timedelta(days=30)
    ]

    def attendance_percentage(records):
        if not records:
            return None

        return round(
            sum(1 for item in records if item.status.lower() == "present")
            / len(records) * 100,
            1,
        )

    recent_scores = (
        db.query(TestScore)
        .filter(TestScore.student_id == student.id)
        .order_by(TestScore.test_date.desc())
        .limit(6)
        .all()
    )

    recent_scores = list(reversed(recent_scores))

    score_values = [
        round(float(item.score) / float(item.max_score) * 100, 1)
        for item in recent_scores
        if item.max_score and float(item.max_score) > 0
    ]

    return {
        "missed_instalments": missed_instalments,
        "recent_attendance_percent": attendance_percentage(recent_attendance),
        "previous_attendance_percent": attendance_percentage(previous_attendance),
        "recent_test_scores_percent": score_values,
        "attendance_records_count": len(attendance_records),
        "test_records_count": len(score_values),
    }


def assess_dropout_risk(student, signals):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    client = OpenAI(api_key=api_key)

    schema = {
        "type": "object",
        "properties": {
            "risk_level": {
                "type": "string",
                "enum": ["low", "medium", "high"],
            },
            "risk_score": {
                "type": "integer",
            },
            "is_flagged": {
                "type": "boolean",
            },
            "summary": {
                "type": "string",
            },
            "evidence": {
                "type": "array",
                "items": {"type": "string"},
            },
            "recommended_action": {
                "type": "string",
            },
        },
        "required": [
            "risk_level",
            "risk_score",
            "is_flagged",
            "summary",
            "evidence",
            "recommended_action",
        ],
        "additionalProperties": False,
    }

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {
                "role": "system",
                "content": (
                    "You assist a coaching institute counsellor by reviewing "
                    "educational engagement indicators. This is only a support "
                    "signal, not a prediction of a student's character or final "
                    "decision about enrolment. Use only the supplied data. "
                    "Do not infer personal circumstances. Missing data is not "
                    "evidence of risk. Consider missed instalments, attendance "
                    "change, and test-score trends. Flag for human review only "
                    "when there is meaningful evidence. Never recommend fee "
                    "penalties, access restrictions, or automated parent contact. "
                    "Recommend a supportive counsellor check-in. Return valid "
                    "structured output."
                ),
            },
            {
                "role": "user",
                "content": json.dumps({
                    "student_id": student.id,
                    "course": student.course,
                    "batch": student.batch,
                    "signals": signals,
                }),
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "dropout_risk_assessment",
                "strict": True,
                "schema": schema,
            },
        },
        temperature=0.2,
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError("AI returned an empty assessment.")

    result = json.loads(content)

    score = result["risk_score"]
    if not isinstance(score, int) or not 0 <= score <= 100:
        raise RuntimeError("AI returned an invalid risk score.")

    # Enforce the flag from the returned risk level and score.
    result["is_flagged"] = (
        result["risk_level"] in ("medium", "high") and score >= 40
    )

    return result
