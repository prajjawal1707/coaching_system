
from datetime import date

from pydantic import BaseModel, Field


class RefundCalculateRequest(BaseModel):
    course_start_date: date
    course_end_date: date
    leaving_date: date


class RefundCalculateResponse(BaseModel):
    student_id: str
    student_name: str
    net_fee: int
    amount_paid: int
    total_course_days: int
    elapsed_course_days: int
    earned_fee: int
    refund_amount: int
    policy_basis: str
