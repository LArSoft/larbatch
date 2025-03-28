#! /usr/bin/env python
######################################################################
#
# Name: larbatch_utilities.py
#
# Purpose: This module contains low level utilities that are used in
#          either modules project_utilities or larbatch_posix.
#
# Created: 13-Jun-2016  Herbert Greenlee
#
# The following functions are provided as interfaces to ifdh.  These
# functions are equipped with authentication checking, timeouts and
# other protections.
#
# ifdh_cp - Interface for "ifdh cp."
# ifdh_ls - Interface for "ifdh ls."
# ifdh_ll - Interface for "ifdh ll."
# ifdh_mkdir - Interface for "ifdh mkdir."
# ifdh_mkdir_p - Interface for "ifdh mkdir_p."
# ifdh_rmdir - Interface for "ifdh rmdir."
# ifdh_mv - Interface for "ifdh mv."
# ifdh_rm - Interface for "ifdh rm."
# ifdh_chmod - Interface for "ifdh chmod."
#
# The following functions are provided as interfaces to posix tools
# with additional protections or timeouts.
#
# posix_cp - Copy file with timeout.
#
# Authentication functions.
#
# test_ticket - Raise an exception of user does not have a valid kerberos ticket.
# get_token - Get a bearer token by calling htgettoken.
# test_token - Get bearer token if necessary.
# get_experiment - Get standard experiment name.
# get_user - Get authenticated user.
# get_prouser - Get production user.
# get_role - Get VO role.
#
# SAM functions.
#
# dimensions - Return sam query dimensions for stage.
# get_sam_metadata - Return sam metadata fcl parameters for stage.
# get_bluearc_server - Sam fictitious server for bluearc.
# get_dcache_server - Sam fictitious server for dCache.
# get_dropbox - Return dropbox based on sam metadata.
#
# Other functions.
#
# get_ups_products - Top level ups products.
# get_setup_script_path - Full path of experiment setup script.
# wait_for_subprocess - For use with subprocesses with timeouts.
# dcache_server - Return dCache server.
# dcache_path - Convert dCache local path to path on server.
# xrootd_server_port - Return xrootd server and port (as <server>:<port>).
# xrootd_uri - Convert dCache path to xrootd uri.
# gridftp_uri - Convert dCache path to gridftp uri.
# nfs_server - Node name of a computer in which /pnfs filesystem is nfs-mounted.
# parse_mode - Parse the ten-character file mode string ("ls -l").
# check_running - Check for running project.py submission process.
# convert_str - Accepting unicode or bytes as input, convert to default python str.
# convert_bytes - Accepting unicode or bytes as input, convert to bytes.
# test_jobsub - Test whether jobsub_client is set up.
# validate_stage - Validate project and stage configurations.
#
######################################################################

from __future__ import absolute_import
from __future__ import print_function
import sys, os
import socket
import stat
import subprocess
import getpass
import threading
try:
    import queue
except ImportError:
    import Queue as queue
from project_modules.ifdherror import IFDHError

# Global variables.

ticket_ok = False
token_ok = False
jobsub_ok = False

# Copy file using ifdh, with timeout.

def ifdh_cp(source, destination):

    # Get token.

    test_token()

    # Make sure environment variables X509_USER_CERT and X509_USER_KEY
    # are not defined (they confuse ifdh, or rather the underlying tools).

    save_vars = {}
    for var in ('X509_USER_CERT', 'X509_USER_KEY'):
        if var in os.environ:
            save_vars[var] = os.environ[var]
            del os.environ[var]

    # Do copy.

    cmd = ['ifdh', 'cp', source, destination]
    jobinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    q = queue.Queue()
    thread = threading.Thread(target=wait_for_subprocess, args=[jobinfo, q])
    thread.start()
    thread.join(timeout=31000000)
    if thread.is_alive():
        print('Terminating subprocess.')
        jobinfo.terminate()
        thread.join()
    rc = q.get()
    jobout = convert_str(q.get())
    joberr = convert_str(q.get())
    if rc != 0:
        for var in list(save_vars.keys()):
            os.environ[var] = save_vars[var]
        raise IFDHError(cmd, rc, jobout, joberr)

    # Restore environment variables.

    for var in list(save_vars.keys()):
        os.environ[var] = save_vars[var]


