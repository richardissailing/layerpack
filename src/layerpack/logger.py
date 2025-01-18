import logging
import sys


def setup_logger(verbose: bool = False) -> logging.Logger:
    """Configure and return logger instance."""
    logger = logging.getLogger("layerpack")

    # Clear any existing handlers
    logger.handlers.clear()

    # Set level based on verbose flag
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    return logger


# Global logger instance
logger = setup_logger()
