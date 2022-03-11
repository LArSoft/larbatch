#! /usr/bin/env python
######################################################################
#
# Name: larbatch_posix.py
#
# Purpose: Python module containing posix-like interfaces for 
#          accessing files in dCache (/pnfs/...) that do not
#          require the /pnfs filesystem to be nfs-mounted.
#
# Created: 8-Dec-2016  Herbert Greenlee
#
# Classes:
#
# dcache_file - File-like class for dCache files.  This class operates
#               on a local copy of the file, which is transferred
#               to/from dCache when the file is closed or opened using
#               ifdh.  For compatibility, this class can be used for
#               non-dCache files, in which case calls are simply
#               passed to standard python File calls, and there is no
#               initial or final file transfer.  This class implements
#               the following methods.
#
#               - close
#               - flush
#               - fileno
#               - next
#               - read
#               - readline
#               - readlines
#               - seek
#               - tell
#               - truncate
#               - write
#               - writelines
#
# Functions:
#
# The following posix-like global functions are provided by this
# module.  These mostly correspond to functions having the same name
# in the os or shutil modules.  Typically, these functions handle paths
# corresponding to dCache files (/pnfs/...) in some special way.  The
# /pnfs filesystem does not have to be nfs-mounted.  Non-dCache paths
# are simply passed to corresponding standard python functions.
#
# open - Similar as built-in python function open.  Returns a
#        file-like object of type dcache_file (in case of dCache
#        paths) or built-in type File (in case of regular files).
# readlines - Open in read mode using this module and call readlines().
# copy - Similar as shutil.copy.  Copy file.
# listdir - Similar as os.listdir.  List directory contents.
# exists - Similar as os.path.exists.  Return True if path exists.
# isdir - Simmilar as os.path.isdir.  Return True if path is a directory.
# stat - Similar as os.stat.  Return status information about a file.
# access - Similar as os.access.  Test file access.
# walk - Similar as os.walk.  Walk directory tree.
# mkdir - Similar as os.mkdir.  Make directory.
# makedirs - Similar as os.makedirs.  Make directory and parent directories.
# rename - Similar as os.rename.  Rename file.
# remove - Similar as os.remove.  Delete file.
# rmdir - Similar as os.rmdir.  Delete empty directory.
# rmtree - Similar as shutil.rmtree.  Delete a directory tree.
# chmod - Similar as os.chmod.  Change file permissions.
# symlink - Similar as os.symlink.  Make a symbolic link.
# readlink - Similar as os.readlink.  Read a symbolic link.
# root_stream - Convert path to streamable path or uri.
#
# Utility functions:
#
# use_grid - Force (or not) the use of grid tools when possible.
#
# Notes on the use of grid tools.
#
# 1.  The functions in this module may process calls using either 
#     standard python posix tools or grid tools.  In general, there
#     are three ways that any request might be handled.
#
#     a) Process requrest using standard posix tools.
#
#     b) Process request using posix tools, but with some extra
#        protections, like timeouts.
#
#     c) Process request using grid tools.
#
# 2.  The following rules are followed in deciding which of the above
#     ways of handling requests is used.
#
#     a) Non-dCache paths (that is paths that do not start with
#        "/pnfs/", including all relative paths) are always handled
#        using standard posix tools.
#
#     b) Absolute paths that start with "/pnfs/" may be handled by any
#        of the methods listed in item 1, depending on the enviromnent
#        and configuration.
#
#     c) If the /pnfs filesystem is not nfs-mounted, then paths that
#        start with "/pnfs/" are always handled using grid tools.
#
#     d) If the /pnfs filesystem is nfs-mounted, the functions in this
#        module may be configured to choose which set of tools to use
#        according to the following rules.
#
#        1) By default, this module prefers posix tools.
#
#        2) The preference for grid or posix tools may be set by
#           calling function use_grid.
#
#        3) A preference for grid tools may be set by setting
#           environment variable LARBATCH_GRID.
#       
#
# 3.  Environment variables:
#
#     a) If LARBATCH_DEBUG is defined, then a message is printed for
#        function call in this module which informs which method is
#        used to process it.
#
#     b) If LARBATCH_GRID is defined, then this module will be
#        configured to prefer grid tools.
#
#
######################################################################

from __future__ import absolute_import
from __future__ import print_function
import os, shutil
import stat as statmod
import subprocess
import threading
try:
    import queue
