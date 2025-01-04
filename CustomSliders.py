import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QSlider, QLabel
)
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QSize
from PyQt5.QtGui import QPainter, QFont, QColor, QFontMetrics


class CustomSliders(QWidget):
    """
    A basic vertical slider with labeled ticks and a value label.
    This class provides:
      - A slider from min_value to max_value.
      - Tick markings displayed on the widget's paint event.
      - A label showing the current slider value.
    """

    def __init__(self, min_value, max_value, colour):
        super().__init__()
        self._min_value = min_value
        self._max_value = max_value

        # Main slider and label
        self._slider = QSlider(Qt.Vertical, self)
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
        interval = max(1, (self._max_value - self._min_value) // 10)
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
        painter.setFont(QFont("Arial", 6))
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
        return self._slider.value()

    def set_value(self, value):
        """
        Programmatically sets the slider to a given integer value.
        """
        self._slider.setValue(value)

    def value_changed(self):
        """
        Exposes the slider's valueChanged signal for external listeners.
        """
        return self._slider.valueChanged



#############################################################################

class DoubleSliderWithTicks(CustomSliders):
    """
    A slider that internally uses integer steps but represents
    floating-point values by applying a scale factor.
    """

    # We re-declare a PyQt signal, so it emits float instead of int.
    valueChanged = pyqtSignal(float)

    def __init__(self, min_value, max_value, colour):
        self._scale_factor = 1000
        super().__init__(min_value, max_value, colour)
        # Connect the slider's "raw" integer changes to our float-based signal
        self._slider.valueChanged.connect(self._emit_corrected_value)

    # -----------------------------------------------------------------------
    #  Private Methods
    # -----------------------------------------------------------------------

    def _setup_slider(self, colour):
        """
        Overridden to set slider's range as scaled integers. Ticks also scaled.
        """
        int_min = int(self._min_value * self._scale_factor)
        int_max = int(self._max_value * self._scale_factor)
        self._slider.setRange(int_min, int_max)
        self._slider.setTickPosition(QSlider.TicksBothSides)

        interval = max(1, (int_max - int_min) // 10)
        self._slider.setTickInterval(interval)

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
        self.setMinimumWidth(75)
        

    def _update_label(self):
        """
        Show the floating-point value with three decimal places.
        """
        self._value_label.setText(f"{self.get_value():.3f}")

    def _emit_corrected_value(self, _):
        """
        Emit the float value via self.valueChanged to external listeners.
        """
        self.valueChanged.emit(self.get_value())

    def _string_by_tick(self, i):
        """
        Convert the scaled integer to a string for tick labeling.
        """
        return str(i / self._scale_factor)
    
    # -----------------------------------------------------------------------
    #  Public Methods
    # -----------------------------------------------------------------------

    def get_value(self):
        """
        Return the float value, unscaled.
        """
        return self._slider.value() / self._scale_factor

    def set_value(self, value):
        """
        Set the slider to a float, using the scale factor internally.
        """
        scaled_val = int(value * self._scale_factor)
        self._slider.setValue(scaled_val)

    def value_changed(self):
        """
        Return the float-based signal instead of the slider's integer signal.
        """
        return self.valueChanged

##############################################################################

class EPowerSliderWithTicks(DoubleSliderWithTicks):
    """
    A floating-point slider that interprets its numeric range as an exponent
    for base-10. For example, if the slider is set to 2, the actual value is 10^2.
    """

    def __init__(self, min_value, max_value, colour):
        self._base_power = 10
        super().__init__(min_value, max_value, colour)
        

    def _update_label(self):
        """
        Display the computed exponent value in scientific notation.
        """
        self._value_label.setText(f"{self.get_value():.1e}")

    def _string_by_tick(self, i):
        """
        Show each tick label as "1E<exponent>" based on the scaled integer.
        """
        exponent = int(i / self._scale_factor)
        return f"1E{exponent}"
    
    # -----------------------------------------------------------------------
    #  Public Methods
    # -----------------------------------------------------------------------


    def get_value(self):
        """
        Return 10^n, where n is the float value from the slider.
        """
        n = self._slider.value() / self._scale_factor
        return self._base_power ** n


  # -----------------------------------------------------------------------
  #  TEST
  # -----------------------------------------------------------------------


def test_custom_sliders():
    """
    A comprehensive manual test for CustomSliders, DoubleSliderWithTicks, 
    and EPowerSliderWithTicks. Demonstrates:
      1. Instantiation of multiple sliders with different ranges and colors.
      2. Printing slider values in real time (connect to the .value_changed() signals).
      3. Programmatically setting slider values via buttons.
      4. Observing tick labels and displayed values for edge cases.
      5. (Optional) A demonstration of exponent-based slider usage with EPowerSliderWithTicks.

    HOW TO USE:
      - Run this function. A window appears with multiple sliders side by side.
      - Each slider logs its changes (float or int) to the console.
      - Buttons below the sliders allow you to jump each slider to particular test values.
      - Interact with the sliders to see real-time console output and label updates.
    """
    import sys
    from PyQt5.QtWidgets import (
        QApplication, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel
    )

    app = QApplication(sys.argv)

    # Create a main container widget
    main_widget = QWidget()
    main_widget.setWindowTitle("CustomSliders Comprehensive Manual Test")

    # Instantiate various sliders with different ranges
    slider_int_0_100 = CustomSliders(0, 100, "blue")
    slider_float_neg2_2 = DoubleSliderWithTicks(-2.0, 2.0, "green")
    slider_exp_0_10 = EPowerSliderWithTicks(0, 10, "red")

    # Connect each slider's signal to print the current value in console
    slider_int_0_100.value_changed().connect(lambda: print(
        f"[CustomSliders INT 0–100] Value: {slider_int_0_100.get_value()}"
    ))
    slider_float_neg2_2.value_changed().connect(lambda val: print(
        f"[DoubleSliderWithTicks FLOAT -2–2] Value: {val:.3f}"
    ))
    slider_exp_0_10.value_changed().connect(lambda val: print(
        f"[EPowerSliderWithTicks 10^x 0–10] Value: {val:.3e}"
    ))

    # Layout for the sliders in a horizontal row
    sliders_layout = QHBoxLayout()
    sliders_layout.addWidget(slider_int_0_100)
    sliders_layout.addWidget(slider_float_neg2_2)
    sliders_layout.addWidget(slider_exp_0_10)

    # Buttons to demonstrate programmatic set_value()
    button_layout = QHBoxLayout()
    label_help = QLabel("Click a button to set each slider to a test value:")

    # Example test buttons for each slider
    btn_set_mid = QPushButton("Set to midpoint")
    btn_set_min = QPushButton("Set to min")
    btn_set_max = QPushButton("Set to max")

    def set_to_midpoint():
        # Midpoints for each slider
        slider_int_0_100.set_value(50)
        slider_float_neg2_2.set_value(0.0)
        slider_exp_0_10.set_value(5)  # 10^5 = 100000

    def set_to_min():
        slider_int_0_100.set_value(0)
        slider_float_neg2_2.set_value(-2.0)
        slider_exp_0_10.set_value(0)  # 10^0 = 1

    def set_to_max():
        slider_int_0_100.set_value(100)
        slider_float_neg2_2.set_value(2.0)
        slider_exp_0_10.set_value(10)  # 10^10 = 10000000000

    btn_set_mid.clicked.connect(set_to_midpoint)
    btn_set_min.clicked.connect(set_to_min)
    btn_set_max.clicked.connect(set_to_max)

    button_layout.addWidget(label_help)
    button_layout.addWidget(btn_set_min)
    button_layout.addWidget(btn_set_mid)
    button_layout.addWidget(btn_set_max)

    # Combine everything in a vertical layout
    main_layout = QVBoxLayout(main_widget)
    main_layout.addLayout(sliders_layout)
    main_layout.addLayout(button_layout)

    # Show the main widget
    main_widget.resize(600, 400)
    main_widget.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    # Possibly some other logic
    # ...
    test_custom_sliders() 