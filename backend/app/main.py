from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from uuid import uuid4
from fastapi import FastAPI, Depends, HTTPException, status
from app.schemas.student import StudentCreate, StudentUpdate
import csv
import io
from fastapi.responses import Response
from app.models import Student, Payment, Instalment
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.database import get_db
from app.schemas.student import StudentResponse, FeeResponse
from app.schemas.instalment import InstalmentResponse
from datetime import date
from app.schemas.refund import (
    RefundCalculateRequest,
    RefundCalculateResponse,
)
from uuid import UUID
from fastapi.responses import StreamingResponse
from app.services.receipts import build_payment_receipt

from app.services.refunds import calculate_prorata_refund
from collections import defaultdict
from dotenv import load_dotenv
load_dotenv()
import math
from decimal import Decimal
# from app.routes.demo_parent import router as demo_parent_router
from app.routes.rbac import router as rbac_router
from app.routes.rbac import require_accountant
import csv
import io

from datetime import date
from fastapi import UploadFile, File, Query
from sqlalchemy import func

from app.models import AttendanceRecord, TestScore
from datetime import date
from decimal import Decimal

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import Student, Instalment, Payment
from app.database import get_db
from app.routes.rbac import require_accountant
import csv
import io
from fastapi.responses import StreamingResponse



app = FastAPI(
    title="FeeFlow API",
    description="Fee Management System Backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(rbac_router)
# app.include_router(demo_parent_router)

@app.get("/")
def home():
    return {
        "message": "Welcome to FeeFlow API",
        "status": "running"
    }


@app.get("/students",dependencies=[Depends(require_accountant)],
)
def get_students(db: Session = Depends(get_db)):
    return db.query(Student).all()


@app.get("/students/{student_id}", dependencies=[Depends(require_accountant)],
)
def get_student(student_id: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return student

@app.post(
    "/students",dependencies=[Depends(require_accountant)],

    status_code=status.HTTP_201_CREATED
)
def create_student(
    student_data: StudentCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(Student).filter(
        Student.id == student_data.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Student ID already exists"
        )

    if student_data.paid_fees > student_data.total_fees:
        raise HTTPException(
            status_code=400,
            detail="Paid fees cannot exceed total fees"
        )

    new_student = Student(**student_data.model_dump())

    try:
        db.add(new_student)
        db.commit()
        db.refresh(new_student)
        return new_student

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not create student"
        )


@app.patch(
    "/students/{student_id}",
    dependencies=[Depends(require_accountant)],
)
def update_student(
    student_id: str,
    student_data: StudentUpdate,
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    changes = student_data.model_dump(exclude_unset=True)

    new_total = changes.get("total_fees", student.total_fees)

    if new_total < student.paid_fees:
        raise HTTPException(
            status_code=400,
            detail="Total fees cannot be less than fees already paid"
        )

    try:
        for field, value in changes.items():
            setattr(student, field, value)

        db.commit()
        db.refresh(student)
        return student

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not update student"
        )

@app.get("/fees/{student_id}", dependencies=[Depends(require_accountant)],
)
def get_student_fees(student_id: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return {
        "student_id": student.id,
        "student_name": student.name,
        "total_fees": student.total_fees,
        "paid_fees": student.paid_fees,
        "pending_fees": student.total_fees - student.paid_fees
    }
@app.post(
    "/payments",
    dependencies=[Depends(require_accountant)],

    status_code=status.HTTP_201_CREATED
)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db)
):
    try:
        # Lock the student row while processing the payment.
        student = (
            db.query(Student)
            .filter(Student.id == payment_data.student_id)
            .with_for_update()
            .first()
        )

        if student is None:
            raise HTTPException(
                status_code=404,
                detail="Student not found"
            )

        pending = student.total_fees - student.paid_fees

        if payment_data.amount > pending:
            raise HTTPException(
                status_code=400,
                detail=f"Payment exceeds pending fees of {pending}"
            )

        # Get the student's instalments in due-date order.
        instalments = (
            db.query(Instalment)
            .filter(Instalment.student_id == student.id)
            .order_by(Instalment.instalment_number.asc())
            .with_for_update()
            .all()
        )

        remaining_payment = payment_data.amount

        # Allocate the payment to the earliest unpaid instalments.
        for instalment in instalments:
            if remaining_payment <= 0:
                break

            outstanding = instalment.amount - instalment.paid_amount

            if outstanding <= 0:
                continue

            allocation = min(outstanding, remaining_payment)

            instalment.paid_amount += allocation
            remaining_payment -= allocation

            if instalment.paid_amount == instalment.amount:
                instalment.status = "paid"
            else:
                instalment.status = "partially_paid"

        # Reject payment if the instalment schedule cannot account for it.
        if remaining_payment > 0:
            raise HTTPException(
                status_code=400,
                detail="Instalment schedule does not cover this payment."
            )

        # Update student's overall fee balance.
        student.paid_fees += payment_data.amount

        new_payment = Payment(
            student_id=student.id,
            amount=payment_data.amount,
            payment_method=payment_data.payment_method,
            transaction_reference=f"FF-{uuid4().hex[:12].upper()}",
            status="successful"
        )

        db.add(new_payment)
        db.commit()
        db.refresh(new_payment)

        return new_payment

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Payment could not be saved"
        )

