import logging
from urllib.parse import urlparse

import requests
from django.conf import settings

from ..exceptions import FileDownloadError

logger = logging.getLogger(__name__)


DEFAULT_TIMEOUT: int = 30  # seconds
DEFAULT_MAX_SIZE_MB: int = 50  # megabytes
CHUNK_SIZE: int = 8192  # bytes


def download_file(
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> bytes:
    """
    Download a file from a remote URL using streaming and a strict size limit.

    Args:
        url: The HTTP/HTTPS URL to download.
        timeout: Request timeout in seconds (connect + read).

    Returns:
        The downloaded content as bytes.

    Raises:
        FileDownloadError: For invalid URLs, network errors,
        HTTP errors, or size limit violations.
    """
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        logger.warning("download_file: unsupported URL scheme for url=%s", url)
        raise FileDownloadError(f"Invalid URL scheme: {parsed.scheme}")

    max_bytes = settings.EMAIL_MAX_ATTACHMENT_MB * 1024 * 1024

    try:
        # Use a session for potential connection pooling; simple and explicit.
        with requests.Session() as session:
            with session.get(url, stream=True, timeout=timeout) as response:
                try:
                    response.raise_for_status()
                except requests.HTTPError as e:
                    logger.error(
                        "download_file: HTTP error for url=%s status=%s",
                        url,
                        response.status_code,
                        exc_info=True,
                    )
                    raise FileDownloadError(f"HTTP error {response.status_code}") from e

                # If Content-Length header is present, fail fast when it's too large.
                content_length = response.headers.get("Content-Length")

                if content_length is not None:
                    try:
                        content_length_int = int(content_length)

                        if content_length_int > max_bytes:
                            logger.warning(
                                "Content-Length %s exceeds max %s for url=%s",
                                content_length_int,
                                max_bytes,
                                url,
                            )
                            raise FileDownloadError(
                                "File exceeds allowed size (Content-Length)"
                            )
                    except ValueError:
                        logger.error(
                            "Invalid Content-Length '%s' for URL: %s",
                            content_length,
                            url,
                        )

                total = 0
                chunks = []

                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > max_bytes:
                        logger.warning(
                            "exceeded max size while streaming url=%s (bytes=%s)",
                            url,
                            total,
                        )
                        raise FileDownloadError(
                            "File exceeds allowed size during download"
                        )
                    chunks.append(chunk)

                content = b"".join(chunks)
                logger.debug(
                    "download_file: downloaded %d bytes from url=%s", len(content), url
                )
                return content

    except requests.RequestException as e:
        logger.error(
            "download_file: network error downloading url=%s: %s", url, e, exc_info=True
        )
        raise FileDownloadError(f"Network error while downloading: {str(e)}") from e
    except FileDownloadError:
        # Re-raise our domain error as-is (already logged where appropriate)
        raise
    except Exception as e:
        logger.error(
            "download_file: unexpected error for url=%s: %s", url, e, exc_info=True
        )
        raise FileDownloadError(f"Unexpected error while downloading: {str(e)}") from e
