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


class Page1(ttk.Frame):

    def __init__(self, master = None):

        ttk.Frame.__init__(self, master)

        self.header = "Input and Output"

        self.in_file_name = tk.StringVar()
        self.image_folder = tk.StringVar()
        self.out_type = tk.StringVar(value='HTML')
        self.out_file_name = tk.StringVar()

        group = ttk.LabelFrame(self, text="Input")
        group.pack(fill="x", expand=True)

        lbl = ttk.Label(group, text="Input file:")
        lbl.grid(row=0, column=0, sticky='e')
        in_file = ttk.Entry(group, textvariable=self.in_file_name)
        in_file.grid(row=0, column=1, sticky='ew')
        in_file_button = ttk.Button(group, text="Select", command=self.open_input)
        in_file_button.grid(row=0, column=2)

        lbl = ttk.Label(group, text="Image folder:")
        lbl.grid(row=1, column=0, sticky='e')
        in_file = ttk.Entry(group, textvariable=self.image_folder)
        in_file.grid(row=1, column=1, sticky='ew')
        in_file_button = ttk.Button(group, text="Select", command=self.choose_img_folder)
        in_file_button.grid(row=1, column=2)

        group.columnconfigure(1, weight=5)
        group.columnconfigure('all', pad=5)
        group.rowconfigure('all', pad=5)

        group = ttk.LabelFrame(self, text="Output")
        group.pack(fill="x", expand=True)

        lbl = ttk.Label(group, text="Output type:")
        lbl.grid(row=0, column=0, sticky='e')
        type_chooser = ttk.Combobox(group, textvariable=self.out_type,
                                    values=["HTML", "OpenDocument"],
                                    state='readonly')
        type_chooser.grid(row=0, column=1, sticky='w')

        lbl = ttk.Label(group, text="Output file:")
        lbl.grid(row=1, column=0, sticky='e')
        out_file = ttk.Entry(group, textvariable=self.out_file_name)
        out_file.grid(row=1, column=1, sticky='ew')
        out_file_button = ttk.Button(group, text="Select", command=self.open_output)
        out_file_button.grid(row=1, column=2)

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


class Wizard(ttk.Frame):
    """
    https://stackoverflow.com/questions/41332955/creating-a-wizard-in-tkinter
    """

    def __init__(self, master = None):

        ttk.Frame.__init__(self, master)
        self.pack(fill="both", expand=True)

        self.current_page = None

        self.header = ttk.Label(self, font="-weight bold")
        self.header.pack(pady=3)

        # container for pages
        self.main = ttk.Frame(self, borderwidth=3)
        self.main.pack(expand=0, fill='x')

        # extra stretchable space
        ttk.Frame(self).pack(expand=1, fill='both')

        # separator line
        separ = ttk.Separator(self,)
        separ.pack(expand=0, fill=tk.X)

        # container for buttons
        buttons = ttk.Frame(self, borderwidth=3)
        buttons.pack(expand=0, fill=tk.X, pady=5)

        self.quit_button = ttk.Button(buttons, text='Quit', command=self.quit)
        self.quit_button.pack(side='right', padx=5)
        self.next_button = ttk.Button(buttons, text='Next >')
        self.next_button.pack(side='right', padx=5)
        self.back_button = ttk.Button(buttons, text='< Back')
        self.back_button.pack(side='right', padx=5)

        self.pages = [Page1(self.main)]

        self.show_page(0)

    def show_page(self, page_idx):
        if self.current_page is not None:
            # remove current step
            page = self.pages[self.current_page]
            page.pack_forget()

        self.current_page = page_idx
        page = self.pages[page_idx]
        page.pack(fill="x", expand=True)

        self.header.config(text=page.header)

        if page_idx == 0:
            self.back_button.config(state='disabled')
        else:
            self.back_button.config(state='normal')


def main():
    """GUI for ged2doc."""
    app = Wizard()
    app.master.title('Sample application')
    app.mainloop()