@app.get("/payments/{student_id}", dependencies=[Depends(require_accountant)], response_model=list[PaymentResponse])
def get_payments(
    student_id: str,
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return (
        db.query(Payment)
        .filter(Payment.student_id == student_id)
        .order_by(Payment.payment_date.desc())
        .all()
    )
@app.get(
    "/instalments/{student_id}",dependencies=[Depends(require_accountant)],
)
def get_instalments(
    student_id: str,
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return (
        db.query(Instalment)
        .filter(Instalment.student_id == student_id)
        .order_by(Instalment.due_date.asc())
        .all()
    )



from app.models import ReminderEvent
from app.services.reminders import (
    get_reminder_stage,
    create_reminder_message,
)

@app.post("/reminders/run", dependencies=[Depends(require_accountant)])
def run_reminders(
    language: str = "en",
    db: Session = Depends(get_db)
):
    if language not in ["en", "hi"]:
        raise HTTPException(
            status_code=400,
            detail="Language must be en or hi"
        )

    instalments = (
        db.query(Instalment)
        .join(Student, Instalment.student_id == Student.id)
        .all()
    )

    prepared = []
    skipped = 0

    try:
        for instalment in instalments:

            # Fully paid instalments never receive reminders.
            outstanding = instalment.amount - instalment.paid_amount

            if outstanding <= 0:
                skipped += 1
                continue

            stage = get_reminder_stage(instalment.due_date)

            if stage is None:
                continue

            # Do not prepare the same stage twice.
            existing = db.query(ReminderEvent).filter(
                ReminderEvent.instalment_id == instalment.id,
                ReminderEvent.stage == stage
            ).first()

            if existing:
                skipped += 1
                continue

            student = db.query(Student).filter(
                Student.id == instalment.student_id
            ).first()

            message = create_reminder_message(
                student_name=student.name,
                amount=outstanding,
                due_date=instalment.due_date,
                stage=stage,
                language=language
            )

            event = ReminderEvent(
                instalment_id=instalment.id,
                student_id=student.id,
                stage=stage,
                language=language,
                message=message,
                status="mock_prepared"
            )

            db.add(event)

            prepared.append({
                "student": student.name,
                "instalment_number": instalment.instalment_number,
                "stage": stage,
                "language": language,
                "message": message,
                "status": "mock_prepared"
            })

        db.commit()

        return {
            "message": "Reminder run completed",
            "prepared_count": len(prepared),
            "skipped_count": skipped,
            "delivery": "MOCK ONLY",
            "reminders": prepared
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not process reminders"
        )
    
@app.get("/reminders", dependencies=[Depends(require_accountant)],)
def get_reminder_history(db: Session = Depends(get_db)):
    events = (
        db.query(ReminderEvent)
        .order_by(ReminderEvent.created_at.desc())
        .all()
    )

    return [
        {
            "id": str(event.id),
            "student_id": event.student_id,
            "instalment_id": str(event.instalment_id),
            "stage": event.stage,
            "language": event.language,
            "message": event.message,
            "status": event.status,
            "created_at": event.created_at
        }
        for event in events
    ]
    

@app.post(
    "/refunds/{student_id}/calculate",
    dependencies=[Depends(require_accountant)]
)
def calculate_student_refund(
    student_id: str,
    refund_data: RefundCalculateRequest,
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    try:
        result = calculate_prorata_refund(
            net_fee=student.total_fees,
            amount_paid=student.paid_fees,
            course_start_date=refund_data.course_start_date,
            course_end_date=refund_data.course_end_date,
            leaving_date=refund_data.leaving_date,
        )

        return {
            "student_id": student.id,
            "student_name": student.name,
            **result,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

@app.get("/reports/dues", dependencies=[Depends(require_accountant)])
def get_dues_dashboard(db: Session = Depends(get_db)):
    today = date.today()

    students = db.query(Student).all()
    instalments = db.query(Instalment).all()

    # Prepare one report group for each centre and batch.
    groups = defaultdict(lambda: {
        "centre": "",
        "batch": "",
        "student_count": 0,
        "total_outstanding": 0,
        "current_due": 0,
        "overdue_1_30": 0,
        "overdue_31_60": 0,
        "overdue_over_60": 0,
    })

    student_lookup = {student.id: student for student in students}

    for student in students:
        key = (student.centre or "Unassigned", student.batch)

        groups[key]["centre"] = student.centre or "Unassigned"
        groups[key]["batch"] = student.batch
        groups[key]["student_count"] += 1

    for instalment in instalments:
        student = student_lookup.get(instalment.student_id)

        if student is None:
            continue

        outstanding = max(
            0,
            instalment.amount - instalment.paid_amount
        )

        if outstanding == 0:
            continue

        key = (student.centre or "Unassigned", student.batch)
        group = groups[key]

        group["total_outstanding"] += outstanding

        days_overdue = (today - instalment.due_date).days

        if days_overdue <= 0:
            group["current_due"] += outstanding
        elif days_overdue <= 30:
            group["overdue_1_30"] += outstanding
        elif days_overdue <= 60:
            group["overdue_31_60"] += outstanding
        else:
            group["overdue_over_60"] += outstanding

    return {
        "report_date": today,
        "ageing_buckets": [
            "current",
            "1-30 days",
            "31-60 days",
            "over 60 days"
        ],
        "groups": list(groups.values()),
        "note": (
            "Ageing is calculated from instalment due dates. "
            "Students without a centre assignment appear as Unassigned."
        )
    }

@app.get("/reports/payments/export.csv", dependencies=[Depends(require_accountant)])
def export_payments_csv(db: Session = Depends(get_db)):
    payments = (
        db.query(Payment, Student)
        .join(Student, Payment.student_id == Student.id)
        .order_by(Payment.payment_date.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Payment ID",
        "Student ID",
        "Student Name",
        "Amount",
        "Payment Date",
        "Payment Method",
        "Transaction Reference",
        "Status",
    ])

    for payment, student in payments:
        payment_date = (
            payment.payment_date.isoformat()
            if payment.payment_date
            else ""
        )

        writer.writerow([
            str(payment.id),
            student.id,
            student.name,
            payment.amount,
            payment_date,
            payment.payment_method,
            payment.transaction_reference or "",
            payment.status,
        ])

    csv_content = "\ufeff" + output.getvalue()

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition":
                'attachment; filename="feeflow-payments.csv"'
        },
    )



@app.get("/exports/tally/payments")
def export_tally_payments(
    db: Session = Depends(get_db),
    accountant=Depends(require_accountant),
):
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Voucher Type",
        "Voucher Date",
        "Voucher Number",
        "Party Ledger",
        "Amount",
        "Narration",
        "Student ID",
        "Student Name",
        "Centre",
        "Batch",
        "Payment Method",
        "Transaction Reference",
    ])

    records = (
        db.query(Payment, Student)
        .join(Student, Payment.student_id == Student.id)
        .filter(Payment.status == "successful")
        .order_by(Payment.payment_date.asc())
        .all()
    )

    for payment, student in records:
        payment_date = payment.payment_date

        if hasattr(payment_date, "strftime"):
            tally_date = payment_date.strftime("%Y%m%d")
        else:
            tally_date = ""

        voucher_number = (
            f"FF-REC-{str(payment.id).replace('-', '').upper()}"
        )

        writer.writerow([
            "Receipt",
            tally_date,
            voucher_number,
            student.name,
            f"{Decimal(str(payment.amount)):.2f}",
            f"Fee payment received from {student.name}",
            student.id,
            student.name,
            student.centre or "",
            student.batch or "",
            payment.payment_method or "",
            payment.transaction_reference or "",
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
                'attachment; filename="FeeFlow_Tally_Payments.csv"'
        },
    )


