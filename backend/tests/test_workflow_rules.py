from fastapi import HTTPException

from app.services.workflow_service import validate_status_transition


def test_submitted_to_under_review():
    validate_status_transition(
        "submitted",
        "under_review"
    )


def test_under_review_to_assigned():
    validate_status_transition(
        "under_review",
        "assigned"
    )


def test_assigned_to_in_progress():
    validate_status_transition(
        "assigned",
        "in_progress"
    )


def test_invalid_transition_raises():
    try:
        validate_status_transition(
            "submitted",
            "closed"
        )

        assert False

    except HTTPException as exc:
        assert exc.status_code == 400