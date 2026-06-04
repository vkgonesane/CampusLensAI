from fastapi import HTTPException, status


VALID_STATUS_TRANSITIONS = {
    "submitted": ["under_review"],
    "under_review": ["assigned", "rework_required"],
    "assigned": ["in_progress"],
    "in_progress": ["fixed_by_staff", "rework_required"],
    "fixed_by_staff": ["supervisor_review"],
    "supervisor_review": ["closed", "rework_required"],
    "rework_required": ["assigned"],
    "closed": ["reopened"],
    "reopened": ["under_review"]
}


def validate_status_transition(
    current_status: str,
    requested_status: str
) -> None:
    allowed_next_statuses = VALID_STATUS_TRANSITIONS.get(
        current_status,
        []
    )

    if requested_status not in allowed_next_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid workflow transition. "
                f"Cannot move from '{current_status}' to '{requested_status}'."
            )
        )