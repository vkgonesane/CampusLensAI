from fastapi import status


class AppException(Exception):
    def __init__(
        self,
        error: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        self.error = error
        self.message = message
        self.status_code = status_code


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            error="not_found",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )


class PermissionDeniedException(AppException):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            error="permission_denied",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class InvalidWorkflowTransitionException(AppException):
    def __init__(self, message: str):
        super().__init__(
            error="invalid_workflow_transition",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )