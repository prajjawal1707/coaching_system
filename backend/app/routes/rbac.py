import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
from app.services.receipts import build_payment_receipt

from app.database import get_db
from app.models import (
    Student,
    Payment,
    PaymentLink,
    Instalment,
    DemoStudentCredential,
    ParentStudentLink,
    UserProfile,
    AttendanceRecord,
    TestScore,
)
from app.services.rbac_auth import (
    FEEFLOW_DEMO_ADMIN_KEY,
    generate_access_code,
    hash_access_code,
    check_access_code,

    create_demo_token,
    read_demo_token,
    verify_supabase_user,
)

router = APIRouter()


class DemoLoginRequest(BaseModel):
    student_id: str = Field(min_length=1, max_length=50)
    code: str = Field(pattern=r"^\d{8}$")


class AccountantLoginRequest(BaseModel):
    access_token: str


def require_demo_admin(
    x_demo_admin_key: str = Header(default=""),
):
    if not secrets.compare_digest(
        x_demo_admin_key,
        FEEFLOW_DEMO_ADMIN_KEY,
    ):
        raise HTTPException(403, "Demo administrator access denied.")


def get_demo_claims(
    authorization: str = Header(default=""),
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Login required.")

    token = authorization[7:].strip()

    try:
        return read_demo_token(token)
    except ValueError:
        raise HTTPException(401, "Invalid or expired session.")

def require_active_parent(
    claims: dict,
    db: Session,
):
    if claims.get("role") != "parent":
        raise HTTPException(403, "Parent access required.")

    try:
        link_id = UUID(claims["link_id"])
    except (KeyError, ValueError, TypeError):
        raise HTTPException(403, "Invalid parent session.")

    link = db.query(ParentStudentLink).filter(
        ParentStudentLink.id == link_id,
        ParentStudentLink.student_id == claims["sub"],
        ParentStudentLink.active.is_(True),
    ).first()

    if not link:
        raise HTTPException(403, "Parent access has been revoked.")

    return claims["sub"]

def require_accountant(
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Accountant login required.")

    token = authorization[7:].strip()

    try:
        supabase_user = verify_supabase_user(token)
        user_id = UUID(supabase_user["id"])
    except Exception:
        raise HTTPException(401, "Invalid Supabase session.")

    profile = db.query(UserProfile).filter(
        UserProfile.user_id == user_id
    ).first()

    if not profile or profile.role != "accountant":
        raise HTTPException(403, "Accountant permission required.")

    return profile


@router.post(
    "/rbac/admin/students/{student_id}/generate-code",
    dependencies=[Depends(require_demo_admin)],
)
def generate_student_code(
    student_id: str,
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if not student:
        raise HTTPException(404, "Student not found.")

    code = generate_access_code()

    credential = db.query(DemoStudentCredential).filter(
        DemoStudentCredential.student_id == student_id
    ).first()

    if credential:
        credential.code_hash = hash_access_code(
            "student", student_id, code
        )
        credential.active = True
        credential.failed_attempts = 0
        credential.locked_until = None
    else:
        credential = DemoStudentCredential(
            student_id=student_id,
            code_hash=hash_access_code("student", student_id, code),
            active=True,
            failed_attempts=0,
        )
        db.add(credential)

    db.commit()

    return {
        "student_id": student.id,
        "student_name": student.name,
        "student_code": code,
        "message": "Give this code to the student. It will not be shown again.",
    }


@router.post(
    "/rbac/admin/students/{student_id}/generate-parent-code",
    dependencies=[Depends(require_demo_admin)],
)
def generate_parent_code(
    student_id: str,
    parent_label: str = "Parent",
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if not student:
        raise HTTPException(404, "Student not found.")

    code = generate_access_code()

    link = ParentStudentLink(
        student_id=student_id,
        parent_label=parent_label,
        code_hash=hash_access_code("parent", student_id, code),
        active=True,
        failed_attempts=0,
    )

    db.add(link)
    db.commit()
    db.refresh(link)

    return {
        "link_id": str(link.id),
        "student_id": student.id,
        "student_name": student.name,
        "parent_label": link.parent_label,
        "parent_code": code,
        "message": "Give this separate code to the linked parent. It will not be shown again.",
    }


@router.post("/rbac/student/login")
def student_login(
    request: DemoLoginRequest,
    db: Session = Depends(get_db),
):
    credential = db.query(DemoStudentCredential).filter(
        DemoStudentCredential.student_id == request.student_id
    ).first()

    if not credential or not credential.active:
        raise HTTPException(401, "Invalid Student ID or code.")

    now = datetime.now(timezone.utc)

    if credential.locked_until and now < credential.locked_until:
        raise HTTPException(429, "Too many attempts. Try again later.")

    if not check_access_code(
        "student",
        request.student_id,
        request.code,
        credential.code_hash,
    ):
        credential.failed_attempts += 1

        if credential.failed_attempts >= 5:
            credential.locked_until = now + timedelta(minutes=15)
            credential.failed_attempts = 0

        db.commit()
        raise HTTPException(401, "Invalid Student ID or code.")

    credential.failed_attempts = 0
    credential.locked_until = None
    db.commit()

    student = db.query(Student).filter(
        Student.id == request.student_id
    ).first()

    token = create_demo_token("student", student.id)

    return {
        "access_token": token,
        "role": "student",
        "student_id": student.id,
        "student_name": student.name,
    }


@router.post("/rbac/parent/login")
def parent_login(
    request: DemoLoginRequest,
    db: Session = Depends(get_db),
):
    links = db.query(ParentStudentLink).filter(
        ParentStudentLink.student_id == request.student_id,
        ParentStudentLink.active.is_(True),
    ).all()

    now = datetime.now(timezone.utc)

    matched_link = None

    for link in links:
        if link.locked_until and now < link.locked_until:
            continue

        if check_access_code(
            "parent",
            request.student_id,
            request.code,
            link.code_hash,
        ):
            matched_link = link
            break

    if not matched_link:
        for link in links:
            if link.locked_until and now < link.locked_until:
                continue

            link.failed_attempts += 1

            if link.failed_attempts >= 5:
                link.locked_until = now + timedelta(minutes=15)
                link.failed_attempts = 0

        db.commit()
        raise HTTPException(401, "Invalid Student ID or parent code.")

    matched_link.failed_attempts = 0
    matched_link.locked_until = None
    db.commit()

    student = db.query(Student).filter(
        Student.id == request.student_id
    ).first()

    token = create_demo_token(
        "parent",
        student.id,
        str(matched_link.id),
    )

    return {
        "access_token": token,
        "role": "parent",
        "student_id": student.id,
        "student_name": student.name,
        "parent_label": matched_link.parent_label,
    }


@router.post("/rbac/accountant/verify")
def accountant_verify(
    request: AccountantLoginRequest,
    db: Session = Depends(get_db),
):
    try:
        user = verify_supabase_user(request.access_token)
        user_id = UUID(user["id"])
    except Exception:
        raise HTTPException(401, "Invalid Supabase session.")

    profile = db.query(UserProfile).filter(
        UserProfile.user_id == user_id
    ).first()

    if not profile or profile.role != "accountant":
        raise HTTPException(403, "This account is not authorised as an accountant.")

    return {
        "role": "accountant",
        "user_id": str(user_id),
        "full_name": profile.full_name,
    }


@router.get("/rbac/me")
def current_demo_user(
    claims: dict = Depends(get_demo_claims),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(
        Student.id == claims["sub"]
    ).first()

    if not student:
        raise HTTPException(404, "Student record not found.")

    if claims["role"] == "parent":
        link_id = claims.get("link_id")

        link = db.query(ParentStudentLink).filter(
            ParentStudentLink.id == UUID(link_id),
            ParentStudentLink.student_id == student.id,
            ParentStudentLink.active.is_(True),
        ).first()

        if not link:
            raise HTTPException(403, "Parent access has been revoked.")

    return {
        "role": claims["role"],
        "student_id": student.id,
        "student_name": student.name,
    }


@router.get("/rbac/student/portal")
def student_portal(
    claims: dict = Depends(get_demo_claims),
    db: Session = Depends(get_db),
):
    if claims["role"] != "student":
        raise HTTPException(403, "Student access required.")

    return build_student_portal(claims["sub"], db)


@router.get("/rbac/parent/portal")
def parent_portal(
    claims: dict = Depends(get_demo_claims),
    db: Session = Depends(get_db),
):
    if claims["role"] != "parent":
        raise HTTPException(403, "Parent access required.")

    link_id = claims.get("link_id")

    link = db.query(ParentStudentLink).filter(
        ParentStudentLink.id == UUID(link_id),
        ParentStudentLink.student_id == claims["sub"],
        ParentStudentLink.active.is_(True),
    ).first()

    if not link:
        raise HTTPException(403, "Parent access has been revoked.")

    result = build_student_portal(claims["sub"], db)
    result["parent_label"] = link.parent_label

    return result


def build_student_portal(student_id: str, db: Session):
    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if not student:
        raise HTTPException(404, "Student not found.")

    instalments = (
        db.query(Instalment)
        .filter(Instalment.student_id == student_id)
        .order_by(Instalment.due_date.asc())
        .all()
    )
    attendance_records = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.student_id == student_id)
        .order_by(AttendanceRecord.attendance_date.desc())
        .all()
    )

    test_scores = (
        db.query(TestScore)
        .filter(TestScore.student_id == student_id)
        .order_by(TestScore.test_date.desc())
        .all()
    )   

    payments = (
        db.query(Payment)
        .filter(Payment.student_id == student_id)
        .order_by(Payment.payment_date.desc())
        .all()
    )

    return {
        "student": {
            "id": student.id,
            "name": student.name,
            "course": student.course,
            "batch": student.batch,
            "centre": getattr(student, "centre", None),
            "total_fees": student.total_fees,
            "paid_fees": student.paid_fees,
            "pending_fees": max(
                0,
                student.total_fees - student.paid_fees,
            ),
            "attendance": student.attendance,
        },
        "instalments": [
            {
                "id": str(item.id),
                "instalment_number": item.instalment_number,
                "amount": item.amount,
                "paid_amount": item.paid_amount,
                "pending_amount": max(0, item.amount - item.paid_amount),
                "due_date": item.due_date.isoformat() if item.due_date else None,
                "status": item.status,
            }
            for item in instalments
        ],
        "payments": [
            {
                "id": str(item.id),
                "amount": item.amount,
                "payment_date": item.payment_date.isoformat() if item.payment_date else None,
                "payment_method": item.payment_method,
                "transaction_reference": item.transaction_reference,
                "status": item.status,
            }
            for item in payments
        ],
        "test_scores": [
        {
            "id": str(item.id),
            "test_name": item.test_name,
            "test_date": item.test_date.isoformat(),
            "score": item.score,
            "max_score": item.max_score,
        }
        for item in test_scores
    ],

    "attendance_records": [
        {
            "id": str(item.id),
            "attendance_date": item.attendance_date.isoformat(),
            "status": item.status,
        }
        for item in attendance_records],
    }

@router.post("/rbac/parent/instalments/{instalment_id}/payment-link")
def create_parent_payment_link(
    instalment_id: str,
    claims: dict = Depends(get_demo_claims),
    db: Session = Depends(get_db),
):
    student_id = require_active_parent(claims, db)

    try:
        instalment_uuid = UUID(instalment_id)
    except ValueError:
        raise HTTPException(400, "Invalid instalment ID.")

    instalment = (
        db.query(Instalment)
        .filter(
            Instalment.id == instalment_uuid,
            Instalment.student_id == student_id,
        )
        .with_for_update()
        .first()
    )

    if not instalment:
        raise HTTPException(404, "Instalment not found.")

    outstanding = int(instalment.amount - instalment.paid_amount)

    if outstanding <= 0:
        raise HTTPException(400, "This instalment is already paid.")

    # Mark any previous unpaid links for this instalment as expired.
    old_links = db.query(PaymentLink).filter(
        PaymentLink.instalment_id == instalment.id,
        PaymentLink.status == "pending",
    ).all()

    for old_link in old_links:
        old_link.status = "expired"

    payment_link = PaymentLink(
        student_id=student_id,
        instalment_id=instalment.id,
        amount=outstanding,
        status="pending",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )

    try:
        db.add(payment_link)
        db.commit()
        db.refresh(payment_link)
    except Exception:
        db.rollback()
        raise HTTPException(500, "Could not create payment link.")

    return {
        "payment_link_id": str(payment_link.id),
        "student_id": student_id,
        "instalment_id": str(instalment.id),
        "instalment_number": instalment.instalment_number,
        "amount": payment_link.amount,
        "status": payment_link.status,
        "expires_at": payment_link.expires_at.isoformat(),
        "message": "Mock payment link created. It expires in 30 minutes.",
    }
@router.get("/rbac/parent/payment-links/{link_id}")
def get_parent_payment_link(
    link_id: str,
    claims: dict = Depends(get_demo_claims),
    db: Session = Depends(get_db),
):
    student_id = require_active_parent(claims, db)

    try:
        link_uuid = UUID(link_id)
    except ValueError:
        raise HTTPException(400, "Invalid payment link.")

    link = db.query(PaymentLink).filter(
        PaymentLink.id == link_uuid,
        PaymentLink.student_id == student_id,
    ).first()

    if not link:
        raise HTTPException(404, "Payment link not found.")

    now = datetime.now(timezone.utc)

    if link.status == "pending" and link.expires_at <= now:
        link.status = "expired"
        db.commit()

    instalment = db.query(Instalment).filter(
        Instalment.id == link.instalment_id,
    ).first()

    return {
        "payment_link_id": str(link.id),
        "student_id": link.student_id,
        "instalment_number": instalment.instalment_number if instalment else None,
        "amount": link.amount,
        "status": link.status,
        "expires_at": link.expires_at.isoformat(),
    }
@router.post("/rbac/parent/payment-links/{link_id}/confirm")
def confirm_parent_mock_payment(
    link_id: str,
    claims: dict = Depends(get_demo_claims),
    db: Session = Depends(get_db),
):
    student_id = require_active_parent(claims, db)

    try:
        link_uuid = UUID(link_id)
    except ValueError:
        raise HTTPException(400, "Invalid payment link.")

    try:
        # Lock the payment link, student and instalment while processing.
        link = (
            db.query(PaymentLink)
            .filter(
                PaymentLink.id == link_uuid,
                PaymentLink.student_id == student_id,
            )
            .with_for_update()
            .first()
        )

        if not link:
            raise HTTPException(404, "Payment link not found.")

        if link.status == "paid":
            raise HTTPException(409, "This payment link has already been used.")

        now = datetime.now(timezone.utc)

        if link.status != "pending" or link.expires_at <= now:
            link.status = "expired"
            db.commit()
            raise HTTPException(410, "This payment link has expired.")

        student = (
            db.query(Student)
            .filter(Student.id == student_id)
            .with_for_update()
            .first()
        )

        instalment = (
            db.query(Instalment)
            .filter(
                Instalment.id == link.instalment_id,
                Instalment.student_id == student_id,
            )
            .with_for_update()
            .first()
        )

        if not student or not instalment:
            raise HTTPException(404, "Student or instalment not found.")

        outstanding = int(instalment.amount - instalment.paid_amount)

        if outstanding <= 0:
            raise HTTPException(409, "This instalment is already paid.")

        if link.amount != outstanding:
            link.status = "expired"
            db.commit()
            raise HTTPException(
                409,
                "The outstanding amount changed. Generate a new payment link.",
            )

        if link.amount > student.total_fees - student.paid_fees:
            raise HTTPException(409, "Payment exceeds the student's outstanding fees.")

        # Simulated successful payment.
        instalment.paid_amount += link.amount
        instalment.status = (
            "paid"
            if instalment.paid_amount >= instalment.amount
            else "partially_paid"
        )

        student.paid_fees += link.amount

        payment = Payment(
            student_id=student_id,
            amount=link.amount,
            payment_method="Mock Checkout",
            transaction_reference=f"FF-{uuid4().hex[:12].upper()}",
            status="successful",
        )

        link.status = "paid"
        link.paid_at = now

        db.add(payment)
        db.commit()
        db.refresh(payment)

        return {
            "message": "Mock payment successful.",
            "payment_id": str(payment.id),
            "transaction_reference": payment.transaction_reference,
            "amount": payment.amount,
            "instalment_id": str(instalment.id),
            "instalment_status": instalment.status,
            "student_paid_fees": student.paid_fees,
            "student_pending_fees": max(
                0,
                student.total_fees - student.paid_fees,
            ),
            "payment_status": "successful",
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(500, "Could not process mock payment.")

@router.get("/rbac/parent/payments/{payment_id}/receipt")
def download_parent_receipt(
    payment_id: str,
    claims: dict = Depends(get_demo_claims),
    db: Session = Depends(get_db),
):
    student_id = require_active_parent(claims, db)

    try:
        payment_uuid = UUID(payment_id)
    except ValueError:
        raise HTTPException(400, "Invalid payment ID.")

    payment = db.query(Payment).filter(
        Payment.id == payment_uuid,
        Payment.student_id == student_id,
        Payment.status == "successful",
    ).first()

    if not payment:
        raise HTTPException(
            404,
            "Successful payment receipt not found.",
        )

    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

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