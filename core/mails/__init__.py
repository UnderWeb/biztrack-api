from .tasks import send_email, send_emails
from .sender import EmailSender
from .exceptions import (
    EmailError,
    EmailBuildError,
    AttachmentError,
    AttachmentNotFoundError,
    AttachmentMimeError,
    AttachmentTooLargeError,
    BatchSendError,
    EmailTransportError,
)

__all__ = [
    "send_email",
    "send_emails",
    "EmailSender",
    "EmailError",
    "EmailBuildError",
    "AttachmentError",
    "AttachmentNotFoundError",
    "AttachmentMimeError",
    "AttachmentTooLargeError",
    "BatchSendError",
    "EmailTransportError",
]
