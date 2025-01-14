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
#  TEST FOR UPDATED ModelManual with CustomSliders
# -----------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import numpy as np
    
    from PyQt5.QtWidgets import (
        QApplication, QWidget, QVBoxLayout,
        QTableWidget, QTableWidgetItem, QHBoxLayout
    )
    from PyQt5.QtCore import Qt
    
    import pyqtgraph as pg

    # Import your classes
    from ModelManual import ModelManual
    from WidgetSliders import WidgetSliders
    # Make sure these sliders are imported or accessible:
    # from CustomSliders import CustomSliders, DoubleSliderWithTicks, EPowerSliderWithTicks

    # ---------------------------
    # 1. Define a sample model_formula
    # ---------------------------
    def my_model_formula(freq, R=10.0, L=1e-3, alpha=1.0):
        """
        Example formula combining a resistor and an inductor in series,
        plus a factor (1 + alpha) for demonstration.
        
        Z = R + j*(2*pi*freq*L)*(1 + alpha)
        """
        omega = 2.0 * np.pi * freq
        Z_complex = R + 1j * omega * L * (1 + alpha)
        return Z_complex

    # ---------------------------
    # 2. Create the ModelManual instance
    # ---------------------------
    model_manual = ModelManual(model_formula=my_model_formula)

    # ---------------------------
    # 3. Setup Frequency Data
    # ---------------------------
    # Example: 50 logarithmically spaced points between 1 Hz and 100 kHz
    freqs = np.logspace(0, 5, 50)
    model_manual.initialize_frequencies("freq", freqs)

    # -------------------------------------------------------------------
    # 4. Define slider configurations
    #
    # Each entry must be (slider_type, min_val, max_val, color),
    # matching the signature in your "WidgetSliders::_create_sliders"
    # -------------------------------------------------------------------
    slider_configurations = {
        "R": ("DoubleSliderWithTicks", 0.0, 100.0, "blue"),    # Resistances: 0 to 100
        "L": ("DoubleSliderWithTicks", 1e-5, 1e-1, "green"),   # Inductance: 1e-5 to 1e-1
        "alpha": ("DoubleSliderWithTicks", 0.0, 2.0, "red"),   # Dimensionless factor: 0 to 2
    }

    # Default values for each slider (matching the range above)
    slider_defaults = {
        "R": 10.0,
        "L": 1e-3,
        "alpha": 1.0
    }

    # ---------------------------
    # 5. Create the QApplication and main window
    # ---------------------------
    app = QApplication(sys.argv)
    main_window = QWidget()
    main_window.setWindowTitle("ModelManual Test - Real-time Sliders & Plot")
    main_window.setGeometry(100, 100, 1200, 600)

    main_layout = QVBoxLayout(main_window)

    # ---------------------------
    # 6. Create the sliders widget
    # ---------------------------
    sliders_widget = WidgetSliders(slider_configurations, slider_defaults)
    main_layout.addWidget(sliders_widget)

    # ---------------------------
    # 7. Create a table to display numeric results
    #    (freq, Z_real, Z_imag)
    # ---------------------------
    freq_array = model_manual._modeled_data["freq"]
    table_imp = QTableWidget(len(freq_array), 3)
    table_imp.setHorizontalHeaderLabels(["Frequency (Hz)", "Z_real", "Z_imag"])

    for i, f in enumerate(freq_array):
        table_imp.setItem(i, 0, QTableWidgetItem(str(f)))
        table_imp.setItem(i, 1, QTableWidgetItem(str(model_manual._modeled_data["Z_real"][i])))
        table_imp.setItem(i, 2, QTableWidgetItem(str(model_manual._modeled_data["Z_imag"][i])))

    # ---------------------------
    # 8. Create a pyqtgraph plot for Real vs Imag
    # ---------------------------
    plot_widget = pg.PlotWidget(title="Nyquist Plot (Z_real vs. Z_imag)")
    plot_widget.setLabel("bottom", "Z_real")
    plot_widget.setLabel("left", "Z_imag")

    curve = plot_widget.plot(
        model_manual._modeled_data["Z_real"],
        model_manual._modeled_data["Z_imag"],
        pen=None, symbol='o', symbolSize=6, symbolBrush='b'
    )

    # ---------------------------
    # 9. Lay out table and plot side-by-side
    # ---------------------------
    h_layout = QHBoxLayout()
    h_layout.addWidget(table_imp)
    h_layout.addWidget(plot_widget)
    main_layout.addLayout(h_layout)

    # ---------------------------
    # 10. Define update functions
    # ---------------------------
    def update_impedance_table_and_plot(freqs, z_reals, z_imags):
        """
        Update the table and the pyqtgraph plot
        with the latest impedance data.
        """
        # Update table size in case freq array length changed
        table_imp.setRowCount(len(freqs))

        for i in range(len(freqs)):
            table_imp.setItem(i, 0, QTableWidgetItem(f"{freqs[i]:.4g}"))
            table_imp.setItem(i, 1, QTableWidgetItem(f"{z_reals[i]:.4g}"))
            table_imp.setItem(i, 2, QTableWidgetItem(f"{z_imags[i]:.4g}"))

        # Update the Nyquist plot (Real on X, Imag on Y)
        curve.setData(z_reals, z_imags)

    def on_model_manual_updated(freqs, z_reals, z_imags):
        """
        Slot for model_manual.model_manual_updated signal.
        Triggered when run_model completes.
        """
        update_impedance_table_and_plot(freqs, z_reals, z_imags)

    # ---------------------------
    # 11. Connect signals
    # ---------------------------
    model_manual.model_manual_updated.connect(on_model_manual_updated)

    def on_slider_value_updated(key, new_value):
        """
        Called whenever a slider changes its value.
        We gather all sliders' current values into dictionaries and
        re-run the model.
        """
        # Get current parameter values for all sliders
        slider_values = sliders_widget.get_current_values()

        # The ModelManual.run_model interface:
        #   run_model(v_sliders, v_second)
        # v_second can be empty if you only use `v_sliders`.
        model_manual.run_model(slider_values, {})

    sliders_widget.slider_value_updated.connect(on_slider_value_updated)

    # ---------------------------
    # 12. Show the main window and run
    # ---------------------------
    # Perform an initial run of the model with the default slider values
    default_values = sliders_widget.get_current_values()
    model_manual.run_model(default_values, {})

    main_window.show()
    sys.exit(app.exec_())