@app.post(
    "/uploads/attendance",
    dependencies=[Depends(require_accountant)],
)
async def upload_attendance_csv(
    batch: str = Query(..., min_length=1),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Please upload a CSV file.")

    content = await file.read()

    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, "CSV file must be smaller than 5 MB.")

    try:
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))

        required = {
            "student_id",
            "attendance_date",
            "status",
        }

        if not reader.fieldnames or not required.issubset(
            set(reader.fieldnames)
        ):
            raise HTTPException(
                422,
                "Required columns: student_id, attendance_date, status",
            )

        rows = list(reader)

    except UnicodeDecodeError:
        raise HTTPException(400, "CSV must use UTF-8 encoding.")

    if not rows:
        raise HTTPException(400, "CSV contains no data rows.")

    validated = []
    errors = []
    seen = set()

    for line_number, row in enumerate(rows, start=2):
        student_id = (row.get("student_id") or "").strip()
        date_value = (row.get("attendance_date") or "").strip()
        status_value = (row.get("status") or "").strip().lower()

        try:
            if not student_id:
                raise ValueError("Student ID is missing.")

            if status_value not in {"present", "absent"}:
                raise ValueError("Status must be present or absent.")

            attendance_date = date.fromisoformat(date_value)

            key = (student_id, attendance_date)

            if key in seen:
                raise ValueError("Duplicate student/date in this CSV.")

            seen.add(key)

            student = db.query(Student).filter(
                Student.id == student_id,
                Student.batch == batch,
            ).first()

            if not student:
                raise ValueError(
                    f"{student_id} does not exist in batch {batch}."
                )

            validated.append({
                "student": student,
                "date": attendance_date,
                "status": status_value,
            })

        except ValueError as error:
            errors.append({
                "row": line_number,
                "student_id": student_id,
                "error": str(error),
            })

    if errors:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "No records were saved. Correct the CSV errors.",
                "errors": errors,
            },
        )

    try:
        affected_students = set()

        for item in validated:
            student = item["student"]
            affected_students.add(student.id)

            existing = db.query(AttendanceRecord).filter(
                AttendanceRecord.student_id == student.id,
                AttendanceRecord.attendance_date == item["date"],
            ).first()

            if existing:
                existing.status = item["status"]
            else:
                db.add(
                    AttendanceRecord(
                        student_id=student.id,
                        attendance_date=item["date"],
                        status=item["status"],
                    )
                )

        db.flush()

        for affected_id in affected_students:
            total_sessions = db.query(AttendanceRecord).filter(
                AttendanceRecord.student_id == affected_id
            ).count()

            present_sessions = db.query(AttendanceRecord).filter(
                AttendanceRecord.student_id == affected_id,
                AttendanceRecord.status == "present",
            ).count()

            student = db.query(Student).filter(
                Student.id == affected_id
            ).first()

            if total_sessions:
                student.attendance = round(
                    present_sessions / total_sessions * 100
                )

        db.commit()

        return {
            "message": "Attendance uploaded successfully.",
            "batch": batch,
            "records_processed": len(validated),
            "students_updated": len(affected_students),
        }

    except Exception:
        db.rollback()
        raise HTTPException(500, "Attendance upload failed.")
