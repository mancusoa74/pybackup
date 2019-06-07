import sys
import time
import os
import logging
from watchdog.observers import Observer
from watchdog.events import RegexMatchingEventHandler
import threading
import random
import subprocess
import yaml
from pybackup.backup_driver import BackupDriver
from pybackup.rsync_driver import rsync

__author__ = 'Antonio Mancuso <mancusoa74@yahoo.com>'
__copyright__ = 'GPL3'

log = logging.getLogger(__name__)


class BackupManager(RegexMatchingEventHandler):
    def __init__(self, cfg):
        super(BackupManager,
              self).__init__(ignore_regexes=cfg['backup_ignore_files'])

        self._file_backlog = {}
        self._dir_backlog = []
        self._observers = []
        self._backup_dirs = cfg['backup_paths']
        self._backup_driver = BackupDriver(eval(cfg['backup_type'])).init(cfg)
        self._add_dirs_observer()

    def _add_dir_observer(self, backup_dir):
        if not self._backup_driver.backup_dir(backup_dir):
            self._dir_backlog.append(backup_dir)
        observer = Observer()
        observer.schedule(self, backup_dir, recursive=True)
        observer.start()
        self._observers.append(observer)

    def _add_dirs_observer(self):
        for backup_paths in self._backup_dirs:
            self._add_dir_observer(backup_paths['local_path'])
        log.info("BackupManager ready to listen to FS changes")

    def stops_observers(self):
        for _ in range(0, len(self._observers)):
            observer = self._observers.pop()
            observer.stop()
            observer.join()

    def _get_files_from_backlog(self):
        files = self._file_backlog.copy()
        self._file_backlog.clear()
        return files

    def _get_dirs_from_backlog(self):
        dirs = self._dir_backlog.copy()
        self._dir_backlog.clear()
        return dirs

    def _synch_dir(self):
        id = threading.current_thread().name
        can_continue = True
        dir_backlog = self._get_dirs_from_backlog()

        log.info("##### DIRECTORY TO BACKUP #####")
        for dir in dir_backlog:
            log.info(dir)
        log.info("##########################")

        if len(dir_backlog) == 0:
            log.info("Thread {} no dir to synchronize".format(id))
        else:
            log.info("Thread {} trying to synchronize dirs".format(id))
            for directory in dir_backlog:
                if not self._backup_driver.backup_dir(directory):
                    self._dir_backlog.append(directory)
                    can_continue = False
        return can_continue

    def _synch_files(self):
        id = threading.current_thread().name
        file_backlog = self._get_files_from_backlog()

        log.info("##### FILE TO BACKUP #####")
        for file in file_backlog:
            log.info(file)
        log.info("##########################")

        file_backlog_keys = list(file_backlog.keys())
        if len(file_backlog_keys) == 0:
            log.info("Thread {} no file to backup".format(id))
        else:
            log.debug("Thread {} processing {} files"
                      .format(id, len(file_backlog_keys)))
            for file in file_backlog_keys:
                file_status = file_backlog.pop(file)
                log.info("{} backing up {}".format(id, file))
                if not os.path.isfile(file):
                    log.critical("The file {} cannot be backup\
                                 as it has been deleted".format(file))
                else:
                    if not self._backup_driver.backup_file(file):
                        log.error("Cannot backup file {}".format(file))
                        self._file_backlog[file] = file_status

    def backup_worker(self):
        id = threading.current_thread().name
        if self._synch_dir():
            self._synch_files()

    def on_any_event(self, event):
        if event.event_type == 'modified' and event.is_directory:
            return
        if event.event_type != 'moved':
            log.info("File Event - {} - {}".format(event.event_type,
                                                   event.src_path))
        else:
            log.info("File Event - {} - {} - {}".format(event.event_type,
                                                        event.src_path,
                                                        event.dest_path))

    def on_moved(self, event):
        if os.path.isdir(event.dest_path):
            # may be add unschedule for moved/renamed directory
            self._add_dir_observer(event.dest_path)
            return
        if event.src_path not in self._file_backlog:
            self._file_backlog[event.dest_path] = 'modified'
        if event.src_path in self._file_backlog:
            del self._file_backlog[event.src_path]
            self._file_backlog[event.dest_path] = 'modified'

    def on_created(self, event):
        if os.path.isdir(event.src_path):
            self._add_dir_observer(event.src_path)
        else:
            self._file_backlog[event.src_path] = event.event_type

    def on_deleted(self, event):
        if event.src_path not in self._file_backlog:
            return
        if event.src_path in self._file_backlog:
            del self._file_backlog[event.src_path]

    def on_modified(self, event):
        if event.is_directory:
            return
        self._file_backlog[event.src_path] = event.event_type
