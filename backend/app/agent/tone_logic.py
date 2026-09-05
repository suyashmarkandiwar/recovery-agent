def determine_tone(days_overdue: int) -> str | None:
    if days_overdue <= 10:
        return None  # Do not send anything
    elif 11 <= days_overdue <= 20:
        return "polite and gentle reminder"
    elif 21 <= days_overdue <= 30:
        return "firm but professional reminder"
    else:
        return "ESCALATE"  # Trigger manual call and audit log