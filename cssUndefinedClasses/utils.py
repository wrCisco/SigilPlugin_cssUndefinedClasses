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


"""
Collection of utilities for Sigil plugins.
"""

import re
import inspect
from pathlib import Path
from functools import reduce
from collections.abc import Sequence, Mapping, Generator
from typing import Any

from bookcontainer import BookContainer
try:
    import css_parser
except ImportError:
    import cssutils as css_parser


SCRIPT_DIR = Path(inspect.getfile(inspect.currentframe())).resolve().parent  # type: ignore

try:
    import tkinter as tk
    from tkinter import ttk

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

    def tk_iterate_children(parent: tk.Widget|ttk.Widget) -> Generator[tk.Widget|ttk.Widget]:
        """
        Yields every descendant of parent widget.
        """
        for child in parent.winfo_children():
            yield child
            for grandchild in tk_iterate_children(child):
                yield grandchild
except ModuleNotFoundError:
    print("Tkinter/ttk module not found.")


try:
    from plugin_utils import QtCore, QtGui

    def tokenize_text(
            text: str,
            boundary_type: QtCore.QTextBoundaryFinder.BoundaryType,
            boundary_reasons: QtCore.QTextBoundaryFinder.BoundaryReason | None = None) -> list[str]:
        """
        Divide text in a list of tokens based on boundary_type.
        boundary_types: Grapheme, Word, Line or Sentence
        """
        if boundary_reasons is None:
            try:
                # BreakOpportunity doesn't come up while iterating over BoundaryReason flags
                # (PySide 6.9), so I use it as the initializer of the reduce function
                boundary_reasons = reduce(
                    lambda x, y: x | y,
                    QtCore.QTextBoundaryFinder.BoundaryReason,
                    QtCore.QTextBoundaryFinder.BoundaryReason.BreakOpportunity
                )
            except TypeError:
                # PyQt5 doesn't allow iterations over Qt enums
                boundary_reasons = (
                    QtCore.QTextBoundaryFinder.BoundaryReason.StartOfItem
                    | QtCore.QTextBoundaryFinder.BoundaryReason.EndOfItem
                    | QtCore.QTextBoundaryFinder.BoundaryReason.MandatoryBreak
                    | QtCore.QTextBoundaryFinder.BoundaryReason.SoftHyphen
                    | QtCore.QTextBoundaryFinder.BoundaryReason.BreakOpportunity
                )
        tbf = QtCore.QTextBoundaryFinder(boundary_type, text)
        tokens = []
        pos = prev = tbf.position()
        while True:
            pos = tbf.toNextBoundary()
            if pos == -1:
                break
            if pos != prev and boundary_reasons & tbf.boundaryReasons():
                token = text[prev:pos]
                tokens.append(text[prev:pos])
                prev = pos
        return tokens

    def compute_words_length(words: Sequence[str], font: QtGui.QFont) -> list[float]:
        """
        Compute the width of every word in words using the QFont font.
        """
        fontMetrics = QtGui.QFontMetricsF(font)
        lengths = []
        for word in words:
            lengths.append(fontMetrics.horizontalAdvance(word))
        return lengths

except ModuleNotFoundError:
    print("plugin_utils module (PyQt5/PySide6 integration) not found.")


def style_rules(rules_collector: Sequence) -> Generator[css_parser.css.CSSRule]:
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


def read_css(bk: BookContainer, css: str) -> str:
    """
    Before Sigil v0.9.7 css and js files were read as byte strings.
    """
    try:
        return bk.readfile(css).decode()
    except AttributeError:
        return bk.readfile(css)


def read_js(bk: BookContainer, js: str) -> str:
    """
    Before Sigil v0.9.7 css and js files were read as byte strings.
    """
    try:
        return bk.readfile(js).decode()
    except AttributeError:
        return bk.readfile(js)


def href_to_basename(href: str, ow: Any = None) -> str | Any:
    """
    From the bookcontainer API. There's a typo until Sigil 0.9.5.
    """
    if href is not None:
        return href.split('/')[-1]
    return ow


def id_to_properties(bk: BookContainer, id: str, ow: Any = None) -> Mapping | Any:
    """
    From the bookcontainer API. Raise AttributeError until Sigil 1.3.0.
    """
    try:
        return bk.id_to_properties(id, ow)
    except AttributeError:
        return bk._w.map_id_to_properties(id, ow)


def id_to_fallback(bk: BookContainer, id: str, ow: Any = None) -> str | Any:
    """
    From the bookcontainer API. Raise AttributeError until Sigil 1.3.0.
    """
    try:
        return bk.id_to_fallback(id, ow)
    except AttributeError:
        return bk._w.map_id_to_fallback(id, ow)


def id_to_overlay(bk: BookContainer, id: str, ow: Any = None) -> str | Any:
    """
    From the bookcontainer API. Raise AttributeError until Sigil 1.3.0.
    """
    try:
        return bk.id_to_overlay(id, ow)
    except AttributeError:
        return bk._w.map_id_to_overlay(id, ow)
