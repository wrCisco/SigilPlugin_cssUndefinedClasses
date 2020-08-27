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


import os
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as msgbox
import tkinter.font as tkfont
from typing import Dict, Set

import regex as re

import core
import utils


class WidgetMixin(tk.BaseWidget):

    def bind_to_mousewheel(self, widget):
        if sys.platform.startswith("linux"):
            widget.bind("<4>", lambda event: self.scroll_on_mousewheel(event, widget))
            widget.bind("<5>", lambda event: self.scroll_on_mousewheel(event, widget))
        else:
            widget.bind("<MouseWheel>", lambda event: self.scroll_on_mousewheel(event, widget))

    @staticmethod
    def scroll_on_mousewheel(event, widget):
        if event.num == 5 or event.delta < 0:
            move = 1
        else:
            move = -1
        widget.yview_scroll(move, tk.UNITS)

    @staticmethod
    def add_bindtag(widget, other):
        bindtags = list(widget.bindtags())
        bindtags.insert(1, str(other))  # self.winfo_pathname(other.winfo_id()))
        widget.bindtags(tuple(bindtags))


class MainWindow(tk.Tk, WidgetMixin):

    def __init__(self, bk):
        self.bk = bk
        self.prefs = self.get_prefs()
        self.success = False  # True when the plugin terminates correctly
        self.undefined_attributes: Dict[str, Set[str]] = {}
        self.check_undefined_attributes = {
            'classes': {},
            'ids': {}
        }

        super().__init__()
        self.style = ttk.Style()
        self.title("cssUndefinedClasses")
        self.set_geometry()
        self.set_fonts()
        self.set_styles()
        self.is_running = True
        self.protocol('WM_DELETE_WINDOW', self.close)
        try:
            icon = tk.PhotoImage(file=os.path.join(utils.SCRIPT_DIR, 'plugin.png'))
            self.iconphoto(True, icon)
        except Exception as E:
            # print("Error in setting plugin's icon: {}".format(E))
            pass

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.mainframe = ttk.Frame(self, padding="5 0 5 5")  # W N E S
        self.mainframe.grid(row=0, column=0, sticky="nsew")
        self.mainframe.bind(
            '<Configure>',
            lambda event: self.update_full_wraplength(event)
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

        self.classes_frame = ttk.Frame(self.panedwindow, style='Paned.TFrame', padding=0)
        self.ids_frame = ttk.Frame(self.panedwindow, style='Paned.TFrame', padding=0)
        self.panedwindow.add(self.classes_frame, weight=1)
        self.panedwindow.add(self.ids_frame, weight=1)
        self.classes_frame.bind(
            '<Configure>',
            lambda event: self.update_paned_wraplength(event, 'Classes.InText')
        )
        self.ids_frame.bind(
            '<Configure>',
            lambda event: self.update_paned_wraplength(event, 'Ids.InText')
        )

        self.scroll_classes_list = ttk.Scrollbar(self.classes_frame, orient=tk.VERTICAL)
        self.classes_text = tk.Text(
            self.classes_frame,
            yscrollcommand=self.scroll_classes_list.set,
            borderwidth=0,
            highlightbackground='#999',
            highlightcolor='#999',
            highlightthickness=1,
            padx=0, pady=0,
            relief=tk.FLAT,
            font=self.text_heading_font,
            wrap=tk.WORD
        )
        self.classes_text.tag_config(
            'heading',
            background=self.text_heading_bg, foreground=self.text_heading_fg,
            spacing1=6, spacing3=6, lmargin1=6, lmargin2=6, rmargin=6
        )
        self.classes_text.tag_config(
            'body',
            lmargin1=6, lmargin2=6, rmargin=6
        )
        self.scroll_classes_list.grid(row=0, column=1, sticky='nsew')
        self.scroll_classes_list['command'] = self.classes_text.yview
        self.classes_text.grid(row=0, column=0, sticky='nsew')
        self.classes_frame.rowconfigure(0, weight=1)
        self.classes_frame.columnconfigure(0, weight=1)
        self.classes_frame.columnconfigure(1, weight=0)
        self.bind_to_mousewheel(self.classes_text)
        self.classes_text.config(state=tk.DISABLED)

        self.scroll_ids_list = ttk.Scrollbar(self.ids_frame, orient=tk.VERTICAL)
        self.ids_text = tk.Text(
            self.ids_frame,
            yscrollcommand=self.scroll_ids_list.set,
            borderwidth=0,
            highlightbackground='#999',
            highlightcolor='#999',
            highlightthickness=1,
            padx=0, pady=0,
            relief=tk.FLAT,
            font=self.text_heading_font,
            wrap=tk.WORD
        )
        self.ids_text.tag_config(
            'heading',
            background=self.text_heading_bg, foreground=self.text_heading_fg,
            spacing1=6, spacing3=6, lmargin1=6, lmargin2=6, rmargin=6
        )
        self.ids_text.tag_config(
            'body',
            lmargin1=6, lmargin2=6, rmargin=6
        )
        self.scroll_ids_list.grid(row=0, column=1, sticky='nsew')
        self.scroll_ids_list['command'] = self.ids_text.yview
        self.ids_text.grid(row=0, column=0, sticky='nsew')
        self.ids_frame.rowconfigure(0, weight=1)
        self.ids_frame.columnconfigure(0, weight=1)
        self.ids_frame.columnconfigure(1, weight=0)
        self.bind_to_mousewheel(self.ids_text)
        self.ids_text.config(state=tk.DISABLED)

        # self.warning_frame = ttk.Frame(self.mainframe, padding="0 5 0 0")
        # self.warning_frame.grid(row=2, column=0, sticky='nsew')
        self.warning_text = tk.StringVar()
        self.warning_label = ttk.Label(
            self.mainframe,
            textvariable=self.warning_text,
            style='Warning.TLabel'
        )
        self.warning_label.grid(row=2, column=0, sticky='nsew')
        self.update_warning()

        self.lower_frame = ttk.Frame(self.mainframe, padding="0 5 0 0")  # W N E S
        self.lower_frame.grid(row=3, column=0, sticky='nsew')
        self.prefs_button = ttk.Button(self.lower_frame, text='Preferences', command=self.prefs_dlg)
        self.prefs_button.grid(row=0, column=0, sticky='nw')
        self.stop_button = ttk.Button(self.lower_frame, text='Cancel', command=self.close)
        self.stop_button.grid(row=0, column=2, sticky='ne')
        self.start_button = ttk.Button(self.lower_frame, text='Proceed', command=self.start_parsing)
        self.start_button.grid(row=0, column=3, sticky='ne')
        self.stop_button.bind('<Return>', self.close)
        self.stop_button.bind('<KP_Enter>', self.close)
        self.start_button.bind('<Return>', self.start_parsing)
        self.start_button.bind('<KP_Enter>', self.start_parsing)
        self.start_button.focus_set()

        self.lower_frame.rowconfigure(0, weight=0)
        self.lower_frame.columnconfigure(0, weight=0)
        self.lower_frame.columnconfigure(1, weight=1)
        self.lower_frame.columnconfigure(2, weight=0)
        self.lower_frame.columnconfigure(3, weight=0)

        self.mainframe.rowconfigure(0, weight=0)
        self.mainframe.rowconfigure(1, weight=1)
        self.mainframe.rowconfigure(2, weight=0)
        self.mainframe.rowconfigure(3, weight=0)
        self.mainframe.columnconfigure(0, weight=1)

    def close(self):
        self.is_running = False
        self.destroy()

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

    def set_fonts(self):
        dummy_label, dummy_text = ttk.Label(self), tk.Text(self)
        self.heading_label_font = tkfont.Font(font=dummy_label['font'])
        label_font_options = self.heading_label_font.actual()
        # self.heading_label_font.configure(size=label_font_options['size'], weight='bold')
        self.text_heading_font = tkfont.Font(font=dummy_text['font'])
        self.text_heading_font.configure(family=label_font_options['family'])
        dummy_label.destroy()
        dummy_text.destroy()

    def set_styles(self):
        if sys.platform.startswith('linux'):
            self.tk.eval(f'''
package ifneeded ttk::theme::clearlooks 0.1 \
    [list source [file join {os.path.join(utils.SCRIPT_DIR, 'clearlooks')} clearlooks.tcl]]
'''
            )
            self.tk.call('package', 'require', 'ttk::theme::clearlooks', '0.1')
            self.style.theme_use('clearlooks')

        dummy_text = tk.Text(self)
        bg = dummy_text['background']
        fg = dummy_text['foreground']
        dummy_text.destroy()
        is_dark_text_bg = False
        if re.fullmatch(r'#[0-9A-Fa-f]{6}', bg):
            for channel in range(1, len(bg), 2):
                if int(bg[channel:channel+2], 16) > 96:
                    break
            else:  # for-else
                is_dark_text_bg = True
        # text colors and background for text widgets header
        if is_dark_text_bg:
            self.text_heading_bg = '#414649'
            self.text_heading_fg = '#F2F2F2'
        else:
            self.text_heading_bg = '#F2F2F2'
            self.text_heading_fg = '#0D0D0D'
        self.style.configure(
            'InText.TCheckbutton',
            background=bg,
            foreground=fg
        )
        self.style.configure(
            'Classes.InText.TCheckbutton',
            wraplength=self.winfo_width() // 2 - 50
        )
        self.style.configure(
            'Ids.InText.TCheckbutton',
            wraplength=self.winfo_width() // 2 - 50
        )
        if is_dark_text_bg:
            self.style.map(
                'InText.TCheckbutton',
                background=[('hover', self.text_heading_fg)],
                foreground=[('hover', self.text_heading_bg)]
            )
        self.style.configure(
            'Top.TLabel',
            font=self.heading_label_font,
            padding=20,
            wraplength=self.winfo_width() - 50
        )
        self.style.configure(
            'Warning.TLabel',
            padding='0 5 0 0',
            wraplength=self.winfo_width() - 50
        )

    def update_full_wraplength(self, event):
        self.style.configure(
            'Top.TLabel',
            wraplength=event.width - 50
        )
        self.style.configure(
            'Warning.TLabel',
            wraplength=event.width - 50
        )

    def update_paned_wraplength(self, event, classname):
        self.style.configure(
            '{}.TCheckbutton'.format(classname),
            wraplength=event.width - (40 + self.scroll_classes_list.winfo_reqwidth())
        )

    def start_parsing(self, event=None):
        try:
            self.populate_text_widgets(core.find_attributes_to_delete(self.bk, self.prefs))
        except core.CSSParsingError as E:
            msgbox.showerror('Error while parsing stylesheets', '{}\nThe plugin will terminate.'.format(E))
            self.close()
        except core.XMLParsingError as E:
            msgbox.showerror('Error while parsing an XML or XHTML file', '{}\nThe plugin will terminate.'.format(E))
            self.close()
        else:
            self.top_label_text.set(
                'Select classes and ids that you want to remove from your xhtml, '
                'then press again the "Proceed" button.'
            )
            self.prefs_button.configure(state=tk.DISABLED)
            self.warning_text.set(
                'Search for classes and ids to remove has been done on {} files.'.format(
                    'selected' if self.prefs['parse_only_selected_files'] else 'all xhtml'
                )
            )
            self.start_button['command'] = self.delete_selected_attributes
            self.start_button.bind('<Return>', self.delete_selected_attributes)
            self.start_button.bind('<KP_Enter>', self.delete_selected_attributes)

    def delete_selected_attributes(self, event=None):
        for attr_type, attributes in self.check_undefined_attributes.items():
            for attribute, has_to_be_deleted in attributes.items():
                if not has_to_be_deleted.get():
                    self.undefined_attributes[attr_type].discard(attribute)
        core.delete_xhtml_attributes(self.bk, self.undefined_attributes, self.prefs)
        self.success = True
        # reset selected files on success
        self.prefs['selected_files'] = []
        self.bk.savePrefs(self.prefs)
        self.close()

    def toggle_all_classes(self):
        if self.toggle_classes.get() == 1:
            self.toggle_classes_str.set('Unselect all')
            for is_selected in self.check_undefined_attributes['classes'].values():
                is_selected.set(True)
        else:
            self.toggle_classes_str.set('Select all')
            for is_selected in self.check_undefined_attributes['classes'].values():
                is_selected.set(False)

    def toggle_all_ids(self):
        if self.toggle_ids.get() == 1:
            self.toggle_ids_str.set('Unselect all')
            for is_selected in self.check_undefined_attributes['ids'].values():
                is_selected.set(True)
        else:
            self.toggle_ids_str.set('Select all')
            for is_selected in self.check_undefined_attributes['ids'].values():
                is_selected.set(False)

    def populate_text_widgets(self, attributes_list: dict):
        self.undefined_attributes = attributes_list
        self.classes_text.config(state=tk.NORMAL)
        self.classes_text.insert(
            'insert',
            'Classes found in XHTML without references in CSS.\nSelect the ones you want to delete:\n',
            'heading'
        )
        self.classes_text.insert('insert', '\n')
        if attributes_list['classes']:
            self.toggle_classes = tk.BooleanVar()
            self.toggle_classes_str = tk.StringVar()
            self.toggle_classes_str.set('Unselect all')
            self.check_toggle_classes = ttk.Checkbutton(
                self.classes_text,
                textvariable=self.toggle_classes_str,
                variable=self.toggle_classes,
                onvalue=True, offvalue=False,
                command=self.toggle_all_classes,
                cursor="arrow",
                style='Classes.InText.TCheckbutton'
            )
            self.add_bindtag(self.check_toggle_classes, self.classes_text)
            self.classes_text.window_create('end', window=self.check_toggle_classes, padx=4, pady=2)
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
                    text='{}  -  Found in: {}'.format(class_, occurrences),
                    variable=self.check_undefined_attributes['classes'][class_],
                    onvalue=True, offvalue=False,
                    cursor='arrow',
                    style='Classes.InText.TCheckbutton'
                )
                self.add_bindtag(class_checkbutton, self.classes_text)
                self.classes_text.window_create('end', window=class_checkbutton, padx=4, pady=2)
                self.classes_text.insert('end', '\n')
                self.check_undefined_attributes['classes'][class_].set(True)
        else:
            self.classes_text.insert('end', 'I found no unreferenced classes.', 'body')
        self.classes_text.config(state=tk.DISABLED)

        self.ids_text.config(state=tk.NORMAL)
        self.ids_text.insert(
            'insert',
            'Ids found in XHTML without references in CSS nor in fragment identifiers.\n'
            'Select the ones you want to delete:\n',
            'heading'
        )
        self.ids_text.insert('insert', '\n')
        if attributes_list['ids']:
            self.toggle_ids = tk.BooleanVar()
            self.toggle_ids_str = tk.StringVar()
            self.toggle_ids_str.set('Unselect all')
            self.check_toggle_ids = ttk.Checkbutton(
                self.ids_text,
                textvariable=self.toggle_ids_str,
                variable=self.toggle_ids,
                onvalue=True, offvalue=False,
                command=self.toggle_all_ids,
                cursor="arrow",
                style='Ids.InText.TCheckbutton'
            )
            self.add_bindtag(self.check_toggle_ids, self.ids_text)
            self.ids_text.window_create('end', window=self.check_toggle_ids, padx=4, pady=2)
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
                    text='{}  -  Found in: {}'.format(id_, occurrences),
                    variable=self.check_undefined_attributes['ids'][id_],
                    onvalue=True, offvalue=False,
                    cursor='arrow',
                    style='Ids.InText.TCheckbutton'
                )
                self.add_bindtag(id_checkbutton, self.ids_text)
                self.ids_text.window_create('end', window=id_checkbutton, padx=4, pady=2)
                self.ids_text.insert('end', '\n')
                self.check_undefined_attributes['ids'][id_].set(True)
        else:
            self.ids_text.insert('end', 'I found no unreferenced ids.', 'body')
        self.ids_text.config(state=tk.DISABLED)

    def get_prefs(self):
        prefs = self.bk.getPrefs()

        prefs.defaults['parse_only_selected_files'] = False
        prefs.defaults['selected_files'] = []
        prefs.defaults['fragid_container_attrs'] = []  # if empty, use core.XHTMLAttributes

        return prefs

    def prefs_dlg(self):
        w = PrefsDialog(self, self.bk)
        self.wait_window(w)
        self.update_warning()

    def update_warning(self):
        self.warning_text.set(
            '{} files will be searched for classes and ids to remove. '
            'Open the Preferences pane to update this option.'.format(
                'Only selected' if self.prefs['parse_only_selected_files'] else 'All xhtml'
            )
        )


class PrefsDialog(tk.Toplevel, WidgetMixin):

    def __init__(self, parent=None, bk=None, prefs=None):
        self.bk = bk
        if prefs:
            self.prefs = prefs
        else:
            self.prefs = parent.prefs

        super().__init__(parent)
        self.transient(parent)
        self.title('Preferences')
        self.geometry('600x400')
        self.resizable(width=tk.TRUE, height=tk.TRUE)
        self.protocol('WM_DELETE_WINDOW', self.destroy)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.mainframe = ttk.Frame(self, padding="12 12 12 12")  # W N E S
        self.mainframe.grid(column=0, row=0, sticky='nwes')
        self.mainframe.bind(
            '<Configure>',
            self.update_full_width
        )

        self.master.style.configure(
            'Preferences.TCheckbutton',
            wraplength=self.winfo_width() - 45
        )
        self.parse_only_selected_value = tk.BooleanVar()
        self.parse_only_selected_check = ttk.Checkbutton(
            self.mainframe,
            text='Search for classes and ids to remove only in selected files',
            variable=self.parse_only_selected_value,
            onvalue=True, offvalue=False,
            style='Preferences.TCheckbutton'
        )
        self.parse_only_selected_check.grid(row=0, column=0, sticky='nsew')
        self.selected_files_frame = ttk.Frame(self.mainframe)
        self.selected_files_frame.grid(row=1, column=0, sticky='nsew')
        self.selected_files_value = tk.StringVar()
        self.selected_files_scroll = ttk.Scrollbar(self.selected_files_frame, orient=tk.VERTICAL)
        self.selected_files_list = tk.Listbox(
            self.selected_files_frame,
            activestyle='dotbox',
            selectmode=tk.MULTIPLE,
            yscrollcommand=self.selected_files_scroll.set,
            listvariable=self.selected_files_value
        )
        self.selected_files_value.set(' '.join('"{}"'.format(href) for id_, href in self.bk.text_iter()))
        self.selected_files_font = tkfont.Font(font=self.selected_files_list['font'])
        self.selected_files_list.grid(sticky='nsew')
        self.selected_files_scroll.grid(row=0, column=1, sticky='nsew')
        self.selected_files_scroll['command'] = self.selected_files_list.yview
        # self.bind_to_mousewheel(self.selected_files_list)
        self.selected_files_frame.rowconfigure(0, weight=1)
        self.selected_files_frame.columnconfigure(0, weight=1)

        self.fragid_attrs_label = ttk.Label(
            self.mainframe,
            text='Comma separated list of attributes that will be used to search for fragment identifiers '
                 '(an empty list will default to {}).'.format(', '.join(core.XHTMLAttributes.fragid_container_attrs)),
            wraplength=self.mainframe.winfo_width() - 30,
            padding='0 18 0 6'
        )
        self.fragid_attrs_label.grid(row=2, column=0, sticky='nsew')
        self.fragid_attrs_value = tk.StringVar()
        self.fragid_attrs_entry = ttk.Entry(
            self.mainframe,
            textvariable=self.fragid_attrs_value,
            exportselection=0
        )
        self.fragid_font = tkfont.Font(font=self.fragid_attrs_entry['font'])
        fragid_entry_width = self.mainframe.winfo_reqwidth() // self.fragid_font.measure('m')
        self.fragid_attrs_entry.configure(width=fragid_entry_width)
        self.fragid_attrs_entry.grid(row=3, column=0, sticky='nsew')

        self.lower_frame = ttk.Frame(self.mainframe, padding="0 12 0 0")
        self.lower_frame.grid(row=4, column=0, sticky='nsew')

        self.cancel_button = ttk.Button(self.lower_frame, text='Cancel', command=self.destroy)
        self.cancel_button.grid(row=0, column=1, sticky='ne')
        self.ok_button = ttk.Button(self.lower_frame, text='OK', command=self.save_and_proceed)
        self.ok_button.grid(row=0, column=2, sticky='ne')
        self.cancel_button.bind('<Return>', self.destroy)
        self.cancel_button.bind('<KP_Enter>', self.destroy)
        self.ok_button.bind('<Return>', self.save_and_proceed)
        self.ok_button.bind('<KP_Enter>', self.save_and_proceed)

        self.lower_frame.rowconfigure(0, weight=0)
        self.lower_frame.columnconfigure(0, weight=1)
        self.lower_frame.columnconfigure(1, weight=0)
        self.lower_frame.columnconfigure(2, weight=0)

        self.mainframe.rowconfigure(1, weight=1)
        self.mainframe.columnconfigure(0, weight=1)

        self.ok_button.focus_set()
        self.grab_set()

        self.get_initial_values()

    def get_initial_values(self):
        if self.prefs.get('fragid_container_attrs'):
            self.fragid_attrs_value.set(', '.join(self.prefs['fragid_container_attrs']))
        else:
            self.fragid_attrs_value.set(', '.join(core.XHTMLAttributes.fragid_container_attrs))
        if self.prefs.get('parse_only_selected_files'):
            self.parse_only_selected_value.set(1)
        else:
            self.parse_only_selected_value.set(0)
        if self.prefs.get('selected_files'):
            selected_files = [self.bk.href_to_id(sel) for sel in self.prefs.get('selected_files')]
        else:
            selected_files = [selected[1] for selected in self.bk.selected_iter()]
        if selected_files:
            selected_files_names = [self.bk.id_to_href(sel) for sel in selected_files]
            lines = self.selected_files_list.get(0, self.selected_files_list.size()-1)
            for index, name in enumerate(lines):
                if name in selected_files_names:
                    self.selected_files_list.selection_set(index)

    def save_and_proceed(self, event=None):
        fragid_attrs = self.fragid_attrs_value.get()
        self.prefs['fragid_container_attrs'] = [attr.strip() for attr in fragid_attrs.split(',') if attr]
        if self.parse_only_selected_value.get() == 1:
            self.prefs['parse_only_selected_files'] = True
        else:
            self.prefs['parse_only_selected_files'] = False
        # reset selected_files in the prefs dictionary before saving: this value doesn't have to be saved permanently
        self.prefs['selected_files'] = []
        self.bk.savePrefs(self.prefs)
        selected_files = [self.selected_files_list.get(i) for i in self.selected_files_list.curselection()]
        self.prefs['selected_files'] = selected_files
        self.destroy()

    def update_full_width(self, event=None):
        self.fragid_attrs_label.configure(wraplength=event.width - 30)
        fragid_entry_width = event.width // self.fragid_font.measure('0')
        self.fragid_attrs_entry.configure(width=fragid_entry_width)
        self.master.style.configure('Preferences.TCheckbutton', wraplength=event.width - 45)
