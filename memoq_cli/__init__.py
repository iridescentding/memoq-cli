# -*- coding: utf-8 -*-
"""
memoQ CLI - memoQ Server Command Line Tool

Supports WSAPI and RSAPI for project management, file import/export,
TM/TB management, and more.
"""

__version__ = "1.0.0"
__author__ = "memoQ CLI Team"

from .config import Config, get_config
from .wsapi import WSAPIClient, ProjectManager, FileManager
from .rsapi import RSAPIClient, TMManager, TBManager
from .exceptions import (
    MemoQError,
    ConfigError,
    AuthenticationError,
    APIError,
    WSAPIError,
    RSAPIError,
    TaskTimeoutError,
    TaskFailedError,
    ValidationError,
    ResourceNotFoundError,
)

__all__ = [
    # Config
    "Config",
    "get_config",
    # WSAPI
    "WSAPIClient",
    "ProjectManager",
    "FileManager",
    # RSAPI
    "RSAPIClient",
    "TMManager",
    "TBManager",
    # Exceptions
    "MemoQError",
    "ConfigError",
    "AuthenticationError",
    "APIError",
    "WSAPIError",
    "RSAPIError",
    "TaskTimeoutError",
    "TaskFailedError",
    "ValidationError",
    "ResourceNotFoundError",
]
