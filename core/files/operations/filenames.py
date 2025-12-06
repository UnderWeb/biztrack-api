import logging
import re
import uuid
from datetime import datetime
from pathlib import PurePosixPath
from typing import Optional, Tuple
from urllib.parse import unquote, urlparse

logger = logging.getLogger(__name__)

# ======================================================
# Constants
# ======================================================
DEFAULT_FILENAME: str = "file"
"""Default fallback filename when inference or sanitization fails."""

MAX_FILENAME_LENGTH: int = 255
"""Maximum allowed filename length (filesystem safe)."""

MAX_ATTEMPTS: int = 100
"""Maximum attempts to generate a unique filename before falling back to UUID."""

UNSAFE_CHAR_PATTERN: re.Pattern = re.compile(r'[<>:"/\\|?*\x00-\x1F\s]+')
"""Regex pattern to detect unsafe characters in filenames."""


def validate_filename(filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate filename for safety and compliance.

    Checks for empty strings, type, length, unsafe characters, and path traversal.

    Args:
        filename: Filename to validate.

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message).
        `error_message` is None if valid.
    """
    if not filename:
        return False, "Filename cannot be empty"

    if not isinstance(filename, str):
        return False, "Filename must be a string"

    if len(filename) > MAX_FILENAME_LENGTH:
        return False, f"Filename exceeds {MAX_FILENAME_LENGTH} characters"

    if UNSAFE_CHAR_PATTERN.search(filename):
        return False, "Filename contains unsafe characters"

    if ".." in filename or filename.startswith("/"):
        return False, "Filename cannot contain path components"

    return True, None


def sanitize_filename(filename: str, default: str = DEFAULT_FILENAME) -> str:
    """
    Remove unsafe characters, trim whitespace/dots, fallback to default.

    Args:
        filename: Original filename.
        default: Fallback filename if sanitization fails.

    Returns:
        str: Sanitized filename safe for filesystem and S3.
    """
    if not filename or not isinstance(filename, str):
        logger.debug(
            "Sanitize: invalid filename '%s', returning default '%s'", filename, default
        )
        return default

    safe = UNSAFE_CHAR_PATTERN.sub("_", filename)
    safe = safe.strip().strip(".")
    if not safe:
        logger.debug(
            "Sanitize: filename became empty after cleanup, returning default '%s'",
            default,
        )
        return default

    return safe


def truncate_filename(filename: str, max_length: int = MAX_FILENAME_LENGTH) -> str:
    """
    Truncate filename preserving extension.

    Args:
        filename: Original filename.
        max_length: Maximum allowed length.

    Returns:
        str: Truncated filename safe for storage.
    """
    if len(filename) <= max_length:
        return filename

    name, ext = split_extension(filename)
    max_name_len = max_length - len(ext) - 1
    if max_name_len <= 0:
        return f"{DEFAULT_FILENAME}{ext}"

    return f"{name[:max_name_len]}{ext}"


def split_extension(filename: str) -> Tuple[str, str]:
    """
    Split filename into base name and extension (including dot).

    Args:
        filename: Full filename.

    Returns:
        Tuple[str, str]: (base_name, extension_with_dot)
    """
    if filename.startswith("."):
        return "", filename

    if "." in filename:
        name, ext = filename.rsplit(".", 1)
        return name, f".{ext}"

    return filename, ""


def infer_filename_from_url(url: str, default: str = DEFAULT_FILENAME) -> str:
    """
    Infer filename from a URL safely.

    Args:
        url: Source URL.
        default: Fallback filename if inference fails.

    Returns:
        str: Sanitized filename.
    """
    if not url or not isinstance(url, str):
        logger.debug("Infer: invalid URL '%s', returning default '%s'", url, default)
        return default

    try:
        path = unquote(urlparse(url).path)
        filename = PurePosixPath(path).name
        filename = filename.split("?", 1)[0].split("#", 1)[0]

        if not filename or filename in (".", ".."):
            logger.debug(
                "Infer: URL '%s' yielded empty filename, returning default '%s'",
                url,
                default,
            )
            return default

        return sanitize_filename(filename, default)
    except Exception as e:
        logger.warning("Infer: failed to extract filename from URL '%s': %s", url, e)
        return default


def infer_filename_from_s3_key(s3_key: str, default: str = DEFAULT_FILENAME) -> str:
    """
    Extract filename from S3 key path safely.

    Args:
        s3_key: S3 object key.
        default: Fallback filename if extraction fails.

    Returns:
        str: Extracted filename.
    """
    if not s3_key:
        logger.debug("Infer: empty S3 key, returning default '%s'", default)
        return default
    return s3_key.rstrip("/").split("/")[-1] or default


def generate_s3_key(
    original_name: str, prefix: str = "uploads", include_date: bool = True
) -> str:
    """
    Generate organized S3 key with optional date-based folders.

    Args:
        original_name: Original filename.
        prefix: S3 key prefix.
        include_date: Whether to include date-based directory (YYYY/MM/DD).

    Returns:
        str: Full S3 key path.
    """
    sanitized = sanitize_filename(original_name)
    parts = [prefix.rstrip("/")]
    if include_date:
        parts.append(datetime.now().strftime("%Y/%m/%d"))
    parts.append(sanitized)
    return "/".join(parts)


def generate_unique_filename(
    base_name: str, directory: str = "", storage_backend=None
) -> str:
    """
    Generate unique filename to avoid collisions in a storage backend.

    Args:
        base_name: Base filename to make unique.
        directory: Optional directory prefix.
        storage_backend: Storage backend instance with `exists` method.

    Returns:
        str: Unique filename or path.
    """
    sanitized = sanitize_filename(base_name)
    name_part, ext = split_extension(sanitized)

    def build_path(name: str) -> str:
        return f"{directory.rstrip('/')}/{name}" if directory else name

    candidate = build_path(sanitized)
    if not storage_backend or not storage_backend.exists(candidate):
        return candidate

    for i in range(1, MAX_ATTEMPTS + 1):
        candidate_name = f"{name_part}_{i}{ext}"
        candidate = build_path(candidate_name)
        if not storage_backend.exists(candidate):
            return candidate

    unique_name = f"{name_part}_{uuid.uuid4().hex[:8]}{ext}"
    logger.info("Unique filename fallback to UUID: %s", unique_name)
    return build_path(unique_name)
