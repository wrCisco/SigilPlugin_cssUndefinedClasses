#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest
from unittest.mock import Mock, MagicMock, patch

import core
from tests import resources

#import sigil_gumbo_bs4_adapter as gumbo_bs4
from bookcontainer import BookContainer


class Parser(unittest.TestCase):

    def setUp(self):
        self.bk = Mock(spec_set=BookContainer)
        self.cssparser = core.CSSParser()

        self.read_css_patch = patch('utils.read_css', side_effect=read_css)
        self.read_css = self.read_css_patch.start()

        read_file = Mock(side_effect=bk_readfile)
        self.bk.readfile = read_file

    def tearDown(self):
        self.read_css_patch.stop()


class CSSParserTest(Parser):

    def test_parse_css_ok(self):
        css_iter = Mock(side_effect=lambda: bk_css_iter([('css1', 'href1')]))
        self.bk.css_iter = css_iter
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
        css_iter = Mock(side_effect=lambda: bk_css_iter([('css2', 'href2')]))
        self.bk.css_iter = css_iter
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
        for k, v in collector.classes.items():
            with self.subTest(type='classes', key=k, val=v):
                self.assertEqual(v, set())
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
        for k, v in collector.classes.items():
            with self.subTest(type='classes', key=k, val=v):
                if k == 'classes':
                    self.assertEqual(v, {'aclass', 'anotherclass'})
                else:
                    self.assertEqual(v, set())

    def test_parse_selector_id_selector(self):
        collector = core.CSSAttributes()
        self.cssparser._parse_selector('#anid, a#anotherid, h2#anid', collector)
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
        for k, v in collector.classes.items():
            with self.subTest(type='classes', key=k, val=v):
                if k == 'classes':
                    self.assertEqual(v, {'aclass', 'anotherclass'})
                elif k == 'equal':
                    self.assertEqual(v, {'a class'})
                else:
                    self.assertEqual(v, set())
        for k, v in collector.ids.items():
            with self.subTest(type='ids', key=k, val=v):
                if k == 'contains':
                    self.assertEqual(v, {'an id'})
                else:
                    self.assertEqual(v, set())


class XMLParserTest(Parser):

    def setUp(self):
        super().setUp()
        self.css_collector = core.CSSAttributes()
        self.prefs = {
            'parse_only_selected_files': False,
            'selected_files': [],
            'fragid_container_attrs': []
        }

    def test_xhtml_parse(self):
        text_iter = Mock(side_effect=lambda: bk_text_iter([('xhtml1', 'file_href1')]))
        self.bk.text_iter = text_iter
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
            {'anid', 'undefinedid', 'someanchor'}
        )
        self.assertEqual(
            collector.fragment_identifier,
            {'someanchor'}
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
                'someanchor': {'file_href1': 1}
            }
        )
        for k, v in self.css_collector.classes.items():
            with self.subTest(type='classes', key=k, val=v):
                if k == 'classes':
                    self.assertEqual(v, {'definedinstyleclass'})
                else:
                    self.assertEqual(v, set())

    def test_xhtml_parse_unselected_file(self):
        text_iter = Mock(side_effect=lambda: bk_text_iter([('xhtml1', 'file_href1')]))
        self.bk.text_iter = text_iter
        self.prefs['parse_only_selected_files'] = True
        collector = core.parse_xhtml(self.bk, self.cssparser, self.css_collector, self.prefs)
        self.assertEqual(collector.class_names, set())
        self.assertEqual(collector.literal_class_values, set())
        self.assertEqual(collector.id_values, set())
        self.assertEqual(collector.fragment_identifier, {'someanchor'})
        self.assertEqual(collector.info_class_names, {})
        self.assertEqual(collector.info_id_values, {})
        for k, v in self.css_collector.classes.items():
            with self.subTest(type='classes', key=k, val=v):
                self.assertEqual(v, set())
        for k, v in self.css_collector.ids.items():
            with self.subTest(type='ids', key=k, val=v):
                self.assertEqual(v, set())

    def test_xml_parse(self):
        manifest_iter = Mock(
            side_effect=lambda: bk_manifest_iter(
                [('media_overlays1', 'file_href1', 'application/smil+xml')]
            )
        )
        text_iter = Mock(side_effect=lambda: bk_text_iter([]))
        self.bk.manifest_iter = manifest_iter
        self.bk.text_iter = text_iter
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


# mock callbacks

def read_css(bk, css_id):
    return resources.css_samples[css_id]


def bk_readfile(file_id):
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
