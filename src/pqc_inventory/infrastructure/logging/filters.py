"""Sensitive-data filtering for application logging."""

import copy
import logging
import re
import traceback


class SensitiveDataFilter(logging.Filter):
    """Redact recognized sensitive values from logging records."""

    PATTERNS = (
        (
            re.compile(
                r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"
                r".*?"
                r"-----END [A-Z0-9 ]*PRIVATE KEY-----",
                re.DOTALL,
            ),
            "[REDACTED PRIVATE KEY]",
        ),
        (
            re.compile(
                r"\b(password|passwd|pwd|secret|token|api[_-]?key|"
                r"access[_-]?key|client[_-]?secret|authorization|"
                r"private[_-]?key|drbg[_-]?seed|seed)"
                r"(\s*[:=]\s*)"
                r'(?:"[^"]*"|\'[^\']*\'|[^\s,;]+)',
                re.IGNORECASE,
            ),
            r"\1\2[REDACTED]",
        ),
        (
            re.compile(
                r"\bBearer\s+[A-Za-z0-9._~+/=-]+",
                re.IGNORECASE,
            ),
            "Bearer [REDACTED]",
        ),
    )

    @classmethod
    def redact(cls, value: str) -> str:
        """Replace recognized sensitive values in a string."""

        for pattern, replacement in cls.PATTERNS:
            value = pattern.sub(replacement, value)

        return value

    def filter(self, record: logging.LogRecord) -> logging.LogRecord:
        """Return a sanitized copy of a logging record."""

        sanitized = copy.copy(record)

        # Render and sanitize the message, including formatting arguments.
        sanitized.msg = self.redact(record.getMessage())
        sanitized.args = ()

        # Sanitize exception information before formatters process it.
        if record.exc_info:
            exception_text = "".join(traceback.format_exception(*record.exc_info))

            sanitized.exc_text = self.redact(exception_text)

            # Prevent formatters from processing the original exception.
            sanitized.exc_info = None

        elif record.exc_text:
            # Handle exception text that was formatted before filtering.
            sanitized.exc_text = self.redact(record.exc_text)

        # Sanitize additional stack information.
        if record.stack_info:
            sanitized.stack_info = self.redact(record.stack_info)

        return sanitized
