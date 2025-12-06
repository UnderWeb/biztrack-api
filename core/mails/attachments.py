import logging
from typing import Any, Dict, Optional

from django.conf import settings

from core.files import (
    download_file,
    infer_filename_from_url,
    read_file,
    sanitize_filename,
)

from .exceptions import AttachmentError

logger = logging.getLogger(__name__)


class AttachmentResolver:
    """
    Resolves attachments coming from S3, URL or in-memory bytes.
    """

    def __init__(self):
        self.max_attachment_mb = settings.EMAIL_MAX_ATTACHMENT_MB
        self.max_bytes = self.max_attachment_mb * 1024 * 1024
        self._cache: Dict[str, Optional[bytes]] = {}

    def _cache_key(self, att: Dict[str, Any]) -> str:
        """
        Generates a deterministic cache key for the attachment.
        """
        match att["type"]:
            case "s3":
                return f"s3:{att['key']}"
            case "url":
                return f"url:{att['url']}"
            case "bytes":
                return f"bytes:{att.get('filename', 'bytes')}"
            case _:
                logger.error("Invalid attachment type received: %s", att["type"])
                return f"invalid:{att['type']}"

    def resolve_bytes(self, att: Dict[str, Any]) -> bytes:
        """
        Resolves the attachment into its byte content.
        """
        key = self._cache_key(att)

        # Cache hit
        if key in self._cache:
            cached = self._cache[key]
            if cached is None:
                logger.warning("Attachment previously failed (cache hit): %s", key)
                raise AttachmentError(
                    "Previously failed attachment", {"cache_key": key}
                )

            logger.info("Attachment resolved from cache: %s", key)
            return cached

        file_type = att["type"]

        try:
            if file_type == "s3":
                content = read_file(att["key"])
                if content is None:
                    logger.warning("S3 object not found: %s", att["key"])
                    raise AttachmentError("S3 object not found", {"key": att["key"]})
            elif file_type == "url":
                try:
                    timeout = att.get("timeout", 30)
                    content = download_file(
                        att["url"],
                        timeout=timeout,
                    )
                except Exception as e:
                    logger.warning("URL download failed for %s: %s", att["url"], e)
                    raise AttachmentError("Failed to download URL", {"url": att["url"]})
            elif file_type == "bytes":
                content = att.get("content")
                if content is None:
                    logger.error("Bytes attachment missing content.")
                    raise AttachmentError("Missing 'content' for bytes attachment")

                if isinstance(content, str):
                    logger.info("Encoding string content for bytes attachment.")
                    content = content.encode()
            else:
                logger.error("Unsupported attachment type: %s", file_type)
                raise AttachmentError(
                    "Unsupported attachment type", {"type": file_type}
                )

            if len(content) > self.max_bytes:
                logger.warning(
                    "Attachment exceeds allowed size (%s MB): %s",
                    self.max_attachment_mb,
                    key,
                )
                raise AttachmentError(
                    "Attachment exceeds allowed size",
                    {"max_mb": self.max_attachment_mb},
                )

            self._cache[key] = content
            logger.info("Attachment successfully resolved: %s", key)
            return content

        except AttachmentError as e:
            self._cache[key] = None
            logger.warning("Attachment failed (cached as None): %s", key, exc_info=e)
            raise

    def resolve_filename(self, att: Dict[str, Any]) -> str:
        """
        Determines the filename for an attachment.
        """
        if "filename" in att and att["filename"]:
            return sanitize_filename(att["filename"])

        match att["type"]:
            case "url":
                return sanitize_filename(infer_filename_from_url(att["url"]))
            case "s3":
                return sanitize_filename(att["key"].split("/")[-1])
            case _:
                logger.info("Falling back to default filename for attachment.")
                return "attachment"

    def clear_cache(self) -> None:
        """Clears the attachment cache."""
        self._cache.clear()
        logger.info("Attachment cache cleared.")
