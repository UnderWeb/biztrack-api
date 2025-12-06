from typing import Any, Dict, Optional


class FileError(Exception):
    """Base exception for all file-related errors."""

    def __init__(
        self,
        message: str,
        *,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize file error with optional debug context.

        Args:
            message: Human-readable error description.
            context: Additional context for debugging.
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        """
        Return a human-readable error message including context when available.

        Returns:
            A formatted string representation of the exception.
        """
        if self.context:
            return f"{self.__class__.__name__}: {self.message} | context={self.context}"
        return f"{self.__class__.__name__}: {self.message}"
    

class FileNotFoundError(FileError):
    """Raised when a file is not found in storage."""


class FileValidationError(FileError):
    """Raised when file validation fails."""


class FileDownloadError(FileError):
    """Raised when remote file download fails."""


class FileUploadError(FileError):
    """Raised when file upload fails."""


class FilePermissionError(FileError):
    """Raised when file operation lacks permissions."""


class FileCorruptedError(FileError):
    """Raised when file appears to be corrupted."""
