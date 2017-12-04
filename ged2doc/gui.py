# -*- coding: utf-8 -*-

"""Console script for ged2doc."""

from __future__ import absolute_import, division, print_function

import logging
try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk
import tkFileDialog
import tkFont
import ttk

from .size import String2Size
from .i18n import I18N, DATE_FORMATS
from .input import make_file_locator
from .html_writer import HtmlWriter
from .name import (FMT_SURNAME_FIRST, FMT_COMMA, FMT_MAIDEN,
                   FMT_MAIDEN_ONLY, FMT_CAPITAL)
from .utils import languages, system_lang
from ged4py.model import (ORDER_LIST, ORDER_SURNAME_GIVEN)

_log = logging.getLogger(__name__)


class PageInputOutput(ttk.Frame):

    def __init__(self, master, in_file_name, image_folder, out_type, out_file_name):

        ttk.Frame.__init__(self, master)

        self.header = "Input and Output"

        self.in_file_name = in_file_name
        self.image_folder = image_folder
        self.out_type = out_type
        self.out_file_name = out_file_name

        group = ttk.LabelFrame(self, text="Input", padding=5)
        group.pack(fill="x", expand=True, padx=10, pady=10)

        ttk.Label(group, text="Input file:").grid(row=0, column=0, sticky='e')
        entry = ttk.Entry(group, textvariable=self.in_file_name)
        entry.grid(row=0, column=1, sticky='ew')
        button = ttk.Button(group, text="Select", command=self.open_input)
        button.grid(row=0, column=2)

        ttk.Label(group, text="Image folder:").grid(row=1, column=0, sticky='e')
        entry = ttk.Entry(group, textvariable=self.image_folder)
        entry.grid(row=1, column=1, sticky='ew')
        button = ttk.Button(group, text="Select", command=self.choose_img_folder)
        button.grid(row=1, column=2)

        group.columnconfigure(1, weight=5)
        group.columnconfigure('all', pad=5)
        group.rowconfigure('all', pad=5)

        group = ttk.LabelFrame(self, text="Output", padding=5)
        group.pack(fill="x", expand=True, padx=10, pady=10)

        ttk.Label(group, text="Document type:").grid(row=0, column=0, sticky='e')
        type_chooser = ttk.Combobox(group, textvariable=self.out_type,
                                    values=["HTML", "OpenDocument"],
                                    state='readonly')
        type_chooser.grid(row=0, column=1, sticky='w')

        ttk.Label(group, text="Output file:").grid(row=1, column=0, sticky='e')
        entry = ttk.Entry(group, textvariable=self.out_file_name)
        entry.grid(row=1, column=1, sticky='ew')
        button = ttk.Button(group, text="Select", command=self.open_output)
        button.grid(row=1, column=2)

        group.columnconfigure(1, weight=5)
        group.columnconfigure('all', pad=5)
        group.rowconfigure('all', pad=5)

    def open_input(self):
        path = tkFileDialog.askopenfilename(defaultextension=".ged",
                                            filetypes=[("GEDCOM", "*.ged*"),
                                                       ("ZIP", "*.zip"),
                                                       ("Anything", "*.*")])
        if path:
            self.in_file_name.set(path)

    def choose_img_folder(self):
        path = tkFileDialog.askdirectory()
        if path:
            self.image_folder.set(path)

    def open_output(self):
        path = tkFileDialog.asksaveasfilename()
        if path:
            self.out_file_name.set(path)


class PageArchive(ttk.Frame):

    def __init__(self, master, zip_file_pattern, zip_file):

        ttk.Frame.__init__(self, master)

        self.header = "ZIP Archive Input"

        self.zip_file_pattern = zip_file_pattern
        self.zip_file = zip_file

        ttk.Label(self, text="Pattern:").grid(row=0, column=0, sticky='e')
        entry = ttk.Entry(self, textvariable=self.zip_file_pattern)
        entry.grid(row=0, column=1, sticky='ew')


class Wizard(ttk.Frame):
    """
    https://stackoverflow.com/questions/41332955/creating-a-wizard-in-tkinter
    """

    def __init__(self, master = None):

        ttk.Frame.__init__(self, master)

        self.in_file_name = tk.StringVar()
        self.image_folder = tk.StringVar()
        self.out_type = tk.StringVar(value='HTML')
        self.out_file_name = tk.StringVar()
        self.zip_file_pattern = tk.StringVar(value="*.ged*")
        self.zip_file = tk.StringVar()

        self.history = []

        self.pack(fill="both", expand=True)

        self.header = ttk.Label(self, font="-weight bold", padding=5)
        self.header.pack(pady=3)

        # container for pages
        self.main = ttk.Frame(self)
        self.main.pack(expand=0, fill='x')

        # extra stretchable space
        ttk.Frame(self).pack(expand=1, fill='both')

        # separator line
        separ = ttk.Separator(self,)
        separ.pack(expand=0, fill=tk.X)

        # container for buttons
        buttons = ttk.Frame(self)
        buttons.pack(expand=0, fill=tk.X, pady=5)

        self.help_button = ttk.Button(buttons, text='Help')
        self.back_button = ttk.Button(buttons, text='< Back', command=self.back)
        self.next_button = ttk.Button(buttons, text='Next >', command=self.next)
        self.quit_button = ttk.Button(buttons, text='Quit', command=self.quit)
        self.help_button.pack(side='left', padx=5)
        self.quit_button.pack(side='right', padx=5)
        self.next_button.pack(side='right', padx=5)
        self.back_button.pack(side='right', padx=5)

        self.next()

    def next(self):

        # validate that data is OK before moving to next page
        if self.history and not self.validate_page(self.history[-1]):
            return

        if self.history :
            # undisplay current step
            self.history[-1].pack_forget()

        if not self.history:
            page = PageInputOutput(self.main, self.in_file_name,
                                   self.image_folder, self.out_type,
                                   self.out_file_name)
            self.history += [page]
        elif len(self.history) == 1:
            page = PageArchive(self.main, self.zip_file_pattern,
                               self.zip_file)
            self.history += [page]
        else:
            page = self.history[-1]

        page.pack(fill="x", expand=True)
        self.header.config(text=page.header)

        if len(self.history) > 1:
            self.back_button.config(state='normal')
        else:
            self.back_button.config(state='disabled')

    def back(self):

        if len(self.history) > 1:
            # undisplay current step
            page = self.history[-1]
            page.pack_forget()

            # forget it completely
            del self.history[-1]

            page = self.history[-1]
            page.pack(fill="x", expand=True)
            self.header.config(text=page.header)

            if len(self.history) == 1:
                self.back_button.config(state='disabled')

    def validate_page(self, page):

        if isinstance(page, PageInputOutput):
            # make sure that input file is a valid GEDCOM or ZIP file
            pass
        return True


def main():
    """GUI for ged2doc."""
    app = Wizard()
    app.master.title('Sample application')
    app.mainloop()
