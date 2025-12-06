import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager

import boto3
from botocore.exceptions import ClientError
from django.conf import settings

from .base import StorageBackend, FileMetadata
from ..enums import S3ACL
from ..exceptions import FileNotFoundError, FilePermissionError, FileError

logger = logging.getLogger(__name__)


class S3StorageBackend(StorageBackend):
    """
    S3 storage backend with proper abstraction.
    Handles 80% private, 10% public, 10% system-generated files.
    """

    def __init__(
        self,
        bucket: Optional[str] = None,
        region: Optional[str] = None,
        default_acl: S3ACL = S3ACL.PRIVATE
    ) -> None:
        self.bucket: str = bucket or settings.AWS_STORAGE_BUCKET_NAME
        self.region: str = region or getattr(settings, 'AWS_REGION', 'us-east-1')
        self.default_acl: S3ACL = default_acl
        self._client: Optional[Any] = None

        # Enterprise configuration
        self.max_retries: int = 3
        self.timeout: int = 30

    @property
    def client(self) -> Any:
        """Lazy initialization of boto3 S3 client."""
        if self._client is None:
            self._client = boto3.client(
                's3',
                region_name=self.region,
                config=boto3.session.Config(
                    connect_timeout=self.timeout,
                    read_timeout=self.timeout,
                    retries={'max_attempts': self.max_retries}
                )
            )
        return self._client

    @contextmanager
    def _handle_s3_errors(self, operation: str, key: str):
        """
        Context manager for consistent S3 error handling and logging.

        Args:
            operation: Name of the S3 operation (read, write, delete, etc.)
            key: S3 object key

        Raises:
            FileNotFoundError, FilePermissionError, FileError
        """
        try:
            yield
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            extra_context = {'bucket': self.bucket, 'key': key, 'operation': operation, 'error_code': error_code}

            if error_code in ('404', 'NoSuchKey', 'NotFound'):
                logger.error("S3 object not found: %s", key, extra=extra_context)
                raise FileNotFoundError(f"S3 object not found: {key}", context=extra_context)
            elif error_code in ('403', 'AccessDenied'):
                logger.error("Access denied to S3 object: %s", key, extra=extra_context)
                raise FilePermissionError(f"Access denied to S3 object: {key}", context=extra_context)
            else:
                logger.error("S3 %s failed for %s: %s", operation, key, str(e), extra=extra_context)
                raise FileError(f"S3 {operation} failed for {key}: {str(e)}", context=extra_context)
        except Exception as e:
            extra_context = {'bucket': self.bucket, 'key': key, 'operation': operation}
            logger.error("Unexpected error during %s for %s: %s", operation, key, str(e), extra=extra_context)
            raise FileError(f"Unexpected error during {operation} for {key}: {str(e)}", context=extra_context)

    def read(self, key: str) -> bytes:
        """
        Read file content from S3.

        Args:
            key: S3 object key

        Returns:
            File content in bytes

        Raises:
            FileNotFoundError, FilePermissionError, FileError
        """
        with self._handle_s3_errors('read', key):
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            return response['Body'].read()

    def write(
        self,
        key: str,
        content: bytes,
        content_type: Optional[str] = None,
        acl: Optional[S3ACL] = None
    ) -> str:
        """
        Write file content to S3.

        Args:
            key: S3 object key
            content: File content in bytes
            content_type: Optional MIME type
            acl: Optional ACL override

        Returns:
            The S3 key

        Raises:
            FilePermissionError, FileError
        """
        extra_args: Dict[str, Any] = {'ACL': acl.value if acl else self.default_acl.value}
        if content_type:
            extra_args['ContentType'] = content_type

        with self._handle_s3_errors('write', key):
            self.client.put_object(Bucket=self.bucket, Key=key, Body=content, **extra_args)
            return key

    def delete(self, key: str) -> None:
        """
        Delete file from S3.

        Args:
            key: S3 object key

        Raises:
            FilePermissionError, FileError
        """
        with self._handle_s3_errors('delete', key):
            self.client.delete_object(Bucket=self.bucket, Key=key)

    def exists(self, key: str) -> bool:
        """
        Check if file exists in S3.

        Args:
            key: S3 object key

        Returns:
            True if exists, False otherwise
        """
        try:
            with self._handle_s3_errors('exists', key):
                self.client.head_object(Bucket=self.bucket, Key=key)
                return True
        except FileNotFoundError:
            return False
        except FileError:
            return False

    def get_metadata(self, key: str) -> Optional[FileMetadata]:
        """
        Get file metadata from S3.

        Args:
            key: S3 object key

        Returns:
            FileMetadata object or None if not found

        Raises:
            FileError
        """
        try:
            with self._handle_s3_errors('head_object', key):
                response = self.client.head_object(Bucket=self.bucket, Key=key)
                return FileMetadata(
                    key=key,
                    size=response.get('ContentLength'),
                    content_type=response.get('ContentType'),
                    last_modified=response.get('LastModified'),
                    etag=response.get('ETag'),
                    extra={
                        'storage_class': response.get('StorageClass'),
                        'server_side_encryption': response.get('ServerSideEncryption'),
                    }
                )
        except FileNotFoundError:
            return None

    def get_presigned_url(
        self,
        key: str,
        expires_in: int = 300,
        response_content_disposition: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate presigned URL for private S3 objects.

        Args:
            key: S3 object key
            expires_in: Expiration in seconds
            response_content_disposition: Optional content disposition

        Returns:
            Presigned URL or None

        Raises:
            FileError
        """
        params: Dict[str, Any] = {'Bucket': self.bucket, 'Key': key}
        if response_content_disposition:
            params['ResponseContentDisposition'] = response_content_disposition

        try:
            with self._handle_s3_errors('generate_presigned_url', key):
                return self.client.generate_presigned_url('get_object', Params=params, ExpiresIn=expires_in)
        except FileError:
            return None

    def get_presigned_upload(
        self,
        key: str,
        content_type: str,
        expires_in: int = 3600,
        max_size_mb: int = 50,
        acl: S3ACL = S3ACL.PRIVATE
    ) -> Optional[Dict[str, Any]]:
        """
        Generate presigned POST for direct client upload.

        Args:
            key: S3 object key
            content_type: MIME type
            expires_in: Expiration in seconds
            max_size_mb: Maximum allowed size in MB
            acl: ACL for uploaded object

        Returns:
            Presigned POST dict or None

        Raises:
            FileError
        """
        conditions = [
            ["content-length-range", 1, max_size_mb * 1024 * 1024],
            {"Content-Type": content_type},
        ]

        fields: Dict[str, Any] = {"Content-Type": content_type}
        if acl != S3ACL.PRIVATE:
            fields["acl"] = acl.value

        try:
            with self._handle_s3_errors('generate_presigned_post', key):
                return self.client.generate_presigned_post(
                    Bucket=self.bucket,
                    Key=key,
                    Fields=fields,
                    Conditions=conditions,
                    ExpiresIn=expires_in,
                )
        except FileError:
            return None
