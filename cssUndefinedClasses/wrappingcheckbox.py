# Copyright (c) 2025 Francesco Martini
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


from plugin_utils import QtWidgets, Qt, QtCore, QtGui
from utils import tokenize_text, compute_words_length


class WrappingCheckBox(QtWidgets.QWidget):

    def __init__(self, text="", margins=(0,0,0,0), spacing=12,
                fillBackground=True, parent=None):
        super().__init__(parent)
        
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(*margins)
        self.layout.setSpacing(spacing)

        self.setAutoFillBackground(bool(fillBackground))

        self.checkbox = CheckBoxHighlighter(self)
        self.label = WrappingLabel(text)
        
        self.layout.addWidget(self.checkbox)
        self.layout.addWidget(self.label, stretch=1)

    def mousePressEvent(self, event):
        """Handle label click to toggle checkbox"""
        super().mousePressEvent(event)
        self.checkbox.toggle()
        self.checkbox.setFocus()

    def setText(self, text):
        """Set the text displayed in the label"""
        self.label.setText(text)
    
    def text(self):
        """Get the text from the label"""
        return self.label.text()
    
    def setChecked(self, checked):
        """Set checkbox checked state"""
        self.checkbox.setChecked(checked)
    
    def isChecked(self):
        """Get checkbox checked state"""
        return self.checkbox.isChecked()
    
    def toggle(self):
        """Toggle checkbox state"""
        self.checkbox.toggle()
    
    def setEnabled(self, enabled):
        """Enable/disable the widget"""
        super().setEnabled(enabled)
        self.checkbox.setEnabled(enabled)
        self.label.setEnabled(enabled)
    
    def checkStateChanged(self):
        """Access to the checkbox's checkStateChanged signal"""
        return self.stateChanged()
    
    def stateChanged(self):
        """Access to the checkbox's stateChanged signal (for older Qt compatibility)"""
        return self.checkbox.stateChanged if hasattr(self.checkbox, 'stateChanged') else self.checkbox.checkStateChanged
    
    def clicked(self):
        """Access to the checkbox's clicked signal"""
        return self.checkbox.clicked
    
    def toggled(self):
        """Access to the checkbox's toggled signal"""
        return self.checkbox.toggled


class CheckBoxHighlighter(QtWidgets.QCheckBox):

    def __init__(self, parent=None):
        super().__init__(parent)

    def focusInEvent(self, event):
        """Handle checkbox focus in from keyboard to highlight the parent widget"""
        super().focusInEvent(event)
        if event.reason() not in (Qt.TabFocusReason, Qt.BacktabFocusReason):
            return
        if self.parent() and self.parent().autoFillBackground():
            palette = self.parent().palette()
            self.oldBgColor = palette.color(self.parent().backgroundRole())
            highlightColor = palette.color(QtGui.QPalette.Highlight)
            palette.setColor(self.parent().backgroundRole(), highlightColor)
            self.parent().setPalette(palette)

            palette = self.parent().label.palette()
            self.oldTextColor = palette.color(self.parent().label.foregroundRole())
            highlightedTextColor = palette.color(QtGui.QPalette.HighlightedText)
            palette.setColor(self.parent().label.foregroundRole(), highlightedTextColor)
            self.parent().label.setPalette(palette)

    def focusOutEvent(self, event):
        """Handle checkbox focus out from keyboard to highlight the parent widget"""
        super().focusOutEvent(event)
        if hasattr(self, 'oldBgColor'):
            palette = self.parent().palette()
            palette.setColor(self.parent().backgroundRole(), self.oldBgColor)
            self.parent().setPalette(palette)
        if hasattr(self, 'oldTextColor'):
            palette = self.parent().label.palette()
            palette.setColor(self.parent().label.foregroundRole(), self.oldTextColor)
            self.parent().label.setPalette(palette)


class WrappingLabel(QtWidgets.QLabel):

    def __init__(self, text='', parent=None):
        super().__init__('', parent)
        self.setWordWrap(True)
        self.setMinimumWidth(10)
        self._text = self._preprocess_text(text)
        self._length_index = -1

    def showEvent(self, event):
        super().showEvent(event)
        self._reset_text()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reset_text()

    def setText(self, text):
        self._text = self._preprocess_text(text)
        self._length_index = -1
        self._reset_text()

    def setFont(self, font):
        super().setFont(font)
        self._text = self._preprocess_text(''.join(self._text['words']))
        self._length_index = -1
        self._reset_text()

    def _update_length_index(self):
        available_width = self.width() - 5
        for i in range(len(self._text['sorted_lengths'])):
            if self._text['sorted_lengths'][i] <= available_width <= self._text['sorted_lengths'][i + 1]:
                self._length_index = i
                break

    def _reset_text(self):
        new_text = self._compose_text(self.width() - 5)
        if new_text:
            super().setText(new_text)

    def _compose_text(self, available_width):
        lengths, i = self._text['sorted_lengths'], self._length_index
        if i != -1 and lengths[i] <= available_width <= lengths[i + 1]:
            return
        self._update_length_index()
        words = []
        for i, word in enumerate(self._text['words']):
            if available_width < self._text['lengths'][i]:
                next_word = self._text['breakable_words'][i]
            else:
                next_word = word
            words.append(next_word)
        return ''.join(words)

    def _preprocess_text(self, text):
        words = tokenize_text(text, QtCore.QTextBoundaryFinder.BoundaryType.Line)
        lengths = compute_words_length(words, self.font())
        breakable_words = []
        for word in words:
            graphemes = tokenize_text(word, QtCore.QTextBoundaryFinder.BoundaryType.Grapheme)
            breakable_words.append('\u200B'.join(graphemes))
        sorted_lengths = [0, *sorted(list(set(lengths))), 999999]
        return {
            'words': words,
            'breakable_words': breakable_words,
            'lengths': lengths,
            'sorted_lengths': sorted_lengths,
        }
