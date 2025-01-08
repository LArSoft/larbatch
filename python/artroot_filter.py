#! /usr/bin/env python
######################################################################
#
# Name: artroot_filter.py
#
# Purpose: Read a list of files from standard input (one per line) and
#          output valid artroot files to standard output (also one per line).
#
# Usage:
#
# This script does not accept any command line options or arguments.
#
# Examples:
#
# ls -1 *.root | artroot_filter.py
# cat files.list | artroot_filter.py
#
# Created: 7-Jan-2025  Herbert Greenlee
#
######################################################################

from __future__ import absolute_import
from __future__ import print_function
import sys, os

# Import ROOT module.
# Globally turn off root warning and error messages.
# Don't let root see our command line options.

myargv = sys.argv
sys.argv = myargv[0:1]
if 'TERM' in os.environ:
    del os.environ['TERM']
import ROOT
ROOT.gErrorIgnoreLevel = ROOT.kFatal
sys.argv = myargv

# Main program.

def main(argv):

    # Loop over stdin lines.

    for line in sys.stdin.readlines():

        # Separate line into words and only keep the first word.
        # Blanks lines are skipped here.

        words = line.split()
        if len(words) > 0:
            f=words[0]

            # Try to open file as a root file.

            root = ROOT.TFile.Open(f, 'read')
            if root and root.IsOpen() and not root.IsZombie():

                # File opened successfully.
                # Loop over this file keys.
                # To qualify as an artroot file, this file must contain the following objects:
                # 1.  A TTree called 'Events'
                # 2.  A TKey called 'RootFileDB'

                has_events = False
                has_db = False
                keys = root.GetListOfKeys()
                for key in keys:
                    objname = key.GetName()
                    obj = root.Get(objname)
                    if objname == 'Events' and obj.InheritsFrom('TTree'):
                        has_events = True
                    if objname == 'RootFileDB' and obj.InheritsFrom('TKey'):
                        has_db = True

                # Is this an artroot file?  Print file name if yes.

                if has_events and has_db:
                    print(f)

    # Done.

    return 0

# Invoke main program.

if __name__ == '__main__':
    sys.exit(main(sys.argv))
