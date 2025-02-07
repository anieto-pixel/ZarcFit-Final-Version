# -*- coding: utf-8 -*-
"""
Created on Thu Feb  6 15:21:01 2025

@author: agarcian
"""

import sys
import math
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal


class ListSliderRange(QtWidgets.QSlider):
    """
    A two-handle slider for *log10* ranges.
    QSlider is still integer-based, but now those integers represent log10(value).
    """
    #valueChanged = pyqtSignal(object, object)
    sliderMoved = pyqtSignal(float, float)

    def __init__(self, values_list=[0.0], *args):
        print("CREATEEEEE")
        
        super(ListSliderRange, self).__init__(*args)

        self.values_list=values_list
        self.setOrientation(Qt.Vertical)
        self.setTickPosition(QtWidgets.QSlider.TicksBelow)

        # Store float min/max in normal linear space (e.g. 2e-2, 6e6)
        
        self.setMinimum(0)
        self.setMaximum(len(self.values_list))

        # Start both handles at extremes
        self._low = self.minimum()
        self._high = self.maximum()

        self.pressed_control = QtWidgets.QStyle.SC_None
        self.hover_control = QtWidgets.QStyle.SC_None
        self.click_offset = 0
        self.active_slider = -1

        self.setMinimumWidth(100)
        self.number_of_ticks = 20

    def low(self):
        return self._low
    
    def low_value(self):
        if 0 <= self._low < len(self.values_list):
            return self.values_list[self._low]
        return None

    def setLow(self, low: int):
        if low<self._high:
            self._low = low
            self.update()
        
    def high(self):
        return self._high
    
    def high_value(self):
        if 0 <= self._high < len(self.values_list):
            return self.values_list[self._high]
        return None
    
    def setHigh(self, high: int):
        if self._low<high:
            self._high = high
            self.update()
    
    def setValue(self, value):
        print(value)
        if value not in self.values_list:
            return  # Ignore if value is not in the list

        index = self.values_list.index(value)
        
        # Decide which handle to move
        if abs(index - self._low) <= abs(index - self._high):
            self.setLow(index)
        else:
            self.setHigh(index)
            
        self.update()

    def setList(self, values_list: list):

        if (len(values_list)<1):
            values_list = [0.0]
            
        else:
            self.values_list=values_list
            # Update the slider range so it matches the new list length
            self.setMinimum(0)
            # If you want valid indices only, use (len(...)-1) as the max:
            self.setMaximum(len(self.values_list) - 1)
        
            # Clamp the current low/high so they're not out of the new range
            self._low = self.minimum()
            self._high = self.maximum()
        
            # Redraw with the new range
            self.update()

    def upMin(self):
        """Example: shift lower handle upward by a certain factor in linear space."""
        new_low = self.low()+1
        if new_low < self.high():
            self.setLow(new_low)
        self.sliderMoved.emit(self.low(), self.high())

    def downMax(self):
        """Example: shift upper handle downward by a certain factor in linear space."""
        new_high = self.high() -1
        if new_high > self.low():
            self.setHigh(new_high)
        self.sliderMoved.emit(self.low(), self.high())

    def default(self):
        """Reset slider to the full float range."""
        self.setLow(self._min)
        self.setHigh(self._max)
        self.sliderMoved.emit(self.low(), self.high())

    # -----------------------------------------------------------------------
    # Painting: we want ticks spaced in exponent (log) scale
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
        groove_rect = style.subControlRect(QtWidgets.QStyle.CC_Slider, opt,
                                           QtWidgets.QStyle.SC_SliderGroove, self)

        # 2) Draw the ticks/labels in log steps
        self._draw_ticks_and_labels(painter, groove_rect, style, opt)

        # 3) Draw the highlighted span
        self._draw_span(painter, style, groove_rect, opt)

        # 4) Draw handles
        self._draw_handles(painter, style, opt)

    def _draw_ticks_and_labels(self, painter, groove_rect, style, opt):
        
        
        print(f"maximum {self.maximum()}")
        print(f"minimum {self.minimum()}")
        print(f" low {self._low}")
        print(f" high {self._high}")
         
        step = math.ceil((self.maximum() - self.minimum()) / (self.number_of_ticks - 1))
        if(step):
#        """
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
            else:
                slider_min = groove_rect.y() + head_thickness
                slider_max = groove_rect.bottom() - head_thickness
                available = slider_max - slider_min
                text_offset = groove_rect.right() - 20
                tick_offset = groove_rect.right() - 35
    
            for i in range(self.minimum(), self.maximum() + 1, step):
                pixel_offset = style.sliderPositionFromValue(
                    self.minimum(), self.maximum(), i, available, opt.upsideDown
                )
    
                label = f"{i}"
    
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
    # Mouse event handling remains the same as your original
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
                hit = style.hitTestComplexControl(style.CC_Slider, opt, event.pos(), self)
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

        # Decide which handle is being moved
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

        # Emit float positions in normal (non-log) space
        self.sliderMoved.emit(self.low(), self.high())

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

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = QtWidgets.QMainWindow()

    central_widget = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(central_widget)

    slider = ListSliderRange([1, 5, 10, 15, 20])
    slider.sliderMoved.connect(lambda low, high: print(f"Low={low}, High={high}"))

    btn_empty = QtWidgets.QPushButton("Set Empty List")
    btn_empty.clicked.connect(lambda: slider.setList([]))

    btn_single = QtWidgets.QPushButton("Set Single Item")
    btn_single.clicked.connect(lambda: slider.setList([10]))

    btn_multi = QtWidgets.QPushButton("Set Multi")
    btn_multi.clicked.connect(lambda: slider.setList([10, 20, 30, 40, 50]))

    btn_up = QtWidgets.QPushButton("UpMin")
    btn_up.clicked.connect(slider.upMin)

    btn_down = QtWidgets.QPushButton("DownMax")
    btn_down.clicked.connect(slider.downMax)

    layout.addWidget(slider)
    layout.addWidget(btn_empty)
    layout.addWidget(btn_single)
    layout.addWidget(btn_multi)
    layout.addWidget(btn_up)
    layout.addWidget(btn_down)

    win.setCentralWidget(central_widget)
    win.show()
    sys.exit(app.exec_())