@app.post(
    "/uploads/test-scores",
    dependencies=[Depends(require_accountant)],
)
async def upload_test_scores_csv(
    batch: str = Query(..., min_length=1),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Please upload a CSV file.")

    content = await file.read()

    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, "CSV file must be smaller than 5 MB.")

    try:
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))

        required = {
            "student_id",
            "test_name",
            "test_date",
            "score",
            "max_score",
        }

        if not reader.fieldnames or not required.issubset(
            set(reader.fieldnames)
        ):
            raise HTTPException(
                422,
                "Required columns: student_id, test_name, test_date, score, max_score",
            )

        rows = list(reader)

    except UnicodeDecodeError:
        raise HTTPException(400, "CSV must use UTF-8 encoding.")

    if not rows:
        raise HTTPException(400, "CSV contains no data rows.")

    validated = []
    errors = []
    seen = set()

    for line_number, row in enumerate(rows, start=2):
        student_id = (row.get("student_id") or "").strip()
        test_name = (row.get("test_name") or "").strip()

        try:
            if not student_id or not test_name:
                raise ValueError("Student ID and test name are required.")

            test_date = date.fromisoformat(
                (row.get("test_date") or "").strip()
            )

            score = float(row.get("score"))
            max_score = float(row.get("max_score"))
            if not math.isfinite(score) or not math.isfinite(max_score):
                raise ValueError("Score values must be valid finite numbers.")

            if max_score <= 0:
                raise ValueError("Maximum score must be greater than zero.")

            if score < 0 or score > max_score:
                raise ValueError(
                    "Score must be between zero and maximum score."
                )

            key = (student_id, test_name, test_date)

            if key in seen:
                raise ValueError("Duplicate student/test/date in this CSV.")

            seen.add(key)

            student = db.query(Student).filter(
                Student.id == student_id,
                Student.batch == batch,
            ).first()

            if not student:
                raise ValueError(
                    f"{student_id} does not exist in batch {batch}."
                )

            validated.append({
                "student_id": student.id,
                "test_name": test_name,
                "test_date": test_date,
                "score": score,
                "max_score": max_score,
            })

        except (ValueError, TypeError) as error:
            errors.append({
                "row": line_number,
                "student_id": student_id,
                "error": str(error),
            })

    if errors:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "No records were saved. Correct the CSV errors.",
                "errors": errors,
            },
        )

    try:
        for item in validated:
            existing = db.query(TestScore).filter(
                TestScore.student_id == item["student_id"],
                TestScore.test_name == item["test_name"],
                TestScore.test_date == item["test_date"],
            ).first()

            if existing:
                existing.score = item["score"]
                existing.max_score = item["max_score"]
            else:
                db.add(TestScore(**item))

        db.commit()

        return {
            "message": "Test scores uploaded successfully.",
            "batch": batch,
            "records_processed": len(validated),
        }

    except Exception:
        db.rollback()
        raise HTTPException(500, "Test-score upload failed.")

