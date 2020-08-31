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
import time
import inspect
import tempfile
from pathlib import Path
import tkinter as tk
import unittest
from unittest.mock import patch

import bs4


SIGIL_STD_PATHS = {
    'plugin launchers': [
        '/usr/local/share/sigil/plugin_launchers/python',
        '/usr/share/sigil/plugin_launchers/python',
        r'C:\Program Files\Sigil\plugin_launchers\python'
    ],
    'shared library': [
        '/usr/local/lib/sigil',
        '/usr/lib/sigil',
        r'C:\Program Files\Sigil'
    ],
    'user directory': [
        '.local/share/sigil-ebook/sigil',
        r'AppData\Local\sigil-ebook\sigil'
    ]
}


def sigil_get_path(to: str, path: str = None) -> str:
    """
    Returns the path to the element specified by the parameter 'to',
    which can be one of the SIGIL_STD_PATHS keys:
    - plugin launchers
    - shared library
    - user directory
    """
    result = ''
    if path and Path(path).is_dir():
        result = path
    else:
        for p in SIGIL_STD_PATHS[to]:
            if to == 'user directory':
                p = str(Path.home() / p)
            if Path(p).is_dir():
                result = p
                break
    if not result:
        raise RuntimeError(f"I cannot find the path to the Sigil's {to}. Exiting...")
    return result


def get_root_path(path: str = None) -> Path:
    """
    Root path of the plugin project. If path is not specified or is not a valid dir,
    the assumption is that this test module is in a directory one level below the root dir.
    E.g. with /rootdir/tests/this_file.py the return value will be '/rootdir'
    """
    if path and Path(path).is_dir():
        root = Path(path)
    else:
        root = Path(inspect.getfile(inspect.currentframe())).resolve().parent.parent  # type: ignore
    return root


def sigil_gumbo_lib_path(path: str = None, name: str = None) -> str:
    if path:
        sigil_lib = path
    else:
        sigil_lib = sigil_get_path('shared library')
    if name:
        gumbo = name
    else:
        if sys.platform.startswith('win'):
            gumbo = 'sigilgumbo.dll'
        elif sys.platform.startswith('darwin'):
            gumbo = 'libsigilgumbo.dylib'
        else:  # linux
            gumbo = 'libsigilgumbo.so'
    return os.path.join(sigil_lib, gumbo)


def sigil_hunspell_dicts(paths: str = None, user_path: str = None) -> str:
    """
    paths, if present, should be a colon separated list of directory paths.
    """
    if paths:
        hunspells = paths  # add here '/usr/share/hunspell'?
    else:
        try:
            hunspells = os.environ['SIGIL_DICTIONARIES']
        except KeyError:
            if user_path:
                hunspells = os.path.join(user_path, 'hunspell_dictionaries')
            else:
                hunspells = '/usr/share/hunspell'
                # there is also the cmake option EXTRA_DICT_DIRS (colon separated list)
                # but I can't get that value outside of Sigil
    return hunspells


def get_opf_path(container_xml: Path) -> str:
    """
    Returns the relative path to the opf file as written in the container.xml.
    Doesn't handle multiple opf epubs.
    """
    with container_xml.open() as fh:
        soup = bs4.BeautifulSoup(fh, 'lxml-xml')
    return soup.rootfile['full-path']


ROOT_PATH = get_root_path()
sys.path.append(str(ROOT_PATH / 'cssUndefinedClasses'))
plugin_launchers_path = sigil_get_path('plugin launchers')
sys.path.insert(1, plugin_launchers_path)
os.environ['SigilGumboLibPath'] = sigil_gumbo_lib_path()

import utils
import plugin
import ui

import preferences
import launcher


class JSONPrefsTest(preferences.JSONPrefs):
    """
    Simple wrapper around Sigil Plugin Framework's JSONPrefs.
    It can change the location where the preferences are saved using
    the value set for plugin_dir_for_tests class attribute.

    E.g. if the plugin name is 'spam_the_plugin' and
    plugin_dir_for_tests = '/root/tests/empty_dir',
    the preferences will be saved in
    /root/tests/plugin_prefs/spam_the_plugin/spam_the_plugin.json

    This class can be used as a patch decorator for a test_function
    that calls the function 'main' of the 'launcher' module:
    @patch('bookcontainer.JSONPrefs', side_effect=JSONPrefsTest)
    """

    plugin_dir_for_tests = ''

    def __init__(self, plugin_dir: str, plugin_name: str) -> None:
        if self.plugin_dir_for_tests:
            plugin_dir = self.plugin_dir_for_tests
        super().__init__(plugin_dir, plugin_name)


class TestMainWindow(ui.MainWindow):
    """
    Add the (mostly) non blocking pump_events method to the tkinter app
    that has to be tested, in order to use it instead of the mainloop.
    """

    def pump_events(self) -> None:
        while self.dooneevent(tk._tkinter.ALL_EVENTS | tk._tkinter.DONT_WAIT):  # type: ignore
            pass


