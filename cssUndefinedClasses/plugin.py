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

import ui
import core


def get_prefs(bk):
    prefs = bk.getPrefs()

    prefs.defaults['parse_only_selected_files'] = False
    prefs.defaults['selected_files'] = []
    prefs.defaults['fragid_container_attrs'] = []  # if empty, use core.XHTMLAttributes
    prefs.defaults['idref_container_attrs'] = []  # if empty, use core.XHTMLAttributes
    prefs.defaults['idref_list_container_attrs'] = []  # if empty use core.XHTMLAttributes
    prefs.defaults['tktheme'] = 'clearlooks'
    prefs.defaults['update_prefs_defaults'] = 0
    prefs.defaults['quiet'] = False

    if prefs['update_prefs_defaults'] == 0:
        if prefs['fragid_container_attrs']:
            for attr in core.XHTMLAttributes.fragid_container_attrs[3:]:
                if attr not in prefs['fragid_container_attrs']:
                    prefs['fragid_container_attrs'].append(attr)
        prefs['update_prefs_defaults'] = 1

    return prefs


def run(bk):
    prefs = get_prefs(bk)
    if prefs['quiet']:
        prefs['parse_only_selected_files'] = False
        attrs = core.find_attributes_to_delete(bk, prefs)
        core.delete_xhtml_attributes(bk, attrs, prefs)
        success = True
    else:
        plug = ui.MainWindow(bk, prefs)
        plug.mainloop()
        success = plug.success
    return 0 if success else 1


def main():
    print("I reached main when I should not have\n")
    return -1


if __name__ == '__main__':
    sys.exit(main())
