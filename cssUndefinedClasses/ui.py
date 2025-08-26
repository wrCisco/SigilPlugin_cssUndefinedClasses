#!/usr/bin/env python

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


import sys
from collections.abc import MutableMapping

import regex as re
from bookcontainer import BookContainer
from preferences import JSONPrefs

from plugin_utils import (
    PluginApplication, QtWidgets, QtCore, Qt, QtGui, iswindows
)
from wrappingcheckbox import WrappingCheckBox
import core
import utils


class MainWindow(QtWidgets.QWidget):

    def __init__(
            self,
            bk: BookContainer,
            prefs: JSONPrefs,
            parent: QtWidgets.QWidget | None = None) -> None:
        self.bk = bk
        self.prefs = prefs
        self.undefined_attributes: core.AttributesToDelete
        self.check_undefined_attributes: dict[str, dict[str, QtWidgets.QCheckBox]] = {
            'classes': {},
            'ids': {},
        }

        super().__init__(parent)
        self.setWindowTitle("cssUndefinedClasses")
        self.set_geometry()

        main_layout = QtWidgets.QGridLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.top_label = QtWidgets.QLabel(
            'Welcome! Please press the "Proceed" button to begin.'
        )
        self.top_label.setWordWrap(True)
        main_layout.addWidget(self.top_label, 0, 0, 1, -1)

        paned_window = QtWidgets.QSplitter()

        classes_area = QtWidgets.QScrollArea()
        classes_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        classes_area.setWidgetResizable(True)
        classes_area.setContentsMargins(0, 0, 0, 0)
        self.classes_frame_layout = QtWidgets.QVBoxLayout()
        self.classes_frame_layout.setSpacing(0)
        self.classes_frame_layout.setContentsMargins(0, 0, 0, 0)
        classes_frame = QtWidgets.QWidget()
        classes_frame.setLayout(self.classes_frame_layout)
        classes_area.setWidget(classes_frame)
        classes_area.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        ids_area = QtWidgets.QScrollArea()
        ids_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        ids_area.setWidgetResizable(True)
        self.ids_frame_layout = QtWidgets.QVBoxLayout()
        self.ids_frame_layout.setSpacing(0)
        self.ids_frame_layout.setContentsMargins(0, 0, 0, 0)
        ids_frame = QtWidgets.QWidget()
        ids_frame.setLayout(self.ids_frame_layout)
        ids_area.setWidget(ids_frame)
        ids_area.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        paned_window.addWidget(classes_area)
        paned_window.addWidget(ids_area)

        main_layout.addWidget(paned_window, 1, 0, 1, -1)
        main_layout.setRowStretch(1, 1)

        self.warning_label = QtWidgets.QLabel()
        self.warning_label.setWordWrap(True)
        self.update_warning()

        main_layout.addWidget(self.warning_label, 2, 0, 1, -1)

        self.prefs_button = QtWidgets.QPushButton('Preferences')
        self.prefs_button.clicked.connect(self.prefs_dlg)
        self.prefs_button.setAutoDefault(True)
        self.stop_button = QtWidgets.QPushButton('Cancel')
        self.stop_button.clicked.connect(lambda: QtWidgets.QApplication.exit(0))
        self.stop_button.setAutoDefault(True)
        self.ok_button = QtWidgets.QPushButton('Proceed')
        self.ok_button.clicked.connect(self.start_parsing)
        self.ok_button.setAutoDefault(True)

        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addWidget(self.prefs_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addWidget(self.ok_button)

        main_layout.addLayout(buttons_layout, 3, 0, 1, -1)

        self.show()
        self.ok_button.setFocus()

    def set_geometry(self) -> None:
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        screen = self.screen()
        if not screen:
            return
        available_size = screen.availableSize()
        screen_width = available_size.width()
        screen_height = available_size.height()
        width = min(screen_width, 1024)
        if width < self.minimumWidth():
            self.setMinimumWidth(width)
        height = min(screen_height, 600)
        if height < self.minimumHeight():
            self.setMinimumHeight(height)
        left = screen_width // 2 - width // 2
        top = screen_height // 2 - height // 2
        self.setGeometry(left, top, width, height)

    def update_warning(self, event: QtCore.QEvent | None = None) -> None:
        self.warning_label.setText(
            '{} files will be searched for classes and ids to remove. '
            'Open the Preferences pane to update this option.'.format(
                'Only selected' if self.prefs['parse_only_selected_files'] else 'All xhtml'
            )
        )

    def prefs_dlg(self, event: QtCore.QEvent | None = None) -> None:
        w = PrefsDialog(self.bk, self.prefs, self)
        w.accepted.connect(self.update_warning)
        w.open()

    def start_parsing(self, event: QtCore.QEvent | None = None) -> None:
        try:
            attributes_to_delete = core.find_attributes_to_delete(self.bk, self.prefs)
        except core.CSSParsingError as E:
            QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Icon.Critical,
                'Error while parsing stylesheets',
                f'{E}\nThe plugin will terminate.',
                QtWidgets.QMessageBox.StandardButton.Ok,
                self
            ).exec()
            QtWidgets.QApplication.exit(2)
        except core.XMLParsingError as E:
            QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Icon.Critical,
                'Error while parsing an XML or XHTML file',
                f'{E}\nThe plugin will terminate.',
                QtWidgets.QMessageBox.StandardButton.Ok,
                self
            ).exec()
            QtWidgets.QApplication.exit(2)
        else:
            self.populate_text_widgets(attributes_to_delete)
            self.top_label.setText(
                'Select classes and ids that you want to remove from your xhtml, '
                'then press again the "Proceed" button.'
            )
            self.prefs_button.setEnabled(False)
            self.warning_label.setText(
                'The search for classes and ids to remove has been done on {} files.'.format(
                    'selected' if self.prefs['parse_only_selected_files'] else 'all xhtml'
                )
            )
            if self.ok_button.clicked.connect(self.start_parsing):
                self.ok_button.clicked.disconnect()
            self.ok_button.clicked.connect(self.delete_selected_attributes)

    def populate_text_widgets(self, attributes_list: core.AttributesToDelete) -> None:
        self.undefined_attributes = attributes_list

        margins_checkboxes = (8, 6, 8, 6)
        margins_headers = (8, 12, 8, 0)

        classes_header = QtWidgets.QLabel(
            'Classes found in XHTML without references in CSS.\n' \
            'Select the ones you want to delete:\n',
        )
        classes_header.setWordWrap(True)
        classes_header.setContentsMargins(*margins_headers)
        classes_header.setAutoFillBackground(True)
        self.classes_frame_layout.addWidget(classes_header)

        palette = classes_header.palette()
        bgColor = palette.color(classes_header.backgroundRole())
        alternateBgColor = palette.color(QtGui.QPalette.ColorRole.AlternateBase)
        if bgColor.getRgb() == alternateBgColor.getRgb():
            alternateBgColor = palette.color(QtGui.QPalette.ColorRole.Base)
        palette.setColor(classes_header.backgroundRole(), alternateBgColor)
        classes_header.setPalette(palette)

        classes_header_separator = QtWidgets.QFrame()
        classes_header_separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        classes_header_separator.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.classes_frame_layout.addWidget(classes_header_separator)

        if attributes_list['classes']:
            self.toggle_classes = WrappingCheckBox(
                'Select / Unselect all',
                margins=(8, 12, 8, 12)
            )
            self.toggle_classes.setChecked(True)
            self.toggle_classes.stateChanged().connect(self.toggle_all_classes)
            self.classes_frame_layout.addWidget(self.toggle_classes)
            
            self._display_attributes_checkboxes(
                attributes_list,
                'classes',
                self.classes_frame_layout,
                margins_checkboxes,
                alternateBgColor
            )
        else:
            no_classes_label = QtWidgets.QLabel('I found no unreferenced classes.')
            no_classes_label.setWordWrap(True)
            no_classes_label.setContentsMargins(*margins_checkboxes)
            self.classes_frame_layout.addWidget(no_classes_label)

        classes_bottom_separator = QtWidgets.QFrame()
        classes_bottom_separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        classes_bottom_separator.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        classes_bottom_separator.setLineWidth(0)
        classes_bottom_separator.setMidLineWidth(1)
        self.classes_frame_layout.addWidget(classes_bottom_separator)

        self.classes_frame_layout.addStretch()

        ids_header = QtWidgets.QLabel(
            'Ids found in XHTML without references in CSS nor in other XHTML or XML files.\n' \
            'Select the ones you want to delete:\n',
        )
        ids_header.setWordWrap(True)
        ids_header.setContentsMargins(*margins_headers)
        ids_header.setAutoFillBackground(True)
        self.ids_frame_layout.addWidget(ids_header)

        palette = ids_header.palette()
        palette.setColor(ids_header.backgroundRole(), alternateBgColor)
        ids_header.setPalette(palette)

        ids_header_separator = QtWidgets.QFrame()
        ids_header_separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        ids_header_separator.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.ids_frame_layout.addWidget(ids_header_separator)

        if attributes_list['ids']:
            self.toggle_ids = WrappingCheckBox(
                'Select / Unselect all',
                margins=(8, 12, 8, 12)
            )
            self.toggle_ids.setChecked(True)
            self.toggle_ids.stateChanged().connect(self.toggle_all_ids)
            self.ids_frame_layout.addWidget(self.toggle_ids)

            self._display_attributes_checkboxes(
                attributes_list,
                'ids',
                self.ids_frame_layout,
                margins_checkboxes,
                alternateBgColor
            )
        else:
            no_ids_label = QtWidgets.QLabel('I found no unreferenced ids.')
            no_ids_label.setWordWrap(True)
            no_ids_label.setContentsMargins(*margins_checkboxes)
            self.ids_frame_layout.addWidget(no_ids_label)

        ids_bottom_separator = QtWidgets.QFrame()
        ids_bottom_separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        ids_bottom_separator.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        ids_bottom_separator.setLineWidth(0)
        ids_bottom_separator.setMidLineWidth(1)
        self.ids_frame_layout.addWidget(ids_bottom_separator)

        self.ids_frame_layout.addStretch()

    def _display_attributes_checkboxes(self, attr_list, attr_type, layout, margins, alternateBgColor):
        for i, attr in enumerate(attr_list[attr_type]):
            occurrences = ', '.join(
                f'{utils.href_to_basename(filename)} ({times})' \
                for filename, times in attr_list[f'info_{attr_type}'][attr].items()
            )
            checkbox = WrappingCheckBox(
                f'{attr}  -  Found in: {occurrences}',
                margins=margins,
            )
            checkbox.setChecked(True)
            if i % 2 == 0:
                palette = checkbox.palette()
                palette.setColor(checkbox.backgroundRole(), alternateBgColor)
                checkbox.setPalette(palette)
            self.check_undefined_attributes[f'{attr_type}'][attr] = checkbox
            layout.addWidget(checkbox)

    def toggle_all_classes(self, event: QtCore.QEvent | None = None) -> None:
        checked = self.toggle_classes.isChecked()
        for class_, checkbox in self.check_undefined_attributes['classes'].items():
            checkbox.setChecked(checked)

    def toggle_all_ids(self, event: QtCore.QEvent | None = None) -> None:
        checked = self.toggle_ids.isChecked()
        for id_, checkbox in self.check_undefined_attributes['ids'].items():
            checkbox.setChecked(checked)

    def delete_selected_attributes(self, event: QtCore.QEvent | None = None) -> None:
        for attr_type, attributes in self.check_undefined_attributes.items():
            for attribute, has_to_be_deleted in attributes.items():
                if not has_to_be_deleted.isChecked():
                    self.undefined_attributes[attr_type].discard(attribute)  # type: ignore[literal-required]
        try:
            core.delete_xhtml_attributes(self.bk, self.undefined_attributes, self.prefs)
        finally:
            # reset selected files on success
            self.prefs['selected_files'] = []
            self.bk.savePrefs(self.prefs)
        QtWidgets.QApplication.exit(0)


