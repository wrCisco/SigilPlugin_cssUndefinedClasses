#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


try:
    os.environ['SigilGumboLibPath']
except KeyError:
    os.environ['SigilGumboLibPath'] = '/usr/local/lib/sigil/libsigilgumbo.so'  # std linux path

import sigil_gumbo_bs4_adapter as gumbo_bs4