except ImportError:
    import Queue as queue
import uuid
import larbatch_utilities
from larbatch_utilities import convert_str
from project_modules.ifdherror import IFDHError

# Global flags.

pnfs_is_mounted = os.path.isdir('/pnfs')
prefer_grid = 'LARBATCH_GRID' in os.environ
debug = 'LARBATCH_DEBUG' in os.environ
if debug:
    print('*** Larbatch_posix: Debugging enabled.')
    


# Force grid function.

def use_grid(force=True):
    prefer_grid = force


# File-like class for dCache files.

class dcache_file:

    # Default constructor.

    def __init__(self):
        self.path = ''            # Path of file.
        self.mode = ''            # File mode.
        self.local_path = ''      # Path of local copy of file.
        self.local_file = None    # Open File object of local copy of file.

    # Initializing constructor.

    def __init__(self, path, mode='r', buf=-1):

        self.path = path
        self.mode = mode
        if path.startswith('/pnfs/'):
            self.local_path = str(uuid.uuid4()) + os.path.basename(path)
        else:
            self.local_path = path

        # Fetch copy of file from dCache, if necessary.

        if path != self.local_path and (mode.find('r') >= 0 or mode.find('a') >= 0):
            larbatch_utilities.ifdh_cp(path, self.local_path)

        # Open local copy of file.

        self.local_file = __builtins__['open'](self.local_path, mode, buf)

    # Destructor.

    def __del__(self):
        self.close()

    # Close file.

    def close(self):

        if self.local_file and not self.local_file.closed:

            # Close local copy of file.

            self.local_file.close()

            # If the local path and real path are different, do some cleanups.

            if self.path != self.local_path:

                # If file was opend for writing, transfer local copy to dCache.

                if self.mode.find('w') >= 0 or self.mode.find('a') >= 0 or self.mode.find('+') >= 0:
                    larbatch_utilities.ifdh_cp(self.local_path, self.path)

                # Delete the local copy regardless of whether the file was open for
                # reading or writing.

                os.remove(self.local_path)

    # Flush file.

    def flush(self):
        self.local_file.flush()

    # File descriptor.

    def fileno(self):
        return self.local_file.fileno()

    # Iterator.

    def __next__(self):
        return next(self.local_file)

    # Read the specified number of bytes.

    def read(self, size=-1):
        return self.local_file.read(size)

    # Read one line, up to specified number of bytes.

    def readline(self, size=-1):
        return self.local_file.readline(size)

    # Read multiple lines.

    def readlines(self, sizehint=-1):
        return self.local_file.readlines()

    # Return file position.

    def tell(self):
        return self.local_file.tell()

    # Truncate file (no argument version).

    def truncate(self):
        self.local_file.truncate()

    # Truncate file (position argument).

    def truncate(self, pos):
        self.local_file.truncate(pos)

    # Write a string.

    def write(self, str):
        self.local_file.write(str)

    # Write multiple strings.

    def writelines(self, strs):
        self.local_file.writelines(strs)

# Global functions.


# Open file

def open(path, mode='r', buf=-1):
    if path.startswith('/pnfs/') and (prefer_grid or not pnfs_is_mounted):
        if debug:
            print('*** Larbatch_posix: Opening dcache_file %s using mode %s.' % (path, mode))
        return dcache_file(path, mode, buf)
    else:
        if debug:
            print('*** Larbatch_posix: Opening normal file %s using mode %s.' % (path, mode))
        return __builtins__['open'](path, mode, buf)


# Read lines from a file.

def readlines(path):
    return open(path).readlines()


# Copy file.

def copy(src, dest):
    if exists(dest):
        remove(dest)
    if (src.startswith('/pnfs/') or dest.startswith('/pnfs/')):
        if prefer_grid or not pnfs_is_mounted:
            if debug:
                print('*** Larbatch_posix: Copy %s to %s using ifdh.' % (src, dest))
            larbatch_utilities.ifdh_cp(src, dest)
        else:
            if debug:
                print('*** Larbatch_posix: Copy %s to %s using posix with timeout.' % (src, dest))
            larbatch_utilities.posix_cp(src, dest)
    else:
        if debug:
            print('*** Larbatch_posix: Copy %s to %s using posix.' % (src, dest))
        shutil.copy(src, dest)

    # Done

    return


