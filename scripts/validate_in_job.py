#!/usr/bin/env python
#=================================================================================
#
# Name: validate_in_job.py
#
# Purpose: Run validation checks on batch worker, including declaring files to sam.
#
# Options:
#
# --dir <dir>     - Directory containing .root files on batch worker.
# --logfiledir <dir> - Log file directory on batch worker (lar.stat and .json files).
# --outdir <dir>  - Final output directory (e.g. dCache) where .root files will be copied.
# --declare <0/1> - Flag for declaring files to sam.
# --copy <0/1>    - Flag for copyoing files directly to dropbox.
# --maintain_parentage <0/1> - If true, override default parentage according to
#                              env variables JOBS_PARENTS and JOBS_AUNTS.
# --data_file_type - Specify data file type (repeatable, default "root").
# --parents <file> - File containing parent files (same as $JOBS_PARENTS).
# --aunts <file>   - File containing aunt files (same as $JOBS_AUNTS).
# --finscript <script> - Run specified finalization script.
#
# Environment variables:
#
# JOBS_PARENTS - Override parent files (space-separated list).
# JOBS_AUNTS   - Override aunt files (space-separated list).
#
#=================================================================================
from __future__ import absolute_import
from __future__ import print_function
import sys, os, json, tempfile, shutil, subprocess
from larbatch_utilities import ifdh_cp
import project_utilities
import samweb_cli

samweb = None           # Initialized SAMWebClient object
extractor_dict = None   # Metadata extractor

# Check a single root file.
# Returns a 2-tuple containing the number of events and stream name.
# The number of events conveys the following information:
# 1.  Number of events (>=0) in TTree named "Events."
# 2.  -1 if root file does not contain an Events TTree, but is otherwise valid (openable).
# 3.  -2 for error (root file does not exist or is not openable).

def check_root_file(path, logdir):

    result = (-2, '')
    json_ok = False
    md = []
    print('Checking %s' % os.path.basename(path))

    # First check if root file exists (error if not).

    if not project_utilities.safeexist(path):
        return result

    # See if we have precalculated metadata for this root file.

    json_path = os.path.join(logdir, os.path.basename(path) + '.json')
    if project_utilities.safeexist(json_path):

        # Get number of events from precalculated metadata.

        try:
            lines = project_utilities.saferead(json_path)
            s = ''
            for line in lines:
               s = s + line

            # Convert json string to python dictionary.

            md = json.loads(s)

            # If we get this far, say the file was at least openable.

            result = (-1, '')

            # Extract number of events and stream name from metadata.

            if len(list(md.keys())) > 0:
                nevroot = -1
                stream = ''
                if 'events' in md:
                    nevroot = int(md['events'])
                if 'data_stream' in md:
                    stream = md['data_stream']
                result = (nevroot, stream)
            json_ok = True
        except:
            result = (-2, '')
    return result


# Check data files in the specified directory.

def check_root(outdir, logdir, data_file_types):

    # This method looks for files with file types matching data_file_types.
    # If such files are found, it also checks for the existence of
    # an Events TTree.
    #
    # Returns a 3-tuple containing the following information.
    # 1.  Total number of events in art root files.
    # 2.  A list of 3-tuples with an entry for each art root file.
    #     The 3-tuple contains the following information.
    #     a) Filename (full path).
    #     b) Number of events
    #     c) Stream name.
    # 3.  A list of histogram root files.

    nev = -1
    roots = []
    hists = []

    print('Checking root files in directory %s.' % outdir)
    filenames = os.listdir(outdir)
    for filename in filenames:
        name, ext = os.path.splitext(filename)
        if len(ext) > 0 and ext[1:] in data_file_types:
            path = os.path.join(outdir, filename)
            nevroot, stream = check_root_file(path, logdir)
            if nevroot >= 0:
                if nev < 0:
                    nev = 0
                nev = nev + nevroot
                roots.append((os.path.join(outdir, filename), nevroot, stream))

            elif nevroot == -1:

                # Valid data file, not an art root file.

                hists.append(os.path.join(outdir, filename))

            else:

                # Found a .root file that is not openable.
                # Print a warning, but don't trigger any other error.

                print('Warning: File %s in directory %s is not a valid root file.' % (filename, outdir))

    # Done.

    return (nev, roots, hists)
    
def import_samweb():

    # Get intialized samweb, if not already done.

    global samweb
    global extractor_dict
    global expMetaData

    if samweb == None:
        samweb = project_utilities.samweb()
        from extractor_dict import expMetaData

# Main program.

