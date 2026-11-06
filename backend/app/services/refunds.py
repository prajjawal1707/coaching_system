
from datetime import date
from decimal import Decimal, ROUND_HALF_UP


def calculate_prorata_refund(
    net_fee: int,
    amount_paid: int,
    course_start_date: date,
    course_end_date: date,
    leaving_date: date,
) -> dict:
    """
    Demo policy assumption:
    Refund = amount paid - fee earned up to the leaving date.

    The fee is earned proportionally across the course duration.
    This is not a substitute for the institute's approved refund policy.
    """

    if net_fee < 0 or amount_paid < 0:
        raise ValueError("Fee and amount paid cannot be negative.")

    if course_end_date < course_start_date:
        raise ValueError("Course end date cannot be before start date.")

    if leaving_date < course_start_date:
        elapsed_days = 0
    elif leaving_date > course_end_date:
        elapsed_days = (
            course_end_date - course_start_date
        ).days + 1
    else:
        elapsed_days = (leaving_date - course_start_date).days + 1

    total_days = (course_end_date - course_start_date).days + 1

    earned_fee = (
        Decimal(net_fee) * Decimal(elapsed_days) / Decimal(total_days)
    )

    earned_fee = earned_fee.quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )

    refund = max(Decimal("0"), Decimal(amount_paid) - earned_fee)
    refund = min(refund, Decimal(amount_paid))

    return {
        "net_fee": net_fee,
        "amount_paid": amount_paid,
        "total_course_days": total_days,
        "elapsed_course_days": elapsed_days,
        "earned_fee": int(earned_fee),
        "refund_amount": int(refund),
        "policy_basis": "Demo pro-rata calculation; confirm written institute policy.",
    }
