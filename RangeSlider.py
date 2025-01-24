#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys, os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter

SCALE_FACTOR = 1e2  # scale float <-> integer. Adjust as needed.


class RangeSlider(QtWidgets.QSlider):
    """
    A slider for floating-point ranges, using two handles (low & high).
    Internally, QSlider is integer-based, so we scale floats into ints.
    """
    sliderMoved = pyqtSignal(float, float)

    def __init__(self, *args):
        super(RangeSlider, self).__init__(*args)

        # If you prefer horizontal, just setOrientation(Qt.Horizontal)
        self.setOrientation(Qt.Vertical)
        self.setTickPosition(QtWidgets.QSlider.TicksBelow)

        # Store these floats for reference, but QSlider min/max will be scaled ints
        self._float_min = 3.0e-2
        self._float_max = 6.0e+6
        self._low=self._float_min
        self._high=self._float_max

        # Set the QSlider’s integer min/max according to the scale:
        self.setFloatRange(self._float_min, self._float_max)

        # Internal integer “positions” of the two handles (low, high)
        self._low = self.minimum()   # start at the integer min
        self._high = self.maximum()  # start at the integer max

        self.pressed_control = QtWidgets.QStyle.SC_None
        self.hover_control = QtWidgets.QStyle.SC_None
        self.click_offset = 0
        self.active_slider = 0

        self.setMinimumWidth(100)
        self.number_of_ticks = 20  # number of labeled ticks

    # -----------------------------------------------------------------------
    # Public API for floats
    # -----------------------------------------------------------------------
    def setFloatRange(self, fmin, fmax):
        """Set the slider’s floating min and max, then scale to QSlider int range."""
        self._float_min = fmin
        self._float_max = fmax
        int_min = self._floatToInt(fmin)
        int_max = self._floatToInt(fmax)
        self.setMinimum(int_min)
        self.setMaximum(int_max)
        # Fix the current handles if needed:
        if self._low < int_min:
            self._low = int_min
        if self._high > int_max:
            self._high = int_max
        self.update()

    def floatMin(self):
        """Return the float minimum (for reference only)."""
        return self._float_min

    def floatMax(self):
        """Return the float maximum (for reference only)."""
        return self._float_max

    def setFloatLow(self, val):
        """Set the lower handle to a float position."""
        self._low = self._clampInt(self._floatToInt(val))
        self.update()

    def floatLow(self):
        """Get the lower handle’s value in float."""
        return self._intToFloat(self._low)

    def setFloatHigh(self, val):
        """Set the upper handle to a float position."""
        self._high = self._clampInt(self._floatToInt(val))
        self.update()

    def floatHigh(self):
        """Get the upper handle’s value in float."""
        return self._intToFloat(self._high)

    # -----------------------------------------------------------------------
    # Internal scaling helpers
    # -----------------------------------------------------------------------
    def _floatToInt(self, val):
        return int(round(val * SCALE_FACTOR))

    def _intToFloat(self, ival):
        return ival / SCALE_FACTOR

    def _clampInt(self, ival):
        return max(self.minimum(), min(self.maximum(), ival))

    # -----------------------------------------------------------------------
    # Overridden painting to show scientific-notation labels
    # -----------------------------------------------------------------------
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        style = QtWidgets.QApplication.style()

        # 1) Draw the groove
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        opt.sliderValue = 0
        opt.sliderPosition = 0
        opt.subControls = QtWidgets.QStyle.SC_SliderGroove
        style.drawComplexControl(QtWidgets.QStyle.CC_Slider, opt, painter, self)

        groove_rect = style.subControlRect(
            QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderGroove, self
        )

        # 2) Draw the ticks/labels
        self._draw_ticks_and_labels(painter, groove_rect, style, opt)

        # 3) Draw the highlighted span
        self._draw_span(painter, style, groove_rect, opt)

        # 4) Draw the two handles
        self._draw_handles(painter, style, opt)

    def _draw_ticks_and_labels(self, painter, groove_rect, style, opt):
        painter.setPen(QtGui.QPen(QtCore.Qt.black))
        painter.setFont(QtGui.QFont("Arial", 7))

        tick_length = 8
        head_thickness = 5

        if opt.orientation == Qt.Horizontal:
            slider_min = groove_rect.x()
            slider_max = groove_rect.right()
            available = slider_max - slider_min
            text_offset = groove_rect.bottom() + 15
            tick_offset = groove_rect.bottom() + 2
        else:  # Vertical
            slider_min = groove_rect.y() + head_thickness
            slider_max = groove_rect.bottom() - head_thickness
            available = slider_max - slider_min
            text_offset = groove_rect.right() - 20
            tick_offset = groove_rect.right() - 35

        step = (self.maximum() - self.minimum()) / (self.number_of_ticks - 1)

        for i in range(self.number_of_ticks):
            int_value = self.minimum() + int(round(i * step))
            float_value = self._intToFloat(int_value)
            pixel_offset = style.sliderPositionFromValue(
                self.minimum(), self.maximum(), int_value, available, opt.upsideDown
            )

            # Print in scientific notation with 2 decimals, e.g. 3.00E-02 or 6.00E+06
            label = "{:.2E}".format(float_value)

            if opt.orientation == Qt.Horizontal:
                x = slider_min + pixel_offset
                painter.drawLine(x, tick_offset, x, tick_offset + tick_length)
                text_rect = QtCore.QRect(x - 15, text_offset, 30, 12)
                painter.drawText(text_rect, QtCore.Qt.AlignCenter, label)
            else:
                y = slider_min + pixel_offset
                painter.drawLine(tick_offset, y, tick_offset + tick_length, y)
                text_rect = QtCore.QRect(text_offset, y - 6, 50, 12)
                painter.drawText(text_rect, QtCore.Qt.AlignVCenter, label)

    def _draw_span(self, painter, style, groove_rect, opt):
        self.initStyleOption(opt)
        opt.subControls = QtWidgets.QStyle.SC_SliderGroove
        opt.sliderValue = 0

        # positions of the two handles in pixels
        opt.sliderPosition = self._low
        low_rect = style.subControlRect(QtWidgets.QStyle.CC_Slider, opt,
                                        QtWidgets.QStyle.SC_SliderHandle, self)
        opt.sliderPosition = self._high
        high_rect = style.subControlRect(QtWidgets.QStyle.CC_Slider, opt,
                                         QtWidgets.QStyle.SC_SliderHandle, self)

        def pick(pt):
            return pt.x() if opt.orientation == Qt.Horizontal else pt.y()

        low_pos = pick(low_rect.center())
        high_pos = pick(high_rect.center())
        min_pos = min(low_pos, high_pos)
        max_pos = max(low_pos, high_pos)
        center_pt = QtCore.QRect(low_rect.center(), high_rect.center()).center()

        if opt.orientation == Qt.Horizontal:
            span_rect = QtCore.QRect(
                QtCore.QPoint(min_pos, center_pt.y() - 2),
                QtCore.QPoint(max_pos, center_pt.y() + 2)
            )
            groove_rect.adjust(0, 0, -1, 0)
        else:
            span_rect = QtCore.QRect(
                QtCore.QPoint(center_pt.x() - 2, min_pos),
                QtCore.QPoint(center_pt.x() + 2, max_pos)
            )
            groove_rect.adjust(0, 0, 0, 1)

        highlight = self.palette().color(QtGui.QPalette.Highlight)
        painter.setBrush(QtGui.QBrush(highlight))
        painter.setPen(QtGui.QPen(highlight, 0))
        painter.drawRect(span_rect.intersected(groove_rect))

    def _draw_handles(self, painter, style, opt):
        for value in [self._low, self._high]:
            opt.sliderPosition = value
            opt.sliderValue = value
            opt.subControls = QtWidgets.QStyle.SC_SliderHandle
            style.drawComplexControl(QtWidgets.QStyle.CC_Slider, opt, painter, self)

    # -----------------------------------------------------------------------
    # Mouse events
    # -----------------------------------------------------------------------
    def mousePressEvent(self, event):
        event.accept()
        style = QtWidgets.QApplication.style()
        button = event.button()

        if button:
            opt = QtWidgets.QStyleOptionSlider()
            self.initStyleOption(opt)
            self.active_slider = -1

            for i, value in enumerate([self._low, self._high]):
                opt.sliderPosition = value
                hit = style.hitTestComplexControl(
                    style.CC_Slider, opt, event.pos(), self
                )
                if hit == style.SC_SliderHandle:
                    self.active_slider = i
                    self.pressed_control = hit
                    self.triggerAction(self.SliderMove)
                    self.setRepeatAction(self.SliderNoAction)
                    self.setSliderDown(True)
                    break

            if self.active_slider < 0:
                self.pressed_control = QtWidgets.QStyle.SC_SliderHandle
                self.click_offset = self.__pixelPosToRangeValue(self.__pick(event.pos()))
                self.triggerAction(self.SliderMove)
                self.setRepeatAction(self.SliderNoAction)
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        if self.pressed_control != QtWidgets.QStyle.SC_SliderHandle:
            event.ignore()
            return

        event.accept()
        new_pos = self.__pixelPosToRangeValue(self.__pick(event.pos()))
        if self.active_slider < 0:
            # dragged outside the handles: move both together
            offset = new_pos - self.click_offset
            self._low += offset
            self._high += offset
            if self._low < self.minimum():
                diff = self.minimum() - self._low
                self._low += diff
                self._high += diff
            if self._high > self.maximum():
                diff = self.maximum() - self._high
                self._low += diff
                self._high += diff
        elif self.active_slider == 0:
            # lower handle
            if new_pos >= self._high:
                new_pos = self._high - 1
            self._low = new_pos
        else:
            # upper handle
            if new_pos <= self._low:
                new_pos = self._low + 1
            self._high = new_pos

        self.click_offset = new_pos
        self.update()

        # Emit float positions to listeners
        self.sliderMoved.emit(self._intToFloat(self._low),
                              self._intToFloat(self._high))

    def __pick(self, pt):
        return pt.x() if self.orientation() == Qt.Horizontal else pt.y()

    def __pixelPosToRangeValue(self, pos):
        style = QtWidgets.QApplication.style()
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)

        gr = style.subControlRect(style.CC_Slider, opt, style.SC_SliderGroove, self)
        sr = style.subControlRect(style.CC_Slider, opt, style.SC_SliderHandle, self)

        if self.orientation() == Qt.Horizontal:
            slider_length = sr.width()
            slider_min = gr.x()
            slider_max = gr.right() - slider_length + 1
        else:
            slider_length = sr.height()
            slider_min = gr.y()
            slider_max = gr.bottom() - slider_length + 1

        return style.sliderValueFromPosition(self.minimum(),
                                             self.maximum(),
                                             pos - slider_min,
                                             slider_max - slider_min,
                                             opt.upsideDown)


    
##############################
# Test
##############################

def echo(low_value, high_value):
    print(low_value, high_value)

def test(argv):

    app = QtWidgets.QApplication(sys.argv)

    slider = RangeSlider()
    slider.setMinimumHeight(300)

    # Example: set the float range to [0.03, 6e6]
    slider.setFloatRange(3.0e-2, 6.0e6)

    # Set where you want the two thumbs to start in float
    slider.setFloatLow(0.5)
    slider.setFloatHigh(1.0e5)

    # Connect the custom signal (which now sends floats)
    slider.sliderMoved.connect(echo)

    slider.show()
    slider.raise_()
    sys.exit(app.exec_())


if __name__ == "__main__":
    test(sys.argv)