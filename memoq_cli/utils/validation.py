# -*- coding: utf-8 -*-
"""
memoQ CLI - Input Validation Helpers
"""

import re
from typing import Optional

from ..exceptions import ValidationError


# GUID pattern (UUID format)
GUID_PATTERN = re.compile(
    r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
)

# Language code pattern (e.g., en-US, zh-CN, ja-JP)
LANG_CODE_PATTERN = re.compile(r'^[a-z]{2,3}(-[A-Z]{2})?$', re.IGNORECASE)

# Common memoQ language codes
COMMON_LANG_CODES = {
    "en-US", "en-GB", "zh-CN", "zh-TW", "ja-JP", "ko-KR",
    "de-DE", "fr-FR", "es-ES", "it-IT", "pt-BR", "pt-PT",
    "ru-RU", "ar-SA", "nl-NL", "pl-PL", "sv-SE", "da-DK",
    "fi-FI", "no-NO", "cs-CZ", "hu-HU", "tr-TR", "th-TH",
    "vi-VN", "id-ID", "ms-MY", "he-IL", "uk-UA", "ro-RO",
}


def is_valid_guid(value: str) -> bool:
    """
    Check if a string is a valid GUID/UUID.

    Args:
        value: String to validate

    Returns:
        True if valid GUID format
    """
    if not value:
        return False
    return bool(GUID_PATTERN.match(value))


def validate_guid(value: str, name: str = "GUID") -> str:
    """
    Validate a GUID and return it if valid.

    Args:
        value: String to validate
        name: Name for error messages (e.g., "Project GUID")

    Returns:
        The validated GUID

    Raises:
        ValidationError: If invalid GUID format
    """
    if not is_valid_guid(value):
        raise ValidationError(
            f"Invalid {name} format",
            f"Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx, got: {value}"
        )
    return value


def is_valid_lang_code(value: str) -> bool:
    """
    Check if a string is a valid language code.

    Args:
        value: String to validate

    Returns:
        True if valid language code format
    """
    if not value:
        return False
    return bool(LANG_CODE_PATTERN.match(value))


def validate_lang_code(value: str, name: str = "language code") -> str:
    """
    Validate a language code and return it if valid.

    Args:
        value: String to validate
        name: Name for error messages

    Returns:
        The validated language code

    Raises:
        ValidationError: If invalid language code format
    """
    if not is_valid_lang_code(value):
        raise ValidationError(
            f"Invalid {name} format",
            f"Expected format: xx-XX (e.g., en-US, zh-CN), got: {value}"
        )
    return value


def validate_not_empty(value: Optional[str], name: str = "value") -> str:
    """
    Validate that a value is not empty.

    Args:
        value: String to validate
        name: Name for error messages

    Returns:
        The validated value

    Raises:
        ValidationError: If value is None or empty
    """
    if not value or not value.strip():
        raise ValidationError(f"{name} cannot be empty")
    return value.strip()


def validate_positive_int(value: int, name: str = "value") -> int:
    """
    Validate that an integer is positive.

    Args:
        value: Integer to validate
        name: Name for error messages

    Returns:
        The validated value

    Raises:
        ValidationError: If value is not positive
    """
    if value <= 0:
        raise ValidationError(f"{name} must be positive", f"Got: {value}")
    return value


def validate_percentage(value: int, name: str = "percentage") -> int:
    """
    Validate that a value is a valid percentage (0-100).

    Args:
        value: Integer to validate
        name: Name for error messages

    Returns:
        The validated value

    Raises:
        ValidationError: If value is not in range 0-100
    """
    if not 0 <= value <= 100:
        raise ValidationError(f"{name} must be between 0 and 100", f"Got: {value}")
    return value
