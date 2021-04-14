#! /usr/bin/env python
######################################################################
#
# Name: projectview.py
#
# Purpose: Python class ProjectView is a widget for displaying 
#          information about projects.
#
# Created: 21-Jan-2015  Herbert Greenlee
#
######################################################################

from __future__ import absolute_import
from __future__ import print_function

# Import GUI stuff

try:
    import tkinter as tk
    import tkinter.messagebox as tkinter_messagebox
except ImportError:
    import Tkinter as tk
    import tkMessageBox as tkinter_messagebox

from project_gui_modules.statusview import ProjectStatusView
from project_gui_modules.textwindow import TextWindow

# Project widget class

class ProjectView(tk.Frame):

    # Constructor.

    def __init__(self, parent, project_name=None, xml_path=None, project_defs=[]):

        self.parent = parent

        # Register our outermost frame in the parent window.

        tk.Frame.__init__(self, self.parent)
        self.pack(expand=1, fill=tk.BOTH)

        # Make widgets that belong to this widget.

        self.make_widgets()
        self.set_project(project_name, xml_path, project_defs)

    # Make widgets.

    def make_widgets(self):

        # Add a frame for information labels.

        self.infoframe = tk.Frame(self, relief=tk.FLAT, bg='aliceblue')
        self.infoframe.pack(side=tk.TOP, fill=tk.X)
        self.infoframe.columnconfigure(1, weight=1)

        # Add a label in info frame which will display the current project xml file path.

        self.pathlabel = tk.Label(self.infoframe, relief=tk.FLAT, bg='aliceblue', text='XML Path:')
        self.pathlabel.grid(row=0, column=0)
        self.path = tk.Label(self.infoframe, relief=tk.SUNKEN, bg='white')
        self.path.grid(row=0, column=1, sticky=tk.E+tk.W)

        # Add a label in info frame which will display the current project name.

        self.projectlabel = tk.Label(self.infoframe, relief=tk.FLAT, bg='aliceblue', 
                                     text='Project:')
        self.projectlabel.grid(row=1, column=0)
        self.projectname = tk.Label(self.infoframe, relief=tk.SUNKEN, bg='white')
        self.projectname.grid(row=1, column=1, sticky=tk.E+tk.W)

        # Add a project status view.

        self.ps = ProjectStatusView(self)
        self.ps.pack(side=tk.BOTTOM, expand=1, fill=tk.BOTH)

    # Select the project.

    def set_project(self, project_name, xml_path, project_defs):
        self.path['text'] = xml_path
        self.projectname['text'] = project_name
        if len(project_defs) > 0:
            self.ps.set_project(project_defs)

    # Make a top level window for displaying xml.

    def make_xml_window(self):

        xml_path = self.path['text']
        if xml_path == None or xml_path == '':
            tkinter_messagebox.showerror('', 'No xml file specified.')
            return

        # Get text of xml file.

        f = open(xml_path)
        if not f:
            tkinter_messagebox.showerror('', 'Error opening xml file %s.' % xml_path)
            return
        xmltext = f.read()

        # Make a new top level window to hold xml text.
        # After we are done making this window, we don't keep track
        # of it any more.  It is owned by window manager.

        w = TextWindow()
        w.append(xmltext)

    # Update status view.

    def update_status(self):
        self.ps.update_status()

    # Update bach jobs.

    def update_jobs(self):
        self.ps.update_jobs()

    # Highlight stage.

    def highlight_stage(self, stagename):
        self.ps.highlight_stage(stagename)
