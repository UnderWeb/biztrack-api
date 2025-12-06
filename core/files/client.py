import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager

from django.conf import settings

from .enums import FileTypeValidation

from .storage.factory import get_storage_backend
from .storage.base import StorageBackend
from .operations.filenames import (
    sanitize_filename,
    generate_unique_filename,
    infer_filename_from_url,
)
from .operations.download import download_file
from .operations.validators import FileValidator, ValidationRules
from .exceptions import (
    FileError,
    FileNotFoundError,
    FileDownloadError,
)

logger = logging.getLogger(__name__)

# ======================================================
# Singleton storage backend
# ======================================================
_storage_backend: Optional[StorageBackend] = None

# ======================================================
# Presigned URL defaults
# ======================================================
DEFAULT_PRESIGNED_UPLOAD_EXPIRES: int = 3600  # seconds (1 hour)

DEFAULT_MAX_SIZE_MB = {
    FileTypeValidation.IMAGE: 10,
    FileTypeValidation.DOCUMENT: 50,
    FileTypeValidation.ANY: 100,
}


def get_storage() -> StorageBackend:
    """
    Get singleton storage backend instance.

    Returns:
        StorageBackend: Initialized storage backend.
    """
    global _storage_backend

    if _storage_backend is None:
        try:
            _storage_backend = get_storage_backend()
        except Exception as e:
            logger.error("Failed to initialize storage backend: %s", e, exc_info=True)
            raise FileError(f"Could not initialize storage backend: {e}") from e

    return _storage_backend


@contextmanager
def storage_context():
    """
    Context manager for storage operations with unified exception handling.

    Yields:
        StorageBackend: Storage instance
    """
    storage = get_storage()

    try:
        yield storage
    except Exception as e:
        logger.error("Storage operation failed: %s", e, exc_info=True)
        raise FileError(str(e)) from e


def read_file(key: str) -> Optional[bytes]:
    """
    Read file content from storage.

    Args:
        key: File key in storage.

    Returns:
        File content bytes, or None if file not found.
    """
    if not isinstance(key, str):
        raise TypeError("key must be a string")

    try:
        with storage_context() as storage:
            return storage.read(key)
    except FileNotFoundError:
        return None
    except FileError as e:
        logger.error("Error reading file %s: %s", key, e, exc_info=True)
        raise


def write_file(
    key: str,
    content: bytes,
    content_type: Optional[str] = None,
    acl: str = 'private'
) -> str:
    """
    Write file to storage.

    Args:
        key: File key
        content: File content in bytes
        content_type: Optional MIME type
        acl: S3 ACL ('private', 'public-read', etc.)

    Returns:
        Stored file key.
    """
    if not isinstance(key, str):
        raise TypeError("key must be a string")

    if not isinstance(content, bytes):
        raise TypeError("content must be bytes")

    with storage_context() as storage:
        return storage.write(key, content, content_type=content_type, acl=acl)


def delete_file(key: str) -> None:
    """
    Delete file from storage.

    Args:
        key: File key
    """
    if not isinstance(key, str):
        raise TypeError("key must be a string")

    with storage_context() as storage:
        storage.delete(key)


def file_exists(key: str) -> bool:
    """
    Check if file exists in storage.

    Args:
        key: File key

    Returns:
        True if file exists, False otherwise.
    """
    if not isinstance(key, str):
        raise TypeError("key must be a string")

    with storage_context() as storage:
        return storage.exists(key)


def get_metadata(key: str) -> Optional[Dict[str, Any]]:
    """
    Get file metadata.

    Args:
        key: File key

    Returns:
        Metadata dictionary if exists, None otherwise.
    """
    if not isinstance(key, str):
        raise TypeError("key must be a string")

    with storage_context() as storage:
        metadata = storage.get_metadata(key)
        return metadata.__dict__ if metadata else None


def get_presigned_url(
    key: str,
    filename: Optional[str] = None,
    expires_in: int = 300
) -> Optional[str]:
    """
    Generate presigned URL for client download.

    Args:
        key: File key
        filename: Optional safe filename for download
        expires_in: Expiration time in seconds

    Returns:
        Presigned URL string or None on error.
    """
    if not isinstance(expires_in, int) or expires_in <= 0:
        raise ValueError("expires_in must be positive integer")

    disposition = None

    if filename:
        safe_name = sanitize_filename(filename)
        disposition = f'attachment; filename="{safe_name}"'

    with storage_context() as storage:
        return storage.get_presigned_url(
            key,
            expires_in=expires_in,
            response_content_disposition=disposition
        )


def get_presigned_upload(
    key: str,
    content_type: str,
    expires_in: int = DEFAULT_PRESIGNED_UPLOAD_EXPIRES,
    acl: str = 'private'
) -> Optional[Dict[str, Any]]:
    """
    Generate presigned POST data for direct client upload.

    Args:
        key: File key
        content_type: MIME type
        expires_in: Expiration time in seconds
        acl: S3 ACL

    Returns:
        Dictionary with presigned POST data, or None on error.
    """
    with storage_context() as storage:
        return storage.get_presigned_upload(
            key,
            content_type,
            expires_in=expires_in,
            max_size_mb=settings.EMAIL_MAX_ATTACHMENT_MB,
            acl=acl
        )


def validate_file(
    key: str,
    rule_type: str = FileTypeValidation.ANY,
    max_size_mb: Optional[int] = None
) -> bool:
    """
    Validate file against common rules.

    Args:
        key: File key
        rule_type: 'image', 'document', 'any'
        max_size_mb: Optional override of default max size

    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(rule_type, FileTypeValidation):
        raise TypeError("rule_type must be a FileTypeValidation enum member")

    with storage_context() as storage:
        validator = FileValidator(storage)
        effective_max_size = max_size_mb or DEFAULT_MAX_SIZE_MB[rule_type]

        match rule_type:
            case FileTypeValidation.IMAGE:
                rule = ValidationRules.image(effective_max_size)
            case FileTypeValidation.DOCUMENT:
                rule = ValidationRules.document(effective_max_size)
            case FileTypeValidation.ANY:
                rule = ValidationRules.any(effective_max_size)
            case _:
                raise ValueError(f"Unsupported file type for validation: {rule_type}")

        is_valid, _, _ = validator.validate(key, rule)
        return is_valid


def download_and_store(
    url: str,
    target_key: Optional[str] = None,
    acl: str = 'private'
) -> str:
    """
    Download file from URL and store in S3.

    Args:
        url: Source URL
        target_key: Optional target storage key (auto-generated if None)
        acl: S3 ACL

    Returns:
        Stored file key.
    """
    if not isinstance(url, str):
        raise TypeError("url must be a string")

    try:
        content = download_file(url)
    except FileDownloadError as e:
        logger.error("Download failed for %s: %s", url, e, exc_info=True)
        raise

    if not target_key:
        filename = infer_filename_from_url(url)
        target_key = generate_unique_filename(
            filename,
            directory="downloads",
            storage_backend=get_storage()
        )

    try:
        return write_file(target_key, content, acl=acl)
    except FileError as e:
        logger.error("Storage failed for %s: %s", target_key, e, exc_info=True)
        raise
