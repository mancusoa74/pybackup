import logging
import os
import subprocess
import sys

log = logging.getLogger(__name__)


class rsync(object):
    def __init__(self, cfg):
        self._backup_dirs = cfg['backup_paths']
        self._backup_host = cfg['backup_host']
        self._backup_host_user = cfg['backup_host_user']
        self._backup_exclude_paths = []
        if 'backup_exclude_paths' in cfg:
            self._backup_exclude_paths = cfg['backup_exclude_paths']

    def _remote_dir_mapping(self, map_dir):
        for dir_item in self._backup_dirs:
            local_path = dir_item['local_path']
            if map_dir.startswith(local_path):
                remote_path = dir_item['remote_path']
                diff_path = os.path.relpath(map_dir, local_path)
                if diff_path != ".":
                    remote_path = dir_item['remote_path'] + diff_path
                return remote_path
        return None

    def _host_available(self, host):
        log.debug("Checking if host {} is available".format(host))
        res = subprocess.run(['ping', '-c 1', '-w 1', host],
                             stdout=subprocess.DEVNULL).returncode
        if res != 0:
            log.error("Backup host {} is not available. No file/dir transfer"
                      .format(host))
            return False
        return True

    def _build_rsync_cmd(self, file, remote_path):
        rsync_cmd_line = ['rsync', '-avh', '--timeout=10']
        if len(self._backup_exclude_paths) > 0:
            for exclude_path in self._backup_exclude_paths:
                rsync_cmd_line.append('--exclude')
                rsync_cmd_line.append(exclude_path)
        rsync_cmd_line.append(file)
        rsync_cmd_line.append(self._backup_host_user +
                              '@' + self._backup_host +
                              ':' + remote_path)
        return rsync_cmd_line

    def _rsync_exec(self, file, remote_path):
        if self._host_available(self._backup_host):
            log.info("backup[rsync] {} to {}".format(file, remote_path))
            rsync_cmd_line = self._build_rsync_cmd(file, remote_path)
            res = subprocess.call(rsync_cmd_line)
            if res != 0:
                log.critical("Cannot backup[rsync] file {}. rsync failed with \
                             code {}".format(file, res))
                return False
            return True
        else:
            return False

    def backup_file(self, file):
        remote_path = self._remote_dir_mapping(os.path.dirname(file))
        return self._rsync_exec(file, remote_path)

    def backup_dir(self, backup_dir):
        remote_path = self._remote_dir_mapping(backup_dir)
        return self._rsync_exec(backup_dir + '/', remote_path)
