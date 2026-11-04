from pydantic import BaseModel, ConfigDict, Field


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    course: str
    batch: str
    total_fees: int = Field(ge=0)
    paid_fees: int = Field(ge=0)
    attendance: int = Field(ge=0, le=100)


class FeeResponse(BaseModel):
    student_id: str
    student_name: str
    total_fees: int
    paid_fees: int
    pending_fees: int