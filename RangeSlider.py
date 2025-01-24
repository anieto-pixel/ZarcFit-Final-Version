#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys, os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QSize
from PyQt5.QtGui import QPainter, QFont, QColor, QFontMetrics

# Originated from
# https://www.mail-archive.com/pyqt@riverbankcomputing.com/msg22889.html
# Modification refered from
# https://gist.github.com/Riateche/27e36977f7d5ea72cf4f
# Second Modification from agarcian

class RangeSlider(QtWidgets.QSlider):
    sliderMoved = QtCore.pyqtSignal(int, int)

    """ A slider for ranges.
    
        This class provides a dual-slider for ranges, where there is a defined
        maximum and minimum, as in a normal slider, but instead of having a
        single slider value, there are 2 slider values.
        
        This class emits the same signals as the QSlider base class, with the 
        exception of valueChanged.
    """
    def __init__(self, *args):
        super(RangeSlider, self).__init__(*args)

        self.setMinimum(10)
        self.setMaximum(10000)
        self.setOrientation(QtCore.Qt.Vertical)  # Vertical slider
        self.setTickPosition(QtWidgets.QSlider.TicksBelow)

        # Internal tracking for our two handles:
        self._low = self.minimum()
        self._high = self.maximum()

        self.pressed_control = QtWidgets.QStyle.SC_None
        self.hover_control   = QtWidgets.QStyle.SC_None
        self.click_offset    = 0
        
        self.setMinimumWidth(100)

        self.number_of_ticks = 20  # *** CHANGED *** Number of label intervals
        self.active_slider   = 0

        # We do NOT use built-in ticks at all, so ignore these:
        self.tick_position   = QtWidgets.QSlider.NoTicks  # *** CHANGED ***

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
    
        # 1. Draw the groove
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        opt.sliderValue = 0
        opt.sliderPosition = 0
        opt.subControls = QtWidgets.QStyle.SC_SliderGroove
        style.drawComplexControl(QtWidgets.QStyle.CC_Slider, opt, painter, self)
    
        groove_rect = style.subControlRect(
            QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderGroove, self
        )
    
        # 2. Draw the ticks and labels
        self._draw_ticks_and_labels(painter, groove_rect, style, opt)
    
        # 3. Draw the span rectangle
        self._draw_span(painter, style, groove_rect, opt)
    
        # 4. Draw the handles
        self._draw_handles(painter, style, opt)
        
    def _draw_ticks_and_labels(self, painter, groove_rect, style, opt):
        tick_length = 8
        head_thickness= 5
        painter.setPen(QtGui.QPen(QtCore.Qt.black))
        painter.setFont(QtGui.QFont("Arial", 7))
    
        if opt.orientation == QtCore.Qt.Horizontal:
            slider_min = groove_rect.x()
            slider_max = groove_rect.right()
            available = slider_max - slider_min
            text_offset = groove_rect.bottom() + 15  # Adjust label position
            tick_offset = groove_rect.bottom() + 2
        else:  # Vertical
            slider_min = groove_rect.y() + head_thickness
            slider_max = groove_rect.bottom() - head_thickness
            available = slider_max - slider_min
            text_offset = groove_rect.right() - 20  # Adjust label position
            tick_offset = groove_rect.right() - 35
    
        step = (self.maximum() - self.minimum()) / (self.number_of_ticks - 1)
    
        for i in range(self.number_of_ticks):
            value = self.minimum() + i * step
            value=int(round(value))
            pixel_offset = style.sliderPositionFromValue(
                self.minimum(), self.maximum(), value, available, opt.upsideDown
            )
    
            if opt.orientation == QtCore.Qt.Horizontal:
                x = slider_min + pixel_offset
                painter.drawLine(x, tick_offset, x, tick_offset + tick_length)
                text_rect = QtCore.QRect(x - 15, text_offset, 30, 12)
                painter.drawText(text_rect, QtCore.Qt.AlignCenter, str(int(value)))
            else:
                y = slider_min + pixel_offset
                painter.drawLine(tick_offset, y, tick_offset + tick_length, y)
                text_rect = QtCore.QRect(text_offset, y - 6, 40, 12)
                painter.drawText(text_rect, QtCore.Qt.AlignVCenter, str(int(value)))
        
    def _draw_span(self, painter, style, groove_rect, opt):
        
        self.initStyleOption(opt)
        opt.subControls = QtWidgets.QStyle.SC_SliderGroove
        opt.sliderValue = 0
    
        # Compute positions of the two handles in pixels:
        opt.sliderPosition = self._low
        low_rect = style.subControlRect(QtWidgets.QStyle.CC_Slider, opt,
                                        QtWidgets.QStyle.SC_SliderHandle, self)
        opt.sliderPosition = self._high
        high_rect = style.subControlRect(QtWidgets.QStyle.CC_Slider, opt,
                                         QtWidgets.QStyle.SC_SliderHandle, self)
    
        low_pos = self.__pick(low_rect.center())
        high_pos = self.__pick(high_rect.center())
    
        min_pos = min(low_pos, high_pos)
        max_pos = max(low_pos, high_pos)
    
        center_pt = QtCore.QRect(low_rect.center(), high_rect.center()).center()
    
        if opt.orientation == QtCore.Qt.Horizontal:
            span_rect = QtCore.QRect(
                QtCore.QPoint(min_pos, center_pt.y() - 2),
                QtCore.QPoint(max_pos, center_pt.y() + 1)
            )
            groove_rect.adjust(0, 0, -1, 0)  # Keep highlight inside
        else:  # Vertical
            span_rect = QtCore.QRect(
                QtCore.QPoint(center_pt.x() - 2, min_pos),
                QtCore.QPoint(center_pt.x() + 1, max_pos)
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
    

    



    ##########################
    # Private Methods
    ##########################

    def mousePressEvent(self, event):
        event.accept()
        
        style = QtWidgets.QApplication.style()
        button = event.button()
        
        # In a normal slider control, when the user clicks on a point in the 
        # slider's total range, but not on the slider part of the control the
        # control would jump the slider value to where the user clicked.
        # For this control, clicks which are not direct hits will slide both
        # slider parts
                
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
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        
        if self.active_slider < 0:
            offset = new_pos - self.click_offset
            self._high += offset
            self._low += offset
            if self._low < self.minimum():
                diff = self.minimum() - self._low
                self._low += diff
                self._high += diff
            if self._high > self.maximum():
                diff = self.maximum() - self._high
                self._low += diff
                self._high += diff            
        elif self.active_slider == 0:
            if new_pos >= self._high:
                new_pos = self._high - 1
            self._low = new_pos
        else:
            if new_pos <= self._low:
                new_pos = self._low + 1
            self._high = new_pos

        self.click_offset = new_pos

        self.update()

        #self.emit(QtCore.SIGNAL('sliderMoved(int)'), new_pos)
        self.sliderMoved.emit(self._low, self._high)
            
    def __pick(self, pt):
        if self.orientation() == QtCore.Qt.Horizontal:
            return pt.x()
        else:
            return pt.y()       
           
    def __pixelPosToRangeValue(self, pos):
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        style = QtWidgets.QApplication.style()
        
        gr = style.subControlRect(style.CC_Slider, opt, style.SC_SliderGroove, self)
        sr = style.subControlRect(style.CC_Slider, opt, style.SC_SliderHandle, self)
        
        if self.orientation() == QtCore.Qt.Horizontal:
            slider_length = sr.width()
            slider_min = gr.x()
            slider_max = gr.right() - slider_length + 1
        else:
            slider_length = sr.height()
            slider_min = gr.y()
            slider_max = gr.bottom() - slider_length + 1
            
        return style.sliderValueFromPosition(self.minimum(), self.maximum(),
                                             pos-slider_min, slider_max-slider_min,
                                             opt.upsideDown)
    

    
##############################
# Test
##############################

def echo(low_value, high_value):
    print(low_value, high_value)

def test(argv):
    app = QtWidgets.QApplication(sys.argv)
    slider = RangeSlider()
    slider.setMinimumHeight(30)
#    slider.setMinimum(0)
#    slider.setMaximum(255)
    slider.setLow(15)
    slider.setHigh(300)
#    slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
    slider.sliderMoved.connect(echo)
    #QtCore.QObject.connect(slider, QtCore.SIGNAL('sliderMoved(int)'), echo)
    slider.show()
    slider.raise_()
    app.exec_()


if __name__ == "__main__":
    test(sys.argv)