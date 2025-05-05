import logging

class LevelSensitiveFormatter(logging.Formatter):
    def format(self, record):
        if record.levelno >= logging.WARNING:
            self._style._fmt = '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        else:
            self._style._fmt = '%(asctime)s - %(levelname)s - %(message)s'
        return super().format(record)

def configure_logger(level: int = logging.INFO):
    """
    Configure logging format. Includes line numbers only for warnings and above.

    Args:
        level (int): Logging level (e.g., logging.DEBUG, logging.INFO)
    """
    handler = logging.StreamHandler()
    handler.setFormatter(LevelSensitiveFormatter(datefmt='%Y-%m-%d %H:%M:%S'))

    logger = logging.getLogger()
    logger.setLevel(level)
    logger.handlers = [handler]
