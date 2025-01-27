import sys
import math
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal

LOG_SCALE_FACTOR = 100  # how finely you want to subdivide each log10 unit

class RangeSlider(QtWidgets.QSlider):
    """
    A two-handle slider for *log10* ranges.
    QSlider is still integer-based, but now those integers represent log10(value).
    """
    sliderMoved = pyqtSignal(float, float)

    def __init__(self, *args):
        super().__init__(*args)

        self.setOrientation(Qt.Vertical)
        self.setTickPosition(QtWidgets.QSlider.TicksBelow)

        # Store float min/max in normal linear space (e.g. 2e-2, 6e6)
        self._float_min = 2.0e-2
        self._float_max = 6.0e+6
        
        self._low = self._float_min 
        self._high = self._float_max

        # Also store them in log space
        self._log_min = math.log10(self._float_min)
        self._log_max = math.log10(self._float_max)

        # We'll let the QSlider run from 0 ... (log_max - log_min)*LOG_SCALE_FACTOR
        self.setFloatRange(self._float_min, self._float_max)

        # Start both handles at extremes
        self._low = self.minimum()
        self._high = self.maximum()

        self.pressed_control = QtWidgets.QStyle.SC_None
        self.hover_control = QtWidgets.QStyle.SC_None
        self.click_offset = 0
        self.active_slider = -1

        self.setMinimumWidth(100)
        self.number_of_ticks = 20

    # -----------------------------------------------------------------------
    # Public API for floats in log scale
    # -----------------------------------------------------------------------
    def setFloatRange(self, fmin, fmax):
        """Define the float range, internally mapped to log10 space for the slider."""
        self._float_min = fmin
        self._float_max = fmax
        self._log_min = math.log10(fmin)
        self._log_max = math.log10(fmax)

        # QSlider integer range: 0 ... (log_max - log_min)*LOG_SCALE_FACTOR
        int_min = 0
        int_max = int(round((self._log_max - self._log_min) * LOG_SCALE_FACTOR))

        self.setMinimum(int_min)
        self.setMaximum(int_max)

        # Clamp existing handles
        if self._low < int_min:
            self._low = int_min
        if self._high > int_max:
            self._high = int_max

        self.update()

    def floatLow(self):
        """Return lower handle as a float (inverse of log scale)."""
        return 10 ** (self._log_min + (self._low / LOG_SCALE_FACTOR))

    def setFloatLow(self, val):
        """Move lower handle to 'val' in linear space (convert to log)."""
        logv = math.log10(val)
        slider_pos = int(round((logv - self._log_min) * LOG_SCALE_FACTOR))
        self._low = self._clampInt(slider_pos)
        self.update()

    def floatHigh(self):
        """Return upper handle as a float."""
        return 10 ** (self._log_min + (self._high / LOG_SCALE_FACTOR))

    def setFloatHigh(self, val):
        """Move upper handle to 'val' in linear space."""
        logv = math.log10(val)
        slider_pos = int(round((logv - self._log_min) * LOG_SCALE_FACTOR))
        self._high = self._clampInt(slider_pos)
        self.update()

    def _clampInt(self, ival):
        return max(self.minimum(), min(self.maximum(), ival))

    # -----------------------------------------------------------------------
    # Example: Methods for keyboard shortcuts (same idea as before)
    # -----------------------------------------------------------------------
    def upMin(self):
        """Example: shift lower handle upward by a certain factor in linear space."""
        factor = 10**0.2  # ~1.584893
        new_low = self.floatLow()*factor
        if new_low > self.floatHigh():
            new_low = self.floatHigh()
        self.setFloatLow(new_low)
        self.sliderMoved.emit(self.floatLow(), self.floatHigh())

    def downMax(self):
        """Example: shift upper handle downward by a certain factor in linear space."""
        factor = 10**0.2  # ~1.584893
        new_high = self.floatHigh()/factor
        if new_high < self.floatLow():
            new_high = self.floatLow()
        self.setFloatHigh(new_high)
        self.sliderMoved.emit(self.floatLow(), self.floatHigh())

    def default(self):
        """Reset slider to the full float range."""
        self.setFloatLow(self._float_min)
        self.setFloatHigh(self._float_max)
        self.sliderMoved.emit(self.floatLow(), self.floatHigh())

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

        # We'll space ticks in exponent. E.g. from log10(fmin) to log10(fmax).
        # We want self.number_of_ticks values between _log_min and _log_max.
        log_range = self._log_max - self._log_min
        step = log_range / (self.number_of_ticks - 1)

        for i in range(self.number_of_ticks):
            # exponent from log_min up to log_max
            exponent = self._log_min + i * step
            float_value = 10 ** exponent

            # Convert exponent to the slider's integer scale
            slider_val = int(round((exponent - self._log_min) * LOG_SCALE_FACTOR))

            # Map that slider_val to a pixel position
            pixel_offset = style.sliderPositionFromValue(
                self.minimum(), self.maximum(), slider_val, available, opt.upsideDown
            )

            # Format the label in scientific notation
            label = f"{float_value:.2E}"

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
        self.sliderMoved.emit(self.floatLow(), self.floatHigh())

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

# Minimal demo
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = QtWidgets.QMainWindow()

    # Create our RangeSlider
    slider = RangeSlider()
    slider.sliderMoved.connect(lambda low, high: print(f"Low={low:.3g}, High={high:.3g}"))

    win.setCentralWidget(slider)
    win.show()
    sys.exit(app.exec_())
