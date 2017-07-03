import pytz
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta
from logging.config import fileConfig
from settings import LOG_LEVEL

TIMEZONE = 'Asia/Hong_Kong'
time_zone = pytz.timezone(TIMEZONE)
def posix2local(timestamp, tz=time_zone):
    """Seconds since the epoch -> local time as an aware datetime object."""
    return datetime.fromtimestamp(timestamp, tz)

class Formatter(logging.Formatter):
    def converter(self, timestamp):
        return posix2local(timestamp)

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        if datefmt:
            s = dt.strftime(datefmt)
        else:
            t = dt.strftime(self.default_time_format)
            s = self.default_msec_format % (t, record.msecs)
        return s

def get_logger(log_name, log_fname=None, log_level=None):
    try:
        fileConfig('logging_cfg.ini')
    except Exception as err:
        fileConfig('funds_crawler/logging_cfg.ini')

    if not log_fname:
        log_fname = log_name + '.log'
    log_fname = 'logs/' + log_fname
    # log_name = datetime.now(time_zone).strftime("%Y%m%d") + '.log'
    format_str = "%(asctime)s [%(name)-2s] %(levelname)-2s: %(message)s"
    # file_handler = logging.FileHandler(log_name)
    # Apply the timerotating file logger.
    file_handler = TimedRotatingFileHandler(log_fname, when='midnight', interval=1, backupCount=7)
    if not log_level:
        log_level = LOG_LEVEL
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(Formatter(format_str))
    if not log_name:
        logger = logging.getLogger(log_name)
    else:
        logger = logging.getLogger(log_name)
    logger.addHandler(file_handler)
    return logger
