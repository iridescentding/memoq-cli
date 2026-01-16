# -*- coding: utf-8 -*-
"""
memoQ CLI - Custom Exception Hierarchy
"""


class MemoQError(Exception):
    """Base exception for memoQ CLI"""

    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(message)

    def __str__(self):
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class ConfigError(MemoQError):
    """Configuration related errors"""
    pass


class AuthenticationError(MemoQError):
    """Authentication failures"""
    pass


class APIError(MemoQError):
    """Base class for API errors"""

    def __init__(self, message: str, status_code: int = None, details: str = None):
        self.status_code = status_code
        super().__init__(message, details)


class WSAPIError(APIError):
    """WSAPI (SOAP) related errors"""
    pass


class RSAPIError(APIError):
    """RSAPI (REST) related errors"""
    pass


class TaskTimeoutError(MemoQError):
    """Async task timeout"""

    def __init__(self, task_id: str, timeout: int):
        self.task_id = task_id
        self.timeout = timeout
        super().__init__(
            f"Task timed out after {timeout}s",
            f"Task ID: {task_id}"
        )


class TaskFailedError(MemoQError):
    """Async task failed"""

    def __init__(self, task_id: str, error_message: str):
        self.task_id = task_id
        super().__init__(
            "Task failed",
            f"Task ID: {task_id}, Error: {error_message}"
        )


class ValidationError(MemoQError):
    """Input validation errors"""
    pass


class ResourceNotFoundError(MemoQError):
    """Resource not found (project, TM, TB, etc.)"""

    def __init__(self, resource_type: str, resource_id: str):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(
            f"{resource_type} not found",
            f"ID: {resource_id}"
        )
