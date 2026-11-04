
from pydantic import BaseModel, Field


class StudentResponse(BaseModel):
    id: str
    name: str
    course: str
    total_fees: int = Field(ge=0)
    paid_fees: int = Field(ge=0)
    attendance: int = Field(ge=0, le=100)


class FeeResponse(BaseModel):
    student_id: str
    student_name: str
    total_fees: int
    paid_fees: int
    pending_fees: int
