#! /usr/bin/env python
######################################################################
#
# Name: statusview.py
#
# Purpose: Python class StatusView is a widget for displaying 
#          project status information.
#
# Created: 22-Jan-2015  Herbert Greenlee
#
######################################################################

from __future__ import absolute_import
from __future__ import print_function
import sys, traceback
from project_modules.projectstatus import ProjectStatus
from project_modules.batchstatus import BatchStatus

# Import GUI stuff

# Import Tkinter GUI stuff

try:
    import tkinter as tk
    import tkinter.messagebox as tkinter_messagebox
    import tkinter.font as tkinter_font
except ImportError:
    import Tkinter as tk
    import tkMessageBox as tkinter_messagebox
    import tkFont as tkinter_font

# Make symbolic names for column indices.

kEXISTS = 1
kNFILE = 2
kNEV = 3
kNANA = 4
kNERROR = 5
kNMISS = 6
kIDLE = 7
kRUNNING = 8
kHELD = 9
kOTHER = 10
kEND = 11

# Project widget class

class ProjectStatusView(tk.Frame):

    # Constructor.

    def __init__(self, parent, project_defs=[]):


        self.parent = parent
        self.project_defs = project_defs

        # Register our outermost frame in the parent window.

        tk.Frame.__init__(self, self.parent)
        self.pack(expand=1, fill=tk.BOTH)
        self.rowconfigure(0, weight=1)

        # Dictionaries to hold stage widgets.

        self.stage_name_labels = {}
        self.exists_labels = {}
        self.nfile_labels = {}
        self.nev_labels = {}
        self.nana_labels = {}
        self.nerror_labels = {}
        self.nmiss_labels = {}
        self.nidle_labels = {}
        self.nrunning_labels = {}
        self.nheld_labels = {}
        self.nother_labels = {}

        # Make widgets that belong to this widget.

        self.make_widgets()
        if len(self.project_defs) > 0:
            self.update_status()

    # Make widgets.

    def make_widgets(self):

        # Add column category headings.

        self.stage_cat = tk.Label(self, bg='powderblue', relief=tk.RIDGE, text='',
                                  padx=10, pady=10, font=tkinter_font.Font(size=12))
        self.stage_cat.grid(row=0, column=0, sticky=tk.N+tk.E+tk.W+tk.S)
        self.files_cat = tk.Frame(self, bd=1, relief=tk.SUNKEN, bg='lightsteelblue')
        files_label = tk.Label(self.files_cat, bg='lightsteelblue', relief=tk.FLAT, text='Output',
                                  padx=10, font=tkinter_font.Font(size=12))
        files_label.pack(side=tk.LEFT, expand=1, fill=tk.BOTH)
        fetchlog_button = tk.Button(self.files_cat, bg='lightcyan', activebackground='aliceblue',
                                    text='Fetchlog', command=self.parent.parent.fetchlog)
        fetchlog_button.pack(side=tk.RIGHT)
        checkana_button = tk.Button(self.files_cat, bg='lightcyan', activebackground='aliceblue',
                                    text='CheckAna', command=self.parent.parent.checkana)
        checkana_button.pack(side=tk.RIGHT)
        check_button = tk.Button(self.files_cat, bg='lightcyan', activebackground='aliceblue', 
                                 text='Check', command=self.parent.parent.check)
        check_button.pack(side=tk.RIGHT)
        self.files_cat.grid(row=0, column=kEXISTS, columnspan=kIDLE-kEXISTS, 
                            sticky=tk.N+tk.E+tk.W+tk.S)
        self.batch_cat = tk.Frame(self, bd=1, relief=tk.SUNKEN, bg='powderblue')
        batch_label = tk.Label(self.batch_cat, bg='powderblue', relief=tk.FLAT, text='Batch Jobs',
                               padx=10, font=tkinter_font.Font(size=12))
        batch_label.pack(side=tk.LEFT, expand=1, fill=tk.BOTH)
        batch_button = tk.Button(self.batch_cat, bg='lightcyan', activebackground='aliceblue', 
                                 text='Update', command=self.update_jobs)
        batch_button.pack(side=tk.RIGHT)
        makeup_button = tk.Button(self.batch_cat, bg='lightcyan', activebackground='aliceblue', 
                                 text='Makeup', command=self.parent.parent.makeup)
        makeup_button.pack(side=tk.RIGHT)
        submit_button = tk.Button(self.batch_cat, bg='lightcyan', activebackground='aliceblue', 
                                 text='Submit', command=self.parent.parent.submit)
        submit_button.pack(side=tk.RIGHT)
        self.batch_cat.grid(row=0, column=kIDLE, columnspan=kEND-kIDLE,
                            sticky=tk.N+tk.E+tk.W+tk.S)

        # Add column headings.

        self.stage_head = tk.Label(self, bg='powderblue', relief=tk.RIDGE, text='Stage',
                                   padx=10, pady=10, font=tkinter_font.Font(size=12))
        self.stage_head.grid(row=1, column=0, sticky=tk.N+tk.E+tk.W+tk.S)
        self.columnconfigure(0, weight=1)
        self.exists_head = tk.Label(self, bg='lightsteelblue', relief=tk.RIDGE, text='Exists?',
                                    padx=10, font=tkinter_font.Font(size=12))
        self.exists_head.grid(row=1, column=kEXISTS, sticky=tk.N+tk.E+tk.W+tk.S)
        self.columnconfigure(kEXISTS, weight=1)
        self.nfile_head = tk.Label(self, bg='lightsteelblue', relief=tk.RIDGE, text='Art Files',
                                   padx=10, font=tkinter_font.Font(size=12))
        self.nfile_head.grid(row=1, column=kNFILE, sticky=tk.N+tk.E+tk.W+tk.S)
        self.columnconfigure(kNFILE, weight=1)
        self.nev_head = tk.Label(self, bg='lightsteelblue', relief=tk.RIDGE, text='Events',
                                 padx=10, font=tkinter_font.Font(size=12))
        self.nev_head.grid(row=1, column=kNEV, sticky=tk.N+tk.E+tk.W+tk.S)
        self.columnconfigure(kNANA, weight=1)
        self.nana_head = tk.Label(self, bg='lightsteelblue', relief=tk.RIDGE, text='Ana Files',
                                  padx=10, font=tkinter_font.Font(size=12))
        self.nana_head.grid(row=1, column=kNANA, sticky=tk.N+tk.E+tk.W+tk.S)
        self.columnconfigure(kNANA, weight=1)
        self.nerror_head = tk.Label(self, bg='lightsteelblue', relief=tk.RIDGE, text='Errors',
                                    padx=10, font=tkinter_font.Font(size=12))
        self.nerror_head.grid(row=1, column=kNERROR, sticky=tk.N+tk.E+tk.W+tk.S)
        self.columnconfigure(kNERROR, weight=1)
        self.miss_head = tk.Label(self, bg='lightsteelblue', relief=tk.RIDGE, text='Missing',
                                  padx=10, font=tkinter_font.Font(size=12))
        self.miss_head.grid(row=1, column=kNMISS, sticky=tk.N+tk.E+tk.W+tk.S)
        self.columnconfigure(kNMISS, weight=1)
        self.idle_head = tk.Label(self, bg='powderblue', relief=tk.RIDGE, text='Idle',
                                  padx=10, font=tkinter_font.Font(size=12))
        self.idle_head.grid(row=1, column=kIDLE, sticky=tk.N+tk.E+tk.W+tk.S)
        self.columnconfigure(kIDLE, weight=1)
        self.running_head = tk.Label(self, bg='powderblue', relief=tk.RIDGE, text='Running',
                                     padx=10, font=tkinter_font.Font(size=12))
        self.running_head.grid(row=1, column=kRUNNING, sticky=tk.N+tk.E+tk.W+tk.S)
        self.columnconfigure(kRUNNING, weight=1)
        self.held_head = tk.Label(self, bg='powderblue', relief=tk.RIDGE, text='Held',
                                  padx=10, font=tkinter_font.Font(size=12))
        self.held_head.grid(row=1, column=kHELD, sticky=tk.N+tk.E+tk.W+tk.S)
        self.columnconfigure(kHELD, weight=1)
        self.other_head = tk.Label(self, bg='powderblue', relief=tk.RIDGE, text='Other',
                                   padx=10, font=tkinter_font.Font(size=12))
        self.other_head.grid(row=1, column=kOTHER, sticky=tk.N+tk.E+tk.W+tk.S)
        self.columnconfigure(kOTHER, weight=1)

    # Set or update project definition.

    def set_project(self, project_defs):
        self.project_defs = project_defs
        self.update_status()

    # Update status display.

    def update_status(self):

        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            ps = ProjectStatus(self.project_defs)
            bs = BatchStatus(self.project_defs)
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])

        # Update label widgets.

        for key in list(self.stage_name_labels.keys()):
            self.stage_name_labels[key].grid_forget()
        for key in list(self.exists_labels.keys()):
            self.exists_labels[key].grid_forget()
        for key in list(self.nfile_labels.keys()):
            self.nfile_labels[key].grid_forget()
        for key in list(self.nev_labels.keys()):
            self.nev_labels[key].grid_forget()
        for key in list(self.nana_labels.keys()):
            self.nana_labels[key].grid_forget()
        for key in list(self.nerror_labels.keys()):
            self.nerror_labels[key].grid_forget()
        for key in list(self.nmiss_labels.keys()):
            self.nmiss_labels[key].grid_forget()
        for key in list(self.nidle_labels.keys()):
            self.nidle_labels[key].grid_forget()
        for key in list(self.nrunning_labels.keys()):
            self.nrunning_labels[key].grid_forget()
        for key in list(self.nheld_labels.keys()):
            self.nheld_labels[key].grid_forget()
        for key in list(self.nother_labels.keys()):
            self.nother_labels[key].grid_forget()

        row = 1
        for project_def in self.project_defs:
            for stage in project_def.stages:
                row = row + 1
                ss = ps.get_stage_status(stage.name)
                bss = bs.get_stage_status(stage.name)

                if stage.name not in self.stage_name_labels:
                    self.stage_name_labels[stage.name] = tk.Label(self, bg='powderblue',
                                                                  relief=tk.RIDGE,
                                                                  padx=10, pady=5,
                                                                  font=tkinter_font.Font(size=12))
                self.stage_name_labels[stage.name]['text'] = stage.name
                self.stage_name_labels[stage.name].bind('<Button-1>', self.click_stage)
                self.stage_name_labels[stage.name].grid(row=row, column=0,
                                                        sticky=tk.N+tk.E+tk.W+tk.S)
                self.rowconfigure(row, weight=1)

                if stage.name not in self.exists_labels:
                    self.exists_labels[stage.name] = tk.Label(self, bg='aliceblue', relief=tk.RIDGE,
                                                              font=tkinter_font.Font(size=12))
                if ss.exists:
                    self.exists_labels[stage.name]['text'] = 'Yes'
                    self.exists_labels[stage.name]['fg'] = 'black'
                else:
                    self.exists_labels[stage.name]['text'] = 'No'
                    self.exists_labels[stage.name]['fg'] = 'red'
                self.exists_labels[stage.name].grid(row=row, column=kEXISTS,
                                                    sticky=tk.N+tk.E+tk.W+tk.S)
                self.rowconfigure(row, weight=1)

                if stage.name not in self.nfile_labels:
                    self.nfile_labels[stage.name] = tk.Label(self, bg='aliceblue', relief=tk.RIDGE,
                                                             font=tkinter_font.Font(size=12))
                self.nfile_labels[stage.name]['text'] = str(ss.nfile)
                self.nfile_labels[stage.name].grid(row=row, column=kNFILE,
                                                   sticky=tk.N+tk.E+tk.W+tk.S)
                self.rowconfigure(row, weight=1)

                if stage.name not in self.nev_labels:
                    self.nev_labels[stage.name] = tk.Label(self, bg='aliceblue', relief=tk.RIDGE,
                                                           font=tkinter_font.Font(size=12))
                self.nev_labels[stage.name]['text'] = str(ss.nev)
                self.nev_labels[stage.name].grid(row=row, column=kNEV, sticky=tk.N+tk.E+tk.W+tk.S)
                self.rowconfigure(row, weight=1)

                if stage.name not in self.nana_labels:
                    self.nana_labels[stage.name] = tk.Label(self, bg='aliceblue', relief=tk.RIDGE,
                                                            font=tkinter_font.Font(size=12))
                self.nana_labels[stage.name]['text'] = str(ss.nana)
                self.nana_labels[stage.name].grid(row=row, column=kNANA, sticky=tk.N+tk.E+tk.W+tk.S)
                self.rowconfigure(row, weight=1)

                if stage.name not in self.nerror_labels:
                    self.nerror_labels[stage.name] = tk.Label(self, bg='aliceblue', relief=tk.RIDGE,
                                                              font=tkinter_font.Font(size=12))
                self.nerror_labels[stage.name]['text'] = str(ss.nerror)
                if ss.nerror == 0:
                    self.nerror_labels[stage.name]['fg'] = 'black'
                else:
                    self.nerror_labels[stage.name]['fg'] = 'red'
                self.nerror_labels[stage.name].grid(row=row, column=kNERROR,
                                                    sticky=tk.N+tk.E+tk.W+tk.S)
                self.rowconfigure(row, weight=1)

                if stage.name not in self.nmiss_labels:
                    self.nmiss_labels[stage.name] = tk.Label(self, bg='aliceblue', relief=tk.RIDGE,
                                                             font=tkinter_font.Font(size=12))
                self.nmiss_labels[stage.name]['text'] = str(ss.nmiss)
                if ss.nmiss == 0:
                    self.nmiss_labels[stage.name]['fg'] = 'black'
                else:
                    self.nmiss_labels[stage.name]['fg'] = 'red'
                self.nmiss_labels[stage.name].grid(row=row, column=kNMISS,
                                                   sticky=tk.N+tk.E+tk.W+tk.S)
                self.rowconfigure(row, weight=1)

                if stage.name not in self.nidle_labels:
                    self.nidle_labels[stage.name] = tk.Label(self, bg='lightcyan', relief=tk.RIDGE,
                                                             font=tkinter_font.Font(size=12))
                self.nidle_labels[stage.name]['text'] = bss[0]
                self.nidle_labels[stage.name].grid(row=row, column=kIDLE,
                                                   sticky=tk.N+tk.E+tk.W+tk.S)
                self.rowconfigure(row, weight=1)

                if stage.name not in self.nrunning_labels:
                    self.nrunning_labels[stage.name] = tk.Label(self, bg='lightcyan',
                                                                relief=tk.RIDGE,
                                                                font=tkinter_font.Font(size=12))
                self.nrunning_labels[stage.name]['text'] = bss[1]
                self.nrunning_labels[stage.name].grid(row=row,
                                                      column=kRUNNING, sticky=tk.N+tk.E+tk.W+tk.S)
                self.rowconfigure(row, weight=1)

                if stage.name not in self.nheld_labels:
                    self.nheld_labels[stage.name] = tk.Label(self, bg='lightcyan', relief=tk.RIDGE,
                                                             font=tkinter_font.Font(size=12))
                self.nheld_labels[stage.name]['text'] = bss[2]
                self.nheld_labels[stage.name].grid(row=row, column=kHELD,
                                                   sticky=tk.N+tk.E+tk.W+tk.S)
                self.rowconfigure(row, weight=1)

                if stage.name not in self.nother_labels:
                    self.nother_labels[stage.name] = tk.Label(self, bg='lightcyan', relief=tk.RIDGE,
                                                              font=tkinter_font.Font(size=12))
                self.nother_labels[stage.name]['text'] = bss[3]
                self.nother_labels[stage.name].grid(row=row, column=kOTHER,
                                                    sticky=tk.N+tk.E+tk.W+tk.S)
                self.rowconfigure(row, weight=1)

        
    # Highlight stage.

    def highlight_stage(self, stagename):
        for key in list(self.stage_name_labels.keys()):
            self.stage_name_labels[key]['bg'] = 'powderblue'
            self.exists_labels[key]['bg'] = 'aliceblue'
            self.nfile_labels[key]['bg'] = 'aliceblue'
            self.nev_labels[key]['bg'] = 'aliceblue'
            self.nana_labels[key]['bg'] = 'aliceblue'
            self.nerror_labels[key]['bg'] = 'aliceblue'
            self.nmiss_labels[key]['bg'] = 'aliceblue'
            self.nidle_labels[key]['bg'] = 'lightcyan'
            self.nrunning_labels[key]['bg'] = 'lightcyan'
            self.nheld_labels[key]['bg'] = 'lightcyan'
            self.nother_labels[key]['bg'] = 'lightcyan'
        if stagename in self.stage_name_labels:
            self.stage_name_labels[stagename]['bg'] = 'white'
            self.exists_labels[stagename]['bg'] = 'white'
            self.nfile_labels[stagename]['bg'] = 'white'
            self.nev_labels[stagename]['bg'] = 'white'
            self.nana_labels[stagename]['bg'] = 'white'
            self.nerror_labels[stagename]['bg'] = 'white'
            self.nmiss_labels[stagename]['bg'] = 'white'
            self.nidle_labels[stagename]['bg'] = 'white'
            self.nrunning_labels[stagename]['bg'] = 'white'
            self.nheld_labels[stagename]['bg'] = 'white'
            self.nother_labels[stagename]['bg'] = 'white'

    # Update jobs button.

    def update_jobs(self):
        top=self.winfo_toplevel()
        old_cursor = top['cursor']
        try:
            top['cursor'] = 'watch'
            top.update_idletasks()
            BatchStatus.update_jobs()
            top['cursor'] = old_cursor
        except:
            top['cursor'] = old_cursor
            e = sys.exc_info()
            traceback.print_tb(e[2])
            tkinter_messagebox.showerror('', e[1])
        self.update_status()

    # Click on stage mouse event callback.

    def click_stage(self, event):
        stagename = event.widget['text']

        # Choose stage in parent app.

        self.parent.parent.choose_stage(stagename)
