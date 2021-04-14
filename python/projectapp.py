#! /usr/bin/env python
######################################################################
#
# Name: projectapp.py
#
# Purpose: Python class ProjectApp for project.py gui interface.
#
# Created: 16-Jan-2015  Herbert Greenlee
#
######################################################################

from __future__ import absolute_import
from __future__ import print_function

# Standard imports

import sys, os, subprocess, traceback
from project_modules.jobsuberror import JobsubError
from larbatch_utilities import convert_str

# Import project.py as a module.

import project
import project_utilities
from project_modules.batchstatus import BatchStatus

# Import Tkinter GUI stuff

try:
    import tkinter as tk
    import tkinter.filedialog as tkinter_filedialog
    import tkinter.messagebox as tkinter_messagebox
    import tkinter.font as tkinter_font
except ImportError:
    import Tkinter as tk
    import tkFileDialog as tkinter_filedialog
    import tkMessageBox as tkinter_messagebox
    import tkFont as tkinter_font

from project_gui_modules.projectview import ProjectView
from project_gui_modules.textwindow import TextWindow

ticket_ok = False

# Main window class for this gui application.

class ProjectApp(tk.Frame):

    # Constructor.

    def __init__(self, parent=None):

        # Root window.

        if parent == None:
            self.root = tk.Tk()
        else:
            self.root = parent
        self.root.title('project')
        self.root.protocol('WM_DELETE_WINDOW', self.close)

        # Register our outermost frame in the parent window.

        tk.Frame.__init__(self, self.root)
        self.pack(expand=1, fill=tk.BOTH)

        # Make widgets that belong to this app.

        self.make_widgets()

        # Current project and stage (menu settable).

        self.current_project_name = ''
        self.current_project_defs = []
        self.current_project_def = None
        self.current_stage_name = ''
        self.current_stage_def = None

        # Known projects (3-tuple: project_name, xml_path, project_defs)

        self.projects = []

        # Process command line arguments.

        for n in range(1, len(sys.argv)):
            xmlpath = sys.argv[n]
            self.open(xmlpath, choose=False)
        if len(self.projects) > 0:
            self.choose_project(self.projects[0][0])

    # Make widgets.  Make and register all widgets in the application window.

    def make_widgets(self):

        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        # Make menu bar (row 0).

        self.make_menubar()

        # Add project view widget (row 1).

        self.project_view = ProjectView(self)
        self.project_view.grid(row=1, column=0, sticky=tk.E+tk.W)

        # Add console window widget (row 2).

        self.console = TextWindow(self)
        self.console.grid(row=2, column=0, sticky=tk.N+tk.E+tk.W+tk.S)

        # From now on, send standard and diagnostic output to console window.

        sys.stdout = self.console
        sys.stderr = self.console

        # Schedule the idle callback.

        self.after(120000, self.often)

    # Periodic callback.

    def often(self):
        self.update_jobs()
        self.after(120000, self.often)

    # Make a menubar widget.

    def make_menubar(self):

        # Put menu in its own frame.

        self.menubar = tk.Frame(self)
        self.menubar.grid(row=0, column=0, sticky=tk.E+tk.W)

        # File menu.

        mbutton = tk.Menubutton(self.menubar, text='File', font=tkinter_font.Font(size=12))
        mbutton.pack(side=tk.LEFT)
        file_menu = tk.Menu(mbutton)
        file_menu.add_command(label='Open Project', command=self.open)
        file_menu.add_command(label='Quit', command=self.close)
        mbutton['menu'] = file_menu

        # View menu.

        mbutton = tk.Menubutton(self.menubar, text='View', font=tkinter_font.Font(size=12))
        mbutton.pack(side=tk.LEFT)
        view_menu = tk.Menu(mbutton)
        view_menu.add_command(label='XML', command=self.xml_display)
        mbutton['menu'] = view_menu

        # Project menu.

        mbutton = tk.Menubutton(self.menubar, text='Project', font=tkinter_font.Font(size=12))
        mbutton.pack(side=tk.LEFT)
        self.project_menu = tk.Menu(mbutton)
        self.project_menu.add_command(label='Next Project', command=self.next_project,
                                      accelerator='PgUp')
        self.project_menu.add_command(label='Previous Project', command=self.previous_project,
                                      accelerator='PgDn')
        self.project_menu.add_separator()
        mbutton['menu'] = self.project_menu

        # Add project menu key bindings.

        self.project_menu.bind_all('<KeyPress-KP_Next>', self.next_project_handler)
        self.project_menu.bind_all('<KeyPress-Next>', self.next_project_handler)
        self.project_menu.bind_all('<KeyPress-KP_Prior>', self.previous_project_handler)
        self.project_menu.bind_all('<KeyPress-Prior>', self.previous_project_handler)

        # Stage menu.

        mbutton = tk.Menubutton(self.menubar, text='Stage', font=tkinter_font.Font(size=12))
        mbutton.pack(side=tk.LEFT)
        self.stage_menu = tk.Menu(mbutton)
        self.stage_menu.add_command(label='Next Stage', command=self.next_stage,
                                    accelerator='Up')
        self.stage_menu.add_command(label='Previous Stage', command=self.previous_stage,
                                    accelerator='Down')
        self.stage_menu.add_separator()
        mbutton['menu'] = self.stage_menu

        # Add stage menu key bindings.

        self.stage_menu.bind_all('<KeyPress-KP_Up>', self.previous_stage_handler)
        self.stage_menu.bind_all('<KeyPress-Up>', self.previous_stage_handler)
        self.stage_menu.bind_all('<KeyPress-KP_Down>', self.next_stage_handler)
        self.stage_menu.bind_all('<KeyPress-Down>', self.next_stage_handler)

        # Output menu.

        mbutton = tk.Menubutton(self.menubar, text='Output', font=tkinter_font.Font(size=12))
        mbutton.pack(side=tk.LEFT)
        self.output_menu = tk.Menu(mbutton)
        self.output_menu.add_command(label='Check', command=self.check)
        self.output_menu.add_command(label='Checkana', command=self.checkana)
        self.output_menu.add_command(label='Fetchlog', command=self.fetchlog)
        self.output_menu.add_command(label='Shorten', command=self.shorten)
        self.output_menu.add_separator()
        self.output_menu.add_command(label='Histogram merge', command=self.mergehist)
        self.output_menu.add_command(label='Ntuple merge', command=self.mergentuple)
        self.output_menu.add_command(label='Custom merge', command=self.merge)
        self.output_menu.add_separator()
        self.output_menu.add_command(label='Clean', command=self.clean)
        mbutton['menu'] = self.output_menu

        # Batch menu.

        mbutton = tk.Menubutton(self.menubar, text='Batch', font=tkinter_font.Font(size=12))
        mbutton.pack(side=tk.LEFT)
        self.batch_menu = tk.Menu(mbutton)
        self.batch_menu.add_command(label='Submit', command=self.submit)
        self.batch_menu.add_command(label='Makeup', command=self.makeup)
        self.batch_menu.add_command(label='Update', command=self.update_jobs)
        self.batch_menu.add_command(label='Kill', command=self.kill_jobs)
        mbutton['menu'] = self.batch_menu

        # SAM-art menu.

        mbutton = tk.Menubutton(self.menubar, text='SAM-art', font=tkinter_font.Font(size=12))
        mbutton.pack(side=tk.LEFT)
        self.sam_menu = tk.Menu(mbutton)
        self.sam_menu.add_command(label='Check Declarations', command=self.check_declarations)
        self.sam_menu.add_command(label='Declare Files', command=self.declare)
        self.sam_menu.add_command(label='Test Declarations', command=self.test_declarations)
        self.sam_menu.add_separator()
        self.sam_menu.add_command(label='Check Dataset Definition', command=self.check_definition)
        self.sam_menu.add_command(label='Create Dataset Definition', command=self.define)
        self.sam_menu.add_command(label='Test Dataset Definition', command=self.test_definition)
        self.sam_menu.add_separator()
        self.sam_menu.add_command(label='Check Locations', command=self.check_locations)
        self.sam_menu.add_command(label='Check Tape Locations', command=self.check_tape)
        self.sam_menu.add_command(label='Add Disk Locations', command=self.add_locations)
        self.sam_menu.add_command(label='Clean Disk Locations', command=self.clean_locations)
        self.sam_menu.add_command(label='Remove Disk Locations', command=self.remove_locations)
        self.sam_menu.add_command(label='Upload to Enstore', command=self.upload)
        self.sam_menu.add_separator()
        self.sam_menu.add_command(label='Audit', command=self.audit)
        mbutton['menu'] = self.sam_menu

        # SAM-ana menu.

        mbutton = tk.Menubutton(self.menubar, text='SAM-ana', font=tkinter_font.Font(size=12))
        mbutton.pack(side=tk.LEFT)
        self.sam_menu = tk.Menu(mbutton)
        self.sam_menu.add_command(label='Check Declarations', command=self.check_ana_declarations)
        self.sam_menu.add_command(label='Declare Files', command=self.declare_ana)
        self.sam_menu.add_command(label='Test Declarations', command=self.test_ana_declarations)
        self.sam_menu.add_separator()
        self.sam_menu.add_command(label='Check Dataset Definition',
                                  command=self.check_ana_definition)
        self.sam_menu.add_command(label='Create Dataset Definition', command=self.define_ana)
        self.sam_menu.add_command(label='Test Dataset Definition',
                                  command=self.test_ana_definition)
        self.sam_menu.add_separator()
        self.sam_menu.add_command(label='Check Locations', command=self.check_ana_locations)
        self.sam_menu.add_command(label='Check Tape Locations', command=self.check_ana_tape)
        self.sam_menu.add_command(label='Add Disk Locations', command=self.add_ana_locations)
        self.sam_menu.add_command(label='Clean Disk Locations', command=self.clean_ana_locations)
        self.sam_menu.add_command(label='Remove Disk Locations', command=self.remove_ana_locations)
        self.sam_menu.add_command(label='Upload to Enstore', command=self.upload_ana)
        #self.sam_menu.add_separator()
        #self.sam_menu.add_command(label='Audit', command=self.audit_ana)
        mbutton['menu'] = self.sam_menu

        # Help menu.

        mbutton = tk.Menubutton(self.menubar, text='Help', font=tkinter_font.Font(size=12))
        mbutton.pack(side=tk.RIGHT)
        self.help_menu = tk.Menu(mbutton)
        self.help_menu.add_command(label='project.py help', command=self.help)
        self.help_menu.add_command(label='XML help', command=self.xmlhelp)
        mbutton['menu'] = self.help_menu

        return

    # Open project.

    def open(self, xml_path=None, choose=True):
        if xml_path == None:
            types = (('XML files', '*.xml'),
                     ('All files', '*'))
            d = tkinter_filedialog.Open(filetypes=types, parent=self.root)
            xml_path = d.show()

        # Parse xml into ProjectDef objects.
        # This step can raise an exception for several reasons.  In that case, 
        # display a message and return without opening the file.

        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        project_defs = []
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            new_project_defs = project.get_projects(xml_path)
            if len(new_project_defs) > 0:
                project_defs.extend(new_project_defs)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            message = 'Error opening %s\n%s' % (xml_path, e[1])
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', message)
            return

        if len(project_defs) > 0:
            project_name = project_defs[0].name
        else:
            xml_name = os.path.basename(xml_path)
            n = xml_name.find('.xml')
            if n > 0:
                project_name = xml_name[0: n]
            else:
                project_name = xml_name        

        # See if this project is already in the list of open projects.
        # If so, just choose this project, but don't open it again.

        for project_tuple in self.projects:
            if project_name == project_tuple[0]:
                if choose:
                    self.choose_project(project_name)
                return

        # Add this project to the list of known projects.

        self.projects.append((project_name, xml_path, project_defs))

        # Update project menu.

        callback = tk._setit(tk.StringVar(), project_name, callback=self.choose_project)
        self.project_menu.add_command(label=project_name, command=callback)

        # Choose just-opened project.

        if choose:
            self.choose_project(project_name)

    # Choose already-opened project.

    def choose_project(self, value):
        self.current_project_name = ''
        self.current_project_defs = []
        self.current_project_def = None
        self.current_stage_name = ''
        self.current_stage_def = None
        self.project_view.highlight_stage(self.current_stage_name)
        for project_tuple in self.projects:
            project_name = project_tuple[0]
            xml_path = project_tuple[1]
            project_defs = project_tuple[2]
            if project_name == value:
                self.current_project_name = value
                self.current_project_defs = project_defs

                # Update project view widget.

                self.project_view.set_project(project_name, xml_path, project_defs)

                # Update stage menu.

                self.stage_menu.delete(3, tk.END)
                self.stage_menu.add_separator()
                for project_def in project_defs:
                    for stage in project_def.stages:
                        callback = tk._setit(tk.StringVar(), stage.name, callback=self.choose_stage)
                        self.stage_menu.add_command(label=stage.name, command=callback)

                return
    
        # It is an error if we fall out of the loop.

        raise 'No project: %s' % value

    # Choose stage.

    def choose_stage(self, value):
        for project_def in self.current_project_defs:
            for stage in project_def.stages:
                if stage.name == value:
                    self.current_stage_name = value
                    self.current_stage_def = stage
                    self.current_project_def = project_def
                    self.project_view.highlight_stage(self.current_stage_name)

    # Key event handlers.

    def next_project_handler(self, event):
        self.next_project()
    def previous_project_handler(self, event):
        self.previous_project()
    def next_stage_handler(self, event):
        self.next_stage()
    def previous_stage_handler(self, event):
        self.previous_stage()
        
    # Select next project.
    def next_project(self):

        # Don't do anything if the project list is empty.

        if len(self.projects) == 0:
            return

        # Cycle through list of known projects.

        found = False
        for project_tuple in self.projects:
            project_name = project_tuple[0]
            if found:
                self.choose_project(project_name)
                return
            if project_name == self.current_project_name:
                found = True

        # Choose first project if we fell out of the loop.

        self.choose_project(self.projects[0][0])

    # Select previous project.

    def previous_project(self):

        # Don't do anything if the project list is empty.

        if len(self.projects) == 0:
            return

        # Cycle through list of known projects.

        previous_project_name = self.projects[-1][0]
        for project_tuple in self.projects:
            project_name = project_tuple[0]
            if project_name == self.current_project_name:
                self.choose_project(previous_project_name)
                return
            previous_project_name = project_name

        # Choose the last project if we fell out of the loop.

        self.choose_project(self.projects[-1][0])

    # Select XML view.

    def xml_display(self):
        self.project_view.make_xml_window()

    # Select next stage.

    def next_stage(self):

        stage = project.next_stage(self.current_project_defs, self.current_stage_name, 
                                   circular=True)
        self.choose_stage(stage.name)
        return


    # Select previous stage.

    def previous_stage(self):

        stage = project.previous_stage(self.current_project_defs, self.current_stage_name, 
                                       circular=True)
        self.choose_stage(stage.name)
        return


    # Check action.

    def check(self):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return
        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            project.docheck(self.current_project_def, self.current_stage_def, ana=False,
                            quick=self.current_stage_def.validate_on_worker)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])
        self.project_view.update_status()

    # Checkana action.

    def checkana(self):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return
        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            project.docheck(self.current_project_def, self.current_stage_def, ana=True)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])
        self.project_view.update_status()

    # Fetchlog action.

    def fetchlog(self):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return
        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            project.dofetchlog(self.current_project_def, self.current_stage_def)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])

    # Shorten action.

    def shorten(self):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return
        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            project.doshorten(self.current_stage_def)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])
        self.project_view.update_status()

    # Clean action.

    def clean(self):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return
        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            project.docleanx(self.current_project_defs, self.current_project_def.name, 
                             self.current_stage_name)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])
        self.project_view.update_status()

    # Submit action.

    def submit(self):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return

        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            project.dosubmit(self.current_project_def, self.current_stage_def, makeup=False,
                             recur=self.current_stage_def.recur)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])
        BatchStatus.update_jobs()
        self.project_view.update_status()

    # Makeup action.

    def makeup(self):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return

        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            project.dosubmit(self.current_project_def, self.current_stage_def, makeup=True,
                             recur=self.current_stage_def.recur)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])
        BatchStatus.update_jobs()
        self.project_view.update_status()

    # Update jobs action.

    def update_jobs(self):
        self.project_view.update_jobs()

    # Kill jobs action.

    def kill_jobs(self):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return

        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            BatchStatus.update_jobs()
            jobs = BatchStatus.get_jobs()
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])

        # Figure out which clusters to kill.
        
        cluster_ids = set()
        for job in jobs:
            words = job.split()
            if len(words) >= 2:
                jobid = words[0]
                script = words[-1]
                workscript = '%s-%s-%s.sh' % (self.current_stage_def.name,
                                           self.current_project_def.name,
                                           self.current_project_def.release_tag)
                if script.find(workscript) == 0:
                    cp_server = jobid.split('@')
                    if len(cp_server) == 2:
                        clusproc = cp_server[0]
                        server = cp_server[1]
                        cp = clusproc.split('.')
                        if len(cp) == 2:
                            cluster = cp[0]
                            process = cp[1]
                            cluster_id = '%s@%s' % (cluster, server)
                            if not cluster_id in cluster_ids:
                                cluster_ids.add(cluster_id)

        # Actually issue kill commands.

        for cluster_id in cluster_ids:
            print('Kill cluster id %s' % cluster_id)
            command = ['jobsub_rm']
            if self.current_project_def.server != '-' and self.current_project_def.server != '':
                command.append('--jobsub-server=%s' % self.current_project_def.server)
            command.append('--jobid=%s' % cluster_id)
            command.append('--role=%s' % project_utilities.get_role())
            jobinfo = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            jobout, joberr = jobinfo.communicate()
            jobout = convert_str(jobout)
            joberr = convert_str(joberr)
            rc = jobinfo.poll()
            if rc != 0:
                raise JobsubError(command, rc, jobout, joberr)

        self.update_jobs()
                           
        
    # Histogram merge.

    def mergehist(self):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return
        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            project.domerge(self.current_stage_def, mergehist=True, mergentuple=False)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])

    # Ntuple merge.

    def mergentuple(self):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return
        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            project.domerge(self.current_stage_def, mergehist=False, mergentuple=True)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])

    # Custom merge.

    def merge(self):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return
        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            project.domerge(self.current_stage_def, mergehist=False, mergentuple=False)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])

    # Declare files to sam.

    def declare(self, ana=False):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return
        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            project.docheck_declarations(self.current_stage_def.logdir,
                                         self.current_stage_def.outdir, declare=True, ana=ana)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])

    # Declare analysis files to sam.

    def declare_ana(self):
        self.declare(ana=True)

    # Check sam declarations.

    def check_declarations(self, ana=False):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return
        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            project.docheck_declarations(self.current_stage_def.logdir,
                                         self.current_stage_def.outdir, declare=False, ana=ana)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])

    # Check sam analysis file declarations.

    def check_ana_declarations(self):
        self.check_declarations(ana=True)

    # Test sam declarations.

    def test_declarations(self, ana=False):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return
        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            dim = project_utilities.dimensions_datastream(self.current_project_def,
                                                          self.current_stage_def,
                                                          ana=ana)
            project.dotest_declarations(dim)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])

    # Test sam analysis file declarations.

    def test_ana_declarations(self):
        self.test_declarations(ana=True)

    # Create sam dataset definition.

    def define(self, ana=False):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return
        top=self.winfo_toplevel()
        old_cursor = top['cursor']

        defname = ''
        if ana:
            defname = self.current_stage_def.ana_defname
        else:
            defname = self.current_stage_def.defname

        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            dim = project_utilities.dimensions_datastream(self.current_project_def,
                                                          self.current_stage_def,
                                                          ana=ana)
            project.docheck_definition(defname, dim, define=True)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])

    # Create sam dataset definition for analysis files.

    def define_ana(self):
        self.define(ana=True)

    # Check whether sam dataset definition exists.

    def check_definition(self, ana=False):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return
        top=self.winfo_toplevel()
        old_cursor = top['cursor']

        defname = ''
        if ana:
            defname = self.current_stage_def.ana_defname
        else:
            defname = self.current_stage_def.defname

        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            dim = project_utilities.dimensions_datastream(self.current_project_def,
                                                          self.current_stage_def,
                                                          ana=ana)
            project.docheck_definition(defname, dim, define=False)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])

    # Check whether sam analysis dataset definition exists.

    def check_ana_definition(self):
        self.check_definition(ana=True)

    # Test sam dataset definition (list files).

    def test_definition(self, ana=False):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return

        defname = ''
        if ana:
            defname = self.current_stage_def.ana_defname
        else:
            defname = self.current_stage_def.defname
        if defname == '':
            tkinter_messagebox.showwarning('No sam dataset definition specified.')
            return

        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            project.dotest_definition(defname)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])

    # Test sam analysis dataset definition (list files).

    def test_ana_definition(self):
        self.test_definition(ana=True)

    # Check locations.

    def check_locations(self, ana=False):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return
        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            dim = project_utilities.dimensions_datastream(self.current_project_def,
                                                          self.current_stage_def,
                                                          ana=ana)
            project.docheck_locations(dim, self.current_stage_def.logdir,
                                      add=False,
                                      clean=False,
                                      remove=False,
                                      upload=False)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])

    # Check locations for analysis files.

    def check_ana_locations(self):
        self.check_locations(ana=True)

    # Check tape locations.

    def check_tape(self, ana=False):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return
        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            dim = project_utilities.dimensions_datastream(self.current_project_def,
                                                          self.current_stage_def,
                                                          ana=ana)
            project.docheck_tape(dim)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])

    # Check tape locations for analysis files.

    def check_ana_tape(self):
        self.check_tape(ana=True)

    # Add disk locations.

    def add_locations(self, ana=False):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return
        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            dim = project_utilities.dimensions_datastream(self.current_project_def,
                                                          self.current_stage_def,
                                                          ana=ana)
            project.docheck_locations(dim, self.current_stage_def.outdir,
                                      add=True,
                                      clean=False,
                                      remove=False,
                                      upload=False)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])

    # Add disk locations for analysis files.

    def add_ana_locations(self):
        self.add_locations(ana=True)

    # Clean disk locations.

    def clean_locations(self, ana):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return
        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            dim = project_utilities.dimensions_datastream(self.current_project_def,
                                                          self.current_stage_def,
                                                          ana=ana)
            project.docheck_locations(dim, self.current_stage_def.outdir,
                                      add=False,
                                      clean=True,
                                      remove=False,
                                      upload=False)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])

    # Clean disk locations for analysis files.

    def clean_ana_locations(self):
        self.clean_locations(ana=True)

    # Remove disk locations.

    def remove_locations(self, ana=False):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return
        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            dim = project_utilities.dimensions_datastream(self.current_project_def,
                                                          self.current_stage_def,
                                                          ana=ana)
            project.docheck_locations(dim, self.current_stage_def.outdir,
                                      add=False,
                                      clean=False,
                                      remove=True,
                                      upload=False)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])

    # Remove disk locations for analysis files.

    def remove_ana_locations(self):
        self.remove_locations(ana=True)

    # Upload.

    def upload(self, ana=False):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return
        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            dim = project_utilities.dimensions_datastream(self.current_project_def,
                                                          self.current_stage_def,
                                                          ana=ana)
            project.docheck_locations(dim, self.current_stage_def.outdir,
                                      add=False,
                                      clean=False,
                                      remove=False,
                                      upload=True)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])

    # Upload analysis files.

    def upload_ana(self):
        self.upload(ana=True)

    # Do a SAM audit.

    def audit(self):
        if self.current_project_def == None:
            tkinter_messagebox.showwarning('', 'No project selected.')
            return
        if self.current_stage_def == None:
            tkinter_messagebox.showwarning('', 'No stage selected.')
            return
        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            project.doaudit(self.current_stage_def)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])

    # Help method.

    def help(self):

        # Capture output from project.py --help.
        # Because of the way this command is implemented in project.py, we have
        # to run in a separate process, not just call method help of project module.

        command = ['project.py', '--help']
        helptext = convert_str(subprocess.check_output(command))
        w = TextWindow()
        w.append(helptext)

    # XML help method.

    def xmlhelp(self):

        # Capture output from project.py --xmlhelp.
        # Because of the way this command is implemented in project.py, we have
        # to run in a separate process, not just call method xmlhelp of project module.

        command = ['project.py', '--xmlhelp']
        helptext = convert_str(subprocess.check_output(command))
        w = TextWindow()
        w.append(helptext)

    # Close window.

    def close(self):
        self.root.destroy()
