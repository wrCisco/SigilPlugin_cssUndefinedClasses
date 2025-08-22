#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Copyright (c) 2020, 2025 Francesco Martini
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
import unittest
from unittest.mock import MagicMock, patch

from bookcontainer import BookContainer

from plugin_utils import (
    QtWidgets, QtCore, Qt, QtGui, iswindows
)
import ui
import core
import utils
from wrappingcheckbox import WrappingCheckBox

class MainWindowTestCase(unittest.TestCase):

    def setUp(self):
        bk = MagicMock(spec_set=BookContainer)
        if not QtWidgets.QApplication.instance():
            self.app = QtWidgets.QApplication([])
        prefs = MagicMock()
        self.root = ui.MainWindow(bk, prefs)

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
            self.root.ok_button.click()
        self.assertNotEqual(self.root.check_undefined_attributes['classes'], {})
        for k, v in self.root.check_undefined_attributes['classes'].items():
            with self.subTest(type='classes', key=k, val=v):
                self.assertIn(k, attributes['classes'])
                self.assertIsInstance(v, WrappingCheckBox)
                self.assertEqual(v.isChecked(), True)
        self.assertNotEqual(self.root.check_undefined_attributes['ids'], {})
        for k, v in self.root.check_undefined_attributes['ids'].items():
            with self.subTest(type='ids', key=k, val=v):
                self.assertIn(k, attributes['ids'])
                self.assertIsInstance(v, WrappingCheckBox)
                self.assertEqual(v.isChecked(), True)

        for i in range(self.root.classes_frame_layout.count()):
            widget = self.root.classes_frame_layout.itemAt(i).widget()
            if isinstance(widget, WrappingCheckBox):
                # in WrappingCheckBoxes, setting text on the label
                # is delayed until the widget's show event and the
                # text is split into words and stored
                # in the label._text['words'] list.
                if ''.join(widget.label._text['words']).startswith('anotherclass'):
                    widget.checkbox.click()
        self.assertNotEqual(self.root.check_undefined_attributes['classes'], {})
        for k, v in self.root.check_undefined_attributes['classes'].items():
            with self.subTest(type='classes', key=k, val=v):
                self.assertIn(k, attributes['classes'])
                self.assertIsInstance(v, WrappingCheckBox)
                if k == 'anotherclass':
                    self.assertEqual(v.isChecked(), False)
                else:
                    self.assertEqual(v.isChecked(), True)
        self.assertNotEqual(self.root.check_undefined_attributes['ids'], {})
        for k, v in self.root.check_undefined_attributes['ids'].items():
            with self.subTest(type='ids', key=k, val=v):
                self.assertIn(k, attributes['ids'])
                self.assertIsInstance(v, WrappingCheckBox)
                self.assertEqual(v.isChecked(), True)

        with patch('core.delete_xhtml_attributes'):
            self.root.ok_button.click()
        self.assertEqual(self.root.undefined_attributes['classes'], {'aclass'})
        self.assertEqual(self.root.undefined_attributes['ids'], {'anid', 'anotherid'})


if __name__ == '__main__':
    unittest.main()
