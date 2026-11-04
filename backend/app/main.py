from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from uuid import uuid4

from app.models import Student, Payment
from app.schemas.payment import PaymentCreate, PaymentResponse

from app.database import get_db
from app.models import Student
from app.schemas.student import StudentResponse, FeeResponse



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
@app.post("/payments", response_model=PaymentResponse)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db)
):
    # Lock the student row while processing this payment.
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

    new_payment = Payment(
        student_id=student.id,
        amount=payment_data.amount,
        payment_method=payment_data.payment_method,
        transaction_reference=f"FF-{uuid4().hex[:12].upper()}",
        status="successful"
    )

    try:
        student.paid_fees += payment_data.amount
        db.add(new_payment)
        db.commit()
        db.refresh(new_payment)
        return new_payment

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