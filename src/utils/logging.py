"""
@author Jack Ringer
Date: 7/26/2024
Description:
Shared utilities related to logging.
"""

import sys

from loguru import logger


def get_and_set_logger(log_out):
    if log_out is None:
        log_out = sys.stdout
    # Remove the default stdout handler
    logger.remove()
    logger.add(
        log_out,
        format="{time} {level} {message}",
        level="INFO",
    )
    return logger
