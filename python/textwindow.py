#! /usr/bin/env python
######################################################################
#
# Name: textwindow.py
#
# Purpose: Python class for displaying arbitrary text in a scrolling
#          window or frame.
#
# Created: 28-Jan-2015  Herbert Greenlee
#
######################################################################

from __future__ import absolute_import
from __future__ import print_function
import sys

# Import GUI stuff

try:
    import tkinter as tk
except ImportError:
    import Tkinter as tk

# Project widget class

class TextWindow(tk.Frame):

    # Constructor.

    def __init__(self, parent=None, rows=24, columns=80):

        # Parent window.

        if parent == None:
            self.parent = tk.Toplevel()
        else:
            self.parent = parent

        # Register our outermost frame in the parent window.

        tk.Frame.__init__(self, self.parent)
        if parent == None:
            self.pack(expand=1, fill=tk.BOTH)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Add an empty text widget.

        self.text = tk.Text(self, height=rows, width=columns, wrap=tk.NONE, takefocus=0)
        self.text.grid(row=0, column=0, sticky=tk.N+tk.E+tk.W+tk.S)

        # Make scroll bars, but don't grid them yet.

        self.vbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.text.yview)
        self.text['yscrollcommand'] = self.vbar.set
        self.vbar_visible = 0

        self.hbar = tk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.text.xview)
        self.text['xscrollcommand'] = self.hbar.set
        self.hbar_visible = 0

        self.check_scroll()
 
        # Set event bindings (check scrollbar visibility when window size 
        # changes).

        self.text.bind('<Configure>', self.check_scroll)

    # See if we need to enable or disable either scrollbar.

    def check_scroll(self, event=None):

        # Check vertical scroll bar.

        yv = self.text.yview()
        if not self.vbar_visible and (yv[0] != 0.0 or yv[1] != 1.0):
            self.vbar_visible = 1
            self.vbar.grid(row=0, column=1, sticky=tk.N+tk.S)
        elif self.vbar_visible and yv[0] == 0.0 and yv[1] == 1.0:
            self.vbar_visible = 0
            self.vbar.grid_forget()

        # Check horizontal scroll bar.

        xv = self.text.xview()
        if not self.hbar_visible and (xv[0] != 0.0 or xv[1] != 1.0):
            self.hbar_visible = 1
            self.hbar.grid(row=1, column=0, sticky=tk.E+tk.W)
        elif self.hbar_visible and xv[0] == 0.0 and xv[1] == 1.0:
            self.hbar_visible = 0
            self.hbar.grid_forget()

    # Insert text.

    def insert(self, pos, text):
        self.text.insert(pos, text)
        self.check_scroll()

    # Insert text at and of buffer.

    def append(self, text):
        self.insert(tk.END, text)

    # File-like methods.

    # If they want our file descriptor, tell them 2 for now (standard error).
    # Python docs say not to implement this method if it doesn't make sense
    # for your file-like object.  But subprocess(stderr=) doesn't work without 
    # this method.

    def fileno(self):
        return 2

    # Close/flush file (don't do anything).

    def close(self):
        return
    def flush(self):
        return

    # Is this a tty?

    def isatty(self):
        return False

    # Read methods (raise IOError).

    def __next__(self):
        raise IOError('File is not open for reading.')
    def read(self, size=0):
        raise IOError('File is not open for reading.')
    def readline(self, size=0):
        raise IOError('File is not open for reading.')
    def readlines(self, size=0):
        raise IOError('File is not open for reading.')
    def readline(self, size=0):
        raise IOError('File is not open for reading.')
    def seek(self, offset, pos=0):
        raise IOError('File is not open for reading.')

    # Current position.

    def tell(self):
        return len(self.text['text'])

    # Truncate.

    def truncate(self, size=0):
        self.text['text'] = self.text['text'][0:size]
        self.check_scroll()
        self.text.yview_moveto(1.0)   # Scroll to bottom

    # Write methods.

    def write(self, text):
        self.append(text)
        self.text.yview_moveto(1.0)   # Scroll to bottom
    def writelines(self, lines):
        for line in lines:
            self.append(line)
        self.text.yview_moveto(1.0)   # Scroll to bottom
