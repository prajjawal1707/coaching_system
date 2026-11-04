from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    student_id: str
    amount: int = Field(gt=0)
    payment_method: str = "other"


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: str
    amount: int
    payment_date: datetime
    payment_method: str
    transaction_reference: str | None
    status: str