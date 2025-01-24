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

        # Internal tracking for our two handles:
        self._low = self.minimum()
        self._high = self.maximum()

        self.pressed_control = QtWidgets.QStyle.SC_None
        self.hover_control   = QtWidgets.QStyle.SC_None
        self.click_offset    = 0

        self.number_of_ticks = 4  # *** CHANGED *** Number of label intervals
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
        """
        Reimplementation of the QSlider paint event to handle:
          1) Drawing the groove
          2) Drawing the 'span' rectangle between self._low and self._high
          3) Drawing each of the two slider handles
          4) Drawing numeric labels (NOT ticks) at self.number_of_ticks intervals
        """
        painter = QtGui.QPainter(self)
        style = QtWidgets.QApplication.style()
    
        #
        # 1) Draw the groove ONLY (no built-in tickmarks)
        #
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        opt.sliderValue = 0
        opt.sliderPosition = 0
        opt.subControls = QtWidgets.QStyle.SC_SliderGroove  # Groove only, no tickmarks
    
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
    
        #
        # 3) Draw the two slider handles ONLY (no built-in tickmarks)
        #
        for value in [self._low, self._high]:
            opt = QtWidgets.QStyleOptionSlider()
            self.initStyleOption(opt)
            opt.subControls = QtWidgets.QStyle.SC_SliderHandle
    
            # If this handle is actively being dragged, highlight it
            if self.pressed_control:
                opt.activeSubControls = self.pressed_control
            else:
                opt.activeSubControls = self.hover_control
    
            opt.sliderPosition = value
            opt.sliderValue = value
    
            style.drawComplexControl(QtWidgets.QStyle.CC_Slider, opt, painter, self)
    
        #
        # 4) Draw numeric labels at self.number_of_ticks intervals
        #
        if self.number_of_ticks > 1:
            # Initialize the style option
            self.initStyleOption(opt)
            groove_rect = style.subControlRect(
                QtWidgets.QStyle.CC_Slider, opt,
                QtWidgets.QStyle.SC_SliderGroove, self
            )
    
            # Tick thickness adjustment
            tick_thickness = 7  # Define the tick thickness explicitly
    
            painter.setPen(QtGui.QPen(QtCore.Qt.black))
            painter.setFont(QtGui.QFont("Arial", 7))
    
            # Determine slider orientation
            if opt.orientation == QtCore.Qt.Horizontal:
                slider_min = groove_rect.x()
                slider_max = groove_rect.right()
                available = slider_max - slider_min
                text_offset = groove_rect.bottom() + tick_thickness + 5
                upside_down = False
            else:  # Vertical
                slider_min = groove_rect.y()+ tick_thickness 
                slider_max = groove_rect.bottom() - tick_thickness 
                available = slider_max - slider_min
                text_offset = groove_rect.right() -15
                upside_down = True  # If highest numbers appear at the top
    
            # Calculate numeric label positions
            total_range = self.maximum() - self.minimum()
            step = (total_range / (self.number_of_ticks - 1)
                    if self.number_of_ticks > 1 else 0)
    
            for i in range(self.number_of_ticks):
                # Calculate the slider value for this label
                val_float = self.minimum() + i * step
                val_int = int(round(val_float))
    
                # Map the slider value to a pixel offset
                pixel_off = style.sliderPositionFromValue(
                    self.minimum(), self.maximum(),
                    val_int, available, upside_down
                )
    
                # Place the text depending on the orientation
                if opt.orientation == QtCore.Qt.Horizontal:
                    x = slider_min + pixel_off
                    text_rect = QtCore.QRect(
                        x - 15, text_offset, 30, 12
                    )  # Adjusted to include tick thickness
                    painter.drawText(text_rect, QtCore.Qt.AlignCenter, str(val_int))
                else:
                    y = slider_min + pixel_off
                    text_rect = QtCore.QRect(
                        text_offset, y -5, 40, 12
                    )  # Adjusted to include tick thickness
                    painter.drawText(text_rect, QtCore.Qt.AlignVCenter, str(val_int))

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
    
    
########################################################  
    
    
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QSlider, QLabel
)
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QSize
from PyQt5.QtGui import QPainter, QFont, QColor, QFontMetrics


