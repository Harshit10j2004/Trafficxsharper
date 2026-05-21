import logging
from pathlib import Path


class LoggerFactory:
    loggers = {}

    @classmethod
    def get_logger(cls, name, log_file, level=logging.INFO):

        if name in cls.loggers:
            return cls.loggers[name]

        logger = logging.getLogger(name)

        if logger.handlers:
            cls.loggers[name] = logger
            return logger


        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.setLevel(level)

        logger.propagate = False

        cls.loggers[name] = logger

        return logger