import csv
import hashlib
import io
import secrets
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Student, Payment, Instalment, ReminderEvent
from app.models import PaymentLink, RefundRequest, UnmatchedPayment
from app.routes.rbac import require_accountant, get_demo_claims

router = APIRouter(prefix="/operations", tags=["finance-operations"])

def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def _claims_student(claims):
    role = claims.get("role")
    if role not in ("parent", "student"):
        raise HTTPException(403, "Parent or student session required.")
    student_id = claims.get("student_id")
    if not student_id:
        raise HTTPException(401, "Invalid demo session.")
    return str(student_id)

def _money(value):
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))

class RefundCreate(BaseModel):
    course_start_date: date
    course_end_date: date
    leaving_date: date

class RefundDecision(BaseModel):
    action: str = Field(pattern="^(approve|reject)$")
    approved_amount: Decimal | None = None
    notes: str | None = None

class RefundPaid(BaseModel):
    payout_reference: str = Field(min_length=1, max_length=100)

class MatchRequest(BaseModel):
    student_id: str
    instalment_id: str
    payment_method: str = "bank_transfer"

@router.post("/instalments/{instalment_id}/payment-link")
def create_mock_payment_link(
    instalment_id: str,
    claims=Depends(get_demo_claims),
    db: Session = Depends(get_db),
):
    student_id = _claims_student(claims)
    item = db.query(Instalment).filter(
        Instalment.id == instalment_id,
        Instalment.student_id == student_id
    ).with_for_update().first()
    if not item:
        raise HTTPException(404, "Instalment not found for this account.")
    due = _money(item.amount) - _money(item.paid_amount)
    if due <= 0:
        raise HTTPException(409, "This instalment is already paid.")
    raw = secrets.token_urlsafe(32)
    link = PaymentLink(
        id=uuid4(), instalment_id=item.id, student_id=student_id,
        token_hash=_hash(raw), expires_at=datetime.now(timezone.utc)+timedelta(minutes=30),
        status="open"
    )
    db.add(link)
    db.commit()
    return {
        "payment_link_id": str(link.id),
        "checkout_token": raw,
        "instalment_id": str(item.id),
        "amount": float(due),
        "expires_at": link.expires_at.isoformat(),
        "mode": "MOCK_ONLY_NO_MONEY_COLLECTED"
    }

@router.post("/checkout/{checkout_token}/confirm")
def confirm_mock_checkout(
    checkout_token: str,
    claims=Depends(get_demo_claims),
    db: Session = Depends(get_db),
):
    student_id = _claims_student(claims)
    link = db.query(PaymentLink).filter(
        PaymentLink.token_hash == _hash(checkout_token)
    ).with_for_update().first()
    now = datetime.now(timezone.utc)
    if not link or link.student_id != student_id:
        raise HTTPException(404, "Checkout link not found.")
    if link.status != "open" or link.expires_at <= now:
        raise HTTPException(409, "Checkout link is expired or already used.")
    item = db.query(Instalment).filter(
        Instalment.id == link.instalment_id,
        Instalment.student_id == student_id
    ).with_for_update().first()
    if not item:
        raise HTTPException(404, "Instalment not found.")
    balance = _money(item.amount) - _money(item.paid_amount)
    if balance <= 0:
        link.status = "closed"
        db.commit()
        raise HTTPException(409, "Instalment is already paid.")
    # This is a simulated full settlement of the remaining instalment balance.
    payment = Payment(
        student_id=student_id, instalment_id=item.id, amount=balance,
        payment_date=now, payment_method="mock_checkout",
        transaction_reference=f"MOCK-{uuid4().hex[:16].upper()}",
        status="successful"
    )
    db.add(payment)
    item.paid_amount = _money(item.paid_amount) + balance
    item.status = "paid"
    student = db.query(Student).filter(Student.id == student_id).with_for_update().first()
    if student:
        student.paid_fees = _money(student.paid_fees) + balance
    link.status = "consumed"
    link.consumed_at = now
    db.query(ReminderEvent).filter(
        ReminderEvent.instalment_id == item.id
    ).update({"status": "cancelled_paid"}, synchronize_session=False)
    db.flush()
    payment.receipt_number = f"FF-{now:%Y%m%d}-{str(payment.id)[:8].upper()}"
    db.commit()
    return {
        "status": "mock_payment_recorded",
        "message": "Demo checkout complete. No real money was collected.",
        "payment_id": str(payment.id),
        "receipt_number": payment.receipt_number,
        "amount": float(balance)
    }

