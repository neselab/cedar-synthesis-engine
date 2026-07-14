"""API-key validation helpers for AutoCedar."""

from __future__ import annotations

from autocedar.providers import ChatMessage
from autocedar.providers.anthropic_api import AnthropicAPIBackend


_INVISIBLE_KEY_CHARS = {
    "\ufeff",  # byte order mark
    "\u200b",  # zero-width space
    "\u200c",  # zero-width non-joiner
    "\u200d",  # zero-width joiner
    "\u2060",  # word joiner
}


def normalize_anthropic_api_key(value: str) -> str:
    """Normalize a pasted Anthropic key without changing visible token chars."""
    stripped = value.strip().strip("\"'")
    return "".join(
        char for char in stripped if not char.isspace() and char not in _INVISIBLE_KEY_CHARS
    )


def is_anthropic_auth_error(exc: Exception) -> bool:
    """Return true when an exception is Anthropic rejecting the API key."""
    name = exc.__class__.__name__.lower()
    text = str(exc).lower()
    return (
        "authentication" in name
        or "invalid x-api-key" in text
        or "authentication_error" in text
        or "error code: 401" in text
    )


def validate_anthropic_api_key(api_key: str, *, model: str) -> None:
    """Make a minimal Anthropic request to confirm the key actually works.

    This intentionally runs before persisting user-provided keys so a pasted
    placeholder, expired key, or wrong-provider token does not poison future
    AutoCedar sessions.
    """
    backend = AnthropicAPIBackend(api_key=api_key)
    backend.generate_text(
        model=model,
        max_tokens=1,
        messages=(ChatMessage(role="user", content="Reply with OK."),),
    )


def format_api_key_validation_error(exc: Exception, *, model: str) -> str:
    """Return a user-facing validation failure without leaking SDK internals."""
    if is_anthropic_auth_error(exc):
        return (
            "Anthropic rejected that API key. I did not save it. "
            "Paste the full key from the Anthropic console, not a redacted value."
        )
    return (
        f"I could not validate that API key against model `{model}`, so I did not save it. "
        "Check your network/model setting and try again."
    )


def mask_api_key_for_display(value: str) -> str:
    stripped = value.strip()
    if len(stripped) <= 10:
        return "[redacted]"
    return f"{stripped[:6]}...{stripped[-4:]}"
