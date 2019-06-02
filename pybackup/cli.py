import pbr.version
import argparse
import sys
from pybackup.pybackup import BackupManager
from pybackup.log import ColorLogger
import pybackup.config as config
from pyfiglet import Figlet
import threading
import time

PYBACKUP_SCHEMA = 'pybackup/pybackup_cfg_schema.yml'
PYBACKUP_CONFIG = 'pybackup/pybackup.yml'


__version__ = pbr.version.VersionInfo('pybackup').release_string()


def init_parser():
    parser = argparse.ArgumentParser(
                      description='Near-Real Time backup of directories')
    parser.add_argument('--version', action='version',
                        version='pybackup v{}'.format(__version__))
    args = parser.parse_args()
    return args


def init():
    color_logger = ColorLogger()
    log = color_logger.get_log()
    banner = Figlet(font='c_ascii_')

    log.info(banner.renderText("\npybackup v{}".format(__version__)))
    cfg = config.load_validate_config(PYBACKUP_SCHEMA, PYBACKUP_CONFIG)
    color_logger.set_level(cfg['log_level'])
    return log, cfg


def main():
    args = init_parser()
    log, cfg = init()

    backup_manager = BackupManager(cfg)
    try:
        while True:
            time.sleep(cfg['backup_period'])
            thread1 = threading.Thread(target=backup_manager.backup_worker)
            thread1.start()
            thread1.join()
    except KeyboardInterrupt:
        log.info("Terminating pybackup")
        backup_manager.stops_observers()
        log.info("pybackup terminated correctly. bye bye!")


if __name__ == "__main__":
    sys.exit(main())