# List directory contents.

def listdir(path):

    if not isdir(path):
        raise OSError('%s is not a directory.' % path)
    result = []
    if path.startswith('/pnfs/') and (prefer_grid or not pnfs_is_mounted):
        if debug:
            print('*** Larbatch_posix: Listdir %s using ifdh.' % path)

        # Get normalized tail.

        tail = os.path.normpath(path[-6:])

        # Call "ifdh ls".

        contents = larbatch_utilities.ifdh_ls(path, 1)

        # Loop over contents returned by ifdh.
        # Normalize the paths returned by "ifdh ls", which in this context mainly
        # has the effect of stripping off trailing '/' on directories.
        # Filter out parent directory, which ifdh sometimes (usually?) includes in result.

        for c in contents:
            nc = os.path.normpath(c.strip())
            if not nc.endswith(tail):
                result.append(os.path.basename(nc))

    else:
        if debug:
            print('*** Larbatch_posix: Listdir %s using posix.' % path)
        #result = os.listdir(path)

        # To reduce hang risk, read contents of directory in a subprocess with
        # a timeout.

        cmd = ['ls', path]
        jobinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        q = queue.Queue()
        thread = threading.Thread(target=larbatch_utilities.wait_for_subprocess, args=[jobinfo, q])
        thread.start()
        thread.join(timeout=60)
        if thread.is_alive():
            if debug:
                print('*** Larbatch_posix: Terminating subprocess.')
            jobinfo.terminate()
            thread.join()
        rc = q.get()
        jobout = convert_str(q.get())
        joberr = convert_str(q.get())
        if rc == 0:
            for word in jobout.split():
                result.append(word)

    # Done.

    return result


# Test existence.  Works for files and directories.

def exists(path):

    result = False
    if path.startswith('/pnfs/') and (prefer_grid or not pnfs_is_mounted):
        if debug:
            print('*** Larbatch_posix: Check existence of %s using ifdh.' % path)

        # Do "ifdh ls."

        try:
            larbatch_utilities.ifdh_ls(path, 0)
            result = True
        except:
            result = False

    else:
        if debug:
            print('*** Larbatch_posix: Check existence of %s using posix.' % path)
        #result = os.path.exists(path)

        # In order to reduce hang risk from stat'ing file,
        # check existence by getting contents of parent directory.

        npath = os.path.normpath(path)     # Strip trailing '/'.
        dir = os.path.dirname(npath)
        base = os.path.basename(npath)
        if dir == '':
            dir = '.'
        if isdir(dir):
            files = listdir(dir)
            for filename in files:
                if base == filename:
                    result = True

    # Done.

    return result


# Test existence if directory.

def isdir(path):

    result = False

    # Optimizations for speed and to reduce hang risk by not stat'ing every file.

    if path[-5:] == '.list' or \
            path[-5:] == '.root' or \
            path[-5:] == '.json' or \
            path[-4:] == '.txt' or \
            path[-4:] == '.fcl' or \
            path[-4:] == '.out' or \
            path[-4:] == '.err' or \
            path[-3:] == '.sh' or \
            path[-5:] == '.stat':
        return False

    if path.startswith('/pnfs/') and (prefer_grid or not pnfs_is_mounted):
        if debug:
            print('*** Larbatch_posix: Check existence of directory %s using ifdh.' % path)

        # Make sure path exists before trying to determine if it is a directory.

        if exists(path):

            # The only reliable way to get information about a directory is 
            # to get a listing of the parent directory.

            npath = os.path.normpath(path)      # Strip trailing '/'
            name = os.path.basename(npath)
            dir = os.path.dirname(npath)
            lines = larbatch_utilities.ifdh_ll(dir, 1)
            for line in lines:
                words = line.split()
                if len(words) > 5 and words[-1] == name:
                    if words[0][0] == 'd':
                        result = True


    else:
        if debug:
            print('*** Larbatch_posix: Check existence of directory %s using posix.' % path)
        result = os.path.isdir(path)

    # Done.

    return result


# Get file status.  
#
# This function is a partial emulation of os.stat.  The return value
# is a type os.stat_result, which is a 10-tuple of values.  The following
# values are filled by this function, since information is not always
# available from grid tools.
#
# mode  - File type and permissions.
# uid   - Owner uid.  For compatibility, always set to the process uid.
# gid   - Owner gid.  For compatibility, always set to the process gid.
# nlink - Number of links.
# size  - Object size.

