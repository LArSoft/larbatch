#! /usr/bin/env python
######################################################################
#
# Name: xmlerror.py
#
# Purpose: Python class XMLError (exception class).
#
# Created: 12-Dec-2014  Herbert Greenlee
#
######################################################################

from __future__ import absolute_import
from __future__ import print_function

# XML exception class.

class XMLError(Exception):

    def __init__(self, s):
        self.value = s
        return

    def __str__(self):
        return self.value

