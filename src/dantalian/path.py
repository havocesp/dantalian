import os
import logging
import sys
import re
import subprocess
from functools import lru_cache

from dantalian.errors import DependencyError

logger = logging.getLogger(__name__)


def public(f):
    all = sys.modules[f.__module__].__dict__.setdefault('__all__', [])
    if f.__name__ not in all:
        all.append(f.__name__)
    return f


@public
@lru_cache()
def rootdir(root):
    return os.path.join(root, '.dantalian')


@public
@lru_cache()
def fuserootdir(root):
    return os.path.join(root, '.dantalian-fuse')


@public
@lru_cache()
def rootfile(root):
    return os.path.join(rootdir(root), 'root')


@public
@lru_cache()
def dirsdir(root):
    return os.path.join(rootdir(root), 'dirs')


@public
@lru_cache()
def treefile(root):
    return os.path.join(rootdir(root), 'mount')


@public
@lru_cache()
def ctreefile(root):
    return os.path.join(rootdir(root), 'mount_custom')


@public
def samefile(f1, f2):
    """If `f1` and `f2` refer to same inode.

    :rtype: :class:`bool`

    """
    return os.path.samestat(os.lstat(f1), os.lstat(f2))


@public
def listdir(path):
    """Return full paths of files in `path`.

    :rtype: `iterator`

    """
    return iter(os.path.join(path, f) for f in os.listdir(path))


@public
def fixsymlinks(links, oldprefix, newprefix):
    """Fix symlinks

    Recursively replace symlinks `links` that match `oldprefix` with
    `newprefix`.  `links` is as returned from findsymlinks().
    """
    oldprefix = re.compile(r"^" + re.escape(oldprefix))
    for set in links:
        try:
            f = set.pop(0)
        except IndexError:
            logger.warn("Empty set")
            continue
        newtarget = oldprefix.sub(newprefix, os.readlink(f), count=1)
        logger.debug("unlinking %r", f)
        os.unlink(f)
        logger.debug("symlinking %r to %r", f, newtarget)
        os.symlink(newtarget, f)
        for file in set:
            logger.debug("unlinking %r", file)
            os.unlink(file)
            logger.debug("linking %r to %r", file, f)
            os.link(f, file)


@public
def findsymlinks(dir):
    """Find symlinks

    Returns a list of lists.  Symlinks that are the same inode are grouped
    together.  Relies on 'find' utility, for sheer simplicity and speed.
    If it cannot be found, :exc:`DependencyError` is raised.  Output paths
    are absolute.
    """
    try:
        output = subprocess.check_output(
            ['find', dir, '-type', 'l'])
    except FileNotFoundError:
        raise DependencyError("find could not be found; \
            probably findutils is not installed")
    output = output.decode().rstrip().split('\n')
    result = []
    for file in output:
        found = 0
        for set in result:
            if samefile(set[0], file):
                set.append(file)
                found = 1
                break
        if not found:
            result.append([file])
    return result
