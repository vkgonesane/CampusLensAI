from app.services.notification_service import (
    notify_signal_assigned,
    notify_signal_closed,
    notify_signal_reopened,
)


def test_notification_functions_exist():
    assert callable(notify_signal_assigned)
    assert callable(notify_signal_closed)
    assert callable(notify_signal_reopened)
    