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
        maximum and minimum, as is a normal slider, but instead of having a
        single slider value, there are 2 slider values.
        
        This class emits the same signals as the QSlider base class, with the 
        exception of valueChanged
    """
    def __init__(self, *args):
        super(RangeSlider, self).__init__(*args)
        
        # Set defaults required for Randy's program
        self.setMinimum(10)
        self.setMaximum(10000)
        self.setOrientation(QtCore.Qt.Vertical)    # Vertical slider

        # Internal tracking for our two handles:
        self._low = self.minimum()
        self._high = self.maximum()

        self.pressed_control = QtWidgets.QStyle.SC_None
        self.tick_interval = 100
        self.tick_position = QtWidgets.QSlider.NoTicks
        self.hover_control = QtWidgets.QStyle.SC_None
        self.click_offset = 0
        
        # 0 for the low, 1 for the high, -1 for both
        self.active_slider = 0
        
    ####################
    # Public Methods
    ####################

    def low(self):
        return self._low

    def setLow(self, low:int):
        self._low = low
        self.update()

    def high(self):
        return self._high

    def setHigh(self, high):
        self._high = high
        self.update()

#    def set_frequency(self, frequency : array):
#        number = #number of elements in the array
#        first= #first element of the ordered array
#        last = #last element of the array
        
        #The largest between first and last becomes max. 
        #The minimum between min and max becomes the min
        
#        slider.setMinimum(min)
#        slider.setMaximum(max)
#        slider.setLow(min)
#        slider.setHigh(max)
        
        #use number to set the number of ticks of the paint event, 
        #so there is a tick every num/10

    def paintEvent(self, event):
        """
        Reimplementation of the QSlider paint event to handle:
          - Drawing the groove
          - Drawing the 'span' rectangle between self._low and self._high
          - Drawing each of the two slider handles
          - Drawing numeric tick labels based on the slider's range
        """
        painter = QtGui.QPainter(self)
        style = QtWidgets.QApplication.style()
        
        #
        # 1) Draw the groove (and any built-in tickmarks)
        #
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        opt.sliderValue = 0
        opt.sliderPosition = 0
        opt.subControls = QtWidgets.QStyle.SC_SliderGroove
        if self.tickPosition() != self.NoTicks:
            opt.subControls |= QtWidgets.QStyle.SC_SliderTickmarks
    
        style.drawComplexControl(QtWidgets.QStyle.CC_Slider, opt, painter, self)
    
        # Retrieve the bounding rectangle of the groove
        groove_rect = style.subControlRect(
            QtWidgets.QStyle.CC_Slider, opt,
            QtWidgets.QStyle.SC_SliderGroove, self
        )
    
        #
        # 2) Draw the 'span' rectangle between self._low and self._high
        #
        self.initStyleOption(opt)
        opt.subControls = QtWidgets.QStyle.SC_SliderGroove
        opt.sliderValue = 0
    
        # Compute positions of the two handles (low and high) in pixels:
        opt.sliderPosition = self._low
        low_rect  = style.subControlRect(QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderHandle, self)
        opt.sliderPosition = self._high
        high_rect = style.subControlRect(QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderHandle, self)
    
        low_pos  = self.__pick(low_rect.center())
        high_pos = self.__pick(high_rect.center())
    
        min_pos = min(low_pos, high_pos)
        max_pos = max(low_pos, high_pos)
    
        center_pt = QtCore.QRect(low_rect.center(), high_rect.center()).center()
    
        # Construct a rectangle that spans from min_pos to max_pos inside the groove
        if opt.orientation == QtCore.Qt.Horizontal:
            span_rect = QtCore.QRect(
                QtCore.QPoint(min_pos, center_pt.y() - 2),
                QtCore.QPoint(max_pos, center_pt.y() + 1)
            )
        else:  # Vertical
            span_rect = QtCore.QRect(
                QtCore.QPoint(center_pt.x() - 2, min_pos),
                QtCore.QPoint(center_pt.x() + 1, max_pos)
            )
    
        # Adjust the groove so our highlight doesn’t spill out of the slider track
        if opt.orientation == QtCore.Qt.Horizontal:
            groove_rect.adjust(0, 0, -1, 0)
        else:
            groove_rect.adjust(0, 0, 0, -1)
    
        # Paint the highlight (the filled rectangle between low and high)
        highlight = self.palette().color(QtGui.QPalette.Highlight)
        painter.setBrush(QtGui.QBrush(highlight))
        painter.setPen(QtGui.QPen(highlight, 0))
        painter.drawRect(span_rect.intersected(groove_rect))
    
        #
        # 3) Draw each of the two slider handles
        #
        for i, value in enumerate([self._low, self._high]):
            opt = QtWidgets.QStyleOptionSlider()
            self.initStyleOption(opt)
            opt.subControls = QtWidgets.QStyle.SC_SliderHandle
            if self.tickPosition() != self.NoTicks:
                opt.subControls |= QtWidgets.QStyle.SC_SliderTickmarks
    
            # If this handle is actively being dragged, highlight it appropriately
            if self.pressed_control:
                opt.activeSubControls = self.pressed_control
            else:
                opt.activeSubControls = self.hover_control
    
            opt.sliderPosition = value
            opt.sliderValue = value
    
            style.drawComplexControl(QtWidgets.QStyle.CC_Slider, opt, painter, self)
    
        #
        # 4) Draw numeric tick labels based on the slider range
        #
        if self.tickPosition() != self.NoTicks:
            # Determine an interval step
            tick_interval = self.tickInterval()
            if tick_interval == 0:
                # (A) ADJUST THIS to control how many numeric labels appear 
                #     e.g., use range//10, range//20, or any custom logic.
                total_range = self.maximum() - self.minimum()
                tick_interval = max(1, total_range // 10)
    
            # Re-use style metrics for computing pixel positions
            opt = QtWidgets.QStyleOptionSlider()
            self.initStyleOption(opt)
    
            # The groove rect is where the slider track is drawn
            groove_rect = style.subControlRect(
                QtWidgets.QStyle.CC_Slider, opt,
                QtWidgets.QStyle.SC_SliderGroove, self
            )
    
            # We also need the handle rect to figure out the slider knob size
            handle_rect = style.subControlRect(
                QtWidgets.QStyle.CC_Slider, opt,
                QtWidgets.QStyle.SC_SliderHandle, self
            )
    
            painter.setPen(QtGui.QPen(QtCore.Qt.black))
            painter.setFont(QtGui.QFont("Arial", 7))
    
            # If we want the highest number at the top for a vertical slider,
            # we can set 'upsideDown = True' in the call below.
            if opt.orientation == QtCore.Qt.Horizontal:
                slider_min = groove_rect.x()
                slider_max = groove_rect.right() - handle_rect.width() + 1
                available = slider_max - slider_min
                upside_down = False
            else:
                slider_min = groove_rect.y()
                slider_max = groove_rect.bottom() - handle_rect.height() + 1
                available = slider_max - slider_min
    
                # (B) If you want highest at top in VERTICAL, set True:
                upside_down = True
    
            # For each step in [min, max], jump by tick_interval
            for val in range(self.minimum(), self.maximum() + 1, tick_interval):
                # Convert slider value --> pixel offset within the groove
                pixel_off = style.sliderPositionFromValue(
                    self.minimum(), self.maximum(),
                    val, available,
                    upside_down
                )
    
                # Place text outside the groove + a small margin
                if opt.orientation == QtCore.Qt.Horizontal:
                    x = slider_min + pixel_off
                    # (C) Adjust vertical offset from groove bottom here if needed
                    text_rect = QtCore.QRect(x - 15, groove_rect.bottom() + 5, 30, 12)
                    painter.drawText(text_rect, QtCore.Qt.AlignCenter, str(val))
                else:
                    # y-coord measured from the top of the groove
                    y = slider_min + pixel_off
                    # (C) Adjust horizontal offset from groove right here if needed
                    text_rect = QtCore.QRect(groove_rect.right() + 5, y - 6, 30, 12)
                    painter.drawText(text_rect, QtCore.Qt.AlignVCenter, str(val))



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
    slider = RangeSlider(QtCore.Qt.Horizontal)
    slider.setMinimumHeight(30)
    slider.setMinimum(0)
    slider.setMaximum(255)
    slider.setLow(15)
    slider.setHigh(35)
    slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
    slider.sliderMoved.connect(echo)
    #QtCore.QObject.connect(slider, QtCore.SIGNAL('sliderMoved(int)'), echo)
    slider.show()
    slider.raise_()
    app.exec_()

if __name__ == "__main__":
    test(sys.argv)