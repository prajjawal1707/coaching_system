from datetime import date


def get_reminder_stage(due_date):
    today = date.today()
    days_left = (due_date - today).days

    if 1 <= days_left <= 3:
        return "before"

    if days_left == 0:
        return "due"

    if days_left < 0:
        return "after"

    return None


def create_reminder_message(
    student_name,
    amount,
    due_date,
    stage,
    language
):
    formatted_amount = f"₹{amount:,.0f}"

    if language == "hi":
        if stage == "before":
            return (
                f"नमस्ते {student_name}, आपकी फीस की किस्त "
                f"{formatted_amount} की है। अंतिम तारीख "
                f"{due_date} है। कृपया समय पर भुगतान करें।"
            )

        if stage == "due":
            return (
                f"नमस्ते {student_name}, आपकी फीस की किस्त "
                f"{formatted_amount} आज देय है। कृपया भुगतान करें।"
            )

        return (
            f"नमस्ते {student_name}, आपकी फीस की किस्त "
            f"{formatted_amount} की भुगतान तारीख निकल चुकी है। "
            f"कृपया बकाया राशि जमा करें।"
        )

    if stage == "before":
        return (
            f"Hello {student_name}, your fee instalment of "
            f"{formatted_amount} is due on {due_date}. "
            f"Please pay on time."
        )

    if stage == "due":
        return (
            f"Hello {student_name}, your fee instalment of "
            f"{formatted_amount} is due today. Please make the payment."
        )

    return (
        f"Hello {student_name}, your fee instalment of "
        f"{formatted_amount} is overdue. Please clear the pending amount."
    )