# Ifdh ls, with timeout.
# Return value is list of lines returned by "ifdh ls" command.

def ifdh_ls(path, depth):

    # Get token.

    test_token()

    # Make sure environment variables X509_USER_CERT and X509_USER_KEY
    # are not defined (they confuse ifdh, or rather the underlying tools).

    save_vars = {}
    for var in ('X509_USER_CERT', 'X509_USER_KEY'):
        if var in os.environ:
            save_vars[var] = os.environ[var]
            del os.environ[var]

    # Do listing.

    cmd = ['ifdh', 'ls', path, '%d' % depth]
    jobinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    q = queue.Queue()
    thread = threading.Thread(target=wait_for_subprocess, args=[jobinfo, q])
    thread.start()
    thread.join(timeout=600)
    if thread.is_alive():
        print('Terminating subprocess.')
        jobinfo.terminate()
        thread.join()
    rc = q.get()
    jobout = convert_str(q.get())
    joberr = convert_str(q.get())
    if rc != 0:
        for var in list(save_vars.keys()):
            os.environ[var] = save_vars[var]
        raise IFDHError(cmd, rc, jobout, joberr)

    # Restore environment variables.

    for var in list(save_vars.keys()):
        os.environ[var] = save_vars[var]

    # Done.

    return jobout.splitlines()


# Ifdh ll, with timeout.
# Return value is list of lines returned by "ifdh ls" command.

def ifdh_ll(path, depth):

    # Get token.

    test_token()

    # Make sure environment variables X509_USER_CERT and X509_USER_KEY
    # are not defined (they confuse ifdh, or rather the underlying tools).

    save_vars = {}
    for var in ('X509_USER_CERT', 'X509_USER_KEY'):
        if var in os.environ:
            save_vars[var] = os.environ[var]
            del os.environ[var]

    # Do listing.

    cmd = ['ifdh', 'll', path, '%d' % depth]
    jobinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    q = queue.Queue()
    thread = threading.Thread(target=wait_for_subprocess, args=[jobinfo, q])
    thread.start()
    thread.join(timeout=60)
    if thread.is_alive():
        print('Terminating subprocess.')
        jobinfo.terminate()
        thread.join()
    rc = q.get()
    jobout = convert_str(q.get())
    joberr = convert_str(q.get())
    if rc != 0:
        for var in list(save_vars.keys()):
            os.environ[var] = save_vars[var]
        raise IFDHError(cmd, rc, jobout, joberr)

    # Restore environment variables.

    for var in list(save_vars.keys()):
        os.environ[var] = save_vars[var]

    # Done.

    return jobout.splitlines()


# Ifdh mkdir, with timeout.

def ifdh_mkdir(path):

    # Get token.

    test_token()

    # Make sure environment variables X509_USER_CERT and X509_USER_KEY
    # are not defined (they confuse ifdh, or rather the underlying tools).

    save_vars = {}
    for var in ('X509_USER_CERT', 'X509_USER_KEY'):
        if var in os.environ:
            save_vars[var] = os.environ[var]
            del os.environ[var]

    # Do mkdir.

    cmd = ['ifdh', 'mkdir', path]
    jobinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    q = queue.Queue()
    thread = threading.Thread(target=wait_for_subprocess, args=[jobinfo, q])
    thread.start()
    thread.join(timeout=60)
    if thread.is_alive():
        print('Terminating subprocess.')
        jobinfo.terminate()
        thread.join()
    rc = q.get()
    jobout = convert_str(q.get())
    joberr = convert_str(q.get())
    if rc != 0:
        for var in list(save_vars.keys()):
            os.environ[var] = save_vars[var]
        raise IFDHError(cmd, rc, jobout, joberr)

    # Restore environment variables.

    for var in list(save_vars.keys()):
        os.environ[var] = save_vars[var]

    # Done.

    return


