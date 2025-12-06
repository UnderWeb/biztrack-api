import logging
from typing import Optional, Dict, Any

from django.core.files.storage import Storage, default_storage

from .base import StorageBackend, FileMetadata
from ..exceptions import FileError, FileNotFoundError

logger = logging.getLogger(__name__)


class LocalStorageBackend(StorageBackend):
    """
    Local storage backend.
    Wraps Django's `default_storage` to unify interface with S3 backend.
    """

    def __init__(self, storage: Optional[Storage] = None):
        """
        Initialize local storage backend.

        Args:
            storage: Optional custom Django Storage instance.
        """
        self.storage = storage or default_storage
        logger.debug("Initialized LocalStorageBackend")

    def read(self, key: str) -> bytes:
        """
        Read file content from local storage.

        Args:
            key: Storage key or path identifying the file.

        Returns:
            File content as raw bytes.

        Raises:
            FileNotFoundError: If the file does not exist in the storage location.
            FileError: For errors during the read operation (e.g., permission issues).
        """
        try:
            with self.storage.open(key, 'rb') as file_obj:
                return file_obj.read()
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"File not found: {key}",
                context={'key': key, 'backend': 'local_storage'}
            ) from e
        except Exception as e:
            raise FileError(
                f"Failed to read file: {key}",
                context={'key': key, 'backend': 'local_storage', 'error': str(e)}
            ) from e

    def write(
        self,
        key: str,
        content: bytes,
        content_type: Optional[str] = None,
        **kwargs  # Ignored for local storage
    ) -> str:
        """
        Write file content to local storage.

        Args:
            key: Desired file key or path for storage.
            content: File content as raw bytes.
            content_type: Optional MIME type (stored in Django's `ContentFile` object).
            **kwargs: Extra arguments (ignored by this backend, intended for S3 ACL, etc.).

        Returns:
            The stored file key (path).

        Raises:
            FileError: If the write operation fails (e.g., disk full, permission denied).
        """
        from django.core.files.base import ContentFile

        try:
            file_obj = ContentFile(content)
            if content_type:
                file_obj.content_type = content_type
            return self.storage.save(key, file_obj)
        except Exception as e:
            raise FileError(
                f"Failed to write file: {key}",
                context={'key': key, 'backend': 'local_storage', 'error': str(e)}
            ) from e

    def delete(self, key: str) -> None:
        """
        Delete file from local storage.

        Args:
            key: File key or path to delete.

        Raises:
            FileError: If the delete operation fails.
        """
        try:
            if self.storage.exists(key):
                self.storage.delete(key)
        except Exception as e:
            raise FileError(
                f"Failed to delete file: {key}",
                context={'key': key, 'backend': 'local_storage', 'error': str(e)}
            ) from e

    def exists(self, key: str) -> bool:
        """
        Check if a file exists in local storage.

        Args:
            key: File key or path.

        Returns:
            True if the file exists, False otherwise.
        """
        try:
            return self.storage.exists(key)
        except Exception as e:
            logger.error("Exists check failed for %s: %s", key, e, exc_info=True)
            return False

    def get_metadata(self, key: str) -> Optional[FileMetadata]:
        """
        Retrieve file metadata for a local file.

        Args:
            key: File key or path.

        Returns:
            FileMetadata object if the file exists, None otherwise.
        """
        if not self.exists(key):
            return None

        try:
            size = self.storage.size(key)
            modified = getattr(self.storage, 'get_modified_time', lambda k: None)(key)

            return FileMetadata(
                key=key,
                size=size,
                content_type=None,  # Local storage doesn't store MIME type
                last_modified=str(modified) if modified else None,
                etag=None,
                extra={'backend': 'local_storage'}
            )
        except Exception as e:
            logger.error("Metadata retrieval failed for %s: %s", key, e, exc_info=True)
            return None

    def get_presigned_url(self, key: str, **kwargs) -> Optional[str]:
        """
        Get the direct URL for file access.

        Args:
            key: File key or path.
            **kwargs: Ignored.

        Returns:
            The direct URL string for the file, or None on error.
        """
        try:
            return self.storage.url(key)
        except Exception as e:
            logger.error("URL generation failed for %s: %s", key, e, exc_info=True)
            return None

    def get_presigned_upload(self, key: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Presigned upload is not supported in the LocalStorageBackend.

        Args:
            key: File key.
            content_type: MIME type (required by method signature).
            **kwargs: Ignored.

        Returns:
            None.
        """
        logger.warning(
            "LocalStorageBackend doesn't support presigned uploads. "
            "Use S3StorageBackend for this feature."
        )
        return None
