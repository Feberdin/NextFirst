"""NextFirst custom errors.

Purpose:
- Define explicit error classes for user and system failure modes.

Input/Output:
- Input: raised by domain/manager/storage/AI modules.
- Output: consumed by services and translated into clear messages.

Invariants:
- User-facing validation errors derive from NextFirstUserError.
- System faults derive from NextFirstSystemError.

Debugging:
- Inspect exception type to decide whether input validation or infrastructure failed.
"""

from __future__ import annotations


class NextFirstError(Exception):
    """Base class for all integration errors."""


class NextFirstUserError(NextFirstError):
    """Input or business-rule error caused by user-provided data."""


class NextFirstSystemError(NextFirstError):
    """Infrastructure or external system error."""


class ExperienceNotFoundError(NextFirstUserError):
    """Raised when an experience ID does not exist."""


class InvalidTransitionError(NextFirstUserError):
    """Raised for disallowed state transitions."""


class ValidationError(NextFirstUserError):
    """Raised when required fields or value ranges are invalid."""


class AIProviderError(NextFirstSystemError):
    """Raised when an AI provider call fails."""