def main():
        
    ana = 0
    nproc = 0
    
    import_samweb() 
    
    
    # Parse arguments.
    checkdir=''
    logdir=''
    outdir=''
    declare_file = 0
    copy_to_dropbox = 0
    maintain_parentage = 0
    data_file_types = []
    parents_file = ''
    aunts_file = ''
    finscript = ''
    args = sys.argv[1:]
    while len(args) > 0:

        if args[0] == '--dir' and len(args) > 1:
            checkdir = args[1]
            del args[0:2]
        elif args[0] == '--logfiledir' and len(args) > 1:
            logdir = args[1]
            del args[0:2]
        elif args[0] == '--outdir' and len(args) > 1:
            outdir = args[1]
            del args[0:2]
        elif args[0] == '--declare' and len(args) > 1:
            declare_file = int(args[1])
            del args[0:2]    
        elif args[0] == '--copy' and len(args) > 1:
            copy_to_dropbox = int(args[1])
            del args[0:2]        
        elif args[0] == '--maintain_parentage' and len(args) > 1:
            maintain_parentage = int(args[1])
            del args[0:2]        
        elif args[0] == '--data_file_type' and len(args) > 1:
            data_file_types.append(args[1])
            del args[0:2]        
        elif args[0] == '--parents' and len(args) > 1:
            parents_file = args[1]
            del args[0:2]
        elif args[0] == '--aunts' and len(args) > 1:
            aunts_file = args[1]
            del args[0:2]
        elif args[0] == '--finscript' and len(args) > 1:
            finscript = args[1]
            del args[0:2]
        else:
            print('Unknown option %s' % args[0])
            return 1

    # Add default data_file_types.

    if len(data_file_types) == 0:
        data_file_types.append('root')

    status = 0 #global status code to tell us everything is ok.
    
    print("Do decleration in job: %d" % declare_file) 
    
    # Check lar exit status (if any).
    stat_filename = os.path.join(logdir, 'lar.stat')
    if project_utilities.safeexist(stat_filename):      
        try:
            status = int(project_utilities.saferead(stat_filename)[0].strip())
            if status != 0:
                print('Job in subdirectory %s ended with non-zero exit status %d.' % (checkdir, status))
                status = 1
        
        except:
            print('Bad file lar.stat in subdirectory %s.' % checkdir)
            status = 1
    
    if checkdir == '':
        print('No directory specified (use the --dir option.) Exiting.')
        return 1
    if logdir == '':
        print('No log file directory specified (use the --logfiledir option.) Exiting.')
        return 1  
    
    nevts,rootfiles,hists = check_root(checkdir, logdir, data_file_types)

    # Set flag to do analysis-style validation if all of the following are true:
    #
    # 1.  There is at least one valid histogram file.
    # 2.  The total number of artroot files and artroot events is zero.

    if len(hists) > 0 and len(rootfiles) == 0 and nevts <= 0:
        ana = 1
    
    if not ana:
        if len(rootfiles) == 0 or nevts < 0:
            print('Problem with root file(s) in  %s.' % checkdir)
            status = 1
      
    
    elif nevts < -1 or len(hists) == 0:
        print('Problem with analysis root file(s) in  %s.' % checkdir)
        status = 1
    
    
