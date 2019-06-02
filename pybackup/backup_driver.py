import logging
import os
import subprocess
import sys

log = logging.getLogger(__name__)


class BackupDriver(object):
    def __init__(self, backup_factory=None):
        self._factory = backup_factory

    def init(self, cfg):
        return self._factory(cfg)
