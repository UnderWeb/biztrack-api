import logging
from typing import Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

from ..storage.base import StorageBackend, FileMetadata
from ..exceptions import FileValidationError

logger = logging.getLogger(__name__)


class ContentTypeCategory(Enum):
    """
    Predefined content type categories for validation.
    Use `.value` to access the underlying set of allowed MIME types.
    """
    IMAGES = {
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif',
        'image/webp', 'image/svg+xml', 'image/bmp'
    }
    DOCUMENTS = {
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.oasis.opendocument.text',
    }
    SPREADSHEETS = {
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.oasis.opendocument.spreadsheet',
    }
    ARCHIVES = {
        'application/zip', 'application/x-gzip', 'application/x-tar',
        'application/x-rar-compressed', 'application/x-7z-compressed',
    }
    ALL = IMAGES | DOCUMENTS | SPREADSHEETS | ARCHIVES


@dataclass(frozen=True)
class ValidationRule:
    """
    Immutable definition of a file validation rule.

    Attributes:
        max_size_bytes: Maximum allowed file size in bytes.
        allowed_content_types: Set of allowed MIME types.
        require_content_type: Whether to enforce content type validation.
    """
    max_size_bytes: Optional[int] = None
    allowed_content_types: Optional[Set[str]] = None
    require_content_type: bool = True

    def __post_init__(self):
        # Ensure allowed_content_types is a set
        if self.allowed_content_types and not isinstance(self.allowed_content_types, set):
            object.__setattr__(self, 'allowed_content_types', set(self.allowed_content_types))


class FileValidator:
    """
    Validates files against rules, storage-agnostic via dependency injection.

    Methods:
        validate: returns validation result as tuple (is_valid, metadata, error_message)
        validate_with_exception: raises FileValidationError if validation fails
    """

    def __init__(self, storage_backend: StorageBackend):
        self.storage = storage_backend

    def validate(
        self,
        key: str,
        rule: ValidationRule
    ) -> Tuple[bool, Optional[FileMetadata], Optional[str]]:
        """
        Validate file against a given rule.

        Args:
            key: Storage key of the file.
            rule: ValidationRule object defining constraints.

        Returns:
            Tuple of (is_valid, metadata, error_message). `metadata` is None if file not found.
        """
        try:
            metadata = self.storage.get_metadata(key)
            if not metadata:
                return False, None, f"File not found: {key}"

            # Validate max size
            if rule.max_size_bytes and metadata.size:
                if metadata.size > rule.max_size_bytes:
                    error = (
                        f"File size {metadata.size} exceeds limit of {rule.max_size_bytes} bytes"
                    )
                    logger.debug("Validation failed: %s", error)
                    return False, metadata, error

            # Validate content type
            if rule.allowed_content_types and metadata.content_type:
                if metadata.content_type not in rule.allowed_content_types:
                    error = (
                        f"Content type '{metadata.content_type}' not allowed. "
                        f"Allowed: {sorted(rule.allowed_content_types)}"
                    )
                    logger.debug("Validation failed: %s", error)
                    return False, metadata, error

            return True, metadata, None

        except Exception as e:
            logger.error("Unexpected validation error for key %s: %s", key, e, exc_info=True)
            return False, None, f"Validation error: {str(e)}"

    def validate_with_exception(
        self,
        key: str,
        rule: ValidationRule
    ) -> FileMetadata:
        """
        Validate file and raise FileValidationError on failure.

        Args:
            key: Storage key of the file.
            rule: ValidationRule to enforce.

        Returns:
            FileMetadata if file is valid.

        Raises:
            FileValidationError: if file fails validation.
        """
        is_valid, metadata, error = self.validate(key, rule)
        if not is_valid:
            raise FileValidationError(
                error or "File validation failed",
                context={
                    'key': key,
                    'rule': {
                        'max_size_bytes': rule.max_size_bytes,
                        'allowed_content_types': list(rule.allowed_content_types)
                        if rule.allowed_content_types else None,
                    },
                    'metadata': metadata.__dict__ if metadata else None
                }
            )
        return metadata


class ValidationRules:
    """
    Factory for common validation rules.
    """

    @staticmethod
    def image(max_size_mb: int = 10) -> ValidationRule:
        """Rule for image files."""
        return ValidationRule(
            max_size_bytes=max_size_mb * 1024 * 1024,
            allowed_content_types=ContentTypeCategory.IMAGES.value
        )

    @staticmethod
    def document(max_size_mb: int = 50) -> ValidationRule:
        """Rule for document files."""
        return ValidationRule(
            max_size_bytes=max_size_mb * 1024 * 1024,
            allowed_content_types=ContentTypeCategory.DOCUMENTS.value
        )

    @staticmethod
    def any(max_size_mb: int = 100) -> ValidationRule:
        """Rule allowing any supported file type."""
        return ValidationRule(
            max_size_bytes=max_size_mb * 1024 * 1024,
            allowed_content_types=ContentTypeCategory.ALL.value
        )


# -----------------------------
# Backward compatible helper functions
# -----------------------------

def validate_content_type_allowed(
    storage_backend: StorageBackend,
    key: str,
    allowed_content_types: Set[str]
) -> bool:
    """
    Check if file content type is allowed (legacy function).

    Args:
        storage_backend: Backend instance to check file.
        key: File key in storage.
        allowed_content_types: Set of allowed MIME types.

    Returns:
        True if valid, False otherwise.
    """
    validator = FileValidator(storage_backend)
    rule = ValidationRule(allowed_content_types=allowed_content_types)

    try:
        validator.validate_with_exception(key, rule)
        return True
    except FileValidationError:
        return False


def validate_max_size(
    storage_backend: StorageBackend,
    key: str,
    max_bytes: int
) -> bool:
    """
    Check if file size does not exceed max_bytes (legacy function).

    Args:
        storage_backend: Backend instance to check file.
        key: File key in storage.
        max_bytes: Maximum allowed size in bytes.

    Returns:
        True if valid, False otherwise.
    """
    validator = FileValidator(storage_backend)
    rule = ValidationRule(max_size_bytes=max_bytes)

    try:
        validator.validate_with_exception(key, rule)
        return True
    except FileValidationError:
        return False
