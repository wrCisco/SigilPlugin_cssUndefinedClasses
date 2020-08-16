#!/usr/bin/env python
# -*- coding: utf-8 -*-


css_samples = {
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

markup_samples = {
    'xhtml1':
'''
<?xml version="1.0" encoding="UTF-8" ?>
<html>
  <head>
    <style>
      .definedinstyleclass {}
    </style>
  </head>
  <body>
    <p class="aclass anotherclass">first <a href="section0001.xhtml#someanchor" id="anid">par</a></p>
    <p class="undefinedclass definedinstyleclass">second par</p>
    <p id="undefinedid">third par</p>
    <p class="aclass"><a id="someanchor">anchor</a></p>
  </body>
</html>
''',

    'xhtml1_before_deletions':
'''
<?xml version="1.0" encoding="utf-8" ?>
<html>
  <head>
    <style>
      .definedinstyleclass {}
    </style>
  </head>
  <body>
    <p class="aclass anotherclass">first <a href="section0001.xhtml#someanchor" id="anid">par</a></p>
    <p class="undefinedclass definedinstyleclass">second par</p>
    <p id="undefinedid">third par</p>
    <p class="aclass"><a id="someanchor">anchor</a></p>
  </body>
</html>
''',

    'xhtml1_after_deletions':
'''
<?xml version="1.0" encoding="utf-8" ?>
<html>
  <head>
    <style>
      .definedinstyleclass {}
    </style>
  </head>
  <body>
    <p class="aclass anotherclass">first <a href="section0001.xhtml#someanchor" id="anid">par</a></p>
    <p class="definedinstyleclass">second par</p>
    <p>third par</p>
    <p class="aclass"><a id="someanchor">anchor</a></p>
  </body>
</html>
''',

    'media_overlays1':
'''
<smil xmlns="http://www.w3.org/ns/SMIL" xmlns:epub="http://www.idpf.org/2007/ops" version="3.0">
  <body>
    <seq id="seq_id" epub:textref="Section0003.xhtml#ch3_figure1" epub:type="figure">
      <par id="par1_id">
        <text src="Section0003.xhtml#ch3_figure1_title"/>
        <audio src="Section0003.mp3" clipBegin="0:13:10.000" clipEnd="0:13:19.724"/>
      </par>
      <par id="par2_id">
        <text src="Section0003.xhtml#ch3_figure1_caption"/>
        <audio src="Section0003.mp3" clipBegin="0:13:19.724" clipEnd="0:13:28.401"/>
      </par>
      <par id="par3_id">
        <text src="Section0003.xhtml#ch3_figure1_text1"/>
        <audio src="Section0003.mp3" clipBegin="0:13:28.401" clipEnd="0:15:01.992"/>
      </par>
      <par id="par4_id">
        <text src="Section0003.xhtml#ch3_figure1_text2"/>
        <audio src="Section0003.mp3" clipBegin="0:15:01.992" clipEnd="0:15:55.482"/>
      </par>
    </seq>
  </body>
</smil>
'''
}