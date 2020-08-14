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


import html
import urllib.parse
from typing import Optional

import regex as re
import sigil_bs4
import sigil_gumbo_bs4_adapter as gumbo_bs4

try:
    import css_parser
except ImportError:
    import cssutils as css_parser

import utils


class CSSParsingError(Exception):
    pass


class XHTMLParsingError(Exception):
    pass


class XHTMLAttributes:

    fragid_container_attrs = [
        'href',
        'epub:textref',
        'src'
    ]

    def __init__(self):
        """
        Collects class and id values from parsed xhtml files.

        self.class_names are the names of all the classes found in xhtml elements.
        self.literal_class_values are the textual values of the attribute
        class, used to match against some of the css attribute selectors.
        self.id_values are the names of all the ids found in xhtml elements.
        self.fragment_identifier are the values of all the fragment identifiers
        found in xhtml elements.

        self.info_class_names is a dictionary that has the elements of self.class_names
        as keys and the occurrences in files as values.
        Same for self.info_id_values.
        """
        self.class_names = set()
        self.literal_class_values = set()
        self.id_values = set()
        self.fragment_identifier = set()

        self.info_class_names = {}
        self.info_id_values = {}


class CSSAttributes:

    def __init__(self):
        """
        Collects class and id values from parsed stylesheets.

        classes['classes'] come from class selectors or [class~=...] attribute selectors,
        classes['equal'] come from [class=...] attribute selectors,
        classes['equal_or_startswith_and_next_is_dash'] come from [class|=...],
        classes['startswith'] come from [class^=...],
        classes['endswith'] come from [class$=...],
        classes['contains'] come from [class*=...].

        ids['equal'] come from id selectors or [id=...] or [id~=...] attribute selectors,
        the other keys are derived as those from classes.
        """
        self.classes = {
            'classes': set(),
            'equal': set(),
            'equal_or_startswith_and_next_is_dash': set(),
            'startswith': set(),
            'endswith': set(),
            'contains': set()
        }
        self.ids = {
            'equal': set(),
            'equal_or_startswith_and_next_is_dash': set(),
            'startswith': set(),
            'endswith': set(),
            'contains': set()
        }


class CSSParser:

    def __init__(self) -> None:
        self.cssparser = css_parser.CSSParser(raiseExceptions=True, validate=False)

    def parse_css(self, bk, collector: CSSAttributes = None) -> CSSAttributes:
        """
        Parse the contents of all css files in epub.
        """
        if not collector:
            collector = CSSAttributes()
        for css_id, css_href in bk.css_iter():
            try:
                parsed_css = self.cssparser.parseString(utils.read_css(bk, css_id))
            except Exception as E:
                raise CSSParsingError('Error in {}: {}'.format(utils.href_to_basename(css_href), E))
            for rule in utils.style_rules(parsed_css):
                for selector in rule.selectorList:
                    self._parse_selector(selector.selectorText, collector)
        return collector

    def parse_style(self, embedded_style: str, collector: CSSAttributes = None, filename: str = '') -> CSSAttributes:
        """
        Parse the content of a style tag.
        """
        if not collector:
            collector = CSSAttributes()
        try:
            parsed_css = self.cssparser.parseString(embedded_style)
        except Exception as E:
            raise CSSParsingError('Error in style element of {}: {}'.format(filename, E))
        for rule in utils.style_rules(parsed_css):
            for selector in rule.selectorList:
                self._parse_selector(selector.selectorText, collector)
        return collector

    @staticmethod
    def _parse_selector(selector: str, collector: CSSAttributes) -> None:
        """
        Parse a selector and extract all class and id names,
        which are used to populate classes and ids dictionaries of the collector.
        """
        # This 'ident_token' pattern doesn't consider unicode escape
        # sequences: they are already resolved by the css parser.
        ident_token = re.compile(
            r'''
            -?                           # optional initial dash
            (?:\\[^a-fA-F0-9]|           # ident start char: it can be an escaped character
            [a-zA-Z_]|                   # or an ascii letter or an underscore
            [^\u0000-\u007f])            # or any non-ascii character.
            (?:\\[^a-fA-F0-9]|           # Other chars of the ident:
            [a-zA-Z0-9_-]|               # same as start char, but decimal digits
            [^\u0000-\u007f])*           # and dashes are allowed too.
            ''',
            re.VERBOSE
        )
        i = 0
        while i < len(selector):
            start_i = i
            char = selector[i]

            # class selector
            if char == '.' and (i == 0 or selector[i - 1] != '\\'):
                class_match = ident_token.match(selector[i + 1:])
                if class_match:
                    collector.classes['classes'].add(utils.css_remove_escapes(class_match.group()))
                    i += class_match.end() + 1

            # id selector
            elif char == '#' and (i == 0 or selector[i - 1] != '\\'):
                id_match = ident_token.match(selector[i + 1:])
                if id_match:
                    collector.ids['equal'].add(utils.css_remove_escapes(id_match.group()))
                    i += id_match.end() + 1

            # attribute selector
            elif char == '[' and (i == 0 or selector[i - 1] != '\\'):
                fragment = selector[i:]
                # The pattern doesn't take into account the possibility of
                # escaping the letters 'c', 'l', 'a', 's', 'i', 'd'
                # (if one wants to hurt themselves...)
                attr = re.match(r'\[(?:class|id)[~|^$*]?=', fragment)
                if attr:
                    if 'id' in attr.group():
                        names = collector.ids
                    else:
                        names = collector.classes
                    value_start = attr.end()
                    if fragment[value_start] == '"':
                        value_start += 1
                        end_pattern = re.compile(r'(?<!\\)"')
                    elif fragment[value_start] == "'":
                        value_start += 1
                        end_pattern = re.compile(r"(?<!\\)'")
                    else:
                        end_pattern = re.compile(r'(?<!\\)]')
                    value_end = end_pattern.search(fragment, pos=value_start).end()
                    value = utils.css_remove_escapes(fragment[value_start:value_end - 1])
                    if '~' in attr.group():
                        try:
                            names['classes'].add(value)
                        except KeyError:
                            names['equal'].add(value)
                    elif '|' in attr.group():
                        names['equal_or_startswith_and_next_is_dash'].add(value)
                    elif '^' in attr.group():
                        names['startswith'].add(value)
                    elif '$' in attr.group():
                        names['endswith'].add(value)
                    elif '*' in attr.group():
                        names['contains'].add(value)
                    else:
                        names['equal'].add(value)
                    i += value_end
            if i == start_i:
                i += 1


