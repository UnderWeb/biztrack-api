from typing import Any

ContextType = dict[str, Any] | None


class EmailError(Exception):
    """
    Base class for email-related errors.
    Supports contextual data for better logging (e.g. Sentry).
    """

    def __init__(self, message: str, *, context: ContextType = None):
        """
        Initialize the email error.

        Args:
            message (str): Human-readable error message.
            context (dict | None, optional): Additional structured metadata to
            provide context for logging and debugging. Defaults to None.self.message
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self):
        """
        String representation of the error.

        Returns:
            str: The combined message including context if present.
        """
        if not self.context:
            return self.message

        context_str = "; ".join(
            f"{k}='{v}'"
            for k, v in self.context.items()
            if v is not None and len(str(v)) < 50
        )

        return f"{self.message} | Contexto: {{{context_str}}}"


class EmailBuildError(EmailError):
    """
    Raised when an email cannot be generated.
    """

    pass


class AttachmentError(EmailError):
    """
    Raised when an attachment cannot be retrieved, validated
    or transformed.
    """

    pass


class AttachmentNotFoundError(AttachmentError):
    """
    Raised when an attachment key/path does not exist in storage.
    """

    pass


class AttachmentMimeError(AttachmentError):
    """
    Raised when MIME type cannot be determined or is invalid.
    """

    pass


class AttachmentTooLargeError(AttachmentError):
    """
    Raised when an attachment exceeds defined size limits.
    """

    pass


class BatchSendError(EmailError):
    """
    Raised when one or more emails in a batch fail.
    """

    def __init__(
        self,
        message: str,
        failed_recipients: list[str],
        *,
        context: ContextType = None,
        successful_recipients: list[str] | None = None,
    ):
        """
        Initialize the batch send error.

        Args:
            message (str): Human-readable description of the error.
            failed_recipients (list[str]): List of email addresses
            for which sending failed. Used for diagnostics, reporting,
            and selective retries.
            context (dict | None, optional): Additional structured
            metadata (e.g., batch identifiers, SMTP provider information,
            backend response codes). Defaults to None.
            successful_recipients (list[str] | None): Optional list of
            successfully sent addresses for diagnostics.
        """
        super().__init__(message, context=context)
        self.failed_recipients = failed_recipients
        self.successful_recipients = successful_recipients
        self.context["total_failed"] = len(failed_recipients)

        if successful_recipients is not None:
            self.context["total_successful"] = len(successful_recipients)

    def __str__(self) -> str:
        """
        Returns:
            str: Base message plus recipient list.
        """
        base = super().__str__()

        # Display only a sample of failures if the list is very large.
        failed_count = len(self.failed_recipients)
        recipient_sample = ", ".join(self.failed_recipients[:5])

        if failed_count > 5:
            recipient_info = (
                f"Failed Sample: [{recipient_sample}, ... (+{failed_count - 5} more)]"
            )
        else:
            recipient_info = f"Failed: {self.failed_recipients}"

        return f"{base} | Total Failed={failed_count} | {recipient_info}"


class EmailTransportError(EmailError):
    """
    Raised when the underlying email transport fails.
    """

    pass
