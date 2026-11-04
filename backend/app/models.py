from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    course = Column(String, nullable=False)
    batch = Column(String, nullable=False, default="2026-27")
    total_fees = Column(Integer, nullable=False)
    paid_fees = Column(Integer, nullable=False, default=0)
    attendance = Column(Integer, nullable=False, default=0)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    student_id = Column(
        String,
        ForeignKey("students.id"),
        nullable=False
    )
    amount = Column(Integer, nullable=False)
    payment_date = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    payment_method = Column(String, nullable=False, default="other")
    transaction_reference = Column(String, unique=True)
    status = Column(String, nullable=False, default="successful")