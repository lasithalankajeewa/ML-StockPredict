"""Application logging configuration."""

import logging


def configure_logging(level: int = logging.INFO) -> None:
    """Configure a concise, consistent logging format.

    Args:
        level: Standard-library logging level to apply globally.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