class FunctionalTest(unittest.TestCase):

    test_main_window: TestMainWindow

    root_path = get_root_path()
    src_path = root_path / 'cssUndefinedClasses'
    resources_path = root_path / 'functional_tests' / 'resources'
    ebook_root = resources_path / 'epub_test'
    opf_rel_path = Path(get_opf_path(ebook_root / 'META-INF' / 'container.xml'))

    def setUp(self) -> None:
        self.script_type = 'edit'
        self.script_target = self.src_path / 'plugin.py'
        self.output_dir = tempfile.TemporaryDirectory(
            prefix='cssUndefinedClasses_', dir=self.resources_path
        )
        self.preferences_dir = tempfile.TemporaryDirectory(
            prefix='cssUndefinedClassesPrefs_', dir=self.resources_path
        )
        JSONPrefsTest.plugin_dir_for_tests = os.path.join(self.preferences_dir.name, 'prefs')

    def tearDown(self) -> None:
        if self.output_dir:
            self.output_dir.cleanup()
            del self.output_dir
        if self.preferences_dir:
            self.preferences_dir.cleanup()
            del self.preferences_dir
        try:
            if FunctionalTest.test_main_window.is_running:
                FunctionalTest.test_main_window.destroy()
        except (AttributeError, tk.TclError) as E:
            print(E)

    @staticmethod
    def plugin_run(bk):
        root = TestMainWindow(bk)
        FunctionalTest.test_main_window = root
        root.pump_events()
        return 'test'  # the function returns immediately, so no need to care for the return value

    @patch('bookcontainer.JSONPrefs', side_effect=JSONPrefsTest)
    def test_preferences_only_selected_with_keyboard(self, prefs_mock):
        """
        The user launches the plugin, then uses only the keyboard
        to modify some preferences and proceed with the execution:
        - Shift+Tab, then Return to open the Preferences dialog;
        - Shift+Tab, then Space to check the parse only selected files checkbutton;
        - Tab, Space, Arrow Down, Space to select the first two files in the list;
        - Shift+Tab twice, then Return to save preferences and close the dialog;
        - Tab twice, then Return to proceed with the epub parsing;
        - Return to proceed with the deletion of selected ids and classes from the epub
          and exit the plugin successfully.
        """
        self.create_sigil_cfg()
        utils.SCRIPT_DIR = self.root_path
        plugin.run = self.plugin_run
        # patching launcher.SavedStream mocks away sys.stdout and sys.stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        with patch('launcher.SavedStream'):  #, patch('plugin.run', side_effect=self.plugin_run):
            launcher.main(
                ['', self.ebook_root, self.output_dir.name, self.script_type, self.script_target]
            )
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        window = FunctionalTest.test_main_window
        window.pump_events()
        time.sleep(0.2)
        self.assertEqual(window.focus_get(), window.start_button)
        window.event_generate('<Shift-Tab>')
        time.sleep(0.1)
        window.event_generate('<Shift-Tab>')
        window.pump_events()
        self.assertEqual(window.focus_get(), window.prefs_button)
        time.sleep(0.1)

        # events inside Preferences dialog
        window.after(100, lambda: window.event_generate('<Tab>'))
        window.after(200, lambda: window.event_generate('<space>'))
        window.after(300, lambda: window.event_generate('<Tab>'))
        window.after(400, lambda: window.event_generate('<space>'))
        window.after(500, lambda: window.event_generate('<KeyPress-Down>'))
        window.after(600, lambda: window.event_generate('<space>'))
        window.after(700, lambda: window.event_generate('<Shift-Tab>'))
        window.after(800, lambda: window.event_generate('<Shift-Tab>'))
        window.after(900, lambda: window.event_generate('<Return>'))
        # window.after(1000, lambda: self.get_prefs_dlg(window).event_generate('<Return>'))
        window.event_generate('<Return>')  # this opens the Preferences dialog, execution stops until dlg is closed

        window.pump_events()
        self.assertTrue(window.warning_text.get().startswith('Only selected'))
        window.prefs_button.focus_force()  # why during tests the focus doesn't automatically return to prefs_button?
        self.assertEqual(window.focus_get(), window.prefs_button)
        time.sleep(0.1)
        window.event_generate('<Tab>')
        window.event_generate('<Tab>')
        self.assertEqual(window.focus_get(), window.start_button)
        self.assertEqual(window.check_undefined_attributes['classes'], {})
        self.assertEqual(window.check_undefined_attributes['ids'], {})
        window.event_generate('<Return>')
        window.pump_events()
        time.sleep(0.1)
        self.assertTrue('SectionNumber' in window.check_undefined_attributes['classes'])
        self.assertTrue('Indicegenerale1' in window.check_undefined_attributes['ids'])
        window.event_generate('<Shift-Tab>')
        self.assertEqual(window.focus_get(), window.stop_button)
        time.sleep(0.1)
        window.event_generate('<Tab>')
        self.assertEqual(window.focus_get(), window.start_button)
        window.pump_events()
        window.event_generate('<Return>')
        window.pump_events()
        self.assertTrue(window.success)
        self.assertFalse(window.is_running)

    def get_prefs_dlg(self, window: tk.Tk) -> tk.Toplevel:
        w = None
        for w in utils.tk_iterate_children(window):
            if isinstance(w, ui.PrefsDialog):
                break
        self.assertIsInstance(w, ui.PrefsDialog)
        return w

    def create_sigil_cfg(
            self,
            path='',           # path to folder where to save sigil.cfg, defaults to self.output_dir
            opfbookpath='',    # path to the opf file relative to the folder containing the unzipped epub
            appdir='',         # path to the folder that contains sigil's shared library
            usrsupdir='',      # path to the user's sigil folder (preferences, plugins...)
            linux_hunspell_dict_dirs='',  # linux only, colon separated list of hunspell dictionaries
            sigil_ui_lang='',  # tries to retrieve value from sigil.ini, otherwise defaults to 'en'
            sigil_spellcheck_lang='',  # defaults to 'en-EN' (not sure how to retrieve this from sigil.ini)
            epub_isDirty='',   # defaults to False
            epub_filepath='',  # path to the real epub file, defaults to ''
            colormode='',      # defaults to 'light' unless some env vars are set
            colors='',         # default depends on colormode
            highdpi='',        # tries to retrieve value from sigil.ini, otherwise defaults to 'detect'
            uifont='',         # tries to retrieve value from sigil.ini, otherwise defaults to ''
            selected=''        # defaults to ''
    ) -> str:
        lines = []
        if opfbookpath:
            lines.append(opfbookpath)
        else:
            lines.append(get_opf_path(self.ebook_root / 'META-INF' / 'container.xml'))
        if appdir:
            lines.append(appdir)
        else:
            lines.append(sigil_get_path('shared library'))
        if usrsupdir:
            user_path = usrsupdir
        else:
            user_path = sigil_get_path('user directory')
        lines.append(user_path)
        if linux_hunspell_dict_dirs:
            lines.append(linux_hunspell_dict_dirs)
        elif sys.platform.startswith('linux'):
            lines.append(sigil_hunspell_dicts(user_path=user_path))

        # retrieve info from sigil.ini file
        sigil_ini = Path(user_path) / 'sigil.ini'
        sigil_ui_lang_ini = ''
        sigil_uifont_ini = ''
        sigil_highdpi_ini = ''
        sigil_spellcheck_lang_ini = ''
        with sigil_ini.open() as f:
            for row in f:
                if row.startswith('ui_language='):
                    sigil_ui_lang_ini = row[12:]
                elif row.startswith('ui_font='):
                    sigil_uifont_ini = row[8:]
                elif row.startswith('high_dpi='):
                    hd = row[9:]
                    if hd == '0':
                        sigil_highdpi_ini = 'detect'
                    elif hd == '1':
                        sigil_highdpi_ini = 'yes'
                    elif hd == '2':
                        sigil_highdpi_ini = 'no'
                # elif row.startswith('selected_dictionary='):  # is this the right spot?
                #    sigil_spellcheck_lang_ini = row[20:]  # it'll probably need some more work anyway

        if sigil_ui_lang:
            lines.append(sigil_ui_lang)
        elif sigil_ui_lang_ini:
            lines.append(sigil_ui_lang_ini)
        else:
            lines.append('en')
        if sigil_spellcheck_lang:
            lines.append(sigil_spellcheck_lang)
        elif sigil_spellcheck_lang_ini:
            lines.append(sigil_spellcheck_lang_ini)
        else:
            lines.append('en-EN')
        if epub_isDirty:
            lines.append(epub_isDirty)
        else:
            lines.append('False')
        if epub_filepath:
            lines.append(epub_filepath)
        else:
            lines.append('')
        if colormode:
            lines.append(colormode)
        else:
            if os.environ.get('FORCE_SIGIL_DARKMODE_PALETTE') or os.environ.get('SIGIL_USES_DARK_MODE') != '0':
                lines.append('dark')
            else:
                lines.append('light')
        if colors:
            lines.append(colors)
        else:
            if lines[-1] == 'light':
                lines.append('#efefef,#ffffff,#000000,#308cc6,#ffffff')
            elif lines[-1] == 'dark':
                lines.append('#353535,#2a2a2a,#eeeeee,#2a82da,#eeeeee')
        if highdpi:
            lines.append(highdpi)
        elif sigil_highdpi_ini:
            lines.append(sigil_highdpi_ini)
        else:
            lines.append('detect')
        if uifont:
            lines.append(uifont)
        elif sigil_uifont_ini:
            lines.append(sigil_uifont_ini)
        else:
            lines.append('')
        if selected:
            lines.append(selected)
        else:
            lines.append('')
        if path:
            output_path = path
        else:
            output_path = os.path.join(self.output_dir.name, 'sigil.cfg')
        with open(output_path, mode='w', encoding='utf-8') as fh:
            fh.write('\n'.join(lines))
        return output_path


if __name__ == '__main__':
    unittest.main()