# Then we need to loop over rootfiles and hists because those are good.
# Then we could make a list of those and check that the file in question for
# declaration is in that liast. also require that the par exit code is good for 
# declaration.

    validate_list = open('validate.list','w')
    file_list = open('files.list', 'w')
    ana_file_list = open('filesana.list', 'w')
    
    events_list = open('events.list', 'w')
    
    #will be empty if the checks succeed    
    bad_list = open('bad.list', 'w')
    missing_list = open('missing_files.list', 'w')    
    
    # Print summary.

    if ana:
        print("%d processes completed successfully." % nproc)
        print("%d total good histogram files." % len(hists))
    
    else:
        print("%d total good events." % nevts)
        print("%d total good root files." % len(rootfiles))
        print("%d total good histogram files." % len(hists))
    
    file_list_stream = {}

    # Generate bookkeeping files pertaining to artroot files.

    for rootfile in rootfiles:

        rootpath = rootfile[0]
        nev = rootfile[1]
        streamname = rootfile[2]
        
        # Make sure root file names do not exceed 200 characters.       
        rootname = os.path.basename(rootpath)
        if len(rootname) >= 200:
            print('Filename %s in subdirectory %s is longer than 200 characters.' % (
                rootname, outdir))
            status = 1

        if streamname not in file_list_stream:
            file_list_stream[streamname] = open('files_%s.list' % streamname, 'w')
        validate_list.write(rootpath + '\n')
        file_on_scratch = os.path.join(outdir, os.path.basename(rootpath))
        file_list.write(file_on_scratch + '\n')
        file_list_stream[streamname].write(file_on_scratch + '\n')
        events_list.write('%s %d \n' % (file_on_scratch, nev) )

    # Generate bookkeeping files pertaining to analysis files.
        
    for histfile in hists:
        validate_list.write(histfile + '\n')
        file_on_scratch = os.path.join(outdir, os.path.basename(histfile))
        ana_file_list.write(file_on_scratch + '\n')
    
        
    
    validate_list.close()
    file_list.close()
    ana_file_list.close()
    for streamname in list(file_list_stream.keys()):
        file_list_stream[streamname].close()
    events_list.close()
    
    #decide at this point if all the checks are ok. Write to missing_file_list first
    missing_list.write('%d \n' %status)
    
    if status == 0:
        bad_list.close()

        # begin SAM decleration

        if declare_file:

            # Declare artroot files.

            for rootfile in rootfiles:

                rootpath = rootfile[0]
                fn   = os.path.basename(rootpath)
                declare_ok = False

                # Decide if we need to declare this file.
                # It is OK if the file is already declared.
                # In that case, do not try to declare it again.

                try:
                    md = samweb.getMetadata(fn)
                    if len(md) > 0:
                        declare_ok = True
                        print('File %s is already declared.' % fn)
                except:
                    declare_ok = False

                if not declare_ok:
                    print('Declaring %s' % fn)
                    expSpecificMetaData = expMetaData(project_utilities.get_experiment(), rootpath)
                    md = expSpecificMetaData.getmetadata()

                    # Decide if we want to override the internal parentage metadata.

                    if maintain_parentage == 1:

                        # Delete the old parents, if any.

                        if 'parents' in md:                  
                            del md['parents']

                        # change the parentage of the file based on it's parents and aunts from condor_lar

                        if parents_file != '':
                            md['parents'] = []
                            pf = open(parents_file)
                            for line in pf.readlines():
                                md['parents'].append({'file_name': line.strip()})
                            pf.close()
                        else:
                            jobs_parents = os.getenv('JOBS_PARENTS', '').split(" ")
                            if(jobs_parents[0] != '' ):
                                md['parents'] = [{'file_name': parent} for parent in jobs_parents]

                        if aunts_file != '':
                            af = open(aunts_file)
                            for line in af.readlines():
                                md['parents'].append({'file_name': line.strip()})
                            af.close()
                        else:
                            jobs_aunts   = os.getenv('JOBS_AUNTS', '').split(" ")
                            if(jobs_aunts[0] != '' ):
                                for aunt in jobs_aunts:
                                    mixparent_dict = {'file_name': aunt}
                                    if 'parents' not in md:
                                        md['parents'] = []
                                    md['parents'].append(mixparent_dict)
                                             
                    if len(md) > 0:
                        project_utilities.test_token()

                        # Make lack of parent files a nonfatal error.
                        # This should probably be removed at some point.
      
                        try:
                            samweb.declareFile(md=md)
                            #s = json.dumps(md, indent=2)
                            #print(s)
                            declare_ok = True

                        except samweb_cli.exceptions.SAMWebHTTPError as e:
                            print(e)
                            print('SAM declare failed.')
                            return 1
             
                        except:
                            print('SAM declare failed.')
                            return 1
                     
                    else:
                        print('No sam metadata found for %s.' % fn)
                        declare_ok = False
                        status = 1

                if declare_ok and finscript != '':

                    # If sam declaration is OK, run final check script before
                    # (possibly) copying file to dropbox.

                    print('Running final checks on file %s' % fn)

                    # Create a new empty temporary directory and cd there.

                    curdir = os.getcwd()
                    tempdir = tempfile.mkdtemp(dir=curdir)
                    print('Making temporary directory %s' % tempdir)
                    os.chdir(tempdir)

                    # Make a symbolic link from rootpath to the new directory.

                    os.symlink(rootpath, fn)

                    # Run final checking script.

                    print('Running post-declaration checking script %s' % finscript)
                    sys.stdout.flush()
                    sys.stderr.flush()
                    st = subprocess.run('../%s' % finscript)
                    rc = st.returncode
                    print('%s completed with status %d.' % (finscript, rc))
                    if rc != 0:
                        declare_ok = False
                        status = 1

                    # Cd back to the original current directory and delete the temporary directory.

                    print('Deleting temporary directory %s' % tempdir)
                    os.chdir(curdir)
                    shutil.rmtree(tempdir)                    

                if copy_to_dropbox == 1 and declare_ok:
                    print("Copying to Dropbox")
                    dropbox_dir = project_utilities.get_dropbox(fn)
                    rootPath = os.path.join(dropbox_dir, fn)
                    jsonPath = rootPath + ".json"
                    ifdh_cp(rootpath, rootPath)

            # Declare histogram files.
             
            for histpath in hists:

                declare_ok = False
                fn   = os.path.basename(histpath)

                # Decide if we need to declare this file.
                # It is OK if the file is already declared.
                # In that case, do not try to declare it again.

                try:
                    md = samweb.getMetadata(fn)
                    if len(md) > 0:
                        declare_ok = True
                        print('File %s is already declared.' % fn)
                except:
                    declare_ok = False

                if not declare_ok:
                    print('Declaring %s' % fn)
                    json_file = os.path.join(logdir, fn + '.json')

                    # Get metadata from json

                    md = {}
                    if project_utilities.safeexist(json_file):
                        mdlines = project_utilities.saferead(json_file)
                        mdtext = ''
                        for line in mdlines:
                            mdtext = mdtext + line
                        try:
                            md = json.loads(mdtext)
                        except:
                            md = {}
                            pass

                    if maintain_parentage == 1:

                        # Delete the old parents, if any.

                        if 'parents' in md:                  
                            del md['parents']

                        # change the parentage of the file based on it's parents and aunts from condor_lar

                        if parents_file != '':
                            md['parents'] = []
                            pf = open(parents_file)
                            for line in pf.readlines():
                                md['parents'].append({'file_name': line.strip()})
                            pf.close()
                        else:
                            jobs_parents = os.getenv('JOBS_PARENTS', '').split(" ")
                            if(jobs_parents[0] != '' ):
                                md['parents'] = [{'file_name': parent} for parent in jobs_parents]

                        if aunts_file != '':
                            af = open(aunts_file)
                            for line in af.readlines():
                                md['parents'].append({'file_name': line.strip()})
                            af.close()
                        else:
                            jobs_aunts   = os.getenv('JOBS_AUNTS', '').split(" ")
                            if(jobs_aunts[0] != '' ):
                                for aunt in jobs_aunts:
                                    mixparent_dict = {'file_name': aunt}
                                    if 'parents' not in md:
                                        md['parents'] = []
                                    md['parents'].append(mixparent_dict)
                                             
                    if len(md) > 0 and 'file_type' in md:
                        project_utilities.test_token()

                        # Make lack of parent files a nonfatal error.
                        # This should probably be removed at some point.
      
                        try:
                            samweb.declareFile(md=md)
                            #s = json.dumps(md, indent=2)
                            #print(s)
                            declare_ok = True
             
                        except samweb_cli.exceptions.SAMWebHTTPError as e:
                            print(e)
                            print('SAM declare failed.')
                            declare_ok = False
             
                        except:
                            print('SAM declare failed.')
                            declare_ok = False
                     
                    else:
                        print('No sam metadata found for %s.' % fn)
                        declare_ok = False
             
                if declare_ok and finscript != '':

                    # If sam declaration is OK, run final check script before
                    # (possibly) copying file to dropbox.

                    print('Running final checks on file %s' % fn)

                    # Create a new empty temporary directory and cd there.

                    curdir = os.getcwd()
                    tempdir = tempfile.mkdtemp(dir=curdir)
                    print('Making temporary directory %s' % tempdir)
                    os.chdir(tempdir)

                    # Make a symbolic link from histpath to the new directory.

                    os.symlink(histpath, fn)

                    # Run final checking script.

                    print('Running post-declaration checking script %s' % finscript)
                    st = subprocess.run('../%s' % finscript)
                    rc = st.returncode
                    print('%s completed with status %d.' % (finscript, rc))
                    if rc != 0:
                        declare_ok = False
                        status = 1

                    # Cd back to the original current directory and delete the temporary directory.

                    print('Deleting temporary directory %s' % tempdir)
                    os.chdir(curdir)
                    shutil.rmtree(tempdir)                    

                if copy_to_dropbox == 1 and declare_ok:
                    print("Copying to Dropbox")
                    dropbox_dir = project_utilities.get_dropbox(fn)
                    rootPath = dropbox_dir + "/" + fn
                    jsonPath = rootPath + ".json"
                    ifdh_cp(histpath, rootPath)
             
        return status
    
    # something went wrong, so make a list of bad directories and potentially missing files
    else:      
        # first get the subdir name on pnfs. this contains the job id
        dir_on_scratch = os.path.basename(outdir)
        print('Dir on scratch ' + dir_on_scratch)
        bad_list.write('%s \n' % dir_on_scratch)
        bad_list.close()
        return status  
    

if __name__ == '__main__' :
    sys.exit(main())
