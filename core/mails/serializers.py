from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class AttachmentSerializer(serializers.Serializer):
    """
    Attachment definition supporting S3, external URL or inline bytes.
    """

    type = serializers.ChoiceField(
        choices=["s3", "url", "bytes"],
        help_text="Attachment source type.",
    )

    filename = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        help_text="Optional filename (will be sanitized).",
    )

    content_type = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional MIME type (e.g., 'application/pdf').",
    )

    # S3-specific
    key = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="S3 object key (required for type='s3').",
    )

    # URL-specific
    url = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text="URL to download (required for type='url').",
    )

    timeout = serializers.IntegerField(
        required=False,
        default=30,
        min_value=1,
        max_value=300,
        help_text="Download timeout in seconds (1-300).",
    )

    # Inline-bytes
    content = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Content as string (base64 or plain text).",
    )

    def validate(self, data):
        """
        Validates required fields depending on the attachment type.

        Args:
            data (dict): Partially deserialized attachment payload.

        Returns:
            dict: The validated data.

        Raises:
            rest_framework.exceptions.ValidationError:
                - {"key": "Required"} if type == "s3" and "key" is missing.
                - {"url": "Required"} if type == "url" and "url" is missing.
                - {"content": "Required"} if type == "bytes" and "content"
                is missing.
        """
        file_type = data.get("type")

        if file_type == "s3" and not data.get("key"):
            raise ValidationError({"key": "Required"})

        if file_type == "url" and not data.get("url"):
            raise ValidationError({"url": "Required"})

        if file_type == "bytes" and not data.get("content"):
            raise ValidationError({"content": "Required"})

        return data


class EmailPayloadSerializer(serializers.Serializer):
    """
    Payload for sending a single email.
    """

    to_email = serializers.EmailField(
        help_text="Recipient email address.",
    )

    subject = serializers.CharField(
        max_length=255,
        help_text="Email subject line.",
    )

    html_body = serializers.CharField(
        help_text="HTML content of the email.",
    )

    text_body = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=("Plain text alternative. Auto-generated from HTML if omitted."),
    )

    from_email = serializers.EmailField(
        required=False,
        help_text="Sender email (system default if omitted).",
    )

    reply_to = serializers.EmailField(
        required=False,
        help_text="Reply-to email address.",
    )

    attachments = AttachmentSerializer(
        required=False,
        many=True,
        help_text="Optional file attachments.",
    )

    def validate_attachments(self, value):
        """
        Limit number of attachments allowed per email.
        """
        max_attachments = getattr(settings, "EMAIL_MAX_ATTACHMENTS", 10)

        if len(value) > max_attachments:
            raise serializers.ValidationError(
                f"Maximum {max_attachments} attachments allowed."
            )

        return value
