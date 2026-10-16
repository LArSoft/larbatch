#!/usr/bin/env python
######################################################################
#
# Name: stream.py
#
# Purpose: Extract stream name from internal sam metadata in an
#          artroot file.
#
# Created: 13-Oct-2015  H. Greenlee
#
# Command line usage:
#
# stream.py <artroot file>
#
######################################################################

from __future__ import absolute_import
from __future__ import print_function

# Import stuff.

import sys, subprocess, json
from larbatch_utilities import convert_str

# Read and decode stream encoded in sam metadata.

def get_stream(inputfile):

    result = ''

    # Extract sam metadata in form of json string.

    jobinfo = subprocess.Popen(['sam_metadata_dumper', inputfile],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    jobout, joberr = jobinfo.communicate()
    jobout = convert_str(jobout)
    joberr = convert_str(joberr)
    rc = jobinfo.poll()
    if rc != 0:
        raise RuntimeError('sam_metadata_dumper failed with status %d' % rc)

    # Decode json string to dictionary.
    # Work around art bug by deleting "runs" line.

    json_str = ''
    n = jobout.find('"runs"')
    if n >= 0:
        m = jobout.rfind('\n', 0, n)
        if m > 0:
            json_str = jobout[:m+1]
        k = jobout.find('\n', n)
        if k > n:
            json_str += jobout[k+1:]
    else:
        json_str = jobout

    # End of workaround.

    js = json.loads(json_str)
    md = js[inputfile]

    # Extract stream from json dictionary.

    if 'data_stream' in md:
        result = md['data_stream']
    else:
        raise RuntimeError('Sam metadata does not contain stream.')

    # Done.

    return result

# Main program.

if __name__ == "__main__":
    stream = get_stream(str(sys.argv[1]))
    print(stream)
    sys.exit(0) 
