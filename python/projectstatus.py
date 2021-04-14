#! /usr/bin/env python
######################################################################
#
# Name: projectstatus.py
#
# Purpose: Python class ProjectStatus (used by project.py script).
#          This class contains information about project status.
#
# Created: 12-Dec-2014  Herbert Greenlee
#
######################################################################

from __future__ import absolute_import
from __future__ import print_function
from project_modules.stagestatus import StageStatus

# Project status class.

class ProjectStatus:

    # Constructor.

    def __init__(self, projects):

        # Initialize attributes.

        self.projects = projects
        self.stats = {}
        for project in projects:
            for stage in project.stages:
                self.stats[stage.name] = StageStatus(stage)

    # Update data for the specified project.

    def update(self):

        # Update all stages.

        for stagename in list(self.stats.keys()):
            self.stats[stagename].update()

    # Get stage status for specified stage.

    def get_stage_status(self, stagename):
        return self.stats[stagename]
