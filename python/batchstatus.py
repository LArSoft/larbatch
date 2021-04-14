#! /usr/bin/env python
######################################################################
#
# Name: batchstatus.py
#
# Purpose: Python class BatchStatus (used by project.py script).
#          This class contains information about batch system status
#          corresponding to the specified project.
#
# Created: 12-Dec-2014  Herbert Greenlee
#
######################################################################

from __future__ import absolute_import
from __future__ import print_function
import sys
import project_utilities
import subprocess
from project_modules.jobsuberror import JobsubError
from larbatch_utilities import convert_str

# Cache jobs list independent of project.

jobs = None

# Cache jobsub server.

server = None

# Batch status class.

class BatchStatus:

    # Constructor.

    def __init__(self, projects):

        # Initialize attributes.

        self.projects = projects

        # The status for each stage is a 4-tuple of integers consisting
        # of the following values.
        # 1. Number of idle batch jobs (state 'I')
        # 2. Number of running batch jobs (state 'R')
        # 3. Number of held batch jobs (state 'H')
        # 4. Number of batch jobs in any other stage.

        self.stage_stats = {}
        self.update(projects)
        

    # Update data for the specified project.

    def update(self, projects):

        global jobs, server

        for project in projects:
            if project.server != '-' and project.server != '':
                server = project.server
            for stage in project.stages:
                self.stage_stats[stage.name] = [0, 0, 0, 0]

        # Get information from the batch system.

        if jobs == None:
            BatchStatus.update_jobs()
        for job in jobs:
            words = job.split()
            if len(words) > 4:
                state = words[-4]
                script = words[-1]

                # Loop over stages.

                for project in projects:
                    for stage in project.stages:
                        workscript = '%s-%s-%s.sh' % (stage.name, project.name, project.release_tag)
                        if script.find(workscript) == 0:
                            if state == 'I':
                                self.stage_stats[stage.name][0] = \
                                self.stage_stats[stage.name][0] + 1
                            elif state == 'R':
                                self.stage_stats[stage.name][1] = \
                                self.stage_stats[stage.name][1] + 1
                            elif state == 'H':
                                self.stage_stats[stage.name][2] = \
                                self.stage_stats[stage.name][2] + 1
                            else:
                                self.stage_stats[stage.name][3] = \
                                self.stage_stats[stage.name][3] + 1

    # Update jobs list.

    @staticmethod
    def update_jobs():

        global jobs, server

        command = ['jobsub_q']
        if server != None:
            command.append('--jobsub-server=%s' % server)
        command.append('--group=%s' % project_utilities.get_experiment())
        command.append('--user=%s' % project_utilities.get_user())
        command.append('--role=%s' % project_utilities.get_role())
        jobinfo = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        jobout, joberr = jobinfo.communicate()
        jobout = convert_str(jobout)
        joberr = convert_str(joberr)
        rc = jobinfo.poll()
        if rc != 0:
            #raise JobsubError(command, rc, jobout, joberr)
            # Simply return in case jobsub_q fails.
            return
        jobs = jobout.split('\n')

    # Return jobs list.

    @staticmethod
    def get_jobs():

        global jobs
        return jobs    

    # Get stage status for specified stage.
    # Returns 4-tuple (# idle, # running, # held, # other).

    def get_stage_status(self, stagename):
        return self.stage_stats[stagename]