# Ifdh mkdir_p, with timeout.

def ifdh_mkdir_p(path):

    # Get token.

    test_token()

    # Make sure environment variables X509_USER_CERT and X509_USER_KEY
    # are not defined (they confuse ifdh, or rather the underlying tools).

    save_vars = {}
    for var in ('X509_USER_CERT', 'X509_USER_KEY'):
        if var in os.environ:
            save_vars[var] = os.environ[var]
            del os.environ[var]

    # Do mkdir_p.

    cmd = ['ifdh', 'mkdir_p', path]
    jobinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    q = queue.Queue()
    thread = threading.Thread(target=wait_for_subprocess, args=[jobinfo, q])
    thread.start()
    thread.join(timeout=600)
    if thread.is_alive():
        print('Terminating subprocess.')
        jobinfo.terminate()
        thread.join()
    rc = q.get()
    jobout = convert_str(q.get())
    joberr = convert_str(q.get())
    if rc != 0:
        for var in list(save_vars.keys()):
            os.environ[var] = save_vars[var]
        raise IFDHError(cmd, rc, jobout, joberr)

    # Restore environment variables.

    for var in list(save_vars.keys()):
        os.environ[var] = save_vars[var]

    # Done.

    return


# Ifdh rmdir, with timeout.

def ifdh_rmdir(path):

    # Get token.

    test_token()

    # Make sure environment variables X509_USER_CERT and X509_USER_KEY
    # are not defined (they confuse ifdh, or rather the underlying tools).

    save_vars = {}
    for var in ('X509_USER_CERT', 'X509_USER_KEY'):
        if var in os.environ:
            save_vars[var] = os.environ[var]
            del os.environ[var]

    # Do rmdir.

    cmd = ['ifdh', 'rmdir', path]
    jobinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    q = queue.Queue()
    thread = threading.Thread(target=wait_for_subprocess, args=[jobinfo, q])
    thread.start()
    thread.join(timeout=60)
    if thread.is_alive():
        print('Terminating subprocess.')
        jobinfo.terminate()
        thread.join()
    rc = q.get()
    jobout = convert_str(q.get())
    joberr = convert_str(q.get())
    if rc != 0:
        for var in list(save_vars.keys()):
            os.environ[var] = save_vars[var]
        raise IFDHError(cmd, rc, jobout, joberr)

    # Restore environment variables.

    for var in list(save_vars.keys()):
        os.environ[var] = save_vars[var]

    # Done.

    return


# Ifdh chmod, with timeout.

def ifdh_chmod(path, mode):

    # Get token.

    test_token()

    # Make sure environment variables X509_USER_CERT and X509_USER_KEY
    # are not defined (they confuse ifdh, or rather the underlying tools).

    save_vars = {}
    for var in ('X509_USER_CERT', 'X509_USER_KEY'):
        if var in os.environ:
            save_vars[var] = os.environ[var]
            del os.environ[var]

    # Do chmod.

    cmd = ['ifdh', 'chmod', '%o' % mode, path]
    jobinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    q = queue.Queue()
    thread = threading.Thread(target=wait_for_subprocess, args=[jobinfo, q])
    thread.start()
    thread.join(timeout=60)
    if thread.is_alive():
        print('Terminating subprocess.')
        jobinfo.terminate()
        thread.join()
    rc = q.get()
    jobout = convert_str(q.get())
    joberr = convert_str(q.get())
    if rc != 0:
        print('Warning: ifdh chmod failed for path %s' % path)

    # Restore environment variables.

    for var in list(save_vars.keys()):
        os.environ[var] = save_vars[var]

    # Done.

    return


# Ifdh mv, with timeout.

