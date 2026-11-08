from datetime import datetime, timezone
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey
)
from sqlalchemy import Column, String, BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy import Date, Boolean
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    Boolean,
    Float,
    UniqueConstraint,
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
    centre = Column(
    String,
    nullable=False,
    default="Unassigned",
    server_default="Unassigned"
)
    total_fees = Column(Integer, nullable=False)
    paid_fees = Column(Integer, nullable=False, default=0)
    attendance = Column(Integer, nullable=False, default=0)


class DemoParentCredential(Base):
    __tablename__ = "demo_parent_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(
        String,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    otp_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    consumed_at = Column(DateTime, nullable=True)
    created_at = Column(
    DateTime(timezone=True),
    nullable=False,
    default=lambda: datetime.now(timezone.utc)
)
    
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
    
    
class Instalment(Base):
    __tablename__ = "instalments"

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

    instalment_number = Column(Integer, nullable=False)
    amount = Column(Integer, nullable=False)
    paid_amount = Column(Integer, nullable=False, default=0)
    due_date = Column(Date, nullable=False)
    status = Column(String, nullable=False, default="pending")

class ReminderEvent(Base):
    __tablename__ = "reminder_events"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    instalment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("instalments.id"),
        nullable=False
    )

    student_id = Column(
        String,
        ForeignKey("students.id"),
        nullable=False
    )

    stage = Column(String, nullable=False)
    language = Column(String, nullable=False)
    message = Column(String, nullable=False)
    status = Column(String, nullable=False, default="mock_prepared")
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
class DemoStudentCredential(Base):
    __tablename__ = "demo_student_credentials"

    student_id = Column(
        String,
        ForeignKey("students.id", ondelete="CASCADE"),
        primary_key=True,
    )
    code_hash = Column(String, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    failed_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )


class ParentStudentLink(Base):
    __tablename__ = "parent_student_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(
        String,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_label = Column(
        String,
        nullable=False,
        default="Parent",
    )
    code_hash = Column(String, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    failed_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(UUID(as_uuid=True), primary_key=True)
    full_name = Column(String, nullable=True)
    role = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    
class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "attendance_date",
            name="uq_attendance_student_date",
        ),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    student_id = Column(
        String,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    attendance_date = Column(Date, nullable=False)

    status = Column(String, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class TestScore(Base):
    __tablename__ = "test_scores"

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "test_name",
            "test_date",
            name="uq_test_score_student_test_date",
        ),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    student_id = Column(
        String,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    test_name = Column(String, nullable=False)

    test_date = Column(Date, nullable=False)

    score = Column(Float, nullable=False)

    max_score = Column(Float, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
class PaymentLink(Base):
    __tablename__ = "payment_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    student_id = Column(
        String,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    instalment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("instalments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    amount = Column(BigInteger, nullable=False)

    status = Column(String, nullable=False, default="pending")

    expires_at = Column(DateTime(timezone=True), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    paid_at = Column(DateTime(timezone=True), nullable=True)