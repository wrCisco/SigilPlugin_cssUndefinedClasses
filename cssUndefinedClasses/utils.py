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


"""
Collection of utilities for Sigil plugins.
"""

import re
import inspect
from tkinter import ttk
from pathlib import Path


SCRIPT_DIR = Path(inspect.getfile(inspect.currentframe())).resolve().parent


class ReturnButton(ttk.Button):
    """
    Simple wrapper over ttk.Button to make buttons always
    bound with <Return> and <KP_Enter> events (with the same
    callback as the button's command option).
    Only usable if the command's callback doesn't require arguments.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind('<Return>', lambda e: self.invoke())
        self.bind('<KP_Enter>', lambda e: self.invoke())


def tk_iterate_children(parent):
    """
    Yields every descendant of parent widget.
    """
    for child in parent.winfo_children():
        yield child
        for grandchild in tk_iterate_children(child):
            yield grandchild


def style_rules(rules_collector):
    """
    Yields style rules in a css parsed with css_parser/cssutils,
    both at top level and nested inside @media rules
    (with unlimited nesting levels).
    """
    for rule in rules_collector:
        if rule.typeString == "STYLE_RULE":
            yield rule
        elif rule.typeString == "MEDIA_RULE":
            for nested_rule in style_rules(rule):
                yield nested_rule


def css_remove_escapes(val: str) -> str:
    """
    Remove backslash in non unicode escape sequences
    (unicode escape sequences are resolved within css_parser/cssutils).
    Useful for comparisons with tag and attribute names parsed by gumbo_bs4.
    """
    return re.sub(r'\\([^a-fA-F0-9])', r'\1', val)


def read_css(bk, css):
    """
    Before Sigil v0.9.7 css and js files were read as byte strings.
    """
    try:
        return bk.readfile(css).decode()
    except AttributeError:
        return bk.readfile(css)


def read_js(bk, js):
    """
    Before Sigil v0.9.7 css and js files were read as byte strings.
    """
    try:
        return bk.readfile(js).decode()
    except AttributeError:
        return bk.readfile(js)


def href_to_basename(href, ow=None):
    """
    From the bookcontainer API. There's a typo until Sigil 0.9.5.
    """
    if href is not None:
        return href.split('/')[-1]
    return ow


def id_to_properties(bk, id, ow=None):
    """
    From the bookcontainer API. Raise AttributeError until Sigil 1.3.0.
    """
    try:
        return bk.id_to_properties(id, ow)
    except AttributeError:
        return bk._w.map_id_to_properties(id, ow)


def id_to_fallback(bk, id, ow=None):
    """
    From the bookcontainer API. Raise AttributeError until Sigil 1.3.0.
    """
    try:
        return bk.id_to_fallback(id, ow)
    except AttributeError:
        return bk._w.map_id_to_fallback(id, ow)


def id_to_overlay(bk, id, ow=None):
    """
    From the bookcontainer API. Raise AttributeError until Sigil 1.3.0.
    """
    try:
        return bk.id_to_overlay(id, ow)
    except AttributeError:
        return bk._w.map_id_to_overlay(id, ow)