def get_fragid(element: sigil_bs4.Tag, attr_name: str = 'href') -> str:
    try:
        return urllib.parse.unquote(urllib.parse.urldefrag(element[attr_name]).fragment)
    except KeyError:
        return ''


def parse_xhtml(bk, cssparser: CSSParser, css_collector: CSSAttributes) -> XHTMLAttributes:
    """
    Parse all the xhtml files in the epub and gather classes, ids
    and fragment identifiers. Also, gather css classes and ids
    from <style> elements.
    """
    a = XHTMLAttributes()
    for xhtml_id, xhtml_href in bk.text_iter():
        filename = utils.href_to_basename(xhtml_href)
        try:
            soup = gumbo_bs4.parse(bk.readfile(xhtml_id))
        except Exception as E:
            raise XHTMLParsingError('Error in {}: {}'.format(filename, E))
        for elem in soup.find_all(True):
            # tag 'style': gather all css classes and ids
            if elem.name == 'style':
                try:
                    style = elem.contents[0]
                except IndexError:
                    pass
                else:
                    cssparser.parse_style(style, css_collector, filename)
            # gather id value, if present
            try:
                id_ = elem['id']
            except KeyError:
                pass
            else:
                if id_ in a.id_values:
                    try:
                        a.info_id_values[id_][xhtml_href] += 1
                    except KeyError:
                        a.info_id_values[id_][xhtml_href] = 1
                else:
                    a.info_id_values[id_] = {xhtml_href: 1}
                    a.id_values.add(id_)
            # gather fragment identifiers, if present
            for attr in a.fragid_container_attrs:
                fragid = get_fragid(elem, attr)
                if fragid:
                    a.fragment_identifier.add(fragid)
            # gather class names and textual value of class attribute, if present
            classes = elem.get('class', [])
            if isinstance(classes, str):
                classes = [classes]
            for class_ in classes:
                if class_ in a.class_names:
                    try:
                        a.info_class_names[class_][xhtml_href] += 1
                    except KeyError:
                        a.info_class_names[class_][xhtml_href] = 1
                else:
                    a.info_class_names[class_] = {xhtml_href: 1}
                    a.class_names.add(class_)
            if classes:
                try:
                    literal_class_value = re.search(r'class=([\'"])(.+?)\1', str(elem)).group(2)
                except AttributeError:
                    pass
                else:
                    a.literal_class_values.add(literal_class_value)
    a.class_names.discard('')
    a.literal_class_values.discard('')
    return a


def parse_xml(bk: 'BookContainer', collector: XHTMLAttributes) -> XHTMLAttributes:
    xhtml_files = set(id_ for id_, href in bk.text_iter())
    for file_id, href, mime in bk.manifest_iter():
        # if file is xhtml or not xml, skip ahead
        if file_id in xhtml_files or not re.search(r'[/+]xml\b', mime):
            continue
        try:
            soup = sigil_bs4.BeautifulSoup(bk.readfile(file_id), 'lxml-xml')
        except Exception as E:
            raise XHTMLParsingError('Error in {}: {}'.format(utils.href_to_basename(href), E))
        for elem in soup.find_all(True):
            # gather fragment identifiers, if present
            for attr in collector.fragid_container_attrs:
                fragid = get_fragid(elem, attr)
                if fragid:
                    collector.fragment_identifier.add(fragid)
    return collector


