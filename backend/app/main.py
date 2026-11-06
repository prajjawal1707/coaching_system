from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from uuid import uuid4
from fastapi import FastAPI, Depends, HTTPException, status
from app.schemas.student import StudentCreate, StudentUpdate

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
from app.services.refunds import calculate_prorata_refund


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


@app.get("/")
def home():
    return {
        "message": "Welcome to FeeFlow API",
        "status": "running"
    }


@app.get("/students", response_model=list[StudentResponse])
def get_students(db: Session = Depends(get_db)):
    return db.query(Student).all()


@app.get("/students/{student_id}", response_model=StudentResponse)
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
    "/students",
    response_model=StudentResponse,
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
    response_model=StudentResponse
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

@app.get("/fees/{student_id}", response_model=FeeResponse)
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
    response_model=PaymentResponse,
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

@app.get("/payments/{student_id}", response_model=list[PaymentResponse])
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
    "/instalments/{student_id}",
    response_model=list[InstalmentResponse]
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

@app.post("/reminders/run")
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
    
@app.get("/reminders")
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
    response_model=RefundCalculateResponse
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
