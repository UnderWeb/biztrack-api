import logging
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.core.mail import get_connection

from .attachments import AttachmentResolver
from .builder import EmailBuilder
from .exceptions import EmailBuildError
from .serializers import EmailPayloadSerializer

logger = logging.getLogger(__name__)


class EmailSender:
    """
    High-level email sending service with batch support.
    """

    def __init__(
        self,
        default_from: Optional[str] = None,
        batch_size: Optional[int] = None,
    ):
        """
        Initialize EmailSender.

        Args:
            default_from: sender email (defaults to settings.DEFAULT_FROM_EMAIL).
            batch_size: emails per batch (defaults to settings.EMAIL_BATCH_SIZE).
        """
        self.default_from = default_from or settings.DEFAULT_FROM_EMAIL
        self.batch_size = batch_size or settings.EMAIL_BATCH_SIZE

    # Public API ---------------------------------------------------------
    def send_one(self, payload: Dict[str, Any]) -> bool:
        """
        Send a single email.

        Returns:
            Bool: True if the email was sent successfully, False otherwise.
        """
        result = self.send_many([payload])
        return result["sent"] == 1

    def send_many(self, payloads: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Send multiple emails in batches.

        Returns:
            Dict: {"sent": int, "failed": int, "total": int}.
        """
        return self._send_batch(payloads)

    # Internal implementation -------------------------------------------
    def _send_batch(self, payloads: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Split the list of payloads into chunks and process each batch.

        Args:
            payloads (List[Dict[str, Any]]): Raw email payload dictionaries to send.

        Returns:
            Dict[str, int]: Summary of the entire batch.
        """
        total = len(payloads)

        if total == 0:
            logger.info("No payloads provided to send.")
            return {"sent": 0, "failed": 0, "total": 0}

        total_sent = 0
        total_failed = 0

        logger.info(
            "Starting batch send: total_payloads=%d batch_size=%d",
            total,
            self.batch_size,
        )

        for i in range(0, total, self.batch_size):
            chunk = payloads[i : i + self.batch_size]
            chunk_result = self._process_chunk(chunk)

            total_sent += chunk_result.get("sent", 0)
            total_failed += chunk_result.get("failed", 0)

            logger.info(
                "Chunk processed: chunk_index=%d chunk_total=%d sent=%d failed=%d",
                i // self.batch_size,
                len(chunk),
                chunk_result.get("sent", 0),
                chunk_result.get("failed", 0),
            )

        logger.info(
            "Batch send finished: total=%d sent=%d failed=%d",
            total,
            total_sent,
            total_failed,
        )

        return {"sent": total_sent, "failed": total_failed, "total": total}

    def _process_chunk(self, payloads: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Validate, build, and send emails for a single batch chunk.

        Args:
            payloads (List[Dict[str, Any]]): Subset of payloads belonging to this chunk.

        Returns:
            Dict[str, int]: {"sent": int, "failed": int}
        """
        sent = 0
        failed = 0

        # Create per-chunk resolver & builder to keep cache isolated.
        resolver = AttachmentResolver()
        builder = EmailBuilder(self.default_from, resolver)

        logger.info("Processing chunk: size=%d", len(payloads))

        try:
            with get_connection() as connection:
                emails = []

                for idx, payload in enumerate(payloads):
                    serializer = EmailPayloadSerializer(data=payload)

                    if not serializer.is_valid():
                        failed += 1
                        logger.error(
                            "Invalid email payload [index=%d]: %s",
                            idx,
                            serializer.errors,
                        )
                        continue

                    try:
                        email = builder.build(serializer.validated_data, connection)
                        emails.append(email)
                    except EmailBuildError as e:
                        failed += 1
                        logger.error(
                            "Failed to build email [index=%d]: %s", idx, e, exc_info=e
                        )
                    except Exception as e:
                        failed += 1
                        logger.exception(
                            "Unexpected error during email build [index=%d]: %s",
                            idx,
                            e,
                        )

                if not emails:
                    logger.info("No valid emails to send in this chunk.")
                    return {"sent": sent, "failed": failed}

                # Attempt to send messages
                try:
                    sent_count = connection.send_messages(emails)
                    # Some backends may return None; treat as 0 in that case.
                    if sent_count is None:
                        logger.warning(
                            "Email backend returned None from send_messages; "
                            "interpreting as 0 sent."
                        )
                        sent_count = 0

                    sent += int(sent_count)
                    failed += len(emails) - int(sent_count)

                    logger.info(
                        "Chunk send result: attempted=%d sent=%d failed=%d",
                        len(emails),
                        sent_count,
                        len(emails) - int(sent_count),
                    )
                except Exception as e:
                    # Sending failed for the entire chunk. Mark all as failed.
                    failed += len(emails)
                    logger.exception("Failed to send emails for this chunk: %s", e)

        except Exception as e:
            failed += len(payloads)
            logger.exception("Connection error during chunk processing: %s", e)

        try:
            resolver.clear_cache()
        except Exception:
            logger.debug("Resolver.clear_cache() raised, ignoring.", exc_info=True)

        return {"sent": sent, "failed": failed}
