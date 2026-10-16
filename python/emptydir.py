#!/usr/bin/env python
######################################################################
#
# Name: emptydir.py
#
# Purpose: This script uses ifdh to remove contents from a specified
#          ifdh-accessible directory.  The directory itself may or may
#          not be deleted depending on the presence or absence of option
#          "-d".
#
#          Environment variable $EXPERIMENT must be defined to properly 
#          initialize ifdh.
#
# Created: 15-May-2015  H. Greenlee
#
# Command line usage:
#
# emptydir.py [-h|--help] [-d] <dir>
#
# Options:
#
# -h, --help - Print help.
# -d         - Delete directory (in addition to contents).
# -v         - Verbose.
#
# Arguments:
#
# <dir>      - Directory to empty or delete.
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

    deldir = 0
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
        elif args[0] == '-d':
            deldir = 1
            del args[0]
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

    if deldir:
        rmdir(dir, verbose)
    else:
        emptydir(dir, verbose)

# Help function.

def help():
    filename = sys.argv[0]
    file = open(filename, 'r')

    doprint=0
    
    for line in file.readlines():
        if line[2:13] == 'emptydir.py':
            doprint = 1
        elif line[0:6] == '######' and doprint:
            doprint = 0
        if doprint:
            if len(line) > 2:
                print(line[2:], end=' ')
            else:
                print()


# This function deletes the contents of a directory, but not the directory itself.

def emptydir(dir, verbose):

    # Remove trailing '/' character(s), if any (except if or until entire path is '/').

    while len(dir) > 1 and dir[-1] == '/':
        dir = dir[:-1]

    # Get contents of directory.

    files = []
    try:
        files = Ifdh.ls(dir, 1)
    except:
        files = []
        print('Caught exception from Ifdh.ls for directory %s.' % dir)

    # First pass: delete files.

    for file in files:

        # Ifdh signals that a file is a directory by ending the path with '/'.

        if file[-1] != '/':
            if verbose:
                print('Deleting %s' % file)
            try:
                Ifdh.rm(file)
            except:
                print('Caught exception from Ifdh.rm for file %s.' % file)
                

    # Second pass: delete subdirectories.

    first = True
    for subdir in files:

        # Ifdh signals that a file is a directory by ending the path
        # with '/'.  Ifdh seems to include the directory itself in its
        # listing.  Furthermore, it can be hard to recognize that a
        # listed path is identical with the original directory.
        # However, ifdh seems to always return the directory itself as
        # the first element of its listing (not sure if this is
        # documented behavior.  Therefore, we only delete the first
        # returned element if its basename doesn't match the basename
        # of the original directory.

        if subdir[-1] == '/':
            if not first or os.path.basename(subdir[:-1]) != os.path.basename(dir):
                rmdir(subdir[:-1], verbose)
            first = False


# Function to recursively delete a directory.

def rmdir(dir, verbose):

    # Remove trailing '/' character(s), if any (except if or until entire path is '/').

    while len(dir) > 1 and dir[-1] == '/':
        dir = dir[:-1]

    emptydir(dir, verbose)
    if verbose:
        print('Deleting directory %s' % dir)
    try:
        Ifdh.rmdir(dir)
    except:
        print('Caught exception from Ifdh.rmdir for directory %s.' % dir)


# Command line.

if __name__ == "__main__":
    rc = main(sys.argv)
    sys.exit(rc)
