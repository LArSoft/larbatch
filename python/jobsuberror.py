#! /usr/bin/env python
######################################################################
#
# Name: jobsuberror.py
#
# Purpose: Python class JobsubError (exception class).  This class captures
#          the error status related to jobsub commands that return nonzero
#          exit statuses.  This exception would normally be raised after
#          any failed jobsub command.
#
#          This class contains four data members.
#
#          command - Jobsub command (string).
#          status  - Jobsub exit status.
#          out     - Jobsub standard output.
#          err     - Jobsub diagnostic output.
#
# Created: 20-May-2015  Herbert Greenlee
#
######################################################################

from __future__ import absolute_import
from __future__ import print_function

# Jobsub exception class.

class JobsubError(Exception):

    def __init__(self, command, status, out, err):

        # Store command as a single string.
        # For compatibility with subprocess module, the command may be passed
        # as a list of words.

        self.command = ''
        if type(command) == type([]):
            for word in command:
                self.command = self.command + ' ' + str(word)
        else:
            self.command = str(command)
        self.status = int(status)
        self.out = str(out)
        self.err = str(err)
        return

    def __str__(self):
        s = '\nCommand: %s\nStatus: %d\nOutput: %s\nError: %s\n' % (
            self.command, self.status, self.out, self.err)
        return s