def match_attribute_selectors(css_attributes: dict, xhtml_attribute_names: set) -> set:
    attrs_to_delete = xhtml_attribute_names.copy()
    for attr in xhtml_attribute_names:
        unescaped_attr = html.unescape(attr)  # css attributes are already unescaped
        to_delete = True
        if unescaped_attr in css_attributes['equal']:
            to_delete = False
        if to_delete:
            for css_attr in css_attributes['equal_or_startswith_and_next_is_dash']:
                if unescaped_attr == css_attr \
                        or (unescaped_attr.startswith(css_attr)
                            and unescaped_attr[len(css_attr):].startswith('-')):
                    to_delete = False
                    break
        if to_delete:
            for css_attr in css_attributes['startswith']:
                if unescaped_attr.startswith(css_attr):
                    to_delete = False
                    break
        if to_delete:
            for css_attr in css_attributes['endswith']:
                if unescaped_attr.endswith(css_attr):
                    to_delete = False
                    break
        if to_delete:
            for css_attr in css_attributes['contains']:
                if css_attr in unescaped_attr:
                    to_delete = False
                    break
        if not to_delete:
            attrs_to_delete.discard(attr)
    return attrs_to_delete


def find_attributes_to_delete(bk) -> dict:
    # search for classes and ids in css
    my_cssparser = CSSParser()
    css_attrs = my_cssparser.parse_css(bk)
    # search for classes, ids and fragment identifiers in xhtml
    xhtml_attrs = parse_xhtml(bk, my_cssparser, css_attrs)
    # search for fragment identifiers also in xml files (ncx, media overlays...)
    xhtml_attrs = parse_xml(bk, xhtml_attrs)

    classes_to_delete = xhtml_attrs.class_names.copy()
    for class_ in xhtml_attrs.class_names:
        if html.unescape(class_) in css_attrs.classes['classes']:
            classes_to_delete.discard(class_)
    if (
            css_attrs.classes['equal']
            or css_attrs.classes['equal_or_startswith_and_next_is_dash']
            or css_attrs.classes['startswith']
            or css_attrs.classes['endswith']
            or css_attrs.classes['contains']
    ):
        literal_classes_to_delete = match_attribute_selectors(
            css_attrs.classes,
            xhtml_attrs.literal_class_values
        )
        literal_classes_to_keep = xhtml_attrs.literal_class_values.difference(literal_classes_to_delete)
    else:
        literal_classes_to_keep = set()
    classes_to_keep = set()
    for class_ in literal_classes_to_keep:
        classes_to_keep.update(re.split(r'[ \r\n\t\f]+', class_))
    classes_to_delete.difference_update(classes_to_keep)

    ids_to_delete = match_attribute_selectors(css_attrs.ids, xhtml_attrs.id_values)
    ids_to_delete.difference_update(xhtml_attrs.fragment_identifier)

    # print('CLASSES IN CSS:')
    # for k, v in css_attrs.classes.items():
    #     print(f'{k}: {v}')
    # print('\nIDS IN CSS:')
    # for k, v in css_attrs.ids.items():
    #     print(f'{k}: {v}')
    # print('')
    #
    # print('CLASSES IN XHTML:')
    # print(xhtml_attrs.class_names)
    # print('LITERAL CLASS VALUES IN XHTML:')
    # print(xhtml_attrs.literal_class_values)
    # print('CLASSES TO DELETE:')
    # print(classes_to_delete)
    # print('ID IN XHTML:')
    # print(xhtml_attrs.id_values)
    # print('FRAGMENTS IN XHTML:')
    # print(xhtml_attrs.fragment_identifier)
    # print('ID TO DELETE:')
    # print(ids_to_delete)

    return {
        'classes': classes_to_delete,
        'ids': ids_to_delete,
        'info_classes': xhtml_attrs.info_class_names,
        'info_ids': xhtml_attrs.info_id_values
    }


def delete_xhtml_attributes(bk, attributes: dict) -> None:
    for xhtml_id, xhtml_href in bk.text_iter():
        soup = gumbo_bs4.parse(bk.readfile(xhtml_id))
        for elem in soup.find_all(True):
            try:
                if elem['id'] in attributes['ids']:
                    del elem['id']
            except KeyError:
                pass
            classes = elem.get('class', [])
            if isinstance(classes, str):
                classes = [classes]
            for class_ in classes.copy():
                if class_ in attributes['classes']:
                    try:
                        elem['class'].remove(class_)
                    except AttributeError:
                        del elem['class']  # this should never raise a KeyError
            # I don't know if it's linked to python, sigil, beautifulsoup or gumbo versions:
            # with some installation the elements keep empty class attributes.
            try:
                if not classes:
                    del elem['class']
            except KeyError:
                pass
        bk.writefile(xhtml_id, soup.serialize_xhtml())
        # print(f"\n\nNew {xhtml_href}:\n")
        # print(soup.serialize_xhtml())
