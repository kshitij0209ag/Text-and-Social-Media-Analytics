import logging


class TransformException(Exception):
    pass


# logging function
logger = logging.getLogger('PortalTransforms')


def log(message, severity=logging.DEBUG):
    logger.log(severity, message)


def safeToInt(value):
    """Convert value to integer or just return 0 if we can't"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