@app.get(
    "/payments/{payment_id}/receipt",
    dependencies=[Depends(require_accountant)],
)
def download_accountant_receipt(
    payment_id: str,
    db: Session = Depends(get_db),
):
    try:
        payment_uuid = UUID(payment_id)
    except ValueError:
        raise HTTPException(400, "Invalid payment ID.")

    payment = db.query(Payment).filter(
        Payment.id == payment_uuid,
        Payment.status == "successful",
    ).first()

    if not payment:
        raise HTTPException(
            404,
            "Successful payment receipt not found.",
        )

    student = db.query(Student).filter(
        Student.id == payment.student_id
    ).first()

    if not student:
        raise HTTPException(404, "Student not found.")

    pdf = build_payment_receipt(payment, student)

    receipt_number = (
        f"FF-REC-{str(payment.id).replace('-', '').upper()}"
    )

    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{receipt_number}.pdf"'
            )
        },
    )

@app.get("/ledger/{student_id}")
def get_student_fee_ledger(
    student_id: str,
    db: Session = Depends(get_db),
    accountant=Depends(require_accountant),
):
    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    instalments = (
        db.query(Instalment)
        .filter(Instalment.student_id == student_id)
        .order_by(Instalment.due_date.asc())
        .all()
    )

    payments = (
        db.query(Payment)
        .filter(Payment.student_id == student_id)
        .order_by(Payment.payment_date.desc())
        .all()
    )

    today = date.today()
    total_fee = Decimal(str(student.total_fees or 0))
    discount = Decimal(str(student.discount_amount or 0))
    paid = Decimal(str(student.paid_fees or 0))
    balance = max(total_fee - paid, Decimal("0"))

    instalment_rows = []
    overdue_total = Decimal("0")
    overdue_days = 0

    for item in instalments:
        amount = Decimal(str(item.amount or 0))
        paid_amount = Decimal(str(item.paid_amount or 0))
        remaining = max(amount - paid_amount, Decimal("0"))

        days_late = 0
        if remaining > 0 and item.due_date < today:
            days_late = (today - item.due_date).days
            overdue_total += remaining
            overdue_days = max(overdue_days, days_late)

        instalment_rows.append({
            "id": str(item.id),
            "instalment_number": item.instalment_number,
            "amount": float(amount),
            "paid_amount": float(paid_amount),
            "balance": float(remaining),
            "due_date": item.due_date.isoformat(),
            "days_overdue": days_late,
            "status": item.status,
        })

    payment_rows = [
        {
            "id": str(payment.id),
            "amount": float(payment.amount),
            "payment_date": payment.payment_date.isoformat(),
            "payment_method": payment.payment_method,
            "transaction_reference": payment.transaction_reference,
            "status": payment.status,
        }
        for payment in payments
    ]

    return {
        "student": {
            "id": student.id,
            "name": student.name,
            "course": student.course,
            "batch": student.batch,
            "centre": student.centre,
            "fee_plan": student.fee_plan or "Not specified",
        },
        "fee_summary": {
            "fee_before_discount": float(total_fee + discount),
            "discount_amount": float(discount),
            "total_fee_payable": float(total_fee),
            "total_paid": float(paid),
            "current_balance": float(balance),
            "overdue_balance": float(overdue_total),
            "maximum_days_overdue": overdue_days,
        },
        "instalments": instalment_rows,
        "payments": payment_rows,
    }
