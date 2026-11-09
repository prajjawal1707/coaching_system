
from datetime import date
from decimal import Decimal

from app.models import Instalment, ReminderEvent, Student


def build_message(student, instalment, stage, language, balance):
    due_date = instalment.due_date.strftime("%d-%m-%Y")

    if language == "hi":
        templates = {
            "before_due": (
                f"Namaste {student.name}, aapki fee ki instalment "
                f"₹{balance:.2f} {due_date} ko due hai. Kripya samay par payment karein."
            ),
            "due_today": (
                f"Namaste {student.name}, aapki fee ki instalment "
                f"₹{balance:.2f} aaj due hai. Kripya payment karein."
            ),
            "overdue": (
                f"Namaste {student.name}, aapki fee ki instalment "
                f"₹{balance:.2f} ki due date {due_date} nikal chuki hai. "
                "Kripya pending payment karein."
            ),
        }
    else:
        templates = {
            "before_due": (
                f"Hello {student.name}, your fee instalment of "
                f"₹{balance:.2f} is due on {due_date}. Please pay on time."
            ),
            "due_today": (
                f"Hello {student.name}, your fee instalment of "
                f"₹{balance:.2f} is due today. Please make the payment."
            ),
            "overdue": (
                f"Hello {student.name}, your fee instalment of "
                f"₹{balance:.2f} was due on {due_date}. "
                "Please clear the pending amount."
            ),
        }

    return templates[stage]


def get_reminder_stage(due_date, today):
    days_until_due = (due_date - today).days

    # Send the advance reminder during the 3 days before the due date.
    if 1 <= days_until_due <= 3:
        return "before_due"

    if days_until_due == 0:
        return "due_today"

    if days_until_due < 0:
        return "overdue"

    return None


def run_automatic_reminders(db, today=None):
    today = today or date.today()
    created = 0
    skipped_paid = 0
    skipped_duplicate = 0

    instalments = db.query(Instalment).all()

    for instalment in instalments:
        outstanding = (
            Decimal(str(instalment.amount))
            - Decimal(str(instalment.paid_amount or 0))
        )

        # A fully paid instalment must never receive another reminder.
        if outstanding <= 0:
            skipped_paid += 1
            continue

        stage = get_reminder_stage(instalment.due_date, today)
        if stage is None:
            continue

        student = db.query(Student).filter(
            Student.id == instalment.student_id
        ).first()

        if student is None:
            continue

        # Generate both language versions for the demo.
        for language in ("en", "hi"):
            existing = db.query(ReminderEvent).filter(
                ReminderEvent.instalment_id == instalment.id,
                ReminderEvent.stage == stage,
                ReminderEvent.language == language,
            ).first()

            if existing:
                skipped_duplicate += 1
                continue

            message = build_message(
                student, instalment, stage, language, outstanding
            )

            event = ReminderEvent(
                instalment_id=instalment.id,
                student_id=student.id,
                stage=stage,
                language=language,
                message=message,
                status="mocked",
            )

            db.add(event)
            created += 1

    db.commit()

    return {
        "date": today.isoformat(),
        "created": created,
        "skipped_paid": skipped_paid,
        "skipped_duplicate": skipped_duplicate,
    }
