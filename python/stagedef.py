#! /usr/bin/env python
######################################################################
#
# Name: stagedef.py
#
# Purpose: Python class StageDef (used by project.py).
#
# Created: 12-Dec-2014  Herbert Greenlee
#
######################################################################

from __future__ import absolute_import
from __future__ import print_function
import sys, os, stat, math, subprocess, random
import threading
try:
    import queue
except ImportError:
    import Queue as queue
import samweb_cli
import project_utilities
import larbatch_utilities
from larbatch_utilities import convert_str
import larbatch_posix
import uuid
import math
from project_modules.xmlerror import XMLError
from project_modules.pubsinputerror import PubsInputError
from project_modules.pubsdeadenderror import PubsDeadEndError

# Stage definition class.

class StageDef:

    # Constructor.

    def __init__(self, stage_element, base_stage, default_input_lists, default_previous_stage, 
                 default_num_jobs, default_num_events, default_max_files_per_job, default_merge,
                 default_anamerge,
                 default_cpu, default_disk, default_memory, default_nthreads, default_nschedules,
                 default_args, default_validate_on_worker,
                 default_copy_to_fts, default_cvmfs, default_stash, default_singularity,
                 default_script, default_start_script, default_stop_script,
                 default_site, default_blacklist, check=True):

        # Assign default values.

        if base_stage != None:
            self.name = base_stage.name
            self.batchname = base_stage.batchname
            self.fclname = base_stage.fclname
            self.outdir = base_stage.outdir
            self.logdir = base_stage.logdir
            self.workdir = base_stage.workdir
            self.bookdir = base_stage.bookdir
            self.dirsize = base_stage.dirsize
            self.dirlevels = base_stage.dirlevels
            self.dynamic = base_stage.dynamic
            self.inputfile = base_stage.inputfile
            self.inputlist = base_stage.inputlist
            self.inputmode = base_stage.inputmode
            self.basedef = base_stage.basedef
            self.inputdef = base_stage.inputdef
            self.inputstream = base_stage.inputstream
            self.previousstage = base_stage.previousstage
            self.mixinputdef = base_stage.mixinputdef
            self.pubs_input_ok = base_stage.pubs_input_ok
            self.pubs_input = base_stage.pubs_input
            self.input_run = base_stage.input_run
            self.input_subruns = base_stage.input_subruns
            self.input_version = base_stage.input_version
            self.pubs_output = base_stage.pubs_output
            self.output_run = base_stage.output_run
            self.output_subruns = base_stage.output_subruns
            self.output_version = base_stage.output_version
            self.ana = base_stage.ana
            self.recur = base_stage.recur
            self.recurtype = base_stage.recurtype
            self.recurlimit = base_stage.recurlimit
            self.singlerun = base_stage.singlerun
            self.filelistdef = base_stage.filelistdef
            self.prestart = base_stage.prestart
            self.activebase = base_stage.activebase
            self.dropboxwait = base_stage.dropboxwait
            self.prestagefraction = base_stage.prestagefraction
            self.maxfluxfilemb = base_stage.maxfluxfilemb
            self.num_jobs = base_stage.num_jobs
            self.num_events = base_stage.num_events
            self.max_files_per_job = base_stage.max_files_per_job
            self.target_size = base_stage.target_size
            self.defname = base_stage.defname
            self.ana_defname = base_stage.ana_defname
            self.data_tier = base_stage.data_tier
            self.data_stream = base_stage.data_stream
            self.ana_data_tier = base_stage.ana_data_tier
            self.ana_data_stream = base_stage.ana_data_stream
            self.submit_script = base_stage.submit_script
            self.init_script = base_stage.init_script
            self.init_source = base_stage.init_source
            self.end_script = base_stage.end_script
            self.mid_source = base_stage.mid_source
            self.mid_script = base_stage.mid_script
            self.project_name = base_stage.project_name
            self.stage_name = base_stage.stage_name
            self.project_version = base_stage.project_version
            self.merge = base_stage.merge
            self.anamerge = base_stage.anamerge
            self.resource = base_stage.resource
            self.lines = base_stage.lines
            self.site = base_stage.site
            self.blacklist = base_stage.blacklist
            self.cpu = base_stage.cpu
            self.disk = base_stage.disk
            self.datafiletypes = base_stage.datafiletypes
            self.memory = base_stage.memory
            self.nthreads = base_stage.nthreads
            self.nschedules = base_stage.nschedules
            self.args = base_stage.args
            self.parameters = base_stage.parameters
            self.output = base_stage.output
            self.TFileName = base_stage.TFileName
            self.jobsub = base_stage.jobsub
            self.jobsub_start = base_stage.jobsub_start
            self.jobsub_timeout = base_stage.jobsub_timeout
            self.exe = base_stage.exe
            self.schema = base_stage.schema
            self.validate_on_worker = base_stage. validate_on_worker
            self.copy_to_fts = base_stage.copy_to_fts
            self.cvmfs = base_stage.cvmfs
            self.stash = base_stage.stash
            self.singularity = base_stage.singularity
            self.script = base_stage.script
            self.start_script = base_stage.start_script
            self.stop_script = base_stage.stop_script
        else:
            self.name = ''         # Stage name.
            self.batchname = ''    # Batch job name
            self.fclname = []
            self.outdir = ''       # Output directory.
            self.logdir = ''       # Log directory.
            self.workdir = ''      # Work directory.
            self.bookdir = ''      # Bookkeeping directory.
            self.dirsize = 0       # Maximum directory size.
            self.dirlevels = 0     # Number of extra directory levels.
            self.dynamic = 0       # Dynamic output/log directory.
            self.inputfile = ''    # Single input file.
            self.inputlist = ''    # Input file list.
            self.inputmode = ''    # Input file type (none or textfile)
            self.basedef = ''      # Base sam dataset definition.
            self.inputdef = ''     # Input sam dataset definition.
            self.inputstream = ''  # Input file stream.
            self.previousstage = '' # Previous stage name.
            self.mixinputdef = ''  # Mix input sam dataset definition.
            self.pubs_input_ok = 1 # Is pubs input allowed?
            self.pubs_input = 0    # Pubs input mode.
            self.input_run = 0     # Pubs input run.
            self.input_subruns = [] # Pubs input subrun number(s).
            self.input_version = 0 # Pubs input version number.
            self.pubs_output = 0   # Pubs output mode.
            self.output_run = 0    # Pubs output run.
            self.output_subruns = [] # Pubs output subrun number.
            self.output_version = 0 # Pubs output version number.
            self.ana = 0           # Analysis flag.
            self.recur = 0         # Recursive flag.
            self.recurtype = ''    # Recursive type.
            self.recurlimit = 0    # Recursive limit.
            self.singlerun=0       # Single run mode.
            self.filelistdef=0     # Convert sam input def to file list.
            self.prestart = 0      # Prestart flag.
            self.activebase = ''   # Active projects base name.
            self.dropboxwait = 0.  # Dropbox waiting interval.
            self.prestagefraction = 0.  # Prestage fraction.
            self.maxfluxfilemb = 0 # MaxFluxFileMB (size of genie flux files to fetch).
            self.num_jobs = default_num_jobs # Number of jobs.
            self.num_events = default_num_events # Number of events.
            self.max_files_per_job = default_max_files_per_job #max num of files per job
            self.target_size = 0   # Target size for output files.
            self.defname = ''      # Sam dataset definition name.
            self.ana_defname = ''  # Sam dataset definition name.
            self.data_tier = ''    # Sam data tier.
            self.data_stream = []  # Sam data stream.
            self.ana_data_tier = '' # Sam data tier.
            self.ana_data_stream = [] # Sam data stream.
            self.submit_script = '' # Submit script.
            self.init_script = []  # Worker initialization script.
            self.init_source = []  # Worker initialization bash source script.
            self.end_script = []   # Worker end-of-job script.
            self.mid_source = {}   # Worker midstage source init scripts.
            self.mid_script = {}   # Worker midstage finalization scripts.
            self.project_name = [] # Project name overrides.
            self.stage_name = []   # Stage name overrides.
            self.project_version = [] # Project version overrides.
            self.merge = default_merge    # Histogram merging program
            self.anamerge = default_anamerge    # Analysis merge flag.
            self.resource = ''     # Jobsub resources.
            self.lines = ''        # Arbitrary condor commands.
            self.site = default_site # Site.
            self.blacklist = default_blacklist # Blacklist site.
            self.cpu = default_cpu # Number of cpus.
            self.disk = default_disk     # Disk space (string value+unit).
            self.datafiletypes = ["root"] # Data file types.
            self.memory = default_memory # Amount of memory (integer MB).
            self.nthreads = default_nthreads # Number of threads (integer).
            self.nschedules = default_nschedules # Number of schedules (integer).
            self.args = default_args # Extra lar arguments (list of strings).
            self.parameters = {}   # Dictionary of metadata parameters.
            self.output = []       # Art output file names.
            self.TFileName = ''    # TFile output file name.
            self.jobsub = ''       # Arbitrary jobsub_submit options.
            self.jobsub_start = '' # Arbitrary jobsub_submit options for sam start/stop jobs.
            self.jobsub_timeout = 0 # Jobsub submit timeout.
            self.exe = []          # Art-like executables.
            self.schema = ''       # Sam schema.
            self.validate_on_worker = default_validate_on_worker # Validate-on-worker flag.
            self.copy_to_fts = default_copy_to_fts   # Upload-on-worker flag.
            self.cvmfs = default_cvmfs               # Default cvmfs flag.
            self.stash = default_stash               # Default stash flag.
            self.singularity = default_singularity   # Default singularity flag.
            self.script = default_script             # Upload-on-worker flag.
            self.start_script = default_start_script # Upload-on-worker flag.
            self.stop_script = default_stop_script   # Upload-on-worker flag.
        
        # Extract values from xml.

        # Stage name (attribute).

        if 'name' in dict(stage_element.attributes):
            self.name = str(stage_element.attributes['name'].firstChild.data)
        if self.name == '':
            raise XMLError("Stage name not specified.")

        # Batch job name (subelement).

        batchname_elements = stage_element.getElementsByTagName('batchname')
        if batchname_elements:
            self.batchname = str(batchname_elements[0].firstChild.data)

        # Fcl file name (repeatable subelement).

        fclname_elements = stage_element.getElementsByTagName('fcl')
        if len(fclname_elements) > 0:
            self.fclname = []
            for fcl in fclname_elements:
                self.fclname.append(str(fcl.firstChild.data).strip())
        if len(self.fclname) == 0:
            raise XMLError('No Fcl names specified for stage %s.' % self.name)

        # Output directory (subelement).

        outdir_elements = stage_element.getElementsByTagName('outdir')
        if outdir_elements:
            self.outdir = str(outdir_elements[0].firstChild.data)
        if self.outdir == '':
            raise XMLError('Output directory not specified for stage %s.' % self.name)

        # Log directory (subelement).

        logdir_elements = stage_element.getElementsByTagName('logdir')
        if logdir_elements:
            self.logdir = str(logdir_elements[0].firstChild.data)
        if self.logdir == '':
            self.logdir = self.outdir

        # Work directory (subelement).

        workdir_elements = stage_element.getElementsByTagName('workdir')
        if workdir_elements:
            self.workdir = str(workdir_elements[0].firstChild.data)
        if self.workdir == '':
            raise XMLError('Work directory not specified for stage %s.' % self.name)

        # Bookkeeping directory (subelement).

        bookdir_elements = stage_element.getElementsByTagName('bookdir')
        if bookdir_elements:
            self.bookdir = str(bookdir_elements[0].firstChild.data)
        if self.bookdir == '':
            self.bookdir = self.logdir

        # Maximum directory size (subelement).

        dirsize_elements = stage_element.getElementsByTagName('dirsize')
        if dirsize_elements:
            self.dirsize = int(dirsize_elements[0].firstChild.data)

        # Extra directory levels (subelement).

        dirlevels_elements = stage_element.getElementsByTagName('dirlevels')
        if dirlevels_elements:
            self.dirlevels = int(dirlevels_elements[0].firstChild.data)

        # Single input file (subelement).

        inputfile_elements = stage_element.getElementsByTagName('inputfile')
        if inputfile_elements:
            self.inputfile = str(inputfile_elements[0].firstChild.data)

        # Input file list (subelement).

        inputlist_elements = stage_element.getElementsByTagName('inputlist')
        if inputlist_elements:
            self.inputlist = str(inputlist_elements[0].firstChild.data)

        # Input file type (subelement).

        inputmode_elements = stage_element.getElementsByTagName('inputmode')
        if inputmode_elements:
            self.inputmode = str(inputmode_elements[0].firstChild.data)

        # Input sam dataset dfeinition (subelement).

        inputdef_elements = stage_element.getElementsByTagName('inputdef')
        if inputdef_elements:
            self.inputdef = str(inputdef_elements[0].firstChild.data)

        # Analysis flag (subelement).

        ana_elements = stage_element.getElementsByTagName('ana')
        if ana_elements:
            self.ana = int(ana_elements[0].firstChild.data)

        # Recursive flag (subelement).

        recur_elements = stage_element.getElementsByTagName('recur')
        if recur_elements:
            self.recur = int(recur_elements[0].firstChild.data)

        # Recursive type (subelement).

        recurtype_elements = stage_element.getElementsByTagName('recurtype')
        if recurtype_elements:
            self.recurtype = str(recurtype_elements[0].firstChild.data)

        # Recursive limit (subelement).

        recurlimit_elements = stage_element.getElementsByTagName('recurlimit')
        if recurlimit_elements:
            self.recurlimit = int(recurlimit_elements[0].firstChild.data)

        # Recursive input sam dataset dfeinition (subelement).

        recurdef_elements = stage_element.getElementsByTagName('recurdef')
        if recurdef_elements:
            self.basedef = self.inputdef
            self.inputdef = str(recurdef_elements[0].firstChild.data)
            self.recur = 1

        # Single run flag (subelement).

        singlerun_elements = stage_element.getElementsByTagName('singlerun')
        if singlerun_elements:
            self.singlerun = int(singlerun_elements[0].firstChild.data)

        # File list definition flag (subelement).

        filelistdef_elements = stage_element.getElementsByTagName('filelistdef')
        if filelistdef_elements:
            self.filelistdef = int(filelistdef_elements[0].firstChild.data)

        # Prestart flag.

        prestart_elements = stage_element.getElementsByTagName('prestart')
        if prestart_elements:
            self.prestart = int(prestart_elements[0].firstChild.data)

        # Active projects basename.

        activebase_elements = stage_element.getElementsByTagName('activebase')
        if activebase_elements:
            self.activebase = str(activebase_elements[0].firstChild.data)

        # Dropbox wait interval.

        dropboxwait_elements = stage_element.getElementsByTagName('dropboxwait')
        if dropboxwait_elements:
            self.dropboxwait = float(dropboxwait_elements[0].firstChild.data)

        # Prestage fraction (subelement).

        prestagefraction_elements = stage_element.getElementsByTagName('prestagefraction')
        if prestagefraction_elements:
            self.prestagefraction = float(prestagefraction_elements[0].firstChild.data)

        # Input stream (subelement).

        inputstream_elements = stage_element.getElementsByTagName('inputstream')
        if inputstream_elements:
            self.inputstream = str(inputstream_elements[0].firstChild.data)

        # Previous stage name (subelement).

        previousstage_elements = stage_element.getElementsByTagName('previousstage')
        if previousstage_elements:
            self.previousstage = str(previousstage_elements[0].firstChild.data)

            # If a base stage was specified, nullify any input inherted from base.

            if base_stage != None:
                self.inputfile = ''
                self.inputlist = ''
                self.inputdef = ''

            # It never makes sense to specify a previous stage with some other input.

            if self.inputfile != '' or self.inputlist != '' or self.inputdef != '':
                raise XMLError('Previous stage and input specified for stage %s.' % self.name)

        # Mix input sam dataset (subelement).

        mixinputdef_elements = stage_element.getElementsByTagName('mixinputdef')
        if mixinputdef_elements:
            self.mixinputdef = str(mixinputdef_elements[0].firstChild.data)

        # It is an error to specify both input file and input list.

        if self.inputfile != '' and self.inputlist != '':
            raise XMLError('Input file and input list both specified for stage %s.' % self.name)

        # It is an error to specify either input file or input list together
        # with a sam input dataset.

        if self.inputdef != '' and (self.inputfile != '' or self.inputlist != ''):
            raise XMLError('Input dataset and input files specified for stage %s.' % self.name)

        # It is an error to use textfile inputmode without an inputlist or inputfile
        if self.inputmode == 'textfile' and self.inputlist == '' and self.inputfile == '':
            raise XMLError('Input list (inputlist) or inputfile is needed for textfile model.')

        # If none of input definition, input file, nor input list were specified, set
        # the input list to the dafault input list.  If an input stream was specified,
        # insert it in front of the file type.

        if self.inputfile == '' and self.inputlist == '' and self.inputdef == '':

            # Get the default input list according to the previous stage.

            default_input_list = ''
            previous_stage_name = default_previous_stage
            if self.previousstage != '':
                previous_stage_name = self.previousstage
            if previous_stage_name in default_input_lists:
                default_input_list = default_input_lists[previous_stage_name]

            # Modify default input list according to input stream, if any.

            if self.inputstream == '' or default_input_list == '':
                self.inputlist = default_input_list
            else:
                n = default_input_list.rfind('.')
                if n < 0:
                    n = len(default_input_list)
                self.inputlist = '%s_%s%s' % (default_input_list[:n],
                                               self.inputstream,
                                               default_input_list[n:])

        # Pubs input flag.

        pubs_input_ok_elements = stage_element.getElementsByTagName('pubsinput')
        if pubs_input_ok_elements:
            self.pubs_input_ok = int(pubs_input_ok_elements[0].firstChild.data)

        # MaxFluxFileMB GENIEHelper fcl parameter (subelement).

        maxfluxfilemb_elements = stage_element.getElementsByTagName('maxfluxfilemb')
        if maxfluxfilemb_elements:
            self.maxfluxfilemb = int(maxfluxfilemb_elements[0].firstChild.data)
        else:

            # If this is a generator job, give maxfluxfilemb parameter a default
            # nonzero value.

            if self.inputfile == '' and self.inputlist == '' and self.inputdef == '':
                self.maxfluxfilemb = 500

        # Number of jobs (subelement).

        num_jobs_elements = stage_element.getElementsByTagName('numjobs')
        if num_jobs_elements:
            self.num_jobs = int(num_jobs_elements[0].firstChild.data)

        # Number of events (subelement).

        num_events_elements = stage_element.getElementsByTagName('numevents')
        if num_events_elements:
            self.num_events = int(num_events_elements[0].firstChild.data)

        # Max Number of files per jobs.

        max_files_per_job_elements = stage_element.getElementsByTagName('maxfilesperjob')
        if max_files_per_job_elements:
            self.max_files_per_job = int(max_files_per_job_elements[0].firstChild.data)
        
        # Run number of events (MC Gen only).
        #overriden by --pubs <run> is running in pubs mode

        run_number = stage_element.getElementsByTagName('runnumber')
        if run_number:
            self.output_run = int(run_number[0].firstChild.data)    

        # Target size for output files (subelement).

        target_size_elements = stage_element.getElementsByTagName('targetsize')
        if target_size_elements:
            self.target_size = int(target_size_elements[0].firstChild.data)
        

        # Sam dataset definition name (subelement).

        defname_elements = stage_element.getElementsByTagName('defname')
        if defname_elements:
            self.defname = str(defname_elements[0].firstChild.data)

        # Sam analysis dataset definition name (subelement).

        ana_defname_elements = stage_element.getElementsByTagName('anadefname')
        if ana_defname_elements:
            self.ana_defname = str(ana_defname_elements[0].firstChild.data)

        # Sam data tier (subelement).

        data_tier_elements = stage_element.getElementsByTagName('datatier')
        if data_tier_elements:
            self.data_tier = str(data_tier_elements[0].firstChild.data)

        # Sam data stream (subelement).

        data_stream_elements = stage_element.getElementsByTagName('datastream')
        if len(data_stream_elements) > 0:
            self.data_stream = []
            for data_stream in data_stream_elements:
                self.data_stream.append(str(data_stream.firstChild.data))

        # Sam analysis data tier (subelement).

        ana_data_tier_elements = stage_element.getElementsByTagName('anadatatier')
        if ana_data_tier_elements:
            self.ana_data_tier = str(ana_data_tier_elements[0].firstChild.data)

        # Sam analysis data stream (subelement).

        ana_data_stream_elements = stage_element.getElementsByTagName('anadatastream')
        if len(ana_data_stream_elements) > 0:
            self.ana_data_stream = []
            for ana_data_stream in ana_data_stream_elements:
                self.ana_data_stream.append(str(ana_data_stream.firstChild.data))

        # Submit script (subelement).

        submit_script_elements = stage_element.getElementsByTagName('submitscript')
        if submit_script_elements:
            self.submit_script = str(submit_script_elements[0].firstChild.data).split()

        # Make sure submit script exists, and convert into a full path.

        if check:
            if len(self.submit_script) > 0:
                if larbatch_posix.exists(self.submit_script[0]):
                    self.submit_script[0] = os.path.realpath(self.submit_script[0])
                else:

                    # Look for script on execution path.

                    try:
                        jobinfo = subprocess.Popen(['which', self.submit_script[0]],
                                                   stdout=subprocess.PIPE,
                                                   stderr=subprocess.PIPE)
                        jobout, joberr = jobinfo.communicate()
                        jobout = convert_str(jobout)
                        joberr = convert_str(joberr)
                        rc = jobinfo.poll()
                        self.submit_script[0] = jobout.splitlines()[0].strip()
                    except:
                        pass
                if not larbatch_posix.exists(self.submit_script[0]):
                    raise IOError('Submit script %s not found.' % self.submit_script[0])

        # Worker initialization script (repeatable subelement).

        init_script_elements = stage_element.getElementsByTagName('initscript')
        if len(init_script_elements) > 0:
            for init_script_element in init_script_elements:
                init_script = str(init_script_element.firstChild.data)

                # Make sure init script exists, and convert into a full path.

                if check:
                    if init_script != '':
                        if larbatch_posix.exists(init_script):
                            init_script = os.path.realpath(init_script)
                        else:

                            # Look for script on execution path.

                            try:
                                jobinfo = subprocess.Popen(['which', init_script],
                                                           stdout=subprocess.PIPE,
                                                           stderr=subprocess.PIPE)
                                jobout, joberr = jobinfo.communicate()
                                rc = jobinfo.poll()
                                init_script = convert_str(jobout.splitlines()[0].strip())
                            except:
                                pass

                        if not larbatch_posix.exists(init_script):
                            raise IOError('Init script %s not found.' % init_script)

                    self.init_script.append(init_script)

        # Worker initialization source script (repeatable subelement).

        init_source_elements = stage_element.getElementsByTagName('initsource')
        if len(init_source_elements) > 0:
            for init_source_element in init_source_elements:
                init_source = str(init_source_element.firstChild.data)

                # Make sure init source script exists, and convert into a full path.

                if init_source != '':
                    if check:
                        if larbatch_posix.exists(init_source):
                            init_source = os.path.realpath(init_source)
                        else:

                            # Look for script on execution path.

                            try:
                                jobinfo = subprocess.Popen(['which', init_source],
                                                           stdout=subprocess.PIPE,
                                                           stderr=subprocess.PIPE)
                                jobout, joberr = jobinfo.communicate()
                                rc = jobinfo.poll()
                                init_source = convert_str(jobout.splitlines()[0].strip())
                            except:
                                pass

                        if not larbatch_posix.exists(init_source):
                            raise IOError('Init source script %s not found.' % init_source)

                    # The <initsource> element can occur at the top level of the <stage>
                    # element, or inside a <fcl> element.
                    # Update the StageDef object differently in these two cases.

                    parent_element = init_source_element.parentNode
                    if parent_element.nodeName == 'fcl':

                        # This <initsource> is located inside a <fcl> element.
                        # Find the index of this fcl file.
                        # Python will raise an exception if the fcl can't be found
                        # (shouldn't happen).

                        fcl = str(parent_element.firstChild.data).strip()
                        n = self.fclname.index(fcl)
                        if not n in self.mid_source:
                            self.mid_source[n] = []
                        self.mid_source[n].append(init_source)

                    else:

                        # This is a <stage> level <initsource> element.

                        self.init_source.append(init_source)

        # Worker end-of-job script (repeatable subelement).

        end_script_elements = stage_element.getElementsByTagName('endscript')
        if len(end_script_elements) > 0:
            for end_script_element in end_script_elements:
                end_script = str(end_script_element.firstChild.data)

                # Make sure end-of-job scripts exists, and convert into a full path.

                if end_script != '':
                    if check:
                        if larbatch_posix.exists(end_script):
                            end_script = os.path.realpath(end_script)
                        else:

                            # Look for script on execution path.

                            try:
                                jobinfo = subprocess.Popen(['which', end_script],
                                                           stdout=subprocess.PIPE,
                                                           stderr=subprocess.PIPE)
                                jobout, joberr = jobinfo.communicate()
                                rc = jobinfo.poll()
                                end_script = convert_str(jobout.splitlines()[0].strip())
                            except:
                                pass

                        if not larbatch_posix.exists(end_script):
                            raise IOError('End-of-job script %s not found.' % end_script)

                    # The <endscript> element can occur at the top level of the <stage>
                    # element, or inside a <fcl> element.
                    # Update the StageDef object differently in these two cases.

                    parent_element = end_script_element.parentNode
                    if parent_element.nodeName == 'fcl':

                        # This <endscript> is located inside a <fcl> element.
                        # Find the index of this fcl file.
                        # Python will raise an exception if the fcl can't be found
                        # (shouldn't happen).

                        fcl = str(parent_element.firstChild.data).strip()
                        n = self.fclname.index(fcl)
                        if not n in self.mid_script:
                            self.mid_script[n] = []
                        self.mid_script[n].append(end_script)

                    else:

                        # This is a <stage> level <endscript> element.

                        self.end_script.append(end_script)

	# Project name overrides (repeatable subelement).

        project_name_elements = stage_element.getElementsByTagName('projectname')
        if len(project_name_elements) > 0:
            for project_name_element in project_name_elements:

                # Match this project name with its parent fcl element.

                fcl_element = project_name_element.parentNode
                if fcl_element.nodeName != 'fcl':
                    raise XMLError("Found <projectname> element outside <fcl> element.")
                fcl = str(fcl_element.firstChild.data).strip()

                # Find the index of this fcl file.
                # Python will raise an exception if the fcl can't be found (shouldn't happen).

                n = self.fclname.index(fcl)

                # Make sure project_name list is long enough.

                while len(self.project_name) < n+1:
                    self.project_name.append('')

                # Extract project name and add it to list.

                project_name = str(project_name_element.firstChild.data)
                self.project_name[n] = project_name

        # Make sure that the size of the project_name list (if present) ia at least as
        # long as the fclname list.
        # If not, extend by adding empty string.

        if len(self.project_name) > 0:
            while len(self.project_name) < len(self.fclname):
                self.project_name.append('')

	# Stage name overrides (repeatable subelement).

        stage_name_elements = stage_element.getElementsByTagName('stagename')
        if len(stage_name_elements) > 0:
            for stage_name_element in stage_name_elements:

                # Match this project name with its parent fcl element.

                fcl_element = stage_name_element.parentNode
                if fcl_element.nodeName != 'fcl':
                    raise XMLError("Found <stagename> element outside <fcl> element.")
                fcl = str(fcl_element.firstChild.data).strip()

                # Find the index of this fcl file.
                # Python will raise an exception if the fcl can't be found (shouldn't happen).

                n = self.fclname.index(fcl)

                # Make sure stage_name list is long enough.

                while len(self.stage_name) < n+1:
                    self.stage_name.append('')

                # Extract stage name and add it to list.

                stage_name = str(stage_name_element.firstChild.data)
                self.stage_name[n] = stage_name

        # Make sure that the size of the stage_name list (if present) ia at least as
        # long as the fclname list.
        # If not, extend by adding empty string.

        if len(self.stage_name) > 0:
            while len(self.stage_name) < len(self.fclname):
                self.stage_name.append('')

	# Project version overrides (repeatable subelement).

        project_version_elements = stage_element.getElementsByTagName('version')
        if len(project_version_elements) > 0:
            for project_version_element in project_version_elements:

                # Match this project version with its parent fcl element.

                fcl_element = project_version_element.parentNode
                if fcl_element.nodeName != 'fcl':
                    raise XMLError("Found stage level <version> element outside <fcl> element.")
                fcl = str(fcl_element.firstChild.data).strip()

                # Find the index of this fcl file.
                # Python will raise an exception if the fcl can't be found (shouldn't happen).

                n = self.fclname.index(fcl)

                # Make sure project_version list is long enough.

                while len(self.project_version) < n+1:
                    self.project_version.append('')

                # Extract project version and add it to list.

                project_version = str(project_version_element.firstChild.data)
                self.project_version[n] = project_version

        # Make sure that the size of the project_version list (if present) ia at least as
        # long as the fclname list.
        # If not, extend by adding empty string.

        if len(self.project_version) > 0:
            while len(self.project_version) < len(self.fclname):
                self.project_version.append('')

        # Histogram merging program.

        merge_elements = stage_element.getElementsByTagName('merge')
        if merge_elements:
            self.merge = str(merge_elements[0].firstChild.data)
	
        # Analysis merge flag.

        anamerge_elements = stage_element.getElementsByTagName('anamerge')
        if anamerge_elements:
            self.anamerge = str(anamerge_elements[0].firstChild.data)
	
        # Resource (subelement).

        resource_elements = stage_element.getElementsByTagName('resource')
        if resource_elements:
            self.resource = str(resource_elements[0].firstChild.data)
            self.resource = ''.join(self.resource.split())

        # Lines (subelement).

        lines_elements = stage_element.getElementsByTagName('lines')
        if lines_elements:
            self.lines = str(lines_elements[0].firstChild.data)

        # Site (subelement).

        site_elements = stage_element.getElementsByTagName('site')
        if site_elements:
            self.site = str(site_elements[0].firstChild.data)
            self.site = ''.join(self.site.split())

        # Blacklist (subelement).

        blacklist_elements = stage_element.getElementsByTagName('blacklist')
        if blacklist_elements:
            self.blacklist = str(blacklist_elements[0].firstChild.data)
            self.blacklist = ''.join(self.blacklist.split())

        # Cpu (subelement).

        cpu_elements = stage_element.getElementsByTagName('cpu')
        if cpu_elements:
            self.cpu = int(cpu_elements[0].firstChild.data)

        # Disk (subelement).

        disk_elements = stage_element.getElementsByTagName('disk')
        if disk_elements:
            self.disk = str(disk_elements[0].firstChild.data)
            self.disk = ''.join(self.disk.split())

        # Data file types (subelement).

        datafiletypes_elements = stage_element.getElementsByTagName('datafiletypes')
        if datafiletypes_elements:
            data_file_types_str = str(datafiletypes_elements[0].firstChild.data)
            data_file_types_str = ''.join(data_file_types_str.split())
            self.datafiletypes = data_file_types_str.split(',')

        # Memory (subelement).

        memory_elements = stage_element.getElementsByTagName('memory')
        if memory_elements:
            self.memory = int(memory_elements[0].firstChild.data)

        # Number of threads (subelement).

        thread_counts = stage_element.getElementsByTagName('nthreads')
        if thread_counts:
            self.nthreads = int(thread_counts[0].firstChild.data)

        # Number of schedules (subelement).

        schedule_counts = stage_element.getElementsByTagName('nschedules')
        if schedule_counts:
            self.nschedules = int(schedule_counts[0].firstChild.data)

        # Extra lar arguments (subelement).

        argses = stage_element.getElementsByTagName('args')
        if argses:
            self.args = str(argses[0].firstChild.data).split()

        # Dictionary of metadata parameters (repeatable subelement).

        param_elements = stage_element.getElementsByTagName('parameter')
        if len(param_elements) > 0:
            self.parameters = {}
            for param_element in param_elements:
                name = str(param_element.attributes['name'].firstChild.data)
                value = str(param_element.firstChild.data)
                self.parameters[name] = value

        # Output file name (repeatable subelement).

        output_elements = stage_element.getElementsByTagName('output')
        if len(output_elements) > 0:

            # The output element can occur once at the top level of the <stage> element, or
            # inside a <fcl> element.  The former applies globally.  The latter applies
            # only to that fcl substage.

            # Loop over global output elements.

            for output_element in output_elements:
                parent_element = output_element.parentNode
                if parent_element.nodeName != 'fcl':
                    output = str(output_element.firstChild.data)
                    self.output = []
                    while len(self.output) < len(self.fclname):
                        self.output.append(output)

            # Loop over fcl output elements.

            for output_element in output_elements:
                parent_element = output_element.parentNode
                if parent_element.nodeName == 'fcl':

                    # Match this output name with its parent fcl element.

                    fcl = str(parent_element.firstChild.data).strip()
                    n = self.fclname.index(fcl)

                    # Make sure project_name list is long enough.

                    while len(self.output) < n+1:
                        self.output.append('')

                    # Extract output name and add it to list.

                    output = str(output_element.firstChild.data)
                    self.output[n] = output

        # Make sure that the size of the output list (if present) ia at least as
        # long as the fclname list.
        # If not, extend by adding empty string.

        if len(self.output) > 0:
            while len(self.output) < len(self.fclname):
                self.output.append('')

	# TFileName (subelement).

        TFileName_elements = stage_element.getElementsByTagName('TFileName')
        if TFileName_elements:
            self.TFileName = str(TFileName_elements[0].firstChild.data)

        # Jobsub.

        jobsub_elements = stage_element.getElementsByTagName('jobsub')
        if jobsub_elements:
            self.jobsub = str(jobsub_elements[0].firstChild.data)

        # Jobsub start/stop.

        jobsub_start_elements = stage_element.getElementsByTagName('jobsub_start')
        if jobsub_start_elements:
            self.jobsub_start = str(jobsub_start_elements[0].firstChild.data)

        # Jobsub submit timeout.

        jobsub_timeout_elements = stage_element.getElementsByTagName('jobsub_timeout')
        if jobsub_timeout_elements:
            self.jobsub_timeout = int(jobsub_timeout_elements[0].firstChild.data)

	# Name of art-like executables (repeatable subelement).

        exe_elements = stage_element.getElementsByTagName('exe')
        if len(exe_elements) > 0:

            # The exe element can occur once at the top level of the <stage> element, or
            # inside a <fcl> element.  The former applies globally.  The latter applies
            # only to that fcl substage.

            # Loop over global exe elements.

            for exe_element in exe_elements:
                parent_element = exe_element.parentNode
                if parent_element.nodeName != 'fcl':
                    exe = str(exe_element.firstChild.data)
                    self.exe = []
                    while len(self.exe) < len(self.fclname):
                        self.exe.append(exe)

            # Loop over fcl exe elements.

            for exe_element in exe_elements:
                parent_element = exe_element.parentNode
                if parent_element.nodeName == 'fcl':

                    # Match this exe name with its parent fcl element.

                    fcl = str(parent_element.firstChild.data).strip()
                    n = self.fclname.index(fcl)

                    # Make sure project_name list is long enough.

                    while len(self.exe) < n+1:
                        self.exe.append('')

                    # Extract exe name and add it to list.

                    exe = str(exe_element.firstChild.data)
                    self.exe[n] = exe

        # Make sure that the size of the exe list (if present) ia at least as
        # long as the fclname list.
        # If not, extend by adding empty string.

        if len(self.exe) > 0:
            while len(self.exe) < len(self.fclname):
                self.exe.append('')

        # Sam schema.

        schema_elements = stage_element.getElementsByTagName('schema')
        if schema_elements:
            self.schema = str(schema_elements[0].firstChild.data)

        # Validate-on-worker.

        validate_on_worker_elements = stage_element.getElementsByTagName('check')
        if validate_on_worker_elements:
            self.validate_on_worker = int(validate_on_worker_elements[0].firstChild.data)

        # Upload-on-worker.

        copy_to_fts_elements = stage_element.getElementsByTagName('copy')
        if copy_to_fts_elements:
            self.copy_to_fts = int(copy_to_fts_elements[0].firstChild.data)

	# Cvmfs flag.

        cvmfs_elements = stage_element.getElementsByTagName('cvmfs')
        if cvmfs_elements:
            self.cvmfs = int(cvmfs_elements[0].firstChild.data)

	# Stash flag.

        stash_elements = stage_element.getElementsByTagName('stash')
        if stash_elements:
            self.stash = int(stash_elements[0].firstChild.data)

	# Singularity flag.

        singularity_elements = stage_element.getElementsByTagName('singularity')
        if singularity_elements:
            self.singularity = int(singularity_elements[0].firstChild.data)

	# Batch script

        script_elements = stage_element.getElementsByTagName('script')
        if script_elements:
            self.script = script_elements[0].firstChild.data

        # Make sure batch script exists, and convert into a full path.

        if check:
            script_path = ''
            try:
                jobinfo = subprocess.Popen(['which', self.script],
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
                jobout, joberr = jobinfo.communicate()
                jobout = convert_str(jobout)
                joberr = convert_str(joberr)
                rc = jobinfo.poll()
                script_path = jobout.splitlines()[0].strip()
            except:
                pass
            if script_path == '' or not larbatch_posix.access(script_path, os.X_OK):
                raise IOError('Script %s not found.' % self.script)
            self.script = script_path
	
	# Start script

        start_script_elements = stage_element.getElementsByTagName('startscript')
        if start_script_elements:
            self.start_script = start_script_elements[0].firstChild.data

        # Make sure start project batch script exists, and convert into a full path.

        if check:
            script_path = ''
            try:
                jobinfo = subprocess.Popen(['which', self.start_script],
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
                jobout, joberr = jobinfo.communicate()
                jobout = convert_str(jobout)
                joberr = convert_str(joberr)
                rc = jobinfo.poll()
                script_path = jobout.splitlines()[0].strip()
            except:
                pass
            self.start_script = script_path

        # Stop script

        stop_script_elements = stage_element.getElementsByTagName('stopscript')
        if stop_script_elements:
            self.stop_script = stop_script_elements[0].firstChild.data

        # Make sure stop project batch script exists, and convert into a full path.

        if check:
            script_path = ''
            try:
                jobinfo = subprocess.Popen(['which', self.stop_script],
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
                jobout, joberr = jobinfo.communicate()
                jobout = convert_str(jobout)
                joberr = convert_str(joberr)
                rc = jobinfo.poll()
                script_path = jobout.splitlines()[0].strip()
            except:
                pass
            self.stop_script = script_path

        # Done.

        return
        
    # String conversion.

    def __str__(self):
        result = 'Stage name = %s\n' % self.name
        result = 'Batch job name = %s\n' % self.batchname
        #result += 'Fcl filename = %s\n' % self.fclname
        for fcl in self.fclname:
          result += 'Fcl filename = %s\n' % fcl 
        result += 'Output directory = %s\n' % self.outdir
        result += 'Log directory = %s\n' % self.logdir
        result += 'Work directory = %s\n' % self.workdir
        result += 'Bookkeeping directory = %s\n' % self.bookdir
        result += 'Maximum directory size = %d\n' % self.dirsize
        result += 'Extra directory levels = %d\n' % self.dirlevels
        result += 'Dynamic directories = %d\n' % self.dynamic
        result += 'Input file = %s\n' % self.inputfile
        result += 'Input list = %s\n' % self.inputlist
        result += 'Input mode = %s\n' % self.inputmode
        result += 'Input sam dataset = %s' % self.inputdef
        if self.recur:
            result += ' (recursive)'
        result += '\n'
        result += 'Base sam dataset = %s\n' % self.basedef
        result += 'Analysis flag = %d\n' % self.ana
        result += 'Recursive flag = %d\n' % self.recur
        result += 'Recursive type = %s\n' % self.recurtype
        result += 'Recursive limit = %d\n' % self.recurlimit
        result += 'Single run flag = %d\n' % self.singlerun
        result += 'File list definition flag = %d\n' % self.filelistdef
        result += 'Prestart flag = %d\n' % self.prestart
        result += 'Active projects base name = %s\n' % self.activebase
        result += 'Dropbox waiting interval = %f\n' % self.dropboxwait
        result += 'Prestage fraction = %f\n' % self.prestagefraction
        result += 'Input stream = %s\n' % self.inputstream
        result += 'Previous stage name = %s\n' % self.previousstage
        result += 'Mix input sam dataset = %s\n' % self.mixinputdef
        result += 'Pubs input allowed = %d\n' % self.pubs_input_ok
        result += 'Pubs input mode = %d\n' % self.pubs_input
        result += 'Pubs input run number = %d\n' % self.input_run
        for subrun in self.input_subruns:
            result += 'Pubs input subrun number = %d\n' % subrun
        result += 'Pubs input version number = %d\n' % self.input_version
        result += 'Pubs output mode = %d\n' % self.pubs_output
        result += 'Pubs output run number = %d\n' % self.output_run
        for subrun in self.output_subruns:
            result += 'Pubs output subrun number = %d\n' % subrun
        result += 'Pubs output version number = %d\n' % self.output_version
        result += 'Output file name = %s\n' % self.output
        result += 'TFileName = %s\n' % self.TFileName   
        result += 'Number of jobs = %d\n' % self.num_jobs
        result += 'Number of events = %d\n' % self.num_events
        result += 'Max flux MB = %d\n' % self.maxfluxfilemb
        result += 'Max files per job = %d\n' % self.max_files_per_job
        result += 'Output file target size = %d\n' % self.target_size
        result += 'Dataset definition name = %s\n' % self.defname
        result += 'Analysis dataset definition name = %s\n' % self.ana_defname
        result += 'Data tier = %s\n' % self.data_tier
        result += 'Data stream = %s\n' % self.data_stream
        result += 'Analysis data tier = %s\n' % self.ana_data_tier
        result += 'Analysis data stream = %s\n' % self.ana_data_stream
        result += 'Submit script = %s\n' % self.submit_script
        result += 'Worker initialization script = %s\n' % self.init_script
        result += 'Worker initialization source script = %s\n' % self.init_source
        result += 'Worker end-of-job script = %s\n' % self.end_script
        result += 'Worker midstage source initialization scripts = %s\n' % self.mid_source
        result += 'Worker midstage finalization scripts = %s\n' % self.mid_script
        result += 'Project name overrides = %s\n' % self.project_name
        result += 'Stage name overrides = %s\n' % self.stage_name
        result += 'Project version overrides = %s\n' % self.project_version
        result += 'Special histogram merging program = %s\n' % self.merge
        result += 'Analysis merge flag = %s\n' % self.anamerge
        result += 'Resource = %s\n' % self.resource
        result += 'Lines = %s\n' % self.lines
        result += 'Site = %s\n' % self.site
        result += 'Blacklist = %s\n' % self.blacklist
        result += 'Cpu = %d\n' % self.cpu
        result += 'Disk = %s\n' % self.disk
        result += 'Datafiletypes = %s\n' % self.datafiletypes
        result += 'Memory = %d MB\n' % self.memory
        result += 'Number of threads = %d\n' % self.nthreads
        result += 'Number of schedules = %d\n' % self.nschedules
        result += 'Extra arguments = %s\n' % str(self.args)
        result += 'Metadata parameters:\n'
        for key in self.parameters:
            result += '%s: %s\n' % (key,self.parameters[key])
        result += 'Output file name = %s\n' % self.output
        result += 'TFile name = %s\n' % self.TFileName
        result += 'Jobsub_submit options = %s\n' % self.jobsub
        result += 'Jobsub_submit start/stop options = %s\n' % self.jobsub_start
        result += 'Jobsub submit timeout = %d\n' % self.jobsub_timeout
        result += 'Executables = %s\n' % self.exe
        result += 'Schema = %s\n' % self.schema
        result += 'Validate-on-worker = %d\n' % self.validate_on_worker
        result += 'Upload-on-worker = %d\n' % self.copy_to_fts
        result += 'Cvmfs flag = %d\n' % self.cvmfs
        result += 'Stash cache flag = %d\n' % self.stash
        result += 'Singularity flag = %d\n' % self.singularity
        result += 'Batch script = %s\n' % self.script
        result += 'Start script = %s\n' % self.start_script
        result += 'Stop script = %s\n' % self.stop_script
        return result

    # The purpose of this method is to limit input to the specified run
    # and subruns.  There are several use cases.
    #
    # 1.  If xml element pubsinput is false (0), do not try to limit the 
    #     input in any way.  Just use whatever is the normal input.
    #
    # 2.  If input is from a sam dataset, create a restricted dataset that
    #     is limited to the specified run and subruns.
    #
    # 3.  If input is from a file list (and pubsinput is true), modify the 
    #     input list assuming that the input area has the standard pubs 
    #     diretory structure.  There are several subcases depending on
    #     whether there is one or multiple subruns.
    #
    #     a) Single subrun.  Reset input list to point to an input
    #        list from pubs input directory (assuming input area has
    #        standard pubs structure).  Raise PubsInputError if input
    #        files.list does not exist.
    #
    #     b) Multiple subruns.  Generate a new input list with a
    #        unique name which will get input from the union of the
    #        specified run and subruns input lists (assuming pubs
    #        directory structure).
    #
    #    In each case 2, 3(a), and 3(b), the original stage parameter
    #    num_jobs is ignored.  Instead, num_jobs is recalculated as
    #
    #     num_jobs = (len(subruns) + max_files_per_job - 1) / max_files_per_job
    #
    #     This formula has the feature that if len(subruns) == 1, or
    #     if max_files_per_job is equal to or greater than the number
    #     of suburns (or effectively infinite), then the final
    #     num_jobs paramater will always be one, meaning all input
    #     files will read in a single job.  On the other hand if
    #     max_files_per_job == 1, then num_jobs will be equal to the
    #     number of subruns, so each batch job will process one subrun.
    #
    # 4.  If input is from a singe file (and pubsinput is true), raise
    #     an exception.  This use case doesn't make sense and isn't
    #     supported.
    #
    # 5.  If no input is specified, don't do anything, since there is no
    #     input to limit.

    def pubsify_input(self, run, subruns, version):

        # Don't do anything if pubs input is disabled.

        if not self.pubs_input_ok:
            return

        # It never makes sense to specify pubs input mode if there are no 
        # input files (i.e. generation jobs).  This is not considered an error.

        if self.inputfile == '' and self.inputlist == '' and self.inputdef == '':
            return

        # The case if input from a single file is not supported.  Raise an exception.

        if self.inputfile != '':
            raise RuntimeError('Pubs input for single file input is not supported.')

        # Set pubs input mode.

        self.pubs_input = 1

        # Save the run, subrun, and version numbers.

        self.input_run = run;
        self.input_subruns = subruns;
        self.input_version = version;

        # if input is from a sam dataset, create a restricted dataset that limits
        # input files to selected run and subruns.

        if self.inputdef != '':
            newdef = project_utilities.create_limited_dataset(self.inputdef,
                                                              run,
                                                              subruns)
            if not newdef:
                raise PubsInputError(run, subruns[0], version)                
            self.inputdef = newdef

            # Set the number of submitted jobs assuming each worker will get 
            # self.max_files_per_job files.

            files_per_job = self.max_files_per_job
            if files_per_job == 0:
                files_per_job = 1
            self.num_jobs = (len(subruns) + files_per_job - 1) / files_per_job

            # Done.

            return

        # If we get to here, we have input from a file list and a previous stage
        # exists.  This normally indicates a daisy chain.  This is where subcases
        # 3 (a), (b) are handled.

        # Case 3(a), single subrun.

        if len(subruns) == 1:

            # Insert run and subrun into input file list path.

            if version == None:
                pubs_path = '%d/%d' % (run, subruns[0])
            else:
                pubs_path = '%d/%d/%d' % (version, run, subruns[0])
            dir = os.path.dirname(self.inputlist)
            base = os.path.basename(self.inputlist)
            self.inputlist = os.path.join(dir, pubs_path, base)

            # Verify that the input list exists and is not empty.

            lines = []
            try:
                lines = larbatch_posix.readlines(self.inputlist)
            except:
                lines = []
            if len(lines) == 0:
                raise PubsInputError(run, subruns[0], version)

            # Verify that input files actually exist.

            for line in lines:
                input_file = line.strip()
                if not larbatch_posix.exists(input_file):
                    raise PubsInputError(run, subruns[0], version)

            # Specify that there will be exactly one job submitted.

            self.num_jobs = 1

            # Everything OK (case 3(a)).

            return

        # Case 3(b), multiple subruns.

        if len(subruns) > 1:

            # Generate a new input file list with a unique name and place 
            # it in the same directory as the original input list.  Note that
            # the input list may not actually exist at this point.  If it
            # doesn't exist, just use the original name.  If it already exists,
            # generate a different name.

            dir = os.path.dirname(self.inputlist)
            base = os.path.basename(self.inputlist)
            new_inputlist_path = self.inputlist
            if larbatch_posix.exists(new_inputlist_path):
                new_inputlist_path = '%s/%s_%s.list' % (dir, base, str(uuid.uuid4()))
            self.inputlist = new_inputlist_path

            # Defer opening the new input list file until after the original
            # input file is successfully opened.

            new_inputlist_file = None

            # Loop over subruns.  Read contents of pubs input list for each subrun.

            nsubruns = 0
            total_size = 0
            actual_subruns = []
            truncate = False
            for subrun in subruns:

                if truncate:
                    break

                nsubruns += 1

                if version == None:
                    pubs_path = '%d/%d' % (run, subrun)
                else:
                    pubs_path = '%d/%d/%d' % (version, run, subrun)

                subrun_inputlist = os.path.join(dir, pubs_path, base)
                lines = []
                try:
                    lines = larbatch_posix.readlines(subrun_inputlist)
                except:
                    lines = []
                if len(lines) == 0:
                    raise PubsInputError(run, subruns[0], version)
                for line in lines:
                    subrun_inputfile = line.strip()

                    # Test size and accessibility of this input file.

                    sr_size = -1
                    try:
                        sr = larbatch_posix.stat(subrun_inputfile)
                        sr_size = sr.st_size
                    except:
                        sr_size = -1

                    if sr_size > 0:
                        actual_subruns.append(subrun)
                        if new_inputlist_file == None:
                            print('Generating new input list %s\n' % new_inputlist_path)
                            new_inputlist_file = larbatch_posix.open(new_inputlist_path, 'w')
                        new_inputlist_file.write('%s\n' % subrun_inputfile)
                        total_size += sr.st_size

                    # If at this point the total size exceeds the target size,
                    # truncate the list of subruns and break out of the loop.

                    if self.max_files_per_job > 1 and self.target_size != 0 \
                            and total_size >= self.target_size:
                        truncate = True
                        break

            # Done looping over subruns.

            new_inputlist_file.close()

            # Raise an exception if the actual list of subruns is empty.

            if len(actual_subruns) == 0:
                raise PubsInputError(run, subruns[0], version)

            # Update the list of subruns to be the actual list of subruns.

            if len(actual_subruns) != len(subruns):
                print('Truncating subrun list: %s' % str(actual_subruns))
                del subruns[:]
                subruns.extend(actual_subruns)

            # Set the number of submitted jobs assuming each worker will get 
            # self.max_files_per_job files.

            files_per_job = self.max_files_per_job
            if files_per_job == 0:
                files_per_job = 1
            self.num_jobs = (len(subruns) + files_per_job - 1) / files_per_job

            # Everything OK (case 3(b)).

            return

        # Shouldn't ever fall out of loop.

        return


    # Function to convert this stage for pubs output.

    def pubsify_output(self, run, subruns, version):

        # Set pubs mode.

        self.pubs_output = 1

        # Save the run, subrun, and version numbers.

        self.output_run = run;
        self.output_subruns = subruns;
        self.output_version = version;

        # Append run and subrun to workdir, outdir, logdir, and bookdir.
        # In case of multiple subruns, encode the subdir directory as "@s",
        # which informs the batch worker to determine the subrun dynamically.

        if len(subruns) == 1:
            if version == None:
                pubs_path = '%d/%d' % (run, subruns[0])
            else:
                pubs_path = '%d/%d/%d' % (version, run, subruns[0])
            self.workdir = os.path.join(self.workdir, pubs_path)
        else:
            if version == None:
                pubs_path = '%d/@s' % run
            else:
                pubs_path = '%d/%d/@s' % (version, run)
            self.workdir = os.path.join(self.workdir, str(uuid.uuid4()))
            self.dynamic = 1
        self.outdir = os.path.join(self.outdir, pubs_path)
        self.logdir = os.path.join(self.logdir, pubs_path)
        self.bookdir = os.path.join(self.bookdir, pubs_path)

    # Run presubmission check script, if any.
    # Dump output and return exit status.
    # A nonzero exit status generally means that jobs shouldn't be submitted.

    def checksubmit(self):

        rc = 0
        if len(self.submit_script) > 0:
            print('Running presubmission check script', end=' ')
            for word in self.submit_script:
                print(word, end=' ')
            print()
            jobinfo = subprocess.Popen(self.submit_script,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            q = queue.Queue()
            thread = threading.Thread(target=larbatch_utilities.wait_for_subprocess,
                                      args=[jobinfo, q])
            thread.start()
            thread.join(timeout=60)
            if thread.is_alive():
                print('Submit script timed out, terminating.')
                jobinfo.terminate()
                thread.join()
            rc = q.get()
            jobout = convert_str(q.get())
            joberr = convert_str(q.get())
            print('Script exit status = %d' % rc)
            print('Script standard output:')
            print(jobout)
            print('Script diagnostic output:')
            print(joberr)

        # Done.
        # Return exit status.

        return rc


    # Raise an exception if any specified input file/list doesn't exist.
    # (We don't currently check sam input datasets).

    def checkinput(self, checkdef=False):

        if self.inputfile != '' and not larbatch_posix.exists(self.inputfile):
            raise IOError('Input file %s does not exist.' % self.inputfile)
        if self.inputlist != '' and not larbatch_posix.exists(self.inputlist):
            raise IOError('Input list %s does not exist.' % self.inputlist)

        checkok = False

        # Define or update the active projects dataset, if requested.

        if self.activebase != '':
            activedef = '%s_active' % self.activebase
            waitdef = '%s_wait' % self.activebase
            project_utilities.make_active_project_dataset(self.activebase,
                                                          self.dropboxwait,
                                                          activedef,
                                                          waitdef)

        # If target size is nonzero, and input is from a file list, calculate
        # the ideal number of output jobs and override the current number 
        # of jobs.

        if self.target_size != 0 and self.inputlist != '':
            input_filenames = larbatch_posix.readlines(self.inputlist)
            size_tot = 0
            for line in input_filenames:
                filename = line.split()[0]
                filesize = larbatch_posix.stat(filename).st_size
                size_tot = size_tot + filesize
            new_num_jobs = size_tot / self.target_size
            if new_num_jobs < 1:
                new_num_jobs = 1
            if new_num_jobs > self.num_jobs:
                new_num_jobs = self.num_jobs
            print("Ideal number of jobs based on target file size is %d." % new_num_jobs)
            if new_num_jobs != self.num_jobs:
                print("Updating number of jobs from %d to %d." % (self.num_jobs, new_num_jobs))
                self.num_jobs = new_num_jobs

        # If singlerun mode is requested, pick a random file from the input
        # dataset and create (if necessary) a new dataset definition which
        # limits files to be only from that run.  Don't do anything here if 
        # the input dataset is empty.

        if self.singlerun and checkdef:

            samweb = project_utilities.samweb()
            print("Doing single run processing.")

            # First find an input file.

            #dim = 'defname: %s with limit 1' % self.inputdef
            dim = 'defname: %s' % self.inputdef
            if self.filelistdef:
                input_files = list(project_utilities.listFiles(dim))
            else:
                input_files = samweb.listFiles(dimensions=dim)
            if len(input_files) > 0:
                random_file = random.choice(input_files)
                print('Example file: %s' % random_file)

                # Extract run number.

                md = samweb.getMetadata(random_file)
                run_tuples = md['runs']
                if len(run_tuples) > 0:
                    run = run_tuples[0][0]
                    print('Input files will be limited to run %d.' % run)

                    # Make a new dataset definition.
                    # If this definition already exists, assume it is correct.

                    newdef = '%s_run_%d' % (samweb.makeProjectName(self.inputdef), run)
                    def_exists = False
                    try:
                        desc = samweb.descDefinition(defname=newdef)
                        def_exists = True
                    except samweb_cli.exceptions.DefinitionNotFound:
                        pass
                    if not def_exists:
                        print('Creating dataset definition %s' % newdef)
                        newdim = 'defname: %s and run_number %d' % (self.inputdef, run)
                        samweb.createDefinition(defname=newdef, dims=newdim)
                    self.inputdef = newdef

                else:
                    print('Problem extracting run number from example file.')
                    return 1

            else:
                print('Input dataset is empty.')
                return 1

        # If target size is nonzero, and input is from a sam dataset definition,
        # and maxfilesperjob is not one, calculate the ideal number of jobs and
        # maxfilesperjob.

        if self.target_size != 0 and self.max_files_per_job != 1 and self.inputdef != '':

            # Query sam to determine size and number of files in input
            # dataset.

            samweb = project_utilities.samweb()
            dim = 'defname: %s' % self.inputdef
            nfiles = 0
            files = []
            if self.filelistdef:
                files = project_utilities.listFiles(dim)
                nfiles = len(files)
            else:
                sum = samweb.listFilesSummary(dimensions=dim)
                nfiles = sum['file_count']
            print('Input dataset %s has %d files.' % (self.inputdef, nfiles))
            if nfiles > 0:
                checkok = True
                max_files = self.max_files_per_job * self.num_jobs
                size_tot = 0
                if max_files > 0 and max_files < nfiles:
                    if self.filelistdef:
                        while len(files) > max_files:
                            files.pop()
                        dim = 'defname: %s' % project_utilities.makeFileListDefinition(files)
                    else:
                        dim += ' with limit %d' % max_files
                    sum = samweb.listFilesSummary(dimensions=dim)
                    size_tot = sum['total_file_size']
                    nfiles = sum['file_count']
                else:
                    if self.filelistdef:
                        dim = 'defname: %s' % project_utilities.makeFileListDefinition(files)
                    sum = samweb.listFilesSummary(dimensions=dim)
                    size_tot = sum['total_file_size']
                    nfiles = sum['file_count']

                # Calculate updated job parameters.

                new_num_jobs = int(math.ceil(float(size_tot) / float(self.target_size)))
                if new_num_jobs < 1:
                    new_num_jobs = 1
                if new_num_jobs > self.num_jobs:
                    new_num_jobs = self.num_jobs

                new_max_files_per_job = int(math.ceil(float(self.target_size) * float(nfiles) / float(size_tot)))
                if self.max_files_per_job > 0 and new_max_files_per_job > self.max_files_per_job:
                    new_max_files_per_job = self.max_files_per_job
                    new_num_jobs = (nfiles + self.max_files_per_job - 1) / self.max_files_per_job
                    if new_num_jobs < 1:
                        new_num_jobs = 1
                    if new_num_jobs > self.num_jobs:
                        new_num_jobs = self.num_jobs

                print("Ideal number of jobs based on target file size is %d." % new_num_jobs)
                if new_num_jobs != self.num_jobs:
                    print("Updating number of jobs from %d to %d." % (self.num_jobs, new_num_jobs))
                    self.num_jobs = new_num_jobs
                print("Ideal number of files per job is %d." % new_max_files_per_job)
                if new_max_files_per_job != self.max_files_per_job:
                    print("Updating maximum files per job from %d to %d." % (
                        self.max_files_per_job, new_max_files_per_job))
                    self.max_files_per_job = new_max_files_per_job
            else:
                print('Input dataset is empty.')
                return 1

        # If requested, do a final check in the input dataset.
        # Limit the number of jobs to be not more than the number of files, since
        # it never makes sense to have more jobs than that.
        # If the number of input files is zero, return an error.

        if self.inputdef != '' and checkdef and not checkok:
            samweb = project_utilities.samweb()
            n = 0
            if self.filelistdef:
                files = project_utilities.listFiles('defname: %s' % self.inputdef)
                n = len(files)
            else:
                sum = samweb.listFilesSummary(defname=self.inputdef)
                n = sum['file_count']
            print('Input dataset %s contains %d files.' % (self.inputdef, n))
            if n < self.num_jobs:
                self.num_jobs = n
            if n == 0:
                return 1

        # Done (all good).

        return 0


    # Raise an exception if output directory or log directory doesn't exist.

    def check_output_dirs(self):
        if not larbatch_posix.exists(self.outdir):
            raise IOError('Output directory %s does not exist.' % self.outdir)
        if not larbatch_posix.exists(self.logdir):
            raise IOError('Log directory %s does not exist.' % self.logdir)
        return
    
    # Raise an exception if output, log, work, or bookkeeping directory doesn't exist.

    def checkdirs(self):
        if not larbatch_posix.exists(self.outdir):
            raise IOError('Output directory %s does not exist.' % self.outdir)
        if self.logdir != self.outdir and not larbatch_posix.exists(self.logdir):
            raise IOError('Log directory %s does not exist.' % self.logdir)
        if not larbatch_posix.exists(self.workdir):
            raise IOError('Work directory %s does not exist.' % self.workdir)
        if self.bookdir != self.logdir and not larbatch_posix.exists(self.bookdir):
            raise IOError('Bookkeeping directory %s does not exist.' % self.bookdir)
        return
    
    # Make output, log, work, and bookkeeping directory, if they don't exist.

    def makedirs(self):
        if not larbatch_posix.exists(self.outdir):
            larbatch_posix.makedirs(self.outdir)
        if self.logdir != self.outdir and not larbatch_posix.exists(self.logdir):
            larbatch_posix.makedirs(self.logdir)
        if not larbatch_posix.exists(self.workdir):
            larbatch_posix.makedirs(self.workdir)
        if self.bookdir != self.logdir and not larbatch_posix.exists(self.bookdir):
            larbatch_posix.makedirs(self.bookdir)

        # If output is on dcache, make output directory group-writable.

        if self.outdir[0:6] == '/pnfs/':
            mode = stat.S_IMODE(larbatch_posix.stat(self.outdir).st_mode)
            if not mode & stat.S_IWGRP:
                mode = mode | stat.S_IWGRP
                larbatch_posix.chmod(self.outdir, mode)
        if self.logdir[0:6] == '/pnfs/':
            mode = stat.S_IMODE(larbatch_posix.stat(self.logdir).st_mode)
            if not mode & stat.S_IWGRP:
                mode = mode | stat.S_IWGRP
                larbatch_posix.chmod(self.logdir, mode)

        self.checkdirs()
        return