def stat(path):

    result = None
    if path.startswith('/pnfs/') and (prefer_grid or not pnfs_is_mounted):
        if debug:
            print('*** Larbatch_posix: Stat %s using ifdh.' % path)

        # The only reliable way to get information about a directory is 
        # to get a listing of the parent directory.

        npath = os.path.normpath(path)      # Strip trailing '/'
        name = os.path.basename(npath)
        dir = os.path.dirname(npath)
        lines = larbatch_utilities.ifdh_ll(dir, 1)
        for line in lines:
            words = line.split()
            if len(words) >5 and words[-1] == name:

                # Found thie path.  Fill result.

                # Interpret mode string.

                mode = larbatch_utilities.parse_mode(words[0])

                # Get remaining fields.
                    
                nlinks = int(words[1])
                size = int(words[4])
                result = os.stat_result((mode,         # Mode
                                         0,            # Inode
                                         0,            # Device
                                         nlinks,       # Number of links
                                         os.getuid(),  # Uid
                                         os.getgid(),  # Gid
                                         size,         # Size
                                         0,            # Access time
                                         0,            # Mod time
                                         0))           # Creation time

    else:
        if debug:
            print('*** Larbatch_posix: Stat %s using posix.' % path)
        result = os.stat(path)

    if result == None:
        raise OSError('No such file or directory.')

    # Done.

    return result


# Test file access.
# This implementation only tests access to dCache files via the
# user permission, which is a limitation of grid tools.

def access(path, mode):

    result = False
    if path.startswith('/pnfs/') and (prefer_grid or not pnfs_is_mounted):
        if debug:
            print('*** Larbatch_posix: Check access for %s using ifdh.' % path)
        sr = stat(path)
        if sr.st_mode != 0:

            # File exists.

            result = True

            # Test permissions.

            if mode & os.R_OK:
                if not sr.st_mode & statmod.S_IRUSR:
                    result = False
            if mode & os.W_OK:
                if not sr.st_mode & statmod.S_IWUSR:
                    result = False
            if mode & os.X_OK:
                if not sr.st_mode & statmod.S_IXUSR:
                    result = False

    else:
        if debug:
            print('*** Larbatch_posix: Check access for %s using posix.' % path)
        result = os.access(path, mode)

    # Done.

    return result


# Walk directory tree.  Like os.walk, this function returns an iterator over
# 3-tuples, one for each directory in the tree rooted in the specified
# top directory.  Each 3-tuple contains the following information.
#
# 1.  Path of directory.
# 2.  List of dictory names in this directory.
# 3.  List of non-directory files in this directory.
#
# In case of posix mode, this function includes its own implementation
# of the walking algorithm so that we can take advantage of optimzations
# contained in this module's implementation of isdir.

def walk(top, topdown=True):

    # Quit if top directory doesn't exist.

    if not exists(top):
        return

    # Get contents of top directory using either ifdh or posix.

    dirs = []
    files = []
    if top.startswith('/pnfs/') and (prefer_grid or not pnfs_is_mounted):
        if debug:
            print('*** Larbatch_posix: Walk directory tree for %s using ifdh.' % top)

        # Retrieve the contents of this directory using ifdh.

        lines = larbatch_utilities.ifdh_ll(top, 1)
        for line in lines:
            words = line.split()
            if len(words) > 5 and words[-1] != '__pycache__':
                if words[0][0] == 'd':
                    dirs.append(words[-1])
                else:
                    files.append(words[-1])
    else:
        if debug:
            print('*** Larbatch_posix: Walk directory tree for %s using posix.' % top)
        contents = listdir(top)
        for obj in contents:
            if obj != '__pycache__':
                if isdir(os.path.join(top, obj)):
                    dirs.append(obj)
                else:
                    files.append(obj)

    if topdown:
        yield top, dirs, files

    # Recursively descend into subdirectories.

    for dir in dirs:
        for result in walk(os.path.join(top, dir), topdown):
            yield result

    if not topdown:
        yield top, dirs, files

    # Done.

    return


# Make directory (parent directory must exist).
# Mode argument is ignored for dCache files, but is passed to os.mkdir
# for non-dCache files.

