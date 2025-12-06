from abc import ABC, abstractmethod
from typing import Optional, Mapping, Any, Dict
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FileMetadata:
    """
    Immutable container for file metadata retrieved from the storage backend.

    Attributes:
        key: Identifier or path of the stored file.
        size: File size in bytes, when available.
        content_type: MIME type reported by the backend.
        last_modified: Last modification timestamp in backend-native format.
        etag: Entity tag or suitable checksum value when available.
        extra: Additional backend-specific metadata.
    """
    key: str
    size: Optional[int] = None
    content_type: Optional[str] = None
    last_modified: Optional[str] = None
    etag: Optional[str] = None
    extra: Mapping[str, Any] = field(default_factory=dict)


class StorageBackend(ABC):
    """Abstract definition of a storage backend."""

    @abstractmethod
    def read(self, key: str) -> bytes:
        """
        Read and return the full content of the file.

        Args:
            key: Storage key or path identifying the file.

        Returns:
            File content as raw bytes.

        Raises:
            FileNotFoundError: If the file does not exist.
            FileError: For provider-specific errors.
        """
        raise NotImplementedError

    @abstractmethod
    def write(self, key: str, content: bytes, **kwargs) -> str:
        """
        Write a file to storage and return its final key.

        Args:
            key: Desired storage key.
            content: Raw file bytes.
            kwargs: Backend-specific options (ACL, ContentType, etc.).

        Returns:
            Final storage key.

        Raises:
            FileUploadError: If writing fails.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> None:
        """
        Delete a file from storage.

        Args:
            key: Storage key to delete.

        Raises:
            FileNotFoundError: If the file does not exist.
            FileError: If deletion fails.
        """
        raise NotImplementedError

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check whether a file exists in storage.

        Args:
            key: Storage key.

        Returns:
            True if exists, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def get_metadata(self, key: str) -> Optional[FileMetadata]:
        """
        Retrieve metadata for the file.

        Args:
            key: Storage key.

        Returns:
            A FileMetadata instance, or None if file is missing.
        """
        raise NotImplementedError

    # Optional features (only for S3-like backends)
    def get_presigned_url(self, key: str, **kwargs) -> Optional[str]:
        """
        Generate a presigned URL for private client access.

        Default implementation indicates unsupported feature.
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support presigned URLs.")

    def get_presigned_upload(self, key: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Generate presigned upload instructions (POST/PUT).

        Default implementation indicates unsupported feature.
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support presigned uploads.")
