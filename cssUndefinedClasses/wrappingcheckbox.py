from plugin_utils import QtWidgets, Qt, QtCore, QtGui


class WrappingCheckBox(QtWidgets.QWidget):

    def __init__(self, text="", margins=(0,0,0,0), spacing=12,
                fillBackground=True, parent=None):
        super().__init__(parent)
        
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(*margins)
        self.layout.setSpacing(spacing)

        self.setAutoFillBackground(bool(fillBackground))

        self.checkbox = CheckBoxHighlighter(self)
        
        self.label = QtWidgets.QLabel()
        self.label.setWordWrap(True)
        self.labelText = text  # will be set as label's text in the showEvent method
        
        # Make label clickable to toggle checkbox
        self.label.mousePressEvent = self._on_label_click
        
        self.layout.addWidget(self.checkbox)
        self.layout.addWidget(self.label, stretch=1)

    def _on_label_click(self, event):
        """Handle label click to toggle checkbox"""
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
        return self.checkbox.checkStateChanged
    
    def stateChanged(self):
        """Access to the checkbox's stateChanged signal (for older Qt compatibility)"""
        return self.checkbox.stateChanged if hasattr(self.checkbox, 'stateChanged') else self.checkbox.checkStateChanged
    
    def clicked(self):
        """Access to the checkbox's clicked signal"""
        return self.checkbox.clicked
    
    def toggled(self):
        """Access to the checkbox's toggled signal"""
        return self.checkbox.toggled

    def showEvent(self, event):
        super().showEvent(event)
        self.label.setText(
            self.break_long_words(self.labelText, self.width() - 20)
        )
        # self.label.updateGeometry()
        # self.updateGeometry()

    def break_long_words(self, text, availableWidth):
        """Intersperse zero-width white spaces between the characters
        of words longer than the available width."""
        margins = self.layout.contentsMargins()
        spacing = self.layout.spacing()
        if self.checkbox.isVisible():
            checkboxWidth = self.checkbox.width()
        else:
            checkboxWidth = self.checkbox.sizeHint().width()
        minWidthToBreakWord = availableWidth \
            - checkboxWidth \
            - spacing \
            - margins.left() \
            - margins.right()
        separators = ' -\u200B'  # just the most common ones
        words = []
        w_start = 0
        for i, c in enumerate(text):
            if c in separators:
                words.append(text[w_start:i])
                w_start = i
        if w_start != i:
            words.append(text[w_start:])
        fontMetrics = QtGui.QFontMetricsF(self.label.font())
        for i, w in enumerate(words):
            if fontMetrics.horizontalAdvance(w) > minWidthToBreakWord:
                words[i] = '\u200B'.join(w)
        return ''.join(words)


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