def ifdh_mv(src, dest):

    # Get token.

    test_token()

    # Make sure environment variables X509_USER_CERT and X509_USER_KEY
    # are not defined (they confuse ifdh, or rather the underlying tools).

    save_vars = {}
    for var in ('X509_USER_CERT', 'X509_USER_KEY'):
        if var in os.environ:
            save_vars[var] = os.environ[var]
            del os.environ[var]

    # Do rename.

    cmd = ['ifdh', 'mv', src, dest]
    jobinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    q = queue.Queue()
    thread = threading.Thread(target=wait_for_subprocess, args=[jobinfo, q])
    thread.start()
    thread.join(timeout=60)
    if thread.is_alive():
        print('Terminating subprocess.')
        jobinfo.terminate()
        thread.join()
    rc = q.get()
    jobout = convert_str(q.get())
    joberr = convert_str(q.get())
    if rc != 0:
        for var in list(save_vars.keys()):
            os.environ[var] = save_vars[var]
        raise IFDHError(cmd, rc, jobout, joberr)

    # Restore environment variables.

    for var in list(save_vars.keys()):
        os.environ[var] = save_vars[var]

    # Done.

    return


# Ifdh rm, with timeout.

def ifdh_rm(path):

    # Get token.

    test_token()

    # Make sure environment variables X509_USER_CERT and X509_USER_KEY
    # are not defined (they confuse ifdh, or rather the underlying tools).

    save_vars = {}
    for var in ('X509_USER_CERT', 'X509_USER_KEY'):
        if var in os.environ:
            save_vars[var] = os.environ[var]
            del os.environ[var]

    # Do delete.

    cmd = ['ifdh', 'rm', path]
    jobinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    q = queue.Queue()
    thread = threading.Thread(target=wait_for_subprocess, args=[jobinfo, q])
    thread.start()
    thread.join(timeout=60)
    if thread.is_alive():
        print('Terminating subprocess.')
        jobinfo.terminate()
        thread.join()
    rc = q.get()
    jobout = convert_str(q.get())
    joberr = convert_str(q.get())
    if rc != 0:
        for var in list(save_vars.keys()):
            os.environ[var] = save_vars[var]
        raise IFDHError(cmd, rc, jobout, joberr)

    # Restore environment variables.

    for var in list(save_vars.keys()):
        os.environ[var] = save_vars[var]

    # Done.

    return


# Posix copy with timeout.

def posix_cp(source, destination):

    cmd = ['cp', source, destination]

    # Fork buffer process.

    buffer_pid = os.fork()
    if buffer_pid == 0:

        # In child process.
        # Launch cp subprocess.

        jobinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        q = queue.Queue()
        thread = threading.Thread(target=wait_for_subprocess, args=[jobinfo, q])
        thread.start()
        thread.join(timeout=600)
        if thread.is_alive():

            # Subprocess did not finish (may be hanging and unkillable).
            # Try to kill the subprocess and exit process.
            # Unkillable process will become detached.

            print('Terminating subprocess.')
            jobinfo.kill()
            os._exit(1)

        else:

            # Subprocess finished normally.

            rc = q.get()
            jobout = convert_str(q.get())
            joberr = convert_str(q.get())
            os._exit(rc)

    else:

        # In parent process.
        # Wait for buffer subprocess to finish.

        buffer_result = os.waitpid(buffer_pid, 0)
        rc = buffer_result[1]/256
        if rc != 0:
            raise IFDHError(cmd, rc, '', '')

    # Done.

    return


# Function to wait for a subprocess to finish and fetch return code,
# standard output, and standard error.
# Call this function like this:
#
# q = Queue.Queue()
# jobinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# wait_for_subprocess(jobinfo, q, input)
# rc = q.get()      # Return code.
# jobout = q.get()  # Standard output
# joberr = q.get()  # Standard error


def wait_for_subprocess(jobinfo, q, input=None):
    jobout, joberr = jobinfo.communicate(input)
    rc = jobinfo.poll()
    q.put(rc)
    q.put(jobout)
    q.put(joberr)
    return


# Test whether user has a valid kerberos ticket.  Raise exception if no.

def test_ticket():
    global ticket_ok
    if not ticket_ok:
        ok = subprocess.call(['klist', '-s'], stdout=-1, stderr=-1)
        if ok != 0:
            raise RuntimeError('Please get a kerberos ticket.')
        ticket_ok = True
    return ticket_ok