@router.get("/payments/{payment_id}/receipt", response_class=HTMLResponse)
def get_receipt(
    payment_id: str,
    claims=Depends(get_demo_claims),
    db: Session = Depends(get_db),
):
    student_id = _claims_student(claims)
    p = db.query(Payment).filter(
        Payment.id == payment_id, Payment.student_id == student_id
    ).first()
    if not p:
        raise HTTPException(404, "Receipt not found.")
    student = db.query(Student).filter(Student.id == student_id).first()
    # No GST is added until the institute provides verified tax configuration.
    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>FeeFlow demo receipt</title>
    <style>body{{font:16px Arial;margin:40px;color:#172033}}.box{{max-width:650px;border:1px solid #ddd;padding:28px}}
    .muted{{color:#666}}.amount{{font-size:28px;font-weight:bold}}</style></head><body><div class="box">
    <h1>{student.name if student else 'Student'}</h1><p class="muted">FeeFlow payment receipt — DEMO</p>
    <p><b>Receipt:</b> {p.receipt_number or str(p.id)}<br><b>Student ID:</b> {student_id}<br>
    <b>Date:</b> {p.payment_date}<br><b>Method:</b> {p.payment_method}<br>
    <b>Reference:</b> {p.transaction_reference}</p><p class="amount">₹{_money(p.amount):,.2f}</p>
    <p><b>Status:</b> {p.status}</p><hr><p class="muted">GST is not configured. This is a demonstration receipt,
    not a tax invoice and not proof of a real-world payment.</p><button onclick="window.print()">Print</button>
    </div></body></html>"""
    return HTMLResponse(html)

@router.get("/tally/export.csv")
def tally_export(
    db: Session = Depends(get_db),
    accountant=Depends(require_accountant),
):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Voucher Type", "Voucher Number", "Party Ledger", "Fee Ledger",
                     "Bank/Cash Ledger", "Amount", "Reference", "Narration"])
    rows = db.query(Payment, Student).join(Student, Student.id == Payment.student_id).filter(
        Payment.status == "successful"
    ).order_by(Payment.payment_date.asc()).all()
    for p, s in rows:
        writer.writerow([
            p.payment_date.date().isoformat() if p.payment_date else "",
            "Receipt", p.receipt_number or str(p.id), s.name, "Coaching Fee",
            "Bank / Mock Collection", str(_money(p.amount)), p.transaction_reference or "",
            f"Fee receipt for {s.id} ({p.payment_method})"
        ])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="feeflow_tally_export.csv"'})

@router.post("/refunds")
def create_refund_request(
    payload: RefundCreate,
    claims=Depends(get_demo_claims),
    db: Session=Depends(get_db),
):
    student_id = _claims_student(claims)
    if payload.course_end_date <= payload.course_start_date:
        raise HTTPException(400, "Course end date must be after start date.")
    if not payload.course_start_date <= payload.leaving_date <= payload.course_end_date:
        raise HTTPException(400, "Leaving date must be within the course dates.")
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(404, "Student not found.")
    total_days = (payload.course_end_date - payload.course_start_date).days
    remaining_days = (payload.course_end_date - payload.leaving_date).days
    paid = _money(student.paid_fees)
    # Provisional straight-line unused-period calculation; institute policy must replace/approve it.
    amount = (paid * Decimal(max(remaining_days, 0)) / Decimal(total_days)).quantize(Decimal("0.01"))
    now = datetime.now(timezone.utc)
    req = RefundRequest(
        id=uuid4(), student_id=student_id,
        requested_by=f"demo:{claims.get('role','user')}",
        course_start_date=payload.course_start_date,
        course_end_date=payload.course_end_date,
        leaving_date=payload.leaving_date,
        amount_paid=paid, calculated_refund=amount,
        due_date=now.date()+timedelta(days=10), status="pending",
        notes="Provisional demo calculation; subject to published institute refund policy."
    )
    db.add(req)
    db.commit()
    return {"id": str(req.id), "calculated_refund": float(amount),
            "status": req.status, "target_due_date": req.due_date.isoformat(),
            "notice": "Provisional estimate only; not a legal or final refund decision."}

@router.get("/refunds")
def list_refunds(db: Session=Depends(get_db), accountant=Depends(require_accountant)):
    rows = db.query(RefundRequest).order_by(RefundRequest.requested_at.desc()).all()
    return [{
        "id": str(x.id), "student_id": x.student_id, "requested_at": x.requested_at.isoformat(),
        "calculated_refund": float(x.calculated_refund),
        "approved_amount": float(x.approved_amount) if x.approved_amount is not None else None,
        "status": x.status, "due_date": x.due_date.isoformat(),
        "days_to_due": (x.due_date-date.today()).days, "notes": x.notes
    } for x in rows]

@router.post("/refunds/{refund_id}/decision")
def decide_refund(refund_id: str, payload: RefundDecision,
                  db: Session=Depends(get_db), accountant=Depends(require_accountant)):
    x = db.query(RefundRequest).filter(RefundRequest.id == refund_id).with_for_update().first()
    if not x:
        raise HTTPException(404, "Refund request not found.")
    if x.status != "pending":
        raise HTTPException(409, "Only pending requests can be decided.")
    x.status = "approved" if payload.action == "approve" else "rejected"
    x.approved_amount = (_money(payload.approved_amount) if payload.approved_amount is not None
                        else _money(x.calculated_refund)) if payload.action == "approve" else None
    if x.approved_amount is not None and x.approved_amount < 0:
        raise HTTPException(400, "Approved amount cannot be negative.")
    x.decision_by = str(getattr(accountant, "user_id", "accountant"))
    x.decision_at = datetime.now(timezone.utc)
    x.notes = payload.notes or x.notes
    db.commit()
    return {"id": str(x.id), "status": x.status,
            "approved_amount": float(x.approved_amount) if x.approved_amount is not None else None}

@router.post("/refunds/{refund_id}/paid")
def mark_refund_paid(refund_id: str, payload: RefundPaid,
                     db: Session=Depends(get_db), accountant=Depends(require_accountant)):
    x = db.query(RefundRequest).filter(RefundRequest.id == refund_id).with_for_update().first()
    if not x:
        raise HTTPException(404, "Refund request not found.")
    if x.status != "approved":
        raise HTTPException(409, "Only approved refunds can be marked paid.")
    x.status = "paid"
    x.paid_at = datetime.now(timezone.utc)
    x.payout_reference = payload.payout_reference
    db.commit()
    return {"id": str(x.id), "status": x.status, "paid_at": x.paid_at.isoformat()}

@router.post("/bank-import")
async def import_bank_csv(file: UploadFile=File(...), db: Session=Depends(get_db),
                          accountant=Depends(require_accountant)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Upload a CSV file.")
    raw = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(raw))
    required = {"transaction_reference", "amount", "payment_date"}
    if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        raise HTTPException(400, "CSV needs transaction_reference, amount, payment_date columns.")
    added = 0
    duplicates = 0
    for row in reader:
        ref = (row.get("transaction_reference") or "").strip()
        if not ref:
            continue
        if db.query(UnmatchedPayment).filter_by(external_reference=ref).first():
            duplicates += 1
            continue
        try:
            amount = _money(row["amount"])
            paid_on = date.fromisoformat(row["payment_date"][:10])
        except Exception:
            continue
        if amount <= 0:
            continue
        db.add(UnmatchedPayment(id=uuid4(), external_reference=ref, amount=amount,
            payment_date=paid_on, description=row.get("description",""), status="unmatched"))
        added += 1
    db.commit()
    return {"imported": added, "duplicates": duplicates, "status": "unmatched_queue"}

@router.get("/bank-unmatched")
def get_unmatched(db: Session=Depends(get_db), accountant=Depends(require_accountant)):
    rows = db.query(UnmatchedPayment).filter(UnmatchedPayment.status=="unmatched").order_by(
        UnmatchedPayment.payment_date.asc()).all()
    return [{"id":str(x.id), "reference":x.external_reference, "amount":float(x.amount),
             "payment_date":x.payment_date.isoformat(), "description":x.description} for x in rows]

@router.post("/bank-unmatched/{row_id}/match")
def match_bank_row(row_id: str, payload: MatchRequest,
                   db: Session=Depends(get_db), accountant=Depends(require_accountant)):
    row = db.query(UnmatchedPayment).filter(
        UnmatchedPayment.id == row_id, UnmatchedPayment.status=="unmatched"
    ).with_for_update().first()
    if not row:
        raise HTTPException(404, "Unmatched bank row not found.")
    item = db.query(Instalment).filter(
        Instalment.id == payload.instalment_id,
        Instalment.student_id == payload.student_id
    ).with_for_update().first()
    if not item:
        raise HTTPException(404, "Instalment not found for selected student.")
    student = db.query(Student).filter(Student.id==payload.student_id).with_for_update().first()
    if not student:
        raise HTTPException(404, "Student not found.")
    balance = _money(item.amount)-_money(item.paid_amount)
    if row.amount <= 0 or row.amount > balance:
        raise HTTPException(400, "Bank amount must be positive and no greater than instalment balance.")
    payment = Payment(student_id=student.id, instalment_id=item.id, amount=row.amount,
        payment_date=datetime.combine(row.payment_date, datetime.min.time(), tzinfo=timezone.utc),
        payment_method=payload.payment_method, transaction_reference=row.external_reference,
        status="successful")
    db.add(payment)
    item.paid_amount = _money(item.paid_amount)+row.amount
    if item.paid_amount >= _money(item.amount):
        item.status="paid"
        db.query(ReminderEvent).filter(ReminderEvent.instalment_id==item.id).update(
            {"status":"cancelled_paid"}, synchronize_session=False)
    student.paid_fees = _money(student.paid_fees)+row.amount
    row.status="matched"
    row.matched_student_id=student.id
    row.matched_instalment_id=item.id
    row.matched_at=datetime.now(timezone.utc)
    row.matched_by=str(getattr(accountant,"user_id","accountant"))
    db.flush()
    payment.receipt_number=f"FF-{datetime.now(timezone.utc):%Y%m%d}-{str(payment.id)[:8].upper()}"
    row.matched_payment_id=payment.id
    db.commit()
    return {"status":"matched", "payment_id":str(payment.id), "receipt_number":payment.receipt_number}
