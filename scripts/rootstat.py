#! /usr/bin/env python
######################################################################
#
# Name: rootstat.py
#
# Purpose: Analyze art root file and dump object statistics.
#
# Created: 27-Nov-2012  Herbert Greenlee
#
# Usage:
#
# stat.py <options> [@filelist] [file1 file2 ...]
#
# Options:
#
# [-h|--help] - Print help message.
# --level n   - Branch level (default 1).  Use --level 1 to see top
#               branches only.  Use --level 2 to also see subbranches.
# --nfile n   - Number of files to analyze (default all).
# --all       - Print analysis of each file (default is only summary).
# --s1        - Sort branches by uncompressed size.
# --s2        - Sort branches by compressed size (default).
# --s3        - Sort branches by name.
#
# Arguments:
#
# @filelist       - File list containing one input file per line.
# file1 file2 ... - Input files.
#
######################################################################

from __future__ import absolute_import
from __future__ import print_function
import sys, os
import project_utilities
import larbatch_posix

# Import ROOT module.
# Globally turn off root warnings.
# Don't let root see our command line options.

myargv = sys.argv
sys.argv = myargv[0:1]
if 'TERM' in os.environ:
    del os.environ['TERM']
import ROOT
ROOT.gErrorIgnoreLevel = ROOT.kError
sys.argv = myargv

# Print help.

def help():

    filename = sys.argv[0]
    file = open(filename)

    doprint=0
    
    for line in file.readlines():
        if line[2:9] == 'stat.py':
            doprint = 1
        elif line[0:6] == '######' and doprint:
            doprint = 0
        if doprint:
            if len(line) > 2:
                print(line[2:], end=' ')
            else:
                print()

# Analyze root file.

def analyze(root, level, gtrees, gbranches, doprint, sorttype):

    trees = {}
    events = None
    keys = root.GetListOfKeys()
    for key in keys:
        objname = key.GetName()
        if objname not in trees:
            obj = root.Get(objname)
            if obj and obj.InheritsFrom('TTree'):
                trees[objname] = obj
                if objname == 'Events':
                    events = obj

    # Print summary of trees.

    if doprint:
        print('\nTrees:\n')
    for key in sorted(trees.keys()):
        tree = trees[key]
        nentry = tree.GetEntriesFast()
        if doprint:
            print('%s has %d entries.' % (key, nentry))

        # Remember information about trees.

        if key in gtrees:
            gtrees[key] = gtrees[key] + nentry
        else:
            gtrees[key] = nentry

    # Print summary of branches in Events tree.

    if doprint:
        print('\nBranches of Events tree:\n')

    # If level is zero, we are done (don't analyze branches).

    if level == 0:
        return

    if events:

        branch_tuples = {}

        if doprint:
            print('   Total bytes  Zipped bytes   Comp.  Branch name')
            print('   -----------  ------------   -----  -----------')
            
        branches = events.GetListOfBranches()
        ntotall = 0
        nzipall = 0

        # Loop over branche of Events tree.

        for branch in branches:
            branch_class = branch.GetClass().GetName()

            # Only look at data products (class art::Wrapper<T>).
            
            if branch_class[0: 13] == 'art::Wrapper<':

                # Loop over subbranches.
                
                subbranches = branch.GetListOfBranches()
                for subbranch in subbranches:
                    name = subbranch.GetName()

                    # Only look at '.obj' subbranch (wrapped object).
                    
                    if name[-4:] == '.obj':
                        ntot = subbranch.GetTotBytes("*")
                        nzip = subbranch.GetZipBytes("*")
                        ntotall = ntotall + ntot
                        nzipall = nzipall + nzip
                        if doprint:
                            if nzip != 0:
                                comp = float(ntot) / float(nzip)
                            else:
                                comp = 0.
                            branch_key = None
                            if sorttype == 1:
                                branch_key = ntot
                            elif sorttype == 2:
                                branch_key = nzip
                            else:
                                branch_key = name
                            branch_tuples[branch_key] = (ntot, nzip, comp, name)
                            #print('%14d%14d%8.2f  %s' % (ntot, nzip, comp, name))

                        # Remember information about branches.
                        
                        if name in gbranches:
                            gbranches[name][0] = gbranches[name][0] + ntot
                            gbranches[name][1] = gbranches[name][1] + nzip
                        else:
                            gbranches[name] = [ntot, nzip]

                        # Loop over subsubbranches (attributes of wrapped object).
                        
                        if level > 1:
                            subsubbranches = subbranch.GetListOfBranches()
                            for subsubbranch in subsubbranches:
                                name = subsubbranch.GetName()
                                ntot = subsubbranch.GetTotBytes("*")
                                nzip = subsubbranch.GetZipBytes("*")
                                if doprint:
                                    if nzip != 0:
                                        comp = float(ntot) / float(nzip)
                                    else:
                                        comp = 0.
                                branch_key = None
                                if sorttype == 1:
                                    branch_key = ntot
                                elif sorttype == 2:
                                    branch_key = nzip
                                else:
                                    branch_key = name
                                    branch_tuples[branch_key] = (ntot, nzip, comp, name)
                                    #print('%14d%14d%8.2f  %s' % (ntot, nzip, comp,
                                    #                             subsubbranch.GetName()))

                                # Remember information about branches.
                        
                                if name in gbranches:
                                    gbranches[name][0] = gbranches[name][0] + ntot
                                    gbranches[name][1] = gbranches[name][1] + nzip
                                else:
                                    gbranches[name] = [ntot, nzip]

        # Print sorted information about branches.

        if doprint:
            for branch_key in sorted(branch_tuples.keys()):
                branch_tuple = branch_tuples[branch_key]
                ntot = branch_tuple[0]
                nzip = branch_tuple[1]
                comp = branch_tuple[2]
                name = branch_tuple[3]
                print('%14d%14d%8.2f  %s' % (ntot, nzip, comp, name))

        # Do summary of all branches.

        name = 'All branches'
        if doprint:
            if nzipall != 0:
                comp = float(ntotall) / float(nzipall)
            else:
                comp = 0.
            print('%14d%14d%8.2f  %s' % (ntotall, nzipall, comp, name))

            # Print average event size.

            nev = events.GetEntriesFast()
            if nev != 0:
                nevtot = 1.e-6 * float(ntotall) / float(nev)
                nevzip = 1.e-6 * float(nzipall) / float(nev)
            else:
                nevtot = 0.
                nevzip = 0.
            print()
            print('%10d events.' % nev)
            print('%7.2f Mb average size per event.' % nevtot)
            print('%7.2f Mb average zipped size per event.' % nevzip)

        if name in gbranches:
            gbranches[name][0] = gbranches[name][0] + ntotall
            gbranches[name][1] = gbranches[name][1] + nzipall
        else:
            gbranches[name] = [ntotall, nzipall]


    # Done.                     
    
    return
                
