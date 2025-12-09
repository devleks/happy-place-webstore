import logging
import os
from typing import Optional, Dict, Any


LOG_LEVEL = os.getenv("HAPPY_PLACE_LOG_LEVEL", "INFO").upper()


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for the given module name.

    Log format is structured and safe for production; actual PII values
    should never be logged directly by callers.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        level = getattr(logging, LOG_LEVEL, logging.INFO)
        logger.setLevel(level)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def redact_email(email: Optional[str]) -> Optional[str]:
    """Redact email to reduce PII exposure in logs.

    Example: jane.doe@example.com -> j***@example.com
    """
    if not email:
        return email

    try:
        local, domain = email.split("@", 1)
        if not local:
            return f"*@{domain}"
        return f"{local[0]}***@{domain}"
    except ValueError:
        # Not a normal email, just return masked token
        return "***"


def safe_auth_context(email: Optional[str] = None, user_type: Optional[str] = None,
                      ip: Optional[str] = None, user_agent: Optional[str] = None,
                      extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Build a PII-safe context dict for auth/order logs."""
    ctx: Dict[str, Any] = {
        "user_type": user_type,
        "email": redact_email(email) if email else None,
        "ip": ip,
        "user_agent": user_agent,
    }

    if extra:
        ctx.update(extra)

    return ctx
