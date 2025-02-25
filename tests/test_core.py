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


import unittest
from unittest.mock import Mock, patch

import core
from tests import resources

#import sigil_gumbo_bs4_adapter as gumbo_bs4
from bookcontainer import BookContainer


class Parser(unittest.TestCase):

    def setUp(self):
        self.cssparser = core.CSSParser()

        self.bk = Mock(spec_set=BookContainer)
        self.bk.readfile.side_effect = bk_readfile
        self.bk.writefile.side_effect = bk_writefile

        self.read_css_patch = patch('utils.read_css', side_effect=read_css)
        self.read_css = self.read_css_patch.start()

        # self.bk.readfile = Mock(side_effect=bk_readfile)
        # self.bk.writefile = Mock(side_effect=bk_writefile)

    def tearDown(self):
        self.read_css_patch.stop()


class CSSParserTest(Parser):

    def test_parse_css_ok(self):
        self.bk.css_iter.side_effect = lambda: bk_css_iter([('css1', 'href1')])
        collector = self.cssparser.parse_css(self.bk)
        self.assertTrue(self.bk.css_iter.called)
        self.read_css.assert_called_once_with(self.bk, 'css1')
        self.assertEqual(
            collector.classes['classes'],
            {'aclass', 'anotherclass', 'yetanotherclass', 'wholenameclass'}
        )
        self.assertEqual(
            collector.ids['equal'],
            {'anid'}
        )

    def test_parse_css_parsing_error(self):
        self.bk.css_iter.side_effect = lambda: bk_css_iter([('css2', 'href2')])
        self.assertRaises(core.CSSParsingError, self.cssparser.parse_css, self.bk)

    def test_parse_style_ok(self):
        collector = self.cssparser.parse_style(resources.css_samples['css1'], filename='css1')
        self.assertEqual(
            collector.classes['classes'],
            {'aclass', 'anotherclass', 'yetanotherclass', 'wholenameclass'}
        )
        self.assertEqual(
            collector.classes['equal'],
            {'equalclass', 'equal class'}
        )
        self.assertEqual(
            collector.classes['equal_or_startswith_and_next_is_dash'],
            {'startorequal'}
        )
        self.assertEqual(
            collector.classes['startswith'],
            {'startswithclass', 'startswith class'}
        )
        self.assertEqual(
            collector.classes['endswith'],
            {'endswithclass', 'ends with class'}
        )
        self.assertEqual(
            collector.classes['contains'],
            {'containsclass', 'contains class'}
        )

    def test_parse_style_parsing_error(self):
        self.assertRaisesRegex(
            core.CSSParsingError,
            r'^Error in style element of css2.xhtml',
            self.cssparser.parse_style,
            resources.css_samples['css2'], filename='css2.xhtml'
        )

    def test_parse_selector_without_classes_nor_ids(self):
        collector = core.CSSAttributes()
        self.assertNotEqual(collector.classes, {})
        for k, v in collector.classes.items():
            with self.subTest(type='classes', key=k, val=v):
                self.assertEqual(v, set())
        self.assertNotEqual(collector.ids, {})
        for k, v in collector.ids.items():
            with self.subTest(type='ids', key=k, val=v):
                self.assertEqual(v, set())
        self.cssparser._parse_selector('p > p[title=atitle] :not(span)', collector)
        for k, v in collector.classes.items():
            with self.subTest(type='classes', key=k, val=v):
                self.assertEqual(v, set())
        for k, v in collector.ids.items():
            with self.subTest(type='ids', key=k, val=v):
                self.assertEqual(v, set())

    def test_parse_selector_class_selector(self):
        collector = core.CSSAttributes()
        self.cssparser._parse_selector('.aclass, p.anotherclass, div.aclass', collector)
        self.assertNotEqual(collector.classes, {})
        for k, v in collector.classes.items():
            with self.subTest(type='classes', key=k, val=v):
                if k == 'classes':
                    self.assertEqual(v, {'aclass', 'anotherclass'})
                else:
                    self.assertEqual(v, set())

    def test_parse_selector_id_selector(self):
        collector = core.CSSAttributes()
        self.cssparser._parse_selector('#anid, a#anotherid, h2#anid', collector)
        self.assertNotEqual(collector.ids, {})
        for k, v in collector.ids.items():
            with self.subTest(type='ids', key=k, val=v):
                if k == 'equal':
                    self.assertEqual(v, {'anid', 'anotherid'})
                else:
                    self.assertEqual(v, set())

    def test_parse_selector_attribute_selector(self):
        collector = core.CSSAttributes()
        self.cssparser._parse_selector(
            r'p[class~=aclass][class~=anotherclass], div[id*=an\ id][class=a\ class]', collector
        )
        self.assertNotEqual(collector.classes, {})
        for k, v in collector.classes.items():
            with self.subTest(type='classes', key=k, val=v):
                if k == 'classes':
                    self.assertEqual(v, {'aclass', 'anotherclass'})
                elif k == 'equal':
                    self.assertEqual(v, {'a class'})
                else:
                    self.assertEqual(v, set())
        self.assertNotEqual(collector.ids, {})
        for k, v in collector.ids.items():
            with self.subTest(type='ids', key=k, val=v):
                if k == 'contains':
                    self.assertEqual(v, {'an id'})
                else:
                    self.assertEqual(v, set())

    def test_parse_selector_accept_invalid_ident_token(self):
        """
        The cssparser recognizes also identifiers that start with
        a digit or two dashes in class and id selectors.
        """
        collector = core.CSSAttributes()
        self.cssparser._parse_selector(
            r'.1aclass.--aclass#1anid #123 #--__-321', collector
        )
        self.assertNotEqual(collector.classes, {})
        for k, v in collector.classes.items():
            with self.subTest(type='classes', key=k, val=v):
                if k == 'classes':
                    self.assertEqual(v, {'1aclass', '--aclass'})
                else:
                    self.assertEqual(v, set())
        self.assertNotEqual(collector.ids, {})
        for k, v in collector.ids.items():
            with self.subTest(type='ids', key=k, val=v):
                if k == 'equal':
                    self.assertEqual(v, {'1anid', '123', '--__-321'})
                else:
                    self.assertEqual(v, set())

    def test_parse_selector_dont_accept_invalid_ident_token(self):
        collector = core.CSSAttributes()
        strict_parser = core.CSSParser(accept_invalid_tokens=False)
        strict_parser._parse_selector(
            r'.valid-class.--_invalid-class.1invalid-class#1invalid-id', collector
        )
        self.assertNotEqual(collector.classes, {})
        for k, v in collector.classes.items():
            with self.subTest(type='classes', key=k, val=v):
                if k == 'classes':
                    self.assertEqual(v, {'valid-class'})
                else:
                    self.assertEqual(v, set())
        self.assertNotEqual(collector.ids, {})
        for k, v in collector.ids.items():
            with self.subTest(type='ids', key=k, val=v):
                self.assertEqual(v, set())

    def test_parse_selector_token_ends_with_double_backslash(self):
        collector = core.CSSAttributes()
        self.cssparser._parse_selector(
            '.class-whose-name-ends-with-backslash\\\\.other-class', collector
        )
        self.assertNotEqual(collector.classes, {})
        for k, v in collector.classes.items():
            with self.subTest(type='classes', key=k, val=v):
                if k == 'classes':
                    self.assertEqual(v, {'class-whose-name-ends-with-backslash\\', 'other-class'})
                else:
                    self.assertEqual(v, set())

    def test_parse_selector_attribute_selector_preceded_by_escaped_bracket(self):
        collector = core.CSSAttributes()
        self.cssparser._parse_selector(
            '.\\\\\\[[class~=aclass]', collector
        )
        self.assertNotEqual(collector.classes, {})
        for k, v in collector.classes.items():
            with self.subTest(type='classes', key=k, val=v):
                if k == 'classes':
                    self.assertEqual(v, {'\\[', 'aclass'})
                else:
                    self.assertEqual(v, set())


