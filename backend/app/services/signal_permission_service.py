from fastapi import HTTPException, status

from app.models.campus_signal import CampusSignal
from app.models.user import User


def ensure_assigned_staff_or_admin(
    signal: CampusSignal,
    current_user: User,
):
    if current_user.role == "admin":
        return

    if current_user.role != "department_staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only assigned department staff or admins can perform this action",
        )

    if signal.assigned_staff_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This signal is not assigned to you",
        )


def ensure_admin_or_supervisor(current_user: User):
    if current_user.role not in ["admin", "supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins or supervisors can perform this action",
        )