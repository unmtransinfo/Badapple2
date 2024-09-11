"""
@author Jack Ringer
Date: 7/26/2024
Description:
Shared utilities related to logging.
"""

import sys

from loguru import logger

VERBOSE_TO_LEVEL = ["ERROR", "INFO", "DEBUG"]


def get_and_set_logger(log_out, verbose: int = 1):
    level = VERBOSE_TO_LEVEL[verbose] if verbose < len(VERBOSE_TO_LEVEL) else "TRACE"
    if log_out is None:
        log_out = sys.stdout
    # Remove the default stdout handler
    logger.remove()
    logger.add(
        log_out,
        format="{time} {level} {message}",
        level=level,
    )
    return logger