# Get a bearer token by calling htgettoken.

def get_token():
    global token_ok
    token_ok = False

    # Construct htgettoken command.

    role = get_role().lower()
    cmd = ['htgettoken',
           '-a',
           'htvaultprod.fnal.gov',
           '-i',
           get_experiment()]
    if role == 'production':
        cmd.extend(['-r', role])

    # Run command.

    try:
        subprocess.check_call(cmd)
        token_ok = True
    except:
        token_ok = False

    # Done.

    return token_ok


# Test whether user has a valid bearer token.  If not, try to get a new one.

def test_token():
    global token_ok
    if not token_ok:

        # Try running httokendecode.

        try:
            subprocess.check_call(['httokendecode'], stdout=-1, stderr=-1)
            token_ok = True
        except:
            token_ok = False

        if not token_ok:
            get_token()

    # Done.

    return token_ok


# Test whether jobsub_client has been set up.

def test_jobsub():
    global jobsub_ok
    if not jobsub_ok:

        # Look for command jobsub_submit on execution path.

        try:
            jobinfo = subprocess.Popen(['which', 'jobsub_submit'],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            jobout, joberr = jobinfo.communicate()
            jobout = convert_str(jobout)
            joberr = convert_str(joberr)
            jobsub_path = jobout.splitlines()[0].strip()
            if jobsub_path != '':
                jobsub_ok = True
        except:
            pass

    if not jobsub_ok:
        print('Please set up jobsub_client')
        sys.exit(1)

    return jobsub_ok

# Function to validate project and stage configurations.
# Return True if good, False if bad.
# Returning false will prevent jobs from being submitted.
# This implementation doesn't do anything.
# Can be overridden in experiment_utilities to provide experiment-dependent validations.

def validate_stage(project, stage):
    return True


# Return dCache server.

def dcache_server():
    return "fndcadoor.fnal.gov"


# Convert a local pnfs path to the path on the dCache server.
# Return the input path unchanged if it isn't on dCache.

def dcache_path(path):
    if path.startswith('/pnfs/') and not path.startswith('/pnfs/fnal.gov/usr/'):
        return '/pnfs/fnal.gov/usr/' + path[6:]


# Return xrootd server and port.

def xrootd_server_port():
    return dcache_server() + ':1094'


# Convert a pnfs path to xrootd uri.
# Return the input path unchanged if it isn't on dCache.

def xrootd_uri(path):
    if path.startswith('/pnfs/'):
        return 'root://' + xrootd_server_port() + dcache_path(path)
    else:
        return path


# Convert a pnfs path to gridftp uri.
# Return the input path unchanged if it isn't on dCache.

def gridftp_uri(path):
    if path.startswith('/pnfs/'):
        return 'gsiftp://' + dcache_server() + dcache_path(path)
    else:
        return path


# Return the name of a computer with login access that has the /pnfs
# filesystem nfs-mounted.  This function makes use of the $EXPERIMENT
# environment variable (as does ifdh), which must be set.

def nfs_server():
    return '%sgpvm01.fnal.gov' % os.environ['EXPERIMENT']


# Parse the ten-character file mode string as returned by "ls -l"
# and return mode bit masek.

def parse_mode(mode_str):

    mode = 0

    # File type.

    if mode_str[0] == 'b':
        mode += stat.S_IFBLK
    elif mode_str[0] == 'c':
        mode += stat.S_IFCHR
    elif mode_str[0] == 'd':
        mode += stat.S_IFDIR
    elif mode_str[0] == 'l':
        mode += stat.S_IFLNK
    elif mode_str[0] == 'p':
        mode += stat.S_IFIFO
    elif mode_str[0] == 's':
        mode += stat.S_IFSOCK
    elif mode_str[0] == '-':
        mode += stat.S_IFREG

    # File permissions.

    # User triad (includes setuid).

    if mode_str[1] == 'r':
        mode += stat.S_IRUSR
    if mode_str[2] == 'w':
        mode += stat.S_IWUSR
    if mode_str[3] == 'x':
        mode += stat.S_IXUSR
    elif mode_str[3] == 's':
        mode += stat.S_ISUID
        mode += stat.S_IXUSR
    elif mode_str[3] == 'S':
        mode += stat.S_ISUID

    # Group triad (includes setgid).

    if mode_str[4] == 'r':
        mode += stat.S_IRGRP
    if mode_str[5] == 'w':
        mode += stat.S_IWGRP
    if mode_str[6] == 'x':
        mode += stat.S_IXGRP
    elif mode_str[6] == 's':
        mode += stat.S_ISGID
        mode += stat.S_IXGRP
    elif mode_str[6] == 'S':
        mode += stat.S_ISGID

    # World triad (includes sticky bit).

    if mode_str[7] == 'r':
        mode += stat.S_IROTH
    if mode_str[8] == 'w':
        mode += stat.S_IWOTH
    if mode_str[9] == 'x':
        mode += stat.S_IXOTH
    elif mode_str[9] == 't':
        mode += stat.S_ISVTX
        mode += stat.S_IXOTH
    elif mode_str[9] == 'T':
        mode += stat.S_ISVTX

    # Done

    return mode

# Function to return the current experiment.
# The following places for obtaining this information are
# tried (in order):
#
# 1.  Environment variable $EXPERIMENT.
# 2.  Environment variable $SAM_EXPERIMENT.
# 3.  Hostname (up to "gpvm").
#
# Raise an exception if none of the above methods works.
#

def get_experiment():

    exp = ''
    for ev in ('EXPERIMENT', 'SAM_EXPERIMENT'):
        if ev in os.environ:
            exp = os.environ[ev]
            break

    if not exp:
        hostname = socket.gethostname()
        n = hostname.find('gpvm')
        if n > 0:
            exp = hostname[:n]

    if not exp:
        raise RuntimeError('Unable to determine experiment.')

    return exp


# Get role (normally 'Analysis' or 'Production').

def get_role():

    # If environment variable ROLE is defined, use that.  Otherwise, make
    # an educated guess based on user name.

    result = 'Analysis'   # Default role.

    # Check environment variable $ROLE.

    if 'ROLE' in os.environ:
        result = os.environ['ROLE']

    # Otherwise, check user.

    else:
        prouser = get_experiment() + 'pro'
        user = getpass.getuser()
        if user == prouser:
            result = 'Production'

    return result


# Function to return a comma-separated list of run-time top level ups products.

def get_ups_products():
    return get_experiment() + 'code'


# Function to return path of experiment bash setup script that is valid
# on the node where this script is being executed.
# This function should be overridden in <experiment>_utilities.py.

def get_setup_script_path():
    raise RuntimeError('Function get_setup_script_path not implemented.')


# Function to return dimension string for project, stage.
# This function should be overridden in experiment_utilities.py

def dimensions(project, stage, ana=False):
    raise RuntimeError('Function dimensions not implemented.')


# Function to return dimension string for project, stage, including data stream.

def dimensions_datastream(project, stage, ana=False, index=0):

    # Default same as no data stream.

    dim = dimensions(project, stage, ana=ana)

    # Append data stream dimension, if appropriate.

    if ana:
        if stage.ana_data_stream != None and len(stage.ana_data_stream) > 0:
            dim1 = '( data_stream %s and %s )' % (stage.ana_data_stream[index], dim)
            dim = dim1
    else:
        if stage.data_stream != None and len(stage.data_stream) > 0:
            dim1 = '( data_stream %s and %s )' % (stage.data_stream[index], dim)
            dim = dim1

    # Done.

    return dim


# Function to return the production user name

def get_prouser():
    return get_experiment() + 'pro'


# Function to return the fictitious disk server node
# name used by sam for bluearc disks.

def get_bluearc_server():
    return get_experiment() + 'data:'


# Function to return the fictitious disk server node
# name used by sam for dCache disks.

def get_dcache_server():
    return 'fnal-dcache:'


# Function to determine dropbox directory based on sam metadata.
# Raise an exception if the specified file doesn't have metadata.
# This function should be overridden in <experiment>_utilities module.

def get_dropbox(filename):
    raise RuntimeError('Function get_dropbox not implemented.')


# Function to return string containing sam metadata in the form
# of an fcl configuraiton.  It is intended that this function
# may be overridden in experiment_utilities.py.

def get_sam_metadata(project, stage):
    result = ''
    return result


# Get authenticated user.

def get_user():

    # Return production user name if Role is Production

    if get_role() == 'Production':
        return get_prouser()

    else:
        return getpass.getuser()


# Get parent process id of the specified process id.
# This function works by reading information from the /proc filesystem.
# Return 0 in case of any kind of difficulty.

def get_ppid(pid):

    result = 0

    statfname = '/proc/%d/status' % pid
    statf = open(statfname)
    for line in statf.readlines():
        if line.startswith('PPid:'):
            words = line.split()
            if len(words) >= 2 and words[1].isdigit():
                result = int(words[1])

    # Done.

    return result


# Function to check whether there is a running project.py process on this node
# with the specified xml file and stage.
#
# This function works by checking the contents of /proc.  Each process is checked
# for the following properties.
#
# 1.  Owned by same uid as this process.
# 2.  Command line.
#     a) project.py
#     b) Matching --xml option (exact match).
#     c) Matching --stage option (exact match).
#     d) --submit or --makeup option.
#
# Arguments xml and stage should be strings, and must match exactly command
# line arguments.

def check_running(xmlname, stagename):

    result = 0

    # Find all ancestor processes, which we will ignore.

    ignore_pids = set()
    pid = os.getpid()
    while pid > 1:
        ignore_pids.add(pid)
        pid = get_ppid(pid)

    # Look over pids in /proc.

    for pid in os.listdir('/proc'):
        if pid.isdigit() and int(pid) not in ignore_pids:
            procfile = os.path.join('/proc', pid)
            try:
                pstat = os.stat(procfile)

                # Only look at processes that match this process uid.

                if pstat.st_uid == os.getuid():

                    # Get command line.

                    cmdfile = os.path.join('/proc', pid, 'cmdline')
                    cmd = open(cmdfile).read()
                    words = cmd.split('\0')

                    # Check options.

                    project = 0
                    xml = 0
                    stage = 0
                    xmlmatch = 0
                    stagematch = 0
                    submit = 0
                    makeup = 0

                    for word in words:

                        # Check command.

                        if word.endswith('project.py'):
                            project = 1

                        # Check arguments.

                        if xml == 1 and word == xmlname:
                            xmlmatch = 1
                        elif stage == 1 and word == stagename:
                            stagematch = 1

                        xml = 0
                        stage = 0

                        # Check options.

                        if word == '--xml':
                            xml = 1
                        elif word == '--stage':
                            stage = 1
                        elif word == '--submit':
                            submit = 1
                        elif word == '--makeup':
                            makeup = 1

                    if project != 0 and submit+makeup != 0 and xmlmatch != 0 and stagematch != 0:
                        result = 1
                        break

            except:
                pass

    # Done.

    return result


# Convert bytes or unicode string to default python str type.
# Works on python 2 and python 3.

def convert_str(s):

    result = ''

    if type(s) == type(''):

        # Already a default str.
        # Just return the original.

        result = s

    elif type(s) == type(u''):

        # Unicode and not str.
        # Convert to bytes.

        result = s.encode()

    elif type(s) == type(b''):

        # Bytes and not str.
        # Convert to unicode.

        result = s.decode()

    else:

        # Last resort, use standard str conversion.

        result = str(s)

    return result


# Convert bytes or unicode string to bytes.
# Works on python 2 and python 3.

def convert_bytes(s):

    result = ''

    if type(s) == type(b''):

        # Already bytes.
        # Return the original.

        result = s

    elif type(s) == type(u''):

        # Unicode to bytes.

        result = s.encode()

    else:

        # Anything else, just return the original.

        result = s

    return result


# Import experiment-specific utilities.  In this imported module, one can
# override any function or symbol defined above, or add new ones.

from experiment_utilities import *