class XMLParserTest(Parser):

    def setUp(self):
        super().setUp()
        self.css_collector = core.CSSAttributes()
        self.prefs = {
            'parse_only_selected_files': False,
            'selected_files': [],
            'fragid_container_attrs': [],
            'idref_container_attrs': [],
            'idref_list_container_attrs': [],
        }

    def test_xhtml_parse(self):
        self.bk.text_iter.side_effect = lambda: bk_text_iter([('xhtml1', 'file_href1')])
        collector = core.parse_xhtml(self.bk, self.cssparser, self.css_collector, self.prefs)
        self.assertEqual(
            collector.class_names,
            {'aclass', 'anotherclass', 'undefinedclass', 'definedinstyleclass'}
        )
        self.assertEqual(
            collector.literal_class_values,
            {'aclass anotherclass', 'undefinedclass definedinstyleclass', 'aclass'}
        )
        self.assertEqual(
            collector.id_values,
            {'anid', 'undefinedid', 'someanchor', 'referenced-by-aria-attribute'}
        )
        self.assertEqual(
            collector.fragment_identifier,
            {'someanchor', 'referenced-by-aria-attribute'}
        )
        self.assertEqual(
            collector.info_class_names,
            {
                'aclass': {'file_href1': 2},
                'anotherclass': {'file_href1': 1},
                'undefinedclass': {'file_href1': 1},
                'definedinstyleclass': {'file_href1': 1}
            }
        )
        self.assertEqual(
            collector.info_id_values,
            {
                'anid': {'file_href1': 1},
                'undefinedid': {'file_href1': 1},
                'someanchor': {'file_href1': 1},
                'referenced-by-aria-attribute': {'file_href1': 1}
            }
        )
        self.assertNotEqual(self.css_collector.classes, {})
        for k, v in self.css_collector.classes.items():
            with self.subTest(type='classes', key=k, val=v):
                if k == 'classes':
                    self.assertEqual(v, {'definedinstyleclass'})
                else:
                    self.assertEqual(v, set())

    def test_xhtml_parse_unselected_file(self):
        self.bk.text_iter.side_effect = lambda: bk_text_iter([('xhtml1', 'file_href1')])
        self.prefs['parse_only_selected_files'] = True
        collector = core.parse_xhtml(self.bk, self.cssparser, self.css_collector, self.prefs)
        self.assertEqual(collector.class_names, set())
        self.assertEqual(collector.literal_class_values, set())
        self.assertEqual(collector.id_values, set())
        self.assertEqual(collector.fragment_identifier, {'someanchor', 'referenced-by-aria-attribute'})
        self.assertEqual(collector.info_class_names, {})
        self.assertEqual(collector.info_id_values, {})
        self.assertNotEqual(self.css_collector.classes, {})
        for k, v in self.css_collector.classes.items():
            with self.subTest(type='classes', key=k, val=v):
                self.assertEqual(v, set())
        self.assertNotEqual(self.css_collector.ids, {})
        for k, v in self.css_collector.ids.items():
            with self.subTest(type='ids', key=k, val=v):
                self.assertEqual(v, set())

    def test_xml_parse(self):
        self.bk.manifest_iter.side_effect = lambda: bk_manifest_iter(
            [('media_overlays1', 'file_href1', 'application/smil+xml')]
        )
        self.bk.text_iter.side_effect = lambda: bk_text_iter([])
        collector = core.XHTMLAttributes()
        core.parse_xml(self.bk, collector, self.prefs)
        self.assertEqual(collector.class_names, set())
        self.assertEqual(collector.literal_class_values, set())
        self.assertEqual(collector.id_values, set())
        self.assertEqual(
            collector.fragment_identifier,
            {'ch3_figure1', 'ch3_figure1_title', 'ch3_figure1_caption', 'ch3_figure1_text1', 'ch3_figure1_text2'}
        )
        self.assertEqual(collector.info_class_names, {})
        self.assertEqual(collector.info_id_values, {})

    def test_match_attribute_selectors_classes(self):
        self.css_collector.classes = {
            'equal': {'some classes', 'some different classes'},
            'equal_or_startswith_and_next_is_dash': {'strangeone"'},
            'startswith': {'numberedone-', 'aprefix'},
            'endswith': {'asuffix'},
            'contains': {'ch_red'}
        }
        xhtml_collector = core.XHTMLAttributes()
        xhtml_collector.literal_class_values = {
            'some classes',
            'some unreferenced classes',
            'aprefixedclass',
            'anotherprefix',
            'classwithasuffix',
            'classwithanothersuffix',
            'strangeone&quot;'
        }
        attrs_to_delete = core.match_attribute_selectors(
            self.css_collector.classes, xhtml_collector.literal_class_values
        )
        self.assertEqual(
            attrs_to_delete,
            {'some unreferenced classes', 'anotherprefix', 'classwithanothersuffix'}
        )

    def test_match_attribute_selectors_ids(self):
        self.css_collector.ids = {
            'equal': {'page1', 'page2', 'page3', 'page4', 'page5', 'page6', 'page7'},
            'equal_or_startswith_and_next_is_dash': set(),
            'startswith': {'chapter0'},
            'endswith': set(),
            'contains': set()
        }
        xhtml_collector = core.XHTMLAttributes()
        xhtml_collector.id_values = {
            'page1', 'page2', 'page3', 'page10', 'chapter01', 'chapter02', 'chapter03', 'chapter10'
        }
        attrs_to_delete = core.match_attribute_selectors(self.css_collector.ids, xhtml_collector.id_values)
        self.assertEqual(
            attrs_to_delete,
            {'page10', 'chapter10'}
        )

    def test_delete_xhtml_attributes(self):
        self.bk.text_iter.side_effect = lambda: bk_text_iter([('xhtml1_before_deletions', 'file1')])
        attrs_to_delete = {
            'classes': {'undefinedclass'},
            'ids': {'undefinedid'}
        }
        core.delete_xhtml_attributes(self.bk, attrs_to_delete, self.prefs)
        lines_before = [line.strip() for line in resources.markup_samples['xhtml1_before_deletions'].split('\n') if line]
        lines_after = [line.strip() for line in resources.markup_samples['xhtml1_after_deletions'].split('\n') if line]
        for i in range(min(len(lines_before), len(lines_after))):
            self.assertEqual(lines_before[i], lines_after[i])


# mock callbacks

def read_css(bk, css_id):
    return resources.css_samples[css_id]


def bk_readfile(file_id):
    return resources.markup_samples[file_id]


def bk_writefile(file_id, text):
    resources.markup_samples[file_id] = text
    return resources.markup_samples[file_id]


def bk_css_iter(css_list):
    for id_, href in css_list:
        yield id_, href


def bk_text_iter(text_list):
    for id_, href in text_list:
        yield id_, href


def bk_manifest_iter(text_list):
    for id_, href, mime in text_list:
        yield id_, href, mime


if __name__ == '__main__':
    unittest.main()
