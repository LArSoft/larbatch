#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

# Import stuff.

import sys, os, subprocess, json, stream
import larbatch_posix
import larbatch_utilities
from larbatch_utilities import convert_str
import project_utilities

# Import ROOT (hide command line arguments).

myargv = sys.argv
sys.argv = myargv[0:1]
sys.argv.append('-n')
# Prevent root from printing garbage on initialization.
if 'TERM' in os.environ:
    del os.environ['TERM']
import ROOT
ROOT.gErrorIgnoreLevel = ROOT.kError
sys.argv = myargv

# Filter warnings.

import warnings
warnings.filterwarnings('ignore', category = RuntimeWarning, message = 'creating converter.*')

# Convert adler32-1 (used by dcache) to adler32-0 (used by sam).

def convert_1_adler32_to_0_adler32(crc, filesize):
    crc = int(crc)
    filesize = int(filesize)
    size = int(filesize % 65521)
    s1 = (crc & 0xffff)
    s2 = ((crc >> 16) &  0xffff)
    s1 = (s1 + 65521 - 1) % 65521
    s2 = (s2 + 65521 - size) % 65521
    return (s2 << 16) + s1


# Checksum utilities copied from sam_web_client

def enstoreChecksum(fileobj):
    import zlib
    readblocksize = 1024*1024
    crc = 0
    while 1:
        try:
            s = fileobj.read(readblocksize)
        except (OSError, IOError) as ex:
            raise Error(str(ex))
        if not s: break
        crc = zlib.adler32(s,crc)
    crc = int(crc)
    if crc < 0:
        # Return 32 bit unsigned value
        crc  = (crc & 0x7FFFFFFF) | 0x80000000
    return { "crc_value" : str(crc), "crc_type" : "adler 32 crc type" }

def fileEnstoreChecksum(path):
    """Calculate enstore compatible CRC value"""

    crc = {}
    srm_url = project_utilities.path_to_srm_url(path)

    if srm_url == path:
        try:
            f = larbatch_posix.open(path,'rb')
            crc = enstoreChecksum(f)
        except (IOError, OSError) as ex:
            raise Error(str(ex))
        finally:
            f.close()
    else:
        try:
            # Following commented commands are old way of calculating checksum by
            # transferring entire file over network.
            # Should work again if uncommented (if srm way breaks).

            #cmd = ['ifdh', 'cp', path, '/dev/fd/1']
            #p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            #f = p.stdout
            #crc = enstoreChecksum(f)

            # New (clever, efficient, obscure...) way of accessing dCache 
            # stored checksum using srm.
            project_utilities.test_proxy()
            cmd = ['srmls', '-2', '-l', srm_url]
            srmout = convert_str(subprocess.check_output(cmd))
            first = True
            crc0 = 0
            for line in srmout.split('\n'):
                if first:
                    size = int(line[2:line.find('/')-1])
                    first = False
                    continue
                if line.find("Checksum value:") > 0:
                    ssum = line[line.find(':') + 2:]
                    crc1 = int( ssum , base = 16 )
                    crc0 = convert_1_adler32_to_0_adler32(crc1, size)
                    break

            crc = {"crc_value": str(crc0), "crc_type": "adler 32 crc type"}
            
        except:
            # Try the old method
            cmd = ['ifdh', 'cp', path, '/dev/fd/1']
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            f = p.stdout
            crc = enstoreChecksum(f)
    return crc

def get_external_metadata(inputfile):

    # define an empty python dictionary
    md = {}

    # Check whether this file exists.
    if not os.path.exists(inputfile):
        return md
            
    # Get the other meta data field parameters                                          
    md['file_name'] =  os.path.basename(inputfile)
    md['file_size'] =  str(os.path.getsize(inputfile))
    md['crc'] = fileEnstoreChecksum(inputfile)

    # Quit here if file type is not ".root"

    if not inputfile.endswith('.root'):
        return md

    # Root checks.

    ROOT.gEnv.SetValue('RooFit.Banner', '0')
    file = ROOT.TFile.Open(larbatch_posix.root_stream(inputfile))
    if file and file.IsOpen() and not file.IsZombie():

        # Root file opened successfully.
        # Get number of events.
            
        obj = file.Get('Events')
        if obj and obj.InheritsFrom('TTree'):

            # This has a TTree named Events.

            nev = obj.GetEntriesFast()
            md['events'] = str(nev)

        # Get runs and subruns fro SubRuns tree.

        subrun_tree = file.Get('SubRuns')
        if subrun_tree and subrun_tree.InheritsFrom('TTree'):
            md['subruns'] = []
            nsubruns = subrun_tree.GetEntriesFast()
            tfr = ROOT.TTreeFormula('subruns',
                                    'SubRunAuxiliary.id_.run_.run_',
                                    subrun_tree)
            tfs = ROOT.TTreeFormula('subruns',
                                    'SubRunAuxiliary.id_.subRun_',
                                    subrun_tree)
            for entry in range(nsubruns):
                subrun_tree.GetEntry(entry)
                run = tfr.EvalInstance64()
                subrun = tfs.EvalInstance64()
                run_subrun = (run, subrun)
                if not run_subrun in md['subruns']:
                    md['subruns'].append(run_subrun)

        # Get stream name.

        try:
            stream_name = stream.get_stream(inputfile)
            md['data_stream'] = stream_name
        except:
            pass

    return md

if __name__ == "__main__":
    
    import argparse
    
    Parser = argparse.ArgumentParser \
      (description="Extracts metadata for a ROOT file.")
    
    Parser.add_argument("InputFile", help="ROOT file to extract metadata about")
    Parser.add_argument("--output", "-o", dest="OutputFile", default=None,
      help="JSON file to write the output to [default: screen]"
      )
    
    args = Parser.parse_args()
    
    md = get_external_metadata(args.InputFile)
    mdtext = json.dumps(md, indent=2, sort_keys=True)
    
    outputFile = open(args.OutputFile, 'w') if args.OutputFile else sys.stdout
    print(mdtext, file=outputFile)
    
    sys.exit(0)
