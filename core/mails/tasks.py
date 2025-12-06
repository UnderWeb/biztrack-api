import logging
from typing import Any, Dict, List

from celery import shared_task
from celery.exceptions import Retry
from django.core.exceptions import ImproperlyConfigured

from .sender import EmailSender

logger = logging.getLogger(__name__)


@shared_task(
    name="core.mails.send_email",
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    acks_late=True,
)
def send_email(payload: Dict[str, Any]) -> bool:
    """
    Celery task to send a single email.

    Args:
        payload (Dict[str, Any]): Raw email payload. It will be validated
        inside EmailSender.

    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """
    logger.info("Task send_email started.")

    try:
        sender = EmailSender()
        result = sender.send_one(payload)

        if not result:
            logger.warning("send_email: EmailSender.send_one returned False.")
        else:
            logger.info("send_email: Email sent successfully.")

        return result

    except ImproperlyConfigured as e:
        logger.error("send_email: configuration error: %s", e, exc_info=True)
        raise  # Do NOT retry: configuration errors are not recoverable.

    except Exception as e:
        logger.exception("send_email: unexpected error: %s", e)

        try:
            raise send_email.retry(exc=e)
        except Retry:
            # Celery will handle the retry; just exit cleanly.
            return False


@shared_task(
    name="core.mails.send_emails",
    max_retries=3,
    default_retry_delay=120,  # 2 minutes
    acks_late=True,
)
def send_emails(messages: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Celery task to send multiple emails in batches.

    Args:
        messages (List[Dict[str, Any]]): List of raw email payloads.

    Returns:
        Dict[str, int]: {
            "sent": int,
            "failed": int,
            "total": int
        }
    """
    logger.info("Task send_emails started: total_messages=%d", len(messages))

    try:
        sender = EmailSender()
        result = sender.send_many(messages)

        logger.info(
            "send_emails finished: sent=%d failed=%d total=%d",
            result["sent"],
            result["failed"],
            result["total"],
        )

        return result

    except ImproperlyConfigured as e:
        logger.error("send_emails: configuration error: %s", e, exc_info=True)
        raise  # Not retryable.

    except Exception as e:
        logger.exception("send_emails: unexpected error: %s", e)

        try:
            raise send_emails.retry(exc=e)
        except Retry:
            return {"sent": 0, "failed": len(messages), "total": len(messages)}