def mkdir(path, mode=0o777):
    if path.startswith('/pnfs/') and (prefer_grid or not pnfs_is_mounted):
        if debug:
            print('*** Larbatch_posix: Make directory for %s using ifdh.' % path)
        larbatch_utilities.ifdh_mkdir(path)
    else:
        if debug:
            print('*** Larbatch_posix: Make directory for %s using posix.' % path)
        os.mkdir(path, mode)


# Make directory and parents.
# Mode argument is ignored for dCache files, but is passed to os.mkdir
# for non-dCache files.
# "ifdh mkdir_p" is buggy, so we do the recursion locally.

def makedirs(path, mode=0o777):
    if path.startswith('/pnfs/') and (prefer_grid or not pnfs_is_mounted):
        if debug:
            print('*** Larbatch_posix: Make directory recursively for %s using ifdh.' % path)

        # Make sure parent directory exists.

        np = os.path.normpath(path)    # Stip trailing '/', if present.
        parent = os.path.dirname(np)
        if not isdir(parent):
            makedirs(parent, mode)

        # Now make directory itself.

        larbatch_utilities.ifdh_mkdir(path)
    else:
        if debug:
            print('*** Larbatch_posix: Make directory recursively for %s using posix.' % path)
        os.makedirs(path, mode)


# Rename file.
# "ifdh mv" seems to be buggy, so use uberftp.

def rename(src, dest):
    if (src.startswith('/pnfs/') or
        dest.startswith('/pnfs/')) and (prefer_grid or not pnfs_is_mounted):
        if debug:
            print('*** Larbatch_posix: Rename %s to %s using ifdh.' % (src, dest))

        src_uri = larbatch_utilities.gridftp_uri(src)
        dest_path = larbatch_utilities.dcache_path(dest)
        cmd = ['uberftp', '-rename', src_uri, dest_path]
        jobinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        q = queue.Queue()
        thread = threading.Thread(target=larbatch_utilities.wait_for_subprocess, args=[jobinfo, q])
        thread.start()
        thread.join(timeout=60)
        if thread.is_alive():
            if debug:
                print('*** Larbatch_posix: Terminating subprocess.')
            jobinfo.terminate()
            thread.join()
        rc = q.get()
        jobout = convert_str(q.get())
        joberr = convert_str(q.get())
        if rc != 0:
            raise IFDHError(cmd, rc, jobout, joberr)
    else:
        if debug:
            print('*** Larbatch_posix: Rename %s to %s using posix.' % (src, dest))
        os.rename(src, dest)


# Delete file.

def remove(path):
    if path.startswith('/pnfs/') and (prefer_grid or not pnfs_is_mounted):
        if debug:
            print('*** Larbatch_posix: Delete file %s using ifdh.' % path)
        larbatch_utilities.ifdh_rm(path)
    else:
        if debug:
            print('*** Larbatch_posix: Delete file %s using posix.' % path)

        # Deleting a file is a hang risk, especially, but not only, in dCache.
        # Therefore, use the following procedure.
        # 
        # 1.  Rename file to a random name (this can usually be done, even
        #     for undeletable files).
        #
        # 2.  Delete renamed file in a subprocess.  No need to wait for
        #     subprocess to finish, or check its exit status.

        #os.remove(path)
        newpath = path + '_' + str(uuid.uuid4())
        try:
            os.rename(path, newpath)
            os.system('rm -f %s &' % newpath)
            return
        except:
            pass
        os.remove(path)

# Delete empty directory.

def rmdir(path):
    if path.startswith('/pnfs/') and (prefer_grid or not pnfs_is_mounted):
        if debug:
            print('*** Larbatch_posix: Delete directoroy %s using ifdh.' % path)
        larbatch_utilities.ifdh_rmdir(path)
    else:
        if debug:
            print('*** Larbatch_posix: Delete directoroy %s using posix.' % path)
        os.rmdir(path)


# Delete directory tree.

