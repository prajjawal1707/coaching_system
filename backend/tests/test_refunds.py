
from datetime import date
from unittest import result

import pytest

from app.services.refunds import calculate_prorata_refund


def test_refund_for_half_course_completed():
    result = calculate_prorata_refund(
        net_fee=120000,
        amount_paid=120000,
        course_start_date=date(2026, 1, 1),
        course_end_date=date(2026, 12, 31),
        leaving_date=date(2026, 7, 2),
    )

    assert result["earned_fee"] == 60164
    assert result["refund_amount"] == 59836

def test_no_refund_when_all_fee_is_earned():
    result = calculate_prorata_refund(
        net_fee=120000,
        amount_paid=120000,
        course_start_date=date(2026, 1, 1),
        course_end_date=date(2026, 12, 31),
        leaving_date=date(2027, 1, 1),
    )

    assert result["refund_amount"] == 0


def test_refund_cannot_exceed_amount_paid():
    result = calculate_prorata_refund(
        net_fee=120000,
        amount_paid=30000,
        course_start_date=date(2026, 1, 1),
        course_end_date=date(2026, 12, 31),
        leaving_date=date(2026, 1, 1),
    )

    assert result["refund_amount"] <= 30000


def test_negative_fee_is_rejected():
    with pytest.raises(ValueError):
        calculate_prorata_refund(
            net_fee=-1000,
            amount_paid=1000,
            course_start_date=date(2026, 1, 1),
            course_end_date=date(2026, 12, 31),
            leaving_date=date(2026, 6, 1),
        )