class PrefsDialog(QtWidgets.QDialog):

    def __init__(
            self,
            bk: BookContainer,
            prefs: JSONPrefs,
            parent: QtWidgets.QWidget | None = None):
        self.bk = bk
        self.prefs = prefs

        super().__init__(parent)
        self.setWindowTitle('Preferences')
        self.setMinimumWidth(600)
        self.setMinimumHeight(600)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)

        self.parse_only_selected_files = WrappingCheckBox(
            'Search for classes and ids to remove only in selected files',
            margins=(0, 6, 0, 6)
        )

        main_layout.addWidget(self.parse_only_selected_files)

        self.selected_files = QtWidgets.QListWidget()
        self.selected_files.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.selected_files.addItems(href for id_, href in self.bk.text_iter())  # type: ignore[arg-type]
        main_layout.addWidget(self.selected_files, stretch=1)

        fragid_attrs_label = QtWidgets.QLabel(
            'Comma separated lists of attributes that will be used to search for:\n\n' \
            '- fragment identifiers (an empty list will default to ' \
            f'{', '.join(core.XHTMLAttributes.fragid_container_attrs)}):'
        )
        fragid_attrs_label.setWordWrap(True)
        fragid_attrs_label.setContentsMargins(0, 18, 0, 6)
        self.fragid_attrs_edit = QtWidgets.QLineEdit()
        main_layout.addWidget(fragid_attrs_label)
        main_layout.addWidget(self.fragid_attrs_edit)

        idref_attrs_label = QtWidgets.QLabel(
            '- a single id reference (an empty list will default to ' \
            f'{', '.join(core.XHTMLAttributes.idref_container_attrs)}):'
        )
        idref_attrs_label.setWordWrap(True)
        idref_attrs_label.setContentsMargins(0, 18, 0, 6)
        self.idref_attrs_edit = QtWidgets.QLineEdit()
        main_layout.addWidget(idref_attrs_label)
        main_layout.addWidget(self.idref_attrs_edit)

        idref_list_attrs_label = QtWidgets.QLabel(
            '- a list of id references (an empty list will default to '
            f'{', '.join(core.XHTMLAttributes.idref_list_container_attrs)}):'
        )
        idref_list_attrs_label.setWordWrap(True)
        idref_list_attrs_label.setContentsMargins(0, 18, 0, 6)
        self.idref_list_attrs_edit = QtWidgets.QLineEdit()
        main_layout.addWidget(idref_list_attrs_label)
        main_layout.addWidget(self.idref_list_attrs_edit)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok|QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.save_and_proceed)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self.get_initial_values()

    def get_initial_values(self) -> None:
        if self.prefs.get('fragid_container_attrs'):
            self.fragid_attrs_edit.setText(', '.join(self.prefs['fragid_container_attrs']))
        else:
            self.fragid_attrs_edit.setText(', '.join(core.XHTMLAttributes.fragid_container_attrs))
        if self.prefs.get('idref_container_attrs'):
            self.idref_attrs_edit.setText(', '.join(self.prefs['idref_container_attrs']))
        else:
            self.idref_attrs_edit.setText(', '.join(core.XHTMLAttributes.idref_container_attrs))
        if self.prefs.get('idref_list_container_attrs'):
            self.idref_list_attrs_edit.setText(', '.join(self.prefs['idref_list_container_attrs']))
        else:
            self.idref_list_attrs_edit.setText(', '.join(core.XHTMLAttributes.idref_list_container_attrs))
        self.parse_only_selected_files.setChecked(
            bool(self.prefs.get('parse_only_selected_files'))
        )
        if self.prefs.get('selected_files'):
            selected_files = [self.bk.href_to_id(sel) for sel in self.prefs.get('selected_files')]
        else:
            selected_files = [selected[1] for selected in self.bk.selected_iter()]
        if selected_files:
            selected_files_names = [self.bk.id_to_href(sel) for sel in selected_files]
            for item in (self.selected_files.item(i) for i in range(self.selected_files.count())):
                if item.text() in selected_files_names:
                    item.setSelected(True)

    def save_and_proceed(self, event: QtCore.QEvent | None = None) -> None:
        attrs_names = {
            'fragid_container_attrs': self.fragid_attrs_edit.text(),
            'idref_container_attrs': self.idref_attrs_edit.text(),
            'idref_list_container_attrs': self.idref_list_attrs_edit.text(),
        }
        for k, v in attrs_names.items():
            self.prefs[k] = [attr.strip() for attr in v.split(',') if attr]
        self.prefs['parse_only_selected_files'] = self.parse_only_selected_files.isChecked()

        # reset selected_files in the prefs dictionary before saving: this value doesn't have to be saved permanently
        self.prefs['selected_files'] = []
        self.bk.savePrefs(self.prefs)
        selected_files = [item.text() for item in self.selected_files.selectedItems()]
        self.prefs['selected_files'] = selected_files
        self.accept()