def rmtree(path):
    if path.startswith('/pnfs/') and (prefer_grid or not pnfs_is_mounted):
        if debug:
            print('*** Larbatch_posix: Delete directoroy tree %s using ifdh.' % path)

        # Delete contents recursively.

        lines = larbatch_utilities.ifdh_ll(path, 1)
        for line in lines:
            words = line.split()
            if len(words) > 5:
                if words[0][0] == 'd':
                    rmtree(os.path.join(path, words[-1]))
                else:
                    remove(os.path.join(path, words[-1]))

        # Directory should be empty when we get to here.

        rmdir(path)

    else:
        if debug:
            print('*** Larbatch_posix: Delete directoroy tree %s using posix.' % path)

        # Deleting a directory tree is a hang risk, especially, but not only, in dCache.
        # Therefore, use the following procedure.
        # 
        # 1.  Rename directory to a random name (this can usually be done, even
        #     for undeletable directories).
        #
        # 2.  Delete renamed directory in a subprocess.  No need to wait for
        #     subprocess to finish, or check its exit status.

        #shutil.rmtree(path)
        npath = os.path.normpath(path)              # Strip trailing '/'
        newpath = npath + '_' + str(uuid.uuid4())
        os.rename(npath, newpath)
        os.system('rm -rf %s &' % newpath)

    # Done

    return


# Change mode.

def chmod(path, mode):
    if path.startswith('/pnfs/') and (prefer_grid or not pnfs_is_mounted):
        if debug:
            print('*** Larbatch_posix: Change mode for %s using ifdh.' % path)
        larbatch_utilities.ifdh_chmod(path, mode)
    else:
        if debug:
            print('*** Larbatch_posix: Change mode for %s using posix.' % path)
        try:
            os.chmod(path, mode)
        except:
            print('Warning: chmod failed for path %s' % path)


# Make symbolic link.
# Use nfs.

def symlink(src, dest):

    # Make sure we have a kerberos ticket.

    if src.startswith('/pnfs/') and not pnfs_is_mounted:
        if debug:
            print('*** Larbatch_posix: Make symbolic link from %s to %s using nfs server.' % (src, dest))
        larbatch_utilities.test_ticket()
        cmd = ['ssh', larbatch_utilities.nfs_server(), 'ln', '-s', src, dest]
        jobinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        q = queue.Queue()
        thread = threading.Thread(target=larbatch_utilities.wait_for_subprocess, args=[jobinfo, q])
        thread.start()
        thread.join(timeout=60)
        if thread.is_alive():
            if debug:
                print('*** Larbatch_posix: Terminating subprocess.')
            jobinfo.terminate()
            thread.join()
        rc = q.get()
        jobout = convert_str(q.get())
        joberr = convert_str(q.get())
        if rc != 0:
            raise IFDHError(cmd, rc, jobout, joberr)

    else:
        if debug:
            print('*** Larbatch_posix: Make symbolic link from %s to %s using posix.' % (src, dest))
        os.symlink(src, dest)


# Read a symbolic link.
# Use nfs.

def readlink(path):

    result = ''

    # Make sure we have a kerberos ticket.

    if path.startswith('/pnfs/') and not_pnfs_is_mounted:
        if debug:
            print('*** Larbatch_posix: Read symbolic link %s using nfs server.' % path)
        larbatch_utilities.test_ticket()
        cmd = ['ssh', larbatch_utilities.nfs_server(), 'readlink', path]
        jobinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        q = queue.Queue()
        thread = threading.Thread(target=larbatch_utilities.wait_for_subprocess, args=[jobinfo, q])
        thread.start()
        thread.join(timeout=60)
        if thread.is_alive():
            if debug:
                print('*** Larbatch_posix: Terminating subprocess.')
            jobinfo.terminate()
            thread.join()
        rc = q.get()
        jobout = convert_str(q.get())
        joberr = convert_str(q.get())
        if rc != 0:
            raise IFDHError(cmd, rc, jobout, joberr)
        result = jobout.strip()

    else:
        if debug:
            print('*** Larbatch_posix: Read symbolic link %s using posix.' % path)
        result = os.readlink(path)

    # Done.

    return result


# Convert a root file path to a streamable path or uri that can be opened 
# using TFile::Open.
# Non-dCache paths (paths not starting with '/pnfs/') are not changed.
# dCache paths (patsh starting with '/pnfs/') may be converted to an xrootd uri.

def root_stream(path):

    stream = path
    if path.startswith('/pnfs/') and (prefer_grid or not pnfs_is_mounted):
        if debug:
            print('*** Larbatch_posix: Stream path %s using xrootd.' % path)
        larbatch_utilities.test_proxy()
        stream = larbatch_utilities.xrootd_uri(path)
    else:
        if debug:
            print('*** Larbatch_posix: Stream path %s as normal file.' % path)
    return stream