class CustomRangeSliders(QWidget):
    """
    A basic vertical slider with labeled ticks and a value label.
    This class provides:
      - A slider from min_value to max_value.
      - Tick markings displayed on the widget's paint event.
      - A label showing the current slider value.
    """

    def __init__(self, min_value, max_value, colour, number_of_tick_intervals=10):
        super().__init__()
        self._min_value = min_value
        self._max_value = max_value
        self.number_of_tick_intervals = number_of_tick_intervals

        # Main slider and label
        self._slider = RangeSlider(Qt.Vertical, self)
        self._value_label = QLabel(str(self._slider.value()), self)

        # Overall widget layout
        self._layout = QVBoxLayout()

        # Connect slider value changes to an internal update
        self._slider.valueChanged.connect(self._update_label)

        # Configure slider appearance and functionality
        self._setup_slider(colour)

        # Assemble the layout
        self._setup_layout()
        
    # -----------------------------------------------------------------------
    #  Private Methods
    # -----------------------------------------------------------------------

    def _setup_layout(self):
        """
        Create and assign a layout containing the slider and the value label.
        """
        self._layout.addWidget(self._slider)
        self._layout.addWidget(self._value_label)
        self.setLayout(self._layout)
        
    def _setup_slider(self, colour):
        """
        Configure the slider's properties (range, ticks, color).
        """
        self._slider.setRange(self._min_value, self._max_value)
        self._slider.setTickPosition(QSlider.TicksBothSides)

        # Safely set a tick interval (avoid division by zero if ranges are small)
        interval = max(1, (self._max_value - self._min_value) // self.number_of_tick_intervals)
        self._slider.setTickInterval(interval)

        # Style the slider handle and track
        self._slider.setStyleSheet(f"""
            QSlider::handle:vertical {{
                background: {colour};
                width: 20px;
                height: 20px;
                border-radius: 10px;
            }}
            QSlider::add-page:vertical {{
                background: #d3d3d3;
                border-radius: 5px;
            }}
        """)

        # Provide enough width so ticks and label don't overlap
        self.setMinimumWidth(75)

    def _update_label(self):
        """
        Update the on-screen label whenever the slider value changes.
        """
        self._value_label.setText(f"Slider: {self.get_value()}")

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
    # -----------------------------------------------------------------
    
    def get_value(self):
        """
        Returns the current integer value of the slider.
        """
        return self._slider.value()

    def set_value(self, value):
        """
        Programmatically sets the slider to a given integer value.
        """
        
        self._slider.setValue(int(value))

    def value_changed(self):
        """
        Exposes the slider's valueChanged signal for external listeners.
        """
        return self._slider.sliderMoved

    
    
##############################
# Test
##############################

def echo(low_value, high_value):
    print(low_value, high_value)

def test(argv):
    app = QtWidgets.QApplication(sys.argv)
    slider = RangeSlider(QtCore.Qt.Horizontal)
    slider.setMinimumHeight(30)
#    slider.setMinimum(0)
#    slider.setMaximum(255)
    slider.setLow(15)
    slider.setHigh(300)
    slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
    slider.sliderMoved.connect(echo)
    #QtCore.QObject.connect(slider, QtCore.SIGNAL('sliderMoved(int)'), echo)
    slider.show()
    slider.raise_()
    app.exec_()
"""
def test(argv):
        app = QtWidgets.QApplication(sys.argv)
        slider = CustomRangeSliders(0,100,"red")
        slider.value_changed().connect(echo)
        #QtCore.QObject.connect(slider, QtCore.SIGNAL('sliderMoved(int)'), echo)
        slider.show()
        slider.raise_()
        app.exec_()
"""


if __name__ == "__main__":
    test(sys.argv)