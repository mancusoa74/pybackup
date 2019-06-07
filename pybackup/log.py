import logging
from logging.handlers import TimedRotatingFileHandler as TRFH
from logging import StreamHandler
from colorlog import ColoredFormatter
import os


class ColorLogger():
    def __init__(self):
        self._log = logging.getLogger()
        self._logFileHandler = TRFH(os.path.expanduser("~/.pybackup.log"),
                                    when="D",
                                    interval=1)

        self._logStreamHandler = StreamHandler()
        self._formatter =\
            ColoredFormatter(
                "%(asctime)s%(log_color)s-[%(levelname)-8s]-%(white)s%(message)s",
                datefmt=' %d-%m-%Y %H:%M:%S',
                reset=True,
                log_colors={
                    'DEBUG':    'purple',
                    'INFO':     'cyan',
                    'WARNING':  'yellow',
                    'ERROR':    'red',
                    'CRITICAL': 'white,bg_red'
                    }
                    )
        self._logFileHandler.setFormatter(self._formatter)
        self._logStreamHandler.setFormatter(self._formatter)
        self._log.addHandler(self._logFileHandler)
        self._log.addHandler(self._logStreamHandler)
        self.set_level('INFO')

    def set_level(self, level):
        level_map = {'DEBUG':    logging.DEBUG,
                     'INFO':     logging.INFO,
                     'WARNING':  logging.WARNING,
                     'ERROR':    logging.ERROR,
                     'CRITICAL': logging.CRITICAL
                     }
        try:
            log_level = level_map[level]
        except:
            log_level = logging.INFO

        self._log.setLevel(log_level)

    def get_log(self):
        return self._log
