#!/usr/bin/env python
######################################################################
#
# Name: mkdir.py
#
# Purpose: This script uses ifdh to safely create a directory in an 
#          ifdh-accessible location.  This script will create parent
#          directories, if necessary.  It is not an error if the 
#          specified directory alrady exists.  This script functions
#          similarly to the shell command "mkdir -p", except everything
#          is done using ifdh commands.
#
#          Environment variable $EXPERIMENT must be defined to properly 
#          initialize ifdh.
#
# Created: 15-May-2015  H. Greenlee
#
# Command line usage:
#
# mkdir.py [-h|--help] <dir>
#
# Options:
#
# -h, --help - Print help.
# -v         - Verbose.
#
# Arguments:
#
# <dir>      - Directory to create.
#
######################################################################

from __future__ import absolute_import
from __future__ import print_function

# Imports

import sys, os, ifdh

# Initialize ifdh.

Ifdh = ifdh.ifdh()

# Main procedure.

def main(argv):

    verbose = 0
    dir = ''

    # Parse arguments.

    args = argv[1:]
    if len(args) == 0:
        help()
        return 0
    while len(args) > 0:
        if args[0] == '-h' or args[0] == '--help' :
            help()
            return 0
        elif args[0] == '-v':
            verbose = 1
            del args[0]
        elif args[0][0] == '-':
            print('Unknown option %s' % args[0])
            return 1
        else:
            if dir != '':
                print('Too many arguments.')
                return 1
            dir = args[0]
            del args[0]

    mkdir(dir, verbose)
    return

# Help function.

def help():
    filename = sys.argv[0]
    file = open(filename, 'r')

    doprint=0
    
    for line in file.readlines():
        if line[2:10] == 'mkdir.py':
            doprint = 1
        elif line[0:6] == '######' and doprint:
            doprint = 0
        if doprint:
            if len(line) > 2:
                print(line[2:], end=' ')
            else:
                print()
    return


# This function safely creates the specified directory and parent directories
# if they don't exist.  It is not an error if the specified directory already
# exists.

def mkdir(dir, verbose):

    # Remove trailing '/' character(s), if any (except if or until entire path is '/').

    while len(dir) > 1 and dir[-1] == '/':
        dir = dir[:-1]

    # If at this point, the directory path has been reduced to just '/', quit.

    if dir == '/':
        if verbose:
            print('mkdir asked to make directory \'/\'.')
        return

    # Test whether target directory already exists.

    exists = existdir(dir, verbose)
    if exists:

        # If target directory already exists, just return.

        if verbose:
            print('Directory %s already exists.' % dir)
        return

    else:

        # Target directoroy doesn't exist.

        if verbose:
            print('Directory %s doesn\'t exist.' % dir)

        # Make sure that the parent directory exists by calling this function recursively.

        parent = os.path.dirname(dir)
        mkdir(parent, verbose)

        # Make the directory.
        # Catch errors and exit with error status in that case.

        ok = False
        try:
            if verbose:
                print('Making directory %s' % dir)
            Ifdh.mkdir(dir)
            ok = True
        except:
            print('Caught exception from Ifdh.mkdir for directory %s.' % dir)
            ok = False
        if not ok:
            sys.exit(1)

        # Done (success).

        return


# This function tests whether the specified directory exists.

def existdir(dir, verbose):

    # Remove trailing '/' character(s), if any (except if or until entire path is '/').

    while len(dir) > 1 and dir[-1] == '/':
        dir = dir[:-1]

    # If at this point, the directory path has been reduced to just '/', return True.

    if dir == '/':
        return True

    # Check contents of parent directory (if any).
    # If ifdh ls for the parent directory fails, return false.
    # Note that ifdh may print out various alarming but harmless
    # message at this point.

    parent = os.path.dirname(dir)
    base = os.path.basename(dir)
    contents = []
    try:
        contents = Ifdh.ls(parent, 1)
    except:
        contents = []

    # Loop over parent directory contents.
    # Only compare the base part of the path, since the mountpoint may differ.

    for content in contents:

        # Is this a directory (ifdh signals by adding '/' at end)?

        if len(content) > 1 and content[-1] == '/':

            # Does base match?

            if os.path.basename(content[:-1]) == base:
                return True

    # If we fall out of the loopp, that means we didn't find this directory 
    # in the parent directory.

    return False

# Command line.

if __name__ == "__main__":
    rc = main(sys.argv)
    sys.exit(rc)
