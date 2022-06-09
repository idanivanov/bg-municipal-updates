from datetime import datetime as dt
import logging
import os


def create_logger(logger_name, logs_dir=None):
    # create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # create formatter
    fmt = '%(asctime)s [%(filename)s:%(lineno)s] %(levelname)s: %(message)s'
    formatter = logging.Formatter(fmt, datefmt='%Y-%m-%d %H:%M:%S (%Z)')

    # create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if logs_dir:
        # create dir if it doesn't exist
        os.makedirs(logs_dir, exist_ok=True)
        # create file handler
        current_month = dt.now().strftime('%Y_%m')
        log_file_name = os.path.join(
            logs_dir,
            '{}_{}.log'.format(logger.name, current_month)
        )
        fh = logging.FileHandler(log_file_name)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger
