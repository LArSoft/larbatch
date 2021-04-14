#!/usr/bin/env python
#---------------------------------------------------------------------------
#
# Name: merge_json.py
#
# Purpose: Merge json files/objects into a single json file/object.
#
# Created: 3-Apr-2015  H. Greenlee
#
# Command line usage:
#
# merge_json.py <jsonfile1> <jsonfile2> ... > out.json
#
#---------------------------------------------------------------------------

from __future__ import absolute_import
from __future__ import print_function

# Import stuff.

import sys, json

# Function to merge json objects.
# This function assumes that json objects are python dictionaries.

def merge_json_objects(json_objects):

    merged = {}

    # Loop over input objects and insert all keys into merged object.
    # It is an error if the same key is encountered twice unless tha values
    # are identical.

    for json_object in json_objects:
        for key in list(json_object.keys()):
            if key in list(merged.keys()):
                if json_object[key] != merged[key]:
                    raise RuntimeError('Duplicate nonmatching key %s.' % key)
            else:
                merged[key] = json_object[key]

    # Done.

    return merged

# Function to merge json files and print the result on standard output.

def merge_json_files(json_filenames):

    # Decode all json files into json objects.

    json_objects = []
    for json_filename in json_filenames:
        json_file = open(json_filename)
        if not json_file:
            raise IOError('Unable to open json file %s.' % json_filename)
        obj = json.load(json_file)
        json_objects.append(obj)

    # Combine json objects into a single result object.

    merged = merge_json_objects(json_objects)
    print(json.dumps(merged, indent=2, sort_keys=True))

if __name__ == "__main__":

    json_filenames = sys.argv[1:]
    merge_json_files(json_filenames)
    sys.exit(0) 
