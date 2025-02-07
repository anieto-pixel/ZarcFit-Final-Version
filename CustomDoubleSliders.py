#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Originated from
# https://www.mail-archive.com/pyqt@riverbankcomputing.com/msg22889.html
# Modification refered from
# https://gist.github.com/Riateche/27e36977f7d5ea72cf4f
# Second Modification from agarcian

import sys, os
import math
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt, pyqtSignal, Qt, pyqtSignal, QRect, QSize
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QPushButton
)
from PyQt5.QtGui import QPainter, QFont, QColor, QFontMetrics

class RangeSlider(QtWidgets.QSlider):
    valueDoubleChanged = QtCore.pyqtSignal(int, int)

    def __init__(self, *args):
        super(RangeSlider, self).__init__(*args)
        self._low = self.minimum()
        self._high = self.maximum()
        
        self.pressed_control = QtWidgets.QStyle.SC_None
        self.tick_interval = 0
        self.tick_position = QtWidgets.QSlider.NoTicks
        self.hover_control = QtWidgets.QStyle.SC_None
        self.click_offset = 0
        self.active_slider = -1

    def low(self):
        return self._low

    def setLow(self, low: int):
        self._low = low
        self.update()

    def high(self):
        return self._high

    def setHigh(self, high: int):
        self._high = high
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        style = QtWidgets.QApplication.style()

        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        opt.sliderValue = 0
        opt.sliderPosition = 0
        opt.subControls = QtWidgets.QStyle.SC_SliderGroove
        if self.tickPosition() != self.NoTicks:
            opt.subControls |= QtWidgets.QStyle.SC_SliderTickmarks
        
        style.drawComplexControl(QtWidgets.QStyle.CC_Slider, opt, painter, self)
        groove = style.subControlRect(QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderGroove, self)

        opt.sliderPosition = self._low
        low_rect = style.subControlRect(QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderHandle, self)
        opt.sliderPosition = self._high
        high_rect = style.subControlRect(QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderHandle, self)

        if opt.orientation == QtCore.Qt.Horizontal:
            span_rect = QtCore.QRect(low_rect.center().x(), groove.top(), high_rect.center().x(), groove.bottom())
        else:
            span_rect = QtCore.QRect(groove.left(), low_rect.center().y(), groove.right(), high_rect.center().y())

        highlight = self.palette().color(QtGui.QPalette.Highlight)
        painter.setBrush(QtGui.QBrush(highlight))
        painter.setPen(QtGui.QPen(highlight, 0))
        painter.drawRect(span_rect.intersected(groove))

        for value in [self._low, self._high]:
            opt.sliderPosition = value
            opt.sliderValue = value
            opt.subControls = QtWidgets.QStyle.SC_SliderHandle
            style.drawComplexControl(QtWidgets.QStyle.CC_Slider, opt, painter, self)

    def mousePressEvent(self, event):
        event.accept()
        style = QtWidgets.QApplication.style()
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        self.active_slider = -1

        for i, value in enumerate([self._low, self._high]):
            opt.sliderPosition = value
            hit = style.hitTestComplexControl(QtWidgets.QStyle.CC_Slider, opt, event.pos(), self)
            if hit == QtWidgets.QStyle.SC_SliderHandle:
                self.active_slider = i
                self.pressed_control = hit
                self.triggerAction(self.SliderMove)
                self.setRepeatAction(self.SliderNoAction)
                self.setSliderDown(True)
                return

        self.pressed_control = QtWidgets.QStyle.SC_SliderHandle
        self.click_offset = self.__pixelPosToRangeValue(self.__pick(event.pos()))
        self.triggerAction(self.SliderMove)
        self.setRepeatAction(self.SliderNoAction)

    def mouseMoveEvent(self, event):
        if self.pressed_control != QtWidgets.QStyle.SC_SliderHandle:
            event.ignore()
            return

        event.accept()
        new_pos = self.__pixelPosToRangeValue(self.__pick(event.pos()))

        if self.active_slider == 0:
            self._low = min(new_pos, self._high - 1)
        elif self.active_slider == 1:
            self._high = max(new_pos, self._low + 1)

        self.click_offset = new_pos
        self.update()
        self.valueDoubleChanged.emit(self._low, self._high)

    def __pick(self, pt):
        return pt.x() if self.orientation() == Qt.Horizontal else pt.y()

    def __pixelPosToRangeValue(self, pos):
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        style = QtWidgets.QApplication.style()
        gr = style.subControlRect(QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderGroove, self)
        sr = style.subControlRect(QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderHandle, self)

        if self.orientation() == Qt.Horizontal:
            slider_min = gr.x()
            slider_max = gr.right() - sr.width() + 1
        else:
            slider_min = gr.y()
            slider_max = gr.bottom() - sr.height() + 1

        return style.sliderValueFromPosition(self.minimum(), self.maximum(), pos - slider_min, slider_max - slider_min, opt.upsideDown)


