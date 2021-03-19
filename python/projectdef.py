#! /usr/bin/env python
######################################################################
#
# Name: projectdef.py
#
# Purpose: Python class ProjectDef (used by project.py script).
#
# Created: 12-Dec-2014  Herbert Greenlee
#
######################################################################

from __future__ import absolute_import
from __future__ import print_function
import sys, os, subprocess
from project_modules.xmlerror import XMLError
from project_modules.stagedef import StageDef
import larbatch_posix
from larbatch_utilities import convert_str
from larbatch_utilities import get_ups_products

# Project definition class contains data parsed from project defition xml file.

class ProjectDef:

    # Constructor.
    # project_element argument can be an xml element or None.

    def __init__(self, project_element, default_first_input_list, default_input_lists, check=True):

        # Assign default values.
        
        self.name= ''                     # Project name.
        self.num_events = 0               # Total events (all jobs).
        self.num_jobs = 1                 # Number of jobs.
        self.max_files_per_job = 0        # Max number of files per job.
        self.ups = []                     # Top level ups products.
        self.os = ''                      # Batch OS.
        self.resource = 'DEDICATED,OPPORTUNISTIC' # Jobsub resources.
        self.role = ''                    # Role (normally Analysis or Production).
        self.lines = ''                   # Arbitrary condor commands.
        self.server = '-'                 # Jobsub server.
        self.site = ''                    # Site.
        self.blacklist = ''               # Blacklist.
        self.cpu = 0                      # Number of cpus.
        self.disk = ''                    # Disk space (string value+unit).
        self.memory = 0                   # Amount of memory (integer MB).
        self.merge = 'hadd -T'            # histogram merging program.
        self.anamerge = ''                # Analysis merge flag.
        self.release_tag = ''             # Larsoft release tag.
        self.release_qual = 'debug'       # Larsoft release qualifier.
        self.version = ''                 # Project version.
        self.local_release_dir = ''       # Larsoft local release directory.
        self.local_release_tar = ''       # Larsoft local release tarball.
        self.file_type = ''               # Sam file type.
        self.run_type = ''                # Sam run type.
        self.run_number = 0               # Sam run number.
        self.script = 'condor_lar.sh'     # Batch script.
        self.validate_on_worker = 0   # Run post-job validation on the worker node
        self.copy_to_fts = 0          # Copy a copy of the file to a dropbox scanned by fts. Note that a copy is still sent to <outdir>
        self.cvmfs = 1                    # Cvmfs flag.
        self.stash = 1                    # Stash cache flag.
        self.singularity = 1              # Singularity flag.
        self.start_script = 'condor_start_project.sh'  # Sam start project script.
        self.stop_script = 'condor_stop_project.sh'    # Sam stop project script.
        self.force_dag = 0                # Force dag for sam input jobs.
        self.fclpath = []                 # Fcl search path.
        self.stages = []                  # List of stages (StageDef objects).
        self.parameters = {}              # Dictionary of metadata parameters.

        # Extract values from xml.

        # Project name (attribute)

        if 'name' in dict(project_element.attributes):
            self.name = str(project_element.attributes['name'].firstChild.data)
        if self.name == '':
            raise XMLError('Project name not specified.')

        # Total events (subelement).

        num_events_elements = project_element.getElementsByTagName('numevents')
        for num_events_element in num_events_elements:
            if num_events_element.parentNode == project_element:
                self.num_events = int(num_events_element.firstChild.data)
        if self.num_events == 0:
            raise XMLError('Number of events not specified.')

        # Number of jobs (subelement).

        num_jobs_elements = project_element.getElementsByTagName('numjobs')
        for num_jobs_element in num_jobs_elements:
            if num_jobs_element.parentNode == project_element:
                self.num_jobs = int(num_jobs_element.firstChild.data)

        # Max Number of files per jobs.

        max_files_per_job_elements = project_element.getElementsByTagName('maxfilesperjob')
        for max_files_per_job_element in max_files_per_job_elements:
            if max_files_per_job_element.parentNode == project_element:
                self.max_files_per_job = int(max_files_per_job_element.firstChild.data)

        # Top level ups product (repeatable subelement).

        ups_elements = project_element.getElementsByTagName('ups')
        for ups_element in ups_elements:
            self.ups.append(str(ups_element.firstChild.data))

        # If ups products list is empty, set default.

        if len(self.ups) == 0:
            self.ups = get_ups_products().split(',')

        # OS (subelement).

        os_elements = project_element.getElementsByTagName('os')
        for os_element in os_elements:
            if os_element.parentNode == project_element:
                self.os = str(os_element.firstChild.data)
                self.os = ''.join(self.os.split())

        # Resource (subelement).

        resource_elements = project_element.getElementsByTagName('resource')
        for resource_element in resource_elements:
            if resource_element.parentNode == project_element:
                self.resource = str(resource_element.firstChild.data)
                self.resource = ''.join(self.resource.split())

        # Role (subelement).

        role_elements = project_element.getElementsByTagName('role')
        for role_element in role_elements:
            if role_element.parentNode == project_element:
                self.role = str(role_element.firstChild.data)

        # Lines (subelement).

        lines_elements = project_element.getElementsByTagName('lines')
        for lines_element in lines_elements:
            if lines_element.parentNode == project_element:
                self.lines = str(lines_element.firstChild.data)

        # Server (subelement).

        server_elements = project_element.getElementsByTagName('server')
        for server_element in server_elements:
            if server_element.parentNode == project_element:
                self.server = str(server_element.firstChild.data)

        # Site (subelement).

        site_elements = project_element.getElementsByTagName('site')
        for site_element in site_elements:
            if site_element.parentNode == project_element:
                self.site = str(site_element.firstChild.data)
                self.site = ''.join(self.site.split())

        # Blacklist (subelement).

        blacklist_elements = project_element.getElementsByTagName('blacklist')
        for blacklist_element in blacklist_elements:
            if blacklist_element.parentNode == project_element:
                self.blacklist = str(blacklist_element.firstChild.data)
                self.blacklist = ''.join(self.blacklist.split())

        # Cpu (subelement).

        cpu_elements = project_element.getElementsByTagName('cpu')
        for cpu_element in cpu_elements:
            if cpu_element.parentNode == project_element:
                self.cpu = int(cpu_element.firstChild.data)

        # Disk (subelement).

        disk_elements = project_element.getElementsByTagName('disk')
        for disk_element in disk_elements:
            if disk_element.parentNode == project_element:
                self.disk = str(disk_element.firstChild.data)
                self.disk = ''.join(self.disk.split())

        # Memory (subelement).

        memory_elements = project_element.getElementsByTagName('memory')
        for memory_element in memory_elements:
            if memory_element.parentNode == project_element:
                self.memory = int(memory_element.firstChild.data)

        # merge (subelement).
        
        merge_elements = project_element.getElementsByTagName('merge')
        for merge_element in merge_elements:
            if merge_element.parentNode == project_element:
                if merge_element.firstChild:
                    self.merge = str(merge_element.firstChild.data)
                else:
                    self.merge = ''

        # anamerge (subelement).

        anamerge_elements = project_element.getElementsByTagName('anamerge')
        for anamerge_element in anamerge_elements:
            if anamerge_element.parentNode == project_element:
                if anamerge_element.firstChild:
                    self.anamerge = str(anamerge_element.firstChild.data)
                else:
                    self.anamerge = ''

        # Larsoft (subelement).

        larsoft_elements = project_element.getElementsByTagName('larsoft')
        if larsoft_elements:

            # Release tag (subelement).

            tag_elements = larsoft_elements[0].getElementsByTagName('tag')
            if tag_elements and tag_elements[0].firstChild != None:
                self.release_tag = str(tag_elements[0].firstChild.data)

            # Release qualifier (subelement).

            qual_elements = larsoft_elements[0].getElementsByTagName('qual')
            if qual_elements:
                self.release_qual = str(qual_elements[0].firstChild.data)

            # Local release directory or tarball (subelement).
            # 

            local_elements = larsoft_elements[0].getElementsByTagName('local')
            if local_elements:
                local = str(local_elements[0].firstChild.data)
                if larbatch_posix.isdir(local):
                    self.local_release_dir = local
                else:
                    self.local_release_tar = local

        # Version (subelement).

        version_elements = project_element.getElementsByTagName('version')
        if version_elements:
            self.version = str(version_elements[0].firstChild.data)
        else:
            self.version = self.release_tag

        # Make sure local test release directory/tarball exists, if specified.
        # Existence of non-null local_release_dir has already been tested.

        if check and self.local_release_tar != '' and not larbatch_posix.exists(self.local_release_tar):
            raise IOError("Local release directory/tarball %s does not exist." % self.local_release_tar)
            
        # Sam file type (subelement).

        file_type_elements = project_element.getElementsByTagName('filetype')
        if file_type_elements:
            self.file_type = str(file_type_elements[0].firstChild.data)

        # Sam run type (subelement).

        run_type_elements = project_element.getElementsByTagName('runtype')
        if run_type_elements:
            self.run_type = str(run_type_elements[0].firstChild.data)

        # Sam run number (subelement).

        run_number_elements = project_element.getElementsByTagName('runnumber')
        if run_number_elements:
            self.run_number = int(run_number_elements[0].firstChild.data)

        # Batch script (subelement).

        script_elements = project_element.getElementsByTagName('script')
        for script_element in script_elements:
            if script_element.parentNode == project_element:
                self.script = str(script_element.firstChild.data)

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

        # Validate-on-worker flag (subelement).

        worker_validations = project_element.getElementsByTagName('check')
        for worker_validation in worker_validations:
            if worker_validation.parentNode == project_element:
                self.validate_on_worker = int(worker_validation.firstChild.data)

        # Copy to FTS flag (subelement).

        worker_copys = project_element.getElementsByTagName('copy')
        for worker_copy in worker_copys:
            if worker_copy.parentNode == project_element:
                self.copy_to_fts = int(worker_copy.firstChild.data)    

        # Cvmfs flag (subelement).
	
	cvmfs_elements = project_element.getElementsByTagName('cvmfs')
        for cvmfs_element in cvmfs_elements:
            if cvmfs_element.parentNode == project_element:
                self.cvmfs = int(cvmfs_element.firstChild.data)    

        # Stash flag (subelement).
	
	stash_elements = project_element.getElementsByTagName('stash')
        for stash_element in stash_elements:
            if stash_element.parentNode == project_element:
                self.stash = int(stash_element.firstChild.data)    

        # Singularity flag (subelement).
	
	singularity_elements = project_element.getElementsByTagName('singularity')
        for singularity_element in singularity_elements:
            if singularity_element.parentNode == project_element:
                self.singularity = int(singularity_element.firstChild.data)    

        # Start project batch script (subelement).
        
        start_script_elements = project_element.getElementsByTagName('startscript')
        for start_script_element in start_script_elements:
            if start_script_element.parentNode == project_element:
                self.start_script = str(start_script_element.firstChild.data)
                self.force_dag = 1

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

        # Stop project batch script (subelement).
        
        stop_script_elements = project_element.getElementsByTagName('stopscript')
        for stop_script_element in stop_script_elements:
            if stop_script_element.parentNode == project_element:
                self.stop_script = str(stop_script_element.firstChild.data)
                self.force_dag = 1

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

        # Fcl search path (repeatable subelement).

        fclpath_elements = project_element.getElementsByTagName('fcldir')
        for fclpath_element in fclpath_elements:
            self.fclpath.append(str(fclpath_element.firstChild.data))

        # Add $FHICL_FILE_PATH.

        if check and 'FHICL_FILE_PATH' in os.environ:
            for fcldir in os.environ['FHICL_FILE_PATH'].split(':'):
                if larbatch_posix.exists(fcldir):
                    self.fclpath.append(fcldir)

        # Make sure all directories of fcl search path exist.

        if check:
            for fcldir in self.fclpath:
                if not larbatch_posix.exists(fcldir):
                    raise IOError("Fcl search directory %s does not exist." % fcldir)

        # Project stages (repeatable subelement).

        stage_elements = project_element.getElementsByTagName('stage')
        default_previous_stage = ''
        default_input_lists[default_previous_stage] = default_first_input_list
        for stage_element in stage_elements:

            # Get base stage, if any.

            base_stage = None
            if 'base' in dict(stage_element.attributes):
                base_name = str(stage_element.attributes['base'].firstChild.data)
                if base_name != '':
                    for stage in self.stages:
                        if stage.name == base_name:
                            base_stage = stage
                            break

                    if base_stage == None:
                        raise LookupError('Base stage %s not found.' % base_name)

            self.stages.append(StageDef(stage_element, 
                                        base_stage, 
                                        default_input_lists,
                                        default_previous_stage,
                                        self.num_jobs,
                                        self.num_events,
                                        self.max_files_per_job,
                                        self.merge,
                                        self.anamerge,
                                        self.cpu,
                                        self.disk,
                                        self.memory,
                                        self.validate_on_worker,
                                        self.copy_to_fts,
                                        self.cvmfs,
                                        self.stash,
                                        self.singularity,
                                        self.script,
                                        self.start_script,
                                        self.stop_script,
                                        self.site,
                                        self.blacklist,
                                        check=check))
            default_previous_stage = self.stages[-1].name
            default_input_lists[default_previous_stage] = os.path.join(self.stages[-1].bookdir,
                                                                       'files.list')

        # Dictionary of metadata parameters

        param_elements = project_element.getElementsByTagName('parameter')
        for param_element in param_elements:
            name = str(param_element.attributes['name'].firstChild.data)
            value = str(param_element.firstChild.data)
            self.parameters[name] = value

        # Done.
                
        return

    # String conversion.

    def __str__(self):
        result = 'Project name = %s\n' % self.name
        result += 'Total events = %d\n' % self.num_events
        result += 'Number of jobs = %d\n' % self.num_jobs
        result += 'Max files per job = %d\n' % self.max_files_per_job
        result += 'Top level ups products:\n'
        for prod in self.ups:
            result += '    %s\n' % prod
        result += 'OS = %s\n' % self.os
        result += 'Resource = %s\n' % self.resource
        result += 'Role = %s\n' % self.role
        result += 'Lines = %s\n' % self.lines
        result += 'Jobsub server = %s\n' % self.server
        result += 'Site = %s\n' % self.site
        result += 'Blacklist = %s\n' % self.blacklist
        result += 'Cpu = %d\n' % self.cpu
        result += 'Disk = %s\n' % self.disk
        result += 'Memory = %d MB\n' % self.memory
        result += 'Histogram merging program = %s\n' % self.merge
        result += 'Analysis merge flag = %s\n' % self.anamerge
        result += 'Larsoft release tag = %s\n' % self.release_tag
        result += 'Larsoft release qualifier = %s\n' % self.release_qual
        result += 'Version = %s\n' % self.version
        result += 'Local test release directory = %s\n' % self.local_release_dir
        result += 'Local test release tarball = %s\n' % self.local_release_tar
        result += 'File type = %s\n' % self.file_type
        result += 'Run type = %s\n' % self.run_type
        result += 'Run number = %d\n' % self.run_number
        result += 'Batch script = %s\n' % self.script
        result += 'Start sam project script = %s\n' % self.start_script
        result += 'Stop sam project script = %s\n' % self.stop_script
        result += 'Force dag = %d\n' % self.force_dag
        result += 'Fcl search path:\n'
        for fcldir in self.fclpath:
            result += '    %s\n' % fcldir
        result += 'Metadata parameters:\n'
        for key in self.parameters:
            result += '%s: %s\n' % (key,self.parameters[key])
        result += '\nStages:'
        for stage in self.stages:
            result += '\n\n' + str(stage)
        return result

    # Get the specified stage.

    def get_stage(self, stagename):

        if len(self.stages) == 0:
            raise LookupError("Project does not have any stages.")

        elif stagename == '' and len(self.stages) == 1:
            return self.stages[0]

        else:
            for stage in self.stages:
                if stagename == stage.name:
                    return stage

        # If we fell through to here, we didn't find an appropriate stage.

        raise RuntimeError('No stage %s.' % stagename)

    # Find fcl file on fcl search path.

    def get_fcl(self, fclname):
        
        fcl_list = []
        for name in fclname:
         fcl = ''
         for fcldir in self.fclpath:
            fcl = os.path.join(fcldir, name)
            #print fcl
            if larbatch_posix.exists(fcl):
                break
         
         if fcl == '' or not larbatch_posix.exists(fcl):
             raise IOError('Could not find fcl file %s.' % name)
         fcl_list.append(fcl)      
        return fcl_list
