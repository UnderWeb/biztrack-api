import logging
from typing import Any, Mapping

from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

from .attachments import AttachmentResolver
from .exceptions import AttachmentError, EmailBuildError

logger = logging.getLogger(__name__)


class EmailBuilder:
    """
    Builds a Django EmailMultiAlternatives instance from a validated payload.
    """

    def __init__(self, default_from: str, attachment_resolver: AttachmentResolver):
        """
        Initialize the EmailBuilder.

        Args:
            default_from (str): Default sender email address used when the
                payload does not provide a `from_email`.
            attachment_resolver (AttachmentResolver): Component responsible
                for resolving attachments (S3, URL, in-memory bytes).
        """
        self.default_from = default_from
        self.attachment_resolver = attachment_resolver

    def build(
        self, payload: Mapping[str, Any], connection=None
    ) -> EmailMultiAlternatives:
        """
        Build an email object from validated payload data.

        Args:
            payload (Mapping[str, Any]): Data already validated.
            connection (BaseEmailBackend | None): Optional email backend connection.

        Returns:
            EmailMultiAlternatives: A fully prepared email ready to be sent.

        Raises:
            EmailBuildError: If a critical failure occurs during email construction.
        """

        # --- Required fields ---
        try:
            to_email = payload["to_email"]
            subject = payload["subject"]
            html_body = payload["html_body"]
        except KeyError as e:
            logger.warning("Missing required email field: %s", e)
            raise EmailBuildError(
                "Missing required email field", context={"missing": str(e)}
            )

        # Build text body
        text_body = payload.get("text_body") or strip_tags(html_body)
        from_email = payload.get("from_email") or self.default_from

        # --- Construct main email object ---
        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=from_email,
                to=[to_email],
                connection=connection,
            )
        except Exception as e:
            logger.error(
                "Failed to construct EmailMultiAlternatives: %s", e, exc_info=e
            )
            raise EmailBuildError(
                "Failed to construct EmailMultiAlternatives", context={"error": str(e)}
            )

        # Optional reply-to
        if reply_to := payload.get("reply_to"):
            email.reply_to = [reply_to]

        # Add HTML body
        email.attach_alternative(html_body, "text/html")

        # --- Attachments (non-fatal) ---
        for attachment in payload.get("attachments", []):
            try:
                content = self.attachment_resolver.resolve_bytes(attachment)
                filename = self.attachment_resolver.resolve_filename(attachment)
                content_type = attachment.get("content_type")

                email.attach(filename, content, content_type)

            except AttachmentError:
                # Resolver already logged detailed cause
                continue

        logger.info(
            "Email object built successfully for recipient=%s subject='%s'",
            to_email,
            subject,
        )

        return email