# Main program.

def main(argv):

    # Parse arguments.

    input_files = []
    level = 1
    nfilemax = 0
    all = 0
    sorttype = 2

    args = argv[1:]
    while len(args) > 0:
        if args[0] == '-h' or args[0] == '--help':

            # Help.
            
            help()
            return 0

        elif args[0] == '--level' and len(args) > 1:

            # Analyze level.

            level = int(args[1])
            del args[0:2]
            
        elif args[0] == '--nfile' and len(args) > 1:

            # Number of files.

            nfilemax = int(args[1])
            del args[0:2]
            
        elif args[0] == '--all':

            # All files flag.

            all = 1
            del args[0]
            
        elif args[0] == '--s1':

            # Sort flag.

            sorttype = 1
            del args[0]
            
        elif args[0] == '--s2':

            # Sort flag.

            sorttype = 2
            del args[0]
            
        elif args[0] == '--s3':

            # Sort flag.

            sorttype = 3
            del args[0]
            
        elif args[0][0] == '-':

            # Unknown option.

            print('Unknown option %s' % args[0])
            return 1
            
        elif args[0][0] == '@':

            # Read in file list to input files.
            
            filelistname = args[0][1:]
            if larbatch_posix.exists(filelistname):
                for filename in larbatch_posix.readlines(filelistname):
                    input_files.append(filename.strip())
            else:
                print('File list %s does not exist.' % filelistname)
                return 1
            del args[0]
        else:

            # Add single file to input files.
            
            input_files.append(args[0])
            del args[0]

    # Loop over input files.

    gtrees = {}
    gbranches = {}
    nfile = 0

    for input_file in input_files:

        if nfilemax > 0 and nfile >= nfilemax:
            break
        nfile = nfile + 1

        if not larbatch_posix.exists(input_file):
            print('Input file %s does not exist.' % input_file)
            return 1

        print('\nOpening %s' % input_file)
        root = ROOT.TFile.Open(input_file)
        if not root.IsOpen() or root.IsZombie():
            print('Failed to open %s' % input_file)
            return 1

        # Analyze this file.
        
        analyze(root, level, gtrees, gbranches, all, sorttype)

    print('\n%d files analyzed.' % nfile)
                    
    # Print summary of trees.

    print('\nTrees from all files:\n')
    for key in sorted(gtrees.keys()):
        nentry = gtrees[key]
        print('%s has %d total entries.' % (key, nentry))

    # Print summary of branches.

    if level > 0:
        print('\nBranches of Events tree from all files:\n')
        print('   Total bytes  Zipped bytes   Comp.  Branch name')
        print('   -----------  ------------   -----  -----------')
    allname = 'All branches'
    ntot = 0
    nzip = 0
    branch_tuples = {}
    for key in sorted(gbranches.keys()):
        if key != allname:
            ntot = gbranches[key][0]
            nzip = gbranches[key][1]
            if nzip != 0:
                comp = float(ntot) / float(nzip)
            else:
                comp = 0.
            branch_key = None
            if sorttype == 1:
                branch_key = ntot
            elif sorttype == 2:
                branch_key = nzip
            else:
                branch_key = key
            branch_tuples[branch_key] = (ntot, nzip, comp, key)
            #print('%14d%14d%8.2f  %s' % (ntot, nzip, comp, key))

    # Print sorted information about branches.

    for branch_key in sorted(branch_tuples.keys()):
        branch_tuple = branch_tuples[branch_key]
        ntot = branch_tuple[0]
        nzip = branch_tuple[1]
        comp = branch_tuple[2]
        name = branch_tuple[3]
        print('%14d%14d%8.2f  %s' % (ntot, nzip, comp, name))

    if allname in gbranches:
        ntot = gbranches[allname][0]
        nzip = gbranches[allname][1]
        if nzip != 0:
            comp = float(ntot) / float(nzip)
        else:
            comp = 0.
        print('%14d%14d%8.2f  %s' % (ntot, nzip, comp, allname))

    # Print average event size.

    if 'Events' in gtrees:
        nev = gtrees['Events']
        if nev != 0:
            nevtot = 1.e-6 * float(ntot) / float(nev)
            nevzip = 1.e-6 * float(nzip) / float(nev)
        else:
            nevtot = 0.
            nevzip = 0.
        print()
        print('%10d events.' % nev)
        if level > 0:
            print('%7.2f Mb average size per event.' % nevtot)
            print('%7.2f Mb average zipped size per event.' % nevzip)
    

    # Done.

    return 0

# Invoke main program.

if __name__ == '__main__':
    sys.exit(main(sys.argv))
