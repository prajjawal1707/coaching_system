
from datetime import date
from decimal import Decimal
from sqlalchemy.dialects.postgresql import insert
from app.models import Instalment, ReminderEvent, Student


def build_message(student, instalment, stage, language, balance):
    due_date = instalment.due_date.strftime("%d-%m-%Y")

    if language == "hi":
        templates = {
            "before": (
                f"Namaste {student.name}, aapki fee ki instalment "
                f"₹{balance:.2f} {due_date} ko due hai. "
                "Kripya samay par payment karein."
            ),
            "due": (
                f"Namaste {student.name}, aapki fee ki instalment "
                f"₹{balance:.2f} aaj due hai. "
                "Kripya payment karein."
            ),
            "after": (
                f"Namaste {student.name}, aapki fee ki instalment "
                f"₹{balance:.2f} ki due date {due_date} nikal chuki hai. "
                "Kripya pending payment karein."
            ),
        }
    else:
        templates = {
            "before": (
                f"Hello {student.name}, your fee instalment of "
                f"₹{balance:.2f} is due on {due_date}. "
                "Please pay on time."
            ),
            "due": (
                f"Hello {student.name}, your fee instalment of "
                f"₹{balance:.2f} is due today. "
                "Please make the payment."
            ),
            "after": (
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
        return "before"

    if days_until_due == 0:
        return "due"

    if days_until_due < 0:
        return "after"

    return None



def run_automatic_reminders(db, today=None):
    today = today or date.today()

    created = 0
    skipped_paid = 0
    skipped_duplicate = 0

    instalments = db.query(Instalment).all()

    try:
        for instalment in instalments:
            outstanding = (
                Decimal(str(instalment.amount))
                - Decimal(str(instalment.paid_amount or 0))
            )

            # Skip fully paid instalments.
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

            # Generate both English and Hindi messages.
            english_message = build_message(
                student,
                instalment,
                stage,
                "en",
                outstanding,
            )

            hindi_message = build_message(
                student,
                instalment,
                stage,
                "hi",
                outstanding,
            )

            combined_message = (
                f"EN: {english_message}\n"
                f"HI: {hindi_message}"
            )

            # Store one event with both messages.
            # Keep language='en' because the DB allows individual codes only.
            stmt = (
                insert(ReminderEvent)
                .values(
                    instalment_id=instalment.id,
                    student_id=student.id,
                    stage=stage,
                    language="en",
                    message=combined_message,
                    status="mocked",
                )
                .on_conflict_do_nothing(
                    constraint="reminder_events_instalment_id_stage_key"
                )
            )

            result = db.execute(stmt)

            if result.rowcount == 1:
                created += 1
            else:
                skipped_duplicate += 1

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "date": today.isoformat(),
        "created": created,
        "skipped_paid": skipped_paid,
        "skipped_duplicate": skipped_duplicate,
    }
