from pydantic import BaseModel, ConfigDict, Field


class StudentCreate(BaseModel):
    id: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=2, max_length=100)
    course: str = Field(min_length=2, max_length=100)
    batch: str = "2026-27"
    total_fees: int = Field(gt=0)
    paid_fees: int = Field(default=0, ge=0)
    attendance: int = Field(default=0, ge=0, le=100)
    centre: str = "Unassigned"


class StudentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    course: str | None = Field(default=None, min_length=2, max_length=100)
    batch: str | None = None
    total_fees: int | None = Field(default=None, gt=0)
    attendance: int | None = Field(default=None, ge=0, le=100)


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    course: str
    batch: str
    total_fees: int
    paid_fees: int
    attendance: int
    centre: str


class FeeResponse(BaseModel):
    student_id: str
    student_name: str
    total_fees: int
    paid_fees: int
    pending_fees: int