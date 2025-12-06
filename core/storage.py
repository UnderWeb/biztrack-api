from storages.backends.s3boto3 import S3Boto3Storage


class BaseS3Storage(S3Boto3Storage):
    """Base storage class applied to all S3 storage backends."""

    file_overwrite = True


class StaticStorage(BaseS3Storage):
    """S3 storage backend for static assets."""

    location = "static"
    default_acl = "public-read"


class PublicMediaStorage(BaseS3Storage):
    """S3 storage backend for publicly accessible media files."""

    location = "media"
    default_acl = "public-read"


class PrivateMediaStorage(BaseS3Storage):
    """S3 storage backend for private media files."""

    location = "media"
    default_acl = "private"
    custom_domain = False
