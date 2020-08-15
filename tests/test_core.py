#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest
from unittest.mock import Mock, MagicMock, patch

import core

#import sigil_gumbo_bs4_adapter as gumbo_bs4
from bookcontainer import BookContainer


class CSSParserTest(unittest.TestCase):

    css = {
        'css1':
'''
.aclass, .anotherclass {}
#anid {}
*[class=equalclass] {}
*[class="equal class"] {}
h1.aclass + p.yetanotherclass[class|=startorequal] {}
*[class~=wholenameclass] {}
*[class^=startswithclass] {}
*[class^='startswith class'] {}
*[class$=endswithclass] {}
*[class$="ends with class"] {}
*[class*=containsclass] {}
*[class*='contains class'] {}
''',
        'css2':
'''
a.gibb,{}
'''
    }

    def setUp(self):
        self.bk = Mock(spec_set=BookContainer)
        self.cssparser = core.CSSParser()

        self.read_css_patch = patch('utils.read_css', side_effect=read_css)
        self.read_css = self.read_css_patch.start()

    def tearDown(self):
        self.read_css_patch.stop()

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
        collector = self.cssparser.parse_style(CSSParserTest.css['css1'], filename='css1')
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
            CSSParserTest.css['css2'], filename='css2.xhtml'
        )


def read_css(bk, css_id):
    return CSSParserTest.css[css_id]


def bk_css_iter(css_list):
    for id_, href in css_list:
        yield id_, href