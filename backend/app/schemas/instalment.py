from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InstalmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: str
    instalment_number: int
    amount: int
    paid_amount: int = Field(ge=0)
    due_date: date
    status: str