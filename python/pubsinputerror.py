#! /usr/bin/env python
######################################################################
#
# Name: pubsinputerror.py
#
# Purpose: Python class PubsInputError (exception class).
#          This exception is raised if input is temporarily unavailable
#          for a given (run, subrun, version) in pubs mode due to merging.
#
# Created: 22-May-2015  Herbert Greenlee
#
######################################################################

from __future__ import absolute_import
from __future__ import print_function

# PubsInputError class.

class PubsInputError(Exception):

    def __init__(self, run, subrun, version):
        self.run = run
        self.subrun = subrun
        self.version = version
        return

    def __str__(self):
        return 'Input is not yet available for run %d, subrun %d, version %d.' % (
            self.run, self.subrun, self.version)
