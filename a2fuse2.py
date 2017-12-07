'''
Abby-Junyi Shen
269481021
ashe848
'''

#!/usr/bin/env python

from __future__ import print_function, absolute_import, division

import logging

import os
import sys
import errno

from collections import defaultdict
from fuse import FUSE, FuseOSError, Operations, LoggingMixIn
from errno import ENOENT
from stat import S_IFDIR, S_IFREG
from time import time

class A2Fuse2(LoggingMixIn, Operations):
    def __init__(self, root):
        self.root = root
        self.files = {}
        self.data = defaultdict(bytes)
        self.fd = 0
        now = time()
        self.files['/'] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now, st_mtime=now, st_atime=now, st_nlink=2, st_uid=os.getuid(), st_gid=os.getgid())

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    def access(self, path, amode):
        if os.path.basename(path) in os.listdir(self.root):
            full_path = self._full_path(path)
            if not os.access(full_path, amode):
                raise FuseOSError(errno.EACCES)
        else:
            return 0

    def chmod(self, path, mode):
        if os.path.basename(path) in os.listdir(self.root):
            full_path = self._full_path(path)
            return os.chmod(full_path, mode)
        else:
            self.files[path]['st_mode'] &= 0o770000
            self.files[path]['st_mode'] |= mode
            return 0

    def chown(self, path, uid, gid):
        if os.path.basename(path) in os.listdir(self.root):
            full_path = self._full_path(path)
            return os.chown(full_path, uid, gid)
        else:
            self.files[path]['st_uid'] = uid
            self.files[path]['st_gid'] = gid

    def create(self, path, mode, fi=None):
        self.files[path] = dict(st_mode=(S_IFREG | mode), st_nlink=1, st_size=0, st_ctime=time(), st_mtime=time(), st_atime=time(), st_uid=os.getuid(), st_gid=os.getgid())
        self.fd += 1
        return self.fd

    def flush(self, path, fh):
        if os.path.basename(path) in os.listdir(self.root):
            return os.fsync(fh)
        else:
            return 0

    def fsync(self, path, datasync, fh):
        if os.path.basename(path) in os.listdir(self.root):
            return self.flush(path, fh)
        else:
            return 0

    def fsyncdir(self, path, datasync, fh):
        return 0

    def getattr(self, path, fh=None):
        if os.path.basename(path) in os.listdir(self.root):
            full_path = self._full_path(path)
            st = os.lstat(full_path)
            return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime', 'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
        else:
            if path not in self.files:
                raise FuseOSError(ENOENT)                
            return self.files[path]

    def getxattr(self, path, name, position=0):
        if os.path.basename(path) in os.listdir(self.root):
            if name not in ['st_atime', 'st_ctime', 'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid']:
                return ''
            else:
                full_path = self._full_path(path)
                st = os.lstat(full_path)
                return getattr(st, name)
        else:
            attrs = self.files[path].get('attrs', {})    
            try:
                return attrs[name]
            except KeyError:
                return ''  # Should return ENOATTR
            
    def listxattr(self, path):
        if os.path.basename(path) in os.listdir(self.root):
            return getattr(self, path).keys()
        else:
            attrs = self.files[path].get('attrs', {})
            return attrs.keys()
        
    def mkdir(self, path, mode):
        self.files[path] = dict(st_mode=(S_IFDIR | mode), st_nlink=2, st_size=0, st_ctime=time(), st_mtime=time(), st_atime=time(), st_uid=os.getuid(), st_gid=os.getgid())
        self.files['/']['st_nlink'] += 1

    def mknod(self, path, mode, dev):
        return ''  # should raise FuseOSError(EROFS)

    def open(self, path, flags):
        if os.path.basename(path) in os.listdir(self.root):
            full_path = self._full_path(path)
            return os.open(full_path, flags)
        else:
            self.fd += 1
            return self.fd

    def opendir(self, path):
        return 0

    def read(self, path, size, offset, fh):
        if os.path.basename(path) in os.listdir(self.root):
            os.lseek(fh, offset, os.SEEK_SET)
            return os.read(fh, size)
        else:
            self.files[path]['st_atime'] = time()
            return self.data[path][offset:offset + size]

    def readdir(self, path, fh):
        full_path = self._full_path(path)
        dirents = ['.', '..'] + [x[1:] for x in self.files if x != '/']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r

    def readlink(self, path):
        if os.path.basename(path) in os.listdir(self.root):
            pathname = os.readlink(self._full_path(path))
            if pathname.startswith("/"):
                return os.path.relpath(pathname, self.root)
            else:
                return pathname
        else:
            return self.data[path]

    def release(self, path, fh):
        if os.path.basename(path) in os.listdir(self.root):
            return os.close(fh)
        else:
            return 0

    def releasedir(self, path, fh):
        return 0

    def removexattr(self, path, name):
        if os.path.basename(path) in os.listdir(self.root):
            return None
        else:
            attrs = self.files[path].get('attrs', {})    
            try:
                del attrs[name]
            except KeyError:
                pass        # Should return ENOATTR
           
    def rename(self, old, new):
        if os.path.basename(old) in os.listdir(self.root):
            return os.rename(self._full_path(old), self._full_path(new))
        else:
            self.files[new] = self.files.pop(old)
            self.data[new] = self.data.pop(old)
            self.files[new]['st_ctime'] = time()

    def rmdir(self, path):
        if os.path.basename(path) in os.listdir(self.root):
            full_path = self._full_path(path)
            return os.rmdir(full_path)
        else:
            self.files.pop(path)
            self.files['/']['st_nlink'] -= 1
            
    def setxattr(self, path, name, value, options, position=0):
        if os.path.basename(path) in os.listdir(self.root):
            return None
        else:
            # Ignore options
            attrs = self.files[path].setdefault('attrs', {})
            attrs[name] = value

    def statfs(self, path):
        if os.path.basename(path) in os.listdir(self.root):
            full_path = self._full_path(path)
            stv = os.statvfs(full_path)
            return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree', 'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag', 'f_frsize', 'f_namemax'))
        else:
            return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

    def truncate(self, path, length, fh=None):
        if os.path.basename(path) in os.listdir(self.root):
            full_path = self._full_path(path)
            with open(full_path, 'r+') as f:
                f.truncate(length)
        else:
            self.data[path] = self.data[path][:length]
            self.files[path]['st_size'] = length
            now = time()
            self.files[path]['st_ctime'] = now
            self.files[path]['st_mtime'] = now

    def unlink(self, path):
        if os.path.basename(path) in os.listdir(self.root):
            return os.unlink(self._full_path(path))
        else:
            self.files.pop(path)

    def utimens(self, path, times=None):
        if os.path.basename(path) in os.listdir(self.root):
            return os.utime(self._full_path(path), times)
        else:
            now = time()
            atime, mtime = times if times else (now, now)
            self.files[path]['st_atime'] = atime
            self.files[path]['st_ctime'] = time()
            self.files[path]['st_mtime'] = mtime

    def write(self, path, data, offset, fh):
        if os.path.basename(path) in os.listdir(self.root):
            os.lseek(fh, offset, os.SEEK_SET)
            return os.write(fh, data)
        else:
            self.data[path] = self.data[path][:offset] + data
            self.files[path]['st_size'] = len(self.data[path])
            now = time()
            self.files[path]['st_ctime'] = now
            self.files[path]['st_mtime'] = now
            return len(data)
        
def main(mountpoint, root):
    FUSE(A2Fuse2(root), mountpoint, nothreads=True, foreground=True)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main(sys.argv[2], sys.argv[1])
