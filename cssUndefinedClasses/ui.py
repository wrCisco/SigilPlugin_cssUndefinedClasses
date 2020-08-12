#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Copyright (c) 2020 Francesco Martini
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as msgbox
import tkinter.font as tkfont
from typing import Dict, Set

import core
import utils


class MainWindow(tk.Tk):

    def __init__(self, bk):
        self.bk = bk
        self.success = False  # True when the plugin terminates correctly

        super().__init__()
        self.style = ttk.Style()
        self.title("cssUndefinedClasses")
        self.set_geometry()
        self.set_styles()

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.mainframe = ttk.Frame(self, padding="5 0 5 5")  # W N E S
        self.mainframe.grid(row=0, column=0, sticky="nsew")
        self.mainframe.bind(
            '<Configure>',
            lambda event: self.update_wraplength(event, self.style)
        )

        self.top_label_text = tk.StringVar()
        self.top_label_text.set('Welcome! Please press the "Proceed" button to begin.')
        self.top_label = ttk.Label(
            self.mainframe,
            textvariable=self.top_label_text,
            style='Top.TLabel'
        )
        self.top_label.grid(row=0, column=0, sticky='nsew')
        self.panedwindow = ttk.PanedWindow(self.mainframe, orient=tk.HORIZONTAL)
        self.panedwindow.grid(row=1, column=0, sticky='nsew')

        self.classes_frame = ttk.Frame(self.panedwindow, style='Paned.TFrame', padding=4)
        self.ids_frame = ttk.Frame(self.panedwindow, style='Paned.TFrame', padding=4)
        self.panedwindow.add(self.classes_frame, weight=1)
        self.panedwindow.add(self.ids_frame, weight=1)

        self.classes_label_text = tk.StringVar()
        self.classes_label_text.set('')
        self.classes_label = ttk.Label(
            self.classes_frame,
            textvariable=self.classes_label_text,
            style='Paned.TLabel'
        )
        self.classes_label.grid(row=0, column=0, sticky='nsw')
        self.scroll_classes_list = ttk.Scrollbar(self.classes_frame, orient=tk.VERTICAL)
        self.classes_text = tk.Text(
            self.classes_frame,
            yscrollcommand=self.scroll_classes_list.set,
            borderwidth=0,
            padx=4, pady=4,
            relief=tk.FLAT
        )
        self.scroll_classes_list.grid(row=1, column=1, sticky='nsew')
        self.scroll_classes_list['command'] = self.classes_text.yview
        self.classes_text.grid(row=1, column=0, sticky='nsew')
        self.classes_frame.rowconfigure(0, weight=0)
        self.classes_frame.rowconfigure(1, weight=1)
        self.classes_frame.columnconfigure(0, weight=1)
        self.classes_frame.columnconfigure(1, weight=0)
        self.bind_to_mousewheel(self.classes_text)
        self.classes_text.config(state=tk.DISABLED)

        self.ids_label_text = tk.StringVar()
        self.ids_label_text.set('')
        self.ids_label = ttk.Label(
            self.ids_frame,
            textvariable=self.ids_label_text,
            style='Paned.TLabel'
        )
        self.ids_label.grid(row=0, column=0, sticky='nsw')
        self.scroll_ids_list = ttk.Scrollbar(self.ids_frame, orient=tk.VERTICAL)
        self.ids_text = tk.Text(
            self.ids_frame,
            yscrollcommand=self.scroll_ids_list.set,
            borderwidth=0,
            padx=4, pady=4,
            relief=tk.FLAT
        )
        self.scroll_ids_list.grid(row=1, column=1, sticky='nsew')
        self.scroll_ids_list['command'] = self.ids_text.yview
        self.ids_text.grid(row=1, column=0, sticky='nsew')
        self.ids_frame.rowconfigure(0, weight=0)
        self.ids_frame.rowconfigure(1, weight=1)
        self.ids_frame.columnconfigure(0, weight=1)
        self.ids_frame.columnconfigure(1, weight=0)
        self.bind_to_mousewheel(self.ids_text)
        self.ids_text.config(state=tk.DISABLED)

        self.lower_frame = ttk.Frame(self.mainframe, padding="0 5 0 0")  # W N E S
        self.lower_frame.grid(row=2, column=0, sticky='nsew')
        self.stop_button = ttk.Button(self.lower_frame, text='Cancel', command=self.destroy, style='Big.TButton')
        self.stop_button.grid(row=0, column=1, sticky='ne')
        self.start_button = ttk.Button(self.lower_frame, text='Proceed', command=self.start_parsing, style='Big.TButton')
        self.start_button.grid(row=0, column=2, sticky='ne')
        self.stop_button.bind('<Return>', self.destroy)
        self.stop_button.bind('<KP_Enter>', self.destroy)
        self.start_button.bind('<Return>', self.start_parsing)
        self.start_button.bind('<KP_Enter>', self.start_parsing)
        self.start_button.focus_set()

        self.lower_frame.rowconfigure(0, weight=0)
        self.lower_frame.columnconfigure(0, weight=1)
        self.lower_frame.columnconfigure(1, weight=0)
        self.lower_frame.columnconfigure(2, weight=0)

        self.mainframe.rowconfigure(0, weight=0)
        self.mainframe.rowconfigure(1, weight=1)
        self.mainframe.rowconfigure(2, weight=0)
        self.mainframe.columnconfigure(0, weight=1)

        self.undefined_attributes: Dict[str, Set[str]] = {}
        self.check_undefined_attributes = {
            'classes': {},
            'ids': {}
        }

    def set_geometry(self):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        geometry = {
            'width': min(screen_width, 1024),
            'height': min(screen_height, 600),
        }
        geometry['left'] = (screen_width // 2) - (geometry['width'] // 2)
        geometry['top'] = (screen_height // 2) - (geometry['height'] // 2)
        self.geometry(
            "{}x{}+{}+{}".format(
                geometry['width'],
                geometry['height'],
                geometry['left'],
                geometry['top']
            )
        )
        self.resizable(width=tk.TRUE, height=tk.TRUE)

    def set_styles(self):
        self.style.configure(
            'TCheckbutton',
            background='white',
            wraplength=self.winfo_width() // 2 - 50
        )
        # self.style.configure('TPanedwindow', background='white')
        self.style.configure(
            'Paned.TLabel',
            wraplength=self.winfo_width() // 2 - 25,
            background='white'
        )

        self.bigger_font = tkfont.Font(font=ttk.Label(self)['font'])
        font_options = self.bigger_font.actual()
        self.bigger_font.configure(size=font_options['size'] + 1, weight='bold')
        self.style.configure(
            'Top.TLabel',
            font=self.bigger_font,
            padding=20,
            wraplength=self.winfo_width() - 50
        )
        self.style.configure('Big.TButton', font=self.bigger_font)
        self.style.configure(
            'Paned.TFrame',
            relief=tk.RIDGE,
            borderwidth=1,
            background='white'
        )

    def update_wraplength(self, event, style):
        style.configure(
            'TCheckbutton',
            wraplength=event.width // 2 - (50 + self.scroll_classes_list.winfo_reqwidth())
        )
        style.configure(
            'Paned.TLabel',
            wraplength=event.width // 2 - 25
        )
        style.configure(
            'Top.TLabel',
            wraplength=event.width - 40
        )

    def start_parsing(self, event=None):
        try:
            self.populate_text_widgets(core.find_attributes_to_delete(self.bk))
        except core.CSSParsingError as E:
            msgbox.showerror('Error while parsing stylesheets', '{}\nThe plugin will terminate.'.format(E))
            self.destroy()
        except core.XHTMLParsingError as E:
            msgbox.showerror('Error while parsing XHTML', '{}\nThe plugin will terminate.'.format(E))
            self.destroy()
        else:
            self.top_label_text.set(
                'Select classes and ids that you want to remove from your xhtml, '
                'than press again the "Proceed" button.'
            )
            self.start_button['command'] = self.proceed

    def proceed(self, event=None):
        for attr_type, attributes in self.check_undefined_attributes.items():
            for attribute, has_to_be_deleted in attributes.items():
                if not has_to_be_deleted.get():
                    self.undefined_attributes[attr_type].discard(attribute)
        core.delete_xhtml_attributes(self.bk, self.undefined_attributes)
        self.success = True
        self.destroy()
    
    def toggle_all_classes(self):
        if self.toggle_classes.get() == 1:
            self.toggle_classes_str.set('Unselect all classes')
            for is_selected in self.check_undefined_attributes['classes'].values():
                is_selected.set(True)
        else:
            self.toggle_classes_str.set('Select all classes')
            for is_selected in self.check_undefined_attributes['classes'].values():
                is_selected.set(False)
        
    def toggle_all_ids(self):
        if self.toggle_ids.get() == 1:
            self.toggle_ids_str.set('Unselect all ids')
            for is_selected in self.check_undefined_attributes['ids'].values():
                is_selected.set(True)
        else:
            self.toggle_ids_str.set('Select all ids')
            for is_selected in self.check_undefined_attributes['ids'].values():
                is_selected.set(False)

    def populate_text_widgets(self, attributes_list: dict):
        self.undefined_attributes = attributes_list
        self.classes_label_text.set(
            'Classes found in XHTML without references in CSS.\nSelect the ones you want to delete:'
        )
        self.classes_text.config(state=tk.NORMAL)
        if attributes_list['classes']:
            self.toggle_classes = tk.BooleanVar()
            self.toggle_classes_str = tk.StringVar()
            self.toggle_classes_str.set('Unselect all classes')
            self.check_toggle_classes = ttk.Checkbutton(
                self.classes_text,
                textvariable=self.toggle_classes_str,
                variable=self.toggle_classes,
                onvalue=True, offvalue=False,
                command=self.toggle_all_classes,
                cursor="arrow"
            )
            self.add_bindtag(self.check_toggle_classes, self.classes_text)
            self.classes_text.window_create('end', window=self.check_toggle_classes)
            self.classes_text.insert('end', '\n\n')
            self.toggle_classes.set(True)
            
            for class_ in attributes_list['classes']:
                occurrences = ', '.join(
                    '{} ({})'.format(utils.href_to_basename(filename), times) for filename, times in
                    attributes_list['info_classes'][class_].items()
                )
                self.check_undefined_attributes['classes'][class_] = tk.BooleanVar()
                class_checkbutton = ttk.Checkbutton(
                    self.classes_text,
                    text='{}   - Found in: {}'.format(class_, occurrences),
                    variable=self.check_undefined_attributes['classes'][class_],
                    onvalue=True, offvalue=False,
                    cursor='arrow'
                )
                self.add_bindtag(class_checkbutton, self.classes_text)
                self.classes_text.window_create('end', window=class_checkbutton)
                self.classes_text.insert('end', '\n')
                self.check_undefined_attributes['classes'][class_].set(True)
        else:
            self.classes_text.insert('end', 'I found no unreferenced classes.')
        self.classes_text.config(state=tk.DISABLED)

        self.ids_label_text.set(
            'Id found in XHTML without references in CSS and in fragment identifiers.\n'
            'Select the ones you want to delete:'
        )
        self.ids_text.config(state=tk.NORMAL)
        if attributes_list['ids']:
            self.toggle_ids = tk.BooleanVar()
            self.toggle_ids_str = tk.StringVar()
            self.toggle_ids_str.set('Unselect all ids')
            self.check_toggle_ids = ttk.Checkbutton(
                self.ids_text,
                textvariable=self.toggle_ids_str,
                variable=self.toggle_ids,
                onvalue=True, offvalue=False,
                command=self.toggle_all_ids,
                cursor="arrow"
            )
            self.add_bindtag(self.check_toggle_ids, self.ids_text)
            self.ids_text.window_create('end', window=self.check_toggle_ids)
            self.ids_text.insert('end', '\n\n')
            self.toggle_ids.set(True)
            for id_ in attributes_list['ids']:
                occurrences = ', '.join(
                    '{} ({})'.format(filename, times) for filename, times in
                    attributes_list['info_ids'][id_].items()
                )
                self.check_undefined_attributes['ids'][id_] = tk.BooleanVar()
                id_checkbutton = ttk.Checkbutton(
                    self.ids_text,
                    text='{}   - Found in: {}'.format(id_, occurrences),
                    variable=self.check_undefined_attributes['ids'][id_],
                    onvalue=True, offvalue=False,
                    cursor='arrow'
                )
                self.add_bindtag(id_checkbutton, self.ids_text)
                self.ids_text.window_create('end', window=id_checkbutton)
                self.ids_text.insert('end', '\n')
                self.check_undefined_attributes['ids'][id_].set(True)
        else:
            self.ids_text.insert('end', 'I found no unreferenced id.')
        self.ids_text.config(state=tk.DISABLED)

    def add_bindtag(self, widget, other):
        bindtags = list(widget.bindtags())
        bindtags.insert(1, str(other))  # self.winfo_pathname(other.winfo_id()))
        widget.bindtags(tuple(bindtags))

    def bind_to_mousewheel(self, widget):
        if sys.platform.startswith("linux"):
            widget.bind("<4>", lambda event: self.scroll_on_mousewheel(event, widget))
            widget.bind("<5>", lambda event: self.scroll_on_mousewheel(event, widget))
        else:
            widget.bind("<MouseWheel>", lambda event: self.scroll_on_mousewheel(event, widget))

    def scroll_on_mousewheel(self, event, widget):
        if event.num == 5 or event.delta < 0:
            move = 1
        else:
            move = -1
        widget.yview_scroll(move, tk.UNITS)
