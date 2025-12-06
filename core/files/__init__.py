# ======================================================
# Client core operations
# ======================================================
from .client import (
    file_exists,
    read_file,
    write_file,
    delete_file,
    get_metadata,
    get_presigned_upload,
    get_presigned_url,
    validate_file,
    download_and_store,
)

# ======================================================
# Utility functions (from operations)
# ======================================================
from .operations import (
    download_file,
    infer_filename_from_url,
    sanitize_filename,
    validate_content_type_allowed,
    validate_max_size,
)

# ======================================================
# Exceptions
# ======================================================
from .exceptions import (
    FileError,
    FileDownloadError,
    FileValidationError,
    FileNotFoundError,
)

__all__ = [
    # Client core operations
    "file_exists",
    "read_file",
    "write_file",
    "delete_file",
    "get_metadata",
    "get_presigned_upload",
    "get_presigned_url",
    "validate_file",
    "download_and_store",

    # Utility functions
    "download_file",
    "infer_filename_from_url",
    "sanitize_filename",
    "validate_content_type_allowed",
    "validate_max_size",

    # Exceptions
    "FileError",
    "FileDownloadError",
    "FileValidationError",
    "FileNotFoundError",
]
