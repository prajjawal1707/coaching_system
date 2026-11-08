import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Student,
    Payment,
    Instalment,
    DemoStudentCredential,
    ParentStudentLink,
    UserProfile,
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
        "test_scores": [],
    }