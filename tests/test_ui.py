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

# Code for MainWindowTestCase.pump_events comes from https://stackoverflow.com/a/49028688


import os
import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

from bookcontainer import BookContainer

import ui
import core
import utils


class MainWindowTestCase(unittest.TestCase):

    def setUp(self):
        bk = MagicMock(spec_set=BookContainer)
        self.root = ui.MainWindow(bk)
        self.root.withdraw()  # call root.deiconify followed by pump_events in tests to make the GUI visible
        self.pump_events()

    def tearDown(self):
        if self.root.is_running:
            self.root.destroy()
            self.pump_events()

    def pump_events(self):
        while self.root.dooneevent(tk._tkinter.ALL_EVENTS | tk._tkinter.DONT_WAIT):
            pass

    def test_proceed_select_proceed(self):
        """
        User launches the plugin,
        then presses the 'Proceed' button,
        unselects some classes/ids,
        then again presses the 'Proceed' button.
        """
        attributes = {
            'classes': {'aclass', 'anotherclass'},
            'ids': {'anid', 'anotherid'},
            'info_classes': {
                'aclass': {'Text/Section0001.xhtml': 5, 'Text/Section0002.xhtml': 3},
                'anotherclass': {'Text/Section0001.xhtml': 4}
            },
            'info_ids': {
                'anid': {'Text/Section0001.xhtml': 1, 'nav.xhtml': 1},
                'anotherid': {'Text/Section0001.xhtml': 1}
            }
        }
        with patch('core.find_attributes_to_delete', return_value=attributes):
            self.root.start_button.event_generate('<<Invoke>>')
            # self.root.start_button.event_generate('<Button-1>')
            # self.root.start_button.event_generate('<ButtonRelease-1>')
            self.pump_events()
        self.assertNotEqual(self.root.check_undefined_attributes['classes'], {})
        for k, v in self.root.check_undefined_attributes['classes'].items():
            with self.subTest(type='classes', key=k, val=v):
                self.assertIn(k, attributes['classes'])
                self.assertIsInstance(v, tk.BooleanVar)
                self.assertEqual(v.get(), True)
        self.assertNotEqual(self.root.check_undefined_attributes['ids'], {})
        for k, v in self.root.check_undefined_attributes['ids'].items():
            with self.subTest(type='ids', key=k, val=v):
                self.assertIn(k, attributes['ids'])
                self.assertIsInstance(v, tk.BooleanVar)
                self.assertEqual(v.get(), True)

        for checkbutton in utils.tk_iterate_children(self.root.classes_text):
            if checkbutton['text'].startswith('anotherclass '):
                checkbutton.event_generate('<<Invoke>>')
                # checkbutton.event_generate('<Button-1>')
                # checkbutton.event_generate('<ButtonRelease-1>')
        self.pump_events()
        self.assertNotEqual(self.root.check_undefined_attributes['classes'], {})
        for k, v in self.root.check_undefined_attributes['classes'].items():
            with self.subTest(type='classes', key=k, val=v):
                self.assertIn(k, attributes['classes'])
                self.assertIsInstance(v, tk.BooleanVar)
                if k == 'anotherclass':
                    self.assertEqual(v.get(), False)
                else:
                    self.assertEqual(v.get(), True)
        self.assertNotEqual(self.root.check_undefined_attributes['ids'], {})
        for k, v in self.root.check_undefined_attributes['ids'].items():
            with self.subTest(type='ids', key=k, val=v):
                self.assertIn(k, attributes['ids'])
                self.assertIsInstance(v, tk.BooleanVar)
                self.assertEqual(v.get(), True)

        with patch('core.delete_xhtml_attributes'):
            self.root.start_button.event_generate('<<Invoke>>')
            # self.root.start_button.event_generate('<Button-1>')
            # self.root.start_button.event_generate('<ButtonRelease-1>')
            self.pump_events()
        self.assertEqual(self.root.undefined_attributes['classes'], {'aclass'})
        self.assertEqual(self.root.undefined_attributes['ids'], {'anid', 'anotherid'})
        self.assertFalse(self.root.is_running)

    @patch('ui.sys', platform='linux')
    def test_set_theme_on_linux(self, mock_yes_its_linux):
        """
        While in Win and Mac Tkinter uses native widgets, for Linux
        the plugin uses the embedded clearlooks theme.
        Clearlooks is used by default, but Linux users can change
        the preference 'tktheme' to something else.
        The preference will be used only if it's in ttk.Style().theme_names().
        """
        prefs = {'tktheme': 'clearlooks'}
        self.root.prefs.get.side_effect = prefs.get
        self.root.prefs.__getitem__.side_effect = prefs.__getitem__
        root_dir = os.path.dirname(utils.SCRIPT_DIR)
        with patch('ui.utils', SCRIPT_DIR=root_dir):
            self.root.set_theme()
            self.pump_events()
            self.assertEqual(self.root.style.theme_use(), 'clearlooks')
            themes = self.root.style.theme_names()
            prefs['tktheme'] = themes[0]
            self.root.set_theme()
            self.pump_events()
            self.assertEqual(self.root.style.theme_use(), prefs['tktheme'])
            non_existent = 'x'
            while non_existent in self.root.style.theme_names():
                non_existent += 'x'
            prefs['tktheme'] = non_existent
            self.root.set_theme()
            self.pump_events()
            self.assertNotEqual(self.root.style.theme_use(), prefs['tktheme'])
            self.assertEqual(self.root.style.theme_use(), themes[0])

    def test_set_fonts(self):
        class MW(ui.MainWindow):
            def __init__(self):  # noqa
                self.style = ttk.Style()
        mw = MW()
        default_font = tkfont.nametofont('TkDefaultFont')
        text_font = tkfont.nametofont('TkTextFont')
        mw.set_fonts()
        self.assertEqual(text_font.actual(), mw.text_font.actual())
        for k, v in default_font.actual().items():
            with self.subTest(key=k, val=v):
                if k == 'size':
                    self.assertEqual(v + 2, mw.heading_label_font.actual()[k])
                else:
                    self.assertEqual(v, mw.heading_label_font.actual()[k])


if __name__ == '__main__':
    unittest.main()
