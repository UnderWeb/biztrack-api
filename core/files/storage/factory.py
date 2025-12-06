import logging
from typing import Optional, Type

from django.conf import settings

from .base import StorageBackend
from .local_storage import LocalStorageBackend
from .s3_storage import S3StorageBackend

logger = logging.getLogger(__name__)


class StorageBackendFactory:
    """
    Factory class for creating storage backend instances.
    Centralizes backend creation logic and supports backend registration.
    """

    # Registry of supported backends
    _backends: dict[str, Type[StorageBackend]] = {
        "s3": S3StorageBackend,
        "local": LocalStorageBackend,
    }

    @classmethod
    def register_backend(cls, name: str, backend_class: Type[StorageBackend]) -> None:
        """
        Register a new storage backend type.

        Args:
            name: Identifier for the backend.
            backend_class: StorageBackend subclass.

        Raises:
            TypeError: If backend_class does not inherit from StorageBackend.
        """
        if not issubclass(backend_class, StorageBackend):
            logger.error("Attempted to register invalid backend: %s", backend_class)
            raise TypeError(
                f"Backend must inherit from StorageBackend: {backend_class}"
            )

        cls._backends[name] = backend_class
        logger.info("Registered new storage backend: %s", name)

    @classmethod
    def create_backend(
        cls, backend_type: Optional[str] = None, **kwargs
    ) -> StorageBackend:
        """
        Create a storage backend instance.

        Args:
            backend_type: Optional backend identifier ('s3', 'local', etc.).
            **kwargs: Backend-specific configuration.

        Returns:
            StorageBackend instance.

        Raises:
            ValueError: If backend_type is unsupported.
            Exception: If backend instantiation fails.
        """
        backend_type = backend_type or cls._detect_backend_type()
        backend_class = cls._backends.get(backend_type)

        if not backend_class:
            available = ", ".join(cls._backends.keys())
            logger.error("Unsupported storage backend requested: %s", backend_type)
            raise ValueError(
                f"Unsupported storage backend: {backend_type}. "
                f"Available backends: {available}"
            )

        try:
            instance = backend_class(**kwargs)
            logger.debug(
                "Successfully created '%s' storage backend instance", backend_type
            )
            return instance
        except Exception as e:
            logger.exception(
                f"Failed to instantiate {backend_type} storage backend: {e}"
            )
            raise

    @classmethod
    def _detect_backend_type(cls) -> str:
        """
        Detect the appropriate storage backend based on Django settings.

        Returns:
            str: Detected backend type ('s3' or 'local').
        """
        if getattr(settings, "AWS_STORAGE_BUCKET_NAME", None):
            logger.info("Detected S3 configuration. Using 's3' backend.")
            return "s3"

        logger.info("No S3 configuration found. Falling back to 'local' backend.")
        return "local"

    @classmethod
    def get_available_backends(cls) -> list[str]:
        """
        List all registered backend identifiers.

        Returns:
            list[str]: Registered backend names.
        """
        return list(cls._backends.keys())


# Singleton instance for convenience
factory = StorageBackendFactory()


def get_storage_backend(backend_type: Optional[str] = None, **kwargs) -> StorageBackend:
    """
    Main entry point for obtaining a storage backend instance.

    Args:
        backend_type: Optional backend type to use.
        **kwargs: Backend-specific arguments.

    Returns:
        StorageBackend: Instance of the requested storage backend.
    """
    return factory.create_backend(backend_type=backend_type, **kwargs)
