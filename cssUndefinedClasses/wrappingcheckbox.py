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


from collections.abc import Sequence
import typing

from plugin_utils import QtWidgets, Qt, QtCore, QtGui
from utils import tokenize_text, compute_words_length


class ProcessedText(typing.TypedDict):
    words: Sequence[str]
    breakable_words: Sequence[str]
    lengths: Sequence[float]


class WrappingCheckBox(QtWidgets.QWidget):

    def __init__(
            self,
            text: str = "",
            margins: Sequence[int] = (0,0,0,0),
            spacing: int = 12,
            fillBackground: bool = True,
            parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        
        self._layout = QtWidgets.QHBoxLayout(self)
        self._layout.setContentsMargins(*margins)
        self._layout.setSpacing(spacing)

        self.setAutoFillBackground(bool(fillBackground))

        self.checkbox = CheckBoxHighlighter(self)
        self.label = WrappingLabel(text)
        
        self._layout.addWidget(self.checkbox)
        self._layout.addWidget(self.label, stretch=1)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handle label click to toggle checkbox"""
        super().mousePressEvent(event)
        self.checkbox.toggle()
        self.checkbox.setFocus()

    def setText(self, text: str) -> None:
        """Set the text displayed in the label"""
        self.label.setText(text)
    
    def text(self) -> str:
        """Get the text from the label"""
        return self.label.text()
    
    def setChecked(self, checked: bool) -> None:
        """Set checkbox checked state"""
        self.checkbox.setChecked(checked)
    
    def isChecked(self) -> bool:
        """Get checkbox checked state"""
        return self.checkbox.isChecked()
    
    def toggle(self) -> None:
        """Toggle checkbox state"""
        self.checkbox.toggle()
    
    def setEnabled(self, enabled: bool) -> None:
        """Enable/disable the widget"""
        super().setEnabled(enabled)
        self.checkbox.setEnabled(enabled)
        self.label.setEnabled(enabled)
    
    def checkStateChanged(self) -> 'QtCore.SignalInstance':
        """Access to the checkbox's checkStateChanged signal"""
        return self.stateChanged()
    
    def stateChanged(self) -> 'QtCore.SignalInstance':
        """Access to the checkbox's stateChanged signal (for older Qt compatibility)"""
        return self.checkbox.stateChanged if hasattr(self.checkbox, 'stateChanged') else self.checkbox.checkStateChanged
    
    def clicked(self) -> 'QtCore.SignalInstance':
        """Access to the checkbox's clicked signal"""
        return self.checkbox.clicked
    
    def toggled(self) -> 'QtCore.SignalInstance':
        """Access to the checkbox's toggled signal"""
        return self.checkbox.toggled


class CheckBoxHighlighter(QtWidgets.QCheckBox):

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

    def parent(self) -> WrappingCheckBox:
        return typing.cast(WrappingCheckBox, super().parent())

    def focusInEvent(self, event: QtGui.QFocusEvent) -> None:
        """Handle checkbox focus in from keyboard to highlight the parent widget"""
        super().focusInEvent(event)
        if event.reason() not in (Qt.FocusReason.TabFocusReason, Qt.FocusReason.BacktabFocusReason):
            return
        if self.parent() and self.parent().autoFillBackground():
            palette = self.parent().palette()
            self.oldBgColor = palette.color(self.parent().backgroundRole())
            highlightColor = palette.color(QtGui.QPalette.ColorRole.Highlight)
            palette.setColor(self.parent().backgroundRole(), highlightColor)
            self.parent().setPalette(palette)

            palette = self.parent().label.palette()
            self.oldTextColor = palette.color(self.parent().label.foregroundRole())
            highlightedTextColor = palette.color(QtGui.QPalette.ColorRole.HighlightedText)
            palette.setColor(self.parent().label.foregroundRole(), highlightedTextColor)
            self.parent().label.setPalette(palette)

    def focusOutEvent(self, event: QtGui.QFocusEvent) -> None:
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

    def __init__(self, text: str = '', parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__('', parent)
        self.setWordWrap(True)
        self.setMinimumWidth(10)
        self._text = self.preprocess_text(text)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        super().showEvent(event)
        self.reset_text()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self.reset_text()

    def setText(self, text: str) -> None:
        self._text = self.preprocess_text(text)
        self.reset_text()

    def setFont(self, font: QtGui.QFont | str | Sequence[str]) -> None:
        super().setFont(font)
        self._text = self.preprocess_text(''.join(self._text['words']))
        self.reset_text()

    def reset_text(self) -> None:
        super().setText(self.compose_text(self.width()))

    def compose_text(self, availableWidth: int | float) -> str:
        words = []
        for i, word in enumerate(self._text['words']):
            if availableWidth < self._text['lengths'][i]:
                next_word = self._text['breakable_words'][i]
            else:
                next_word = word
            words.append(next_word)
        return ''.join(words)

    def preprocess_text(self, text: str) -> ProcessedText:
        words = tokenize_text(text, QtCore.QTextBoundaryFinder.BoundaryType.Line)
        lengths = compute_words_length(words, self.font())
        breakable_words = []
        for word in words:
            graphemes = tokenize_text(word, QtCore.QTextBoundaryFinder.BoundaryType.Grapheme)
            breakable_words.append('\u200B'.join(graphemes))
        return {
            'words': words,
            'breakable_words': breakable_words,
            'lengths': lengths,
        }
