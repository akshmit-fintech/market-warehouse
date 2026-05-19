"""Structured logging with structlog.

Usage:
    from warehouse.log_setup import setup_logging
    from structlog import get_logger

    setup_logging()
    log = get_logger(__name__)
    log.info("hello", symbol="RELIANCE", price=2850.50)
"""

from __future__ import annotations

import logging
import sys

import structlog


def setup_logging(
    log_level: str = "INFO",
    json_output: bool = False,
    timezone: str = "Asia/Kolkata",
) -> None:
    """Configure structlog with a standard processor pipeline.

    Call once at application startup before any module creates loggers.

    Parameters
    ----------
    log_level:
        One of DEBUG, INFO, WARNING, ERROR, CRITICAL.
    json_output:
        If True, output newline-delimited JSON (for production / scripting).
        If False, output human-readable colored logs (for development).
    timezone:
        IANA timezone string used for timestamp rendering (display only;
        internal representation is always UTC).
    """

    # ── Shared processors (applied in both dev and prod) ────────────────

    shared_processors: list[structlog.typing.Processor] = [
        # Add a UTC timestamp as a float (seconds since epoch).
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        # Add the log level name as a string.
        structlog.stdlib.add_log_level,
        # Add the name of the logger that emitted the event.
        structlog.stdlib.add_logger_name,
        # Include position / call-site info (file, line, function name).
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.FUNC_NAME,
            ],
        ),
    ]

    # ── Output-specific processors ──────────────────────────────────────

    if json_output:
        # Merge existing context with the event dict, then render as JSON.
        processors: list[structlog.typing.Processor] = shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ]
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
            foreign_pre_chain=shared_processors,
        )
    else:
        # Render a human-readable coloured line.
        processors = shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ]
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(
                colors=True,
                sort_keys=False,
            ),
            foreign_pre_chain=shared_processors,
        )

    # ── Wire up structlog ───────────────────────────────────────────────

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # ── Route standard-library logging through structlog ────────────────
    # This ensures third-party libraries (httpx, yfinance, etc.) appear
    # in the same structured format as our own logs.

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    # Remove any default handlers added by imported libraries.
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())

    # Suppress overly verbose loggers from dependencies.
    for noisy_logger in ("httpx", "yfinance", "urllib3", "matplotlib"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