class CustomSliders(QWidget):
    """
    A basic double headed with labeled ticks and a value label.
    Takes an array
    This class provides:
      - A slider from min_value to max_value.
      - Tick markings displayed on the widget's paint event.
      - A label showing the current slider value.
    """
    
    was_disabled = pyqtSignal(bool)

    def __init__(self, my_list, direction, number_of_tick_intervals=10):
        super().__init__()
        
        self.my_list= my_list
        # Setup slider parameters
        self._min_value = 0
        self._max_value = len(my_list)
        self.number_of_tick_intervals = number_of_tick_intervals

        # Main slider
        self._slider = RangeSlider(direction, self) #enabled by default

        # Overall widget layout
        self._layout = QHBoxLayout()
        #label, if at all

        # Configure slider appearance and functionality
        self._setup_slider()
        self.setLayout(self._layout)
        
    # -----------------------------------------------------------------------
    #  Private Methods
    # -----------------------------------------------------------------------

        
    def _setup_slider(self):
        """
        Configure the slider's properties (range, ticks, color).
        """
        self._slider.setRange(self._min_value, self._max_value)
        self._slider.setTickPosition(QSlider.TicksBothSides)

        # Safely set a tick interval (avoid division by zero if ranges are small)
        interval = max(1, (self._max_value - self._min_value) // self.number_of_tick_intervals)
        self._slider.setTickInterval(interval)
        

    def _string_by_tick(self, i):
        """
        Return the string to display next to each tick mark.
        In this default implementation, it's just the integer value.
        """
        return str(i)

    def paintEvent(self, event):
        """
        Draw tick labels for the range of values at fixed intervals.
        """
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setFont(QFont("Arial", 7))#if changed you may want to change WidgetSliders as well to allow extra space between sliders
        painter.setPen(QColor(0, 0, 0))

        # Gather slider range/tick info
        min_val = self._slider.minimum()
        max_val = self._slider.maximum()
        tick_interval = self._slider.tickInterval()

        # Calculate available space for drawing
        height = self._slider.height()
        top_off = 5
        bottom_off = 5
        effective_height = height - top_off - bottom_off

        # For each tick step, compute its position and draw text
        for i in range(min_val, max_val + 1, tick_interval):
            tick_pos = (
                height - bottom_off - (effective_height * (i - min_val)) // (max_val - min_val)
            )
            text_rect = QRect(25, tick_pos, 50, 20)
            painter.drawText(text_rect, Qt.AlignCenter, self._string_by_tick(i))

    # -----------------------------------------------------------------------
    #  Public Methods
    # -----------------------------------------------------------------------

    def get_value(self):
        """
        Returns the current integer value of the slider.
        """
        i = self._slider.value()
        return self.my_list[i]

    def set_value(self, value):
        """
        Find the element in the list, set the slider to the index
        """
        pass


    def value_changed(self):
        """
        Exposes the slider's valueChanged signal for external listeners.
        """
        return self._slider.valueDoubleChanged


# Minimal demo
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = QtWidgets.QMainWindow()

    # Create our RangeSlider
    
    slider = RangeSlider(Qt.Vertical)    
#    slider = CustomSliders([1,2,3,4,5,6,5,4,3,2,1], Qt.Vertical, number_of_tick_intervals=10)
#    slider = CustomSliders([1,2,3,4,5,6,5,4,3,2,1], Qt.Horizontal, number_of_tick_intervals=10)
#    slider.value_changed().connect(lambda low, high: print(f"Low={low:.3g}, High={high:.3g}"))
#
#    win.setCentralWidget(slider)
    slider.show()
    sys.exit(app.exec_())
