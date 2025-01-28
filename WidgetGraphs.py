"""
Created on Mon Dec 30 08:27:11 2024

Graphs for impedance data visualization:
  - ParentGraph (base class)
  - PhaseGraph
  - BodeGraph
  - ColeColeGraph
  - WidgetGraphs (displays 3 graphs side by side)
"""

import sys
import numpy as np
import pyqtgraph as pg

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from ModelManual import CalculationResult


class ParentGraph(pg.PlotWidget):
    """
    A base PlotWidget with methods for:
      - Storing and refreshing 'base' data and 'manual' (dynamic) data
      - Plotting or filtering frequency ranges
      - Overridden methods to transform freq, Z_real, Z_imag into X, Y
    """

    def __init__(self):
        super().__init__()

        # Default data for base and manual plots
        self._base_data = {
            'freq': np.array([1, 10, 100, 1000, 10000]),
            'Z_real': np.array([100, 80, 60, 40, 20]),
            'Z_imag': np.array([-50, -40, -30, -20, -10]),
        }
        self._manual_data = {
            'freq': np.array([1, 10, 100, 1000, 10000]),
            'Z_real': np.array([90, 70, 50, 30, 10]),
            'Z_imag': np.array([-45, -35, -25, -15, -5]),
        }

        self.setTitle("Parent Graph")
        self.showGrid(x=True, y=True)

        # Plot objects for static (base) and dynamic (manual) lines
        self._static_plot = None
        self._dynamic_plot = None

        # Initial display
        self._refresh_graph()

    def _prepare_xy(self, freq, Z_real, Z_imag):
        """
        Transforms impedance data (freq, Z_real, Z_imag) into the (x, y) needed for plotting.
        Default: returns (Z_real, Z_imag). Subclasses override this.
        """
        return Z_real, Z_imag

    def _refresh_plot(self, data_dict, plot_item):
        """
        Updates a single plot (static or dynamic) with new data.
        data_dict must contain 'freq', 'Z_real', 'Z_imag'.
        """
        x, y = self._prepare_xy(
            data_dict['freq'],
            data_dict['Z_real'],
            data_dict['Z_imag']
        )
        if plot_item:
            plot_item.setData(x, y)

    def _refresh_graph(self):
        """Clears and re-displays both the static and dynamic plots."""
        self.clear()

        # Static plot
        self._static_plot = self.plot(
            pen='g',             # green line connecting points
            symbol='o',          # circle marker
            symbolSize=7,        # smaller points
            symbolBrush='g'      # green fill for markers
        )
        self._refresh_plot(self._base_data, self._static_plot)

        # Dynamic plot
        self._dynamic_plot = self.plot(
            pen='b',             # blue line connecting points
            symbol='o',          # circle marker
            symbolSize=7,        # smaller points
            symbolBrush=None     # blue fill
        )
        self._refresh_plot(self._manual_data, self._dynamic_plot)

    def filter_frequency_range(self, f_min, f_max):
        """
        Filters base and manual data to only show points within [f_min, f_max].
        """
        # Filter base data
        base_mask = (
            (self._base_data['freq'] >= f_min) &
            (self._base_data['freq'] <= f_max)
        )
        filtered_base = {
            'freq': self._base_data['freq'][base_mask],
            'Z_real': self._base_data['Z_real'][base_mask],
            'Z_imag': self._base_data['Z_imag'][base_mask],
        }

        # Filter manual data
        manual_mask = (
            (self._manual_data['freq'] >= f_min) &
            (self._manual_data['freq'] <= f_max)
        )
        filtered_manual = {
            'freq': self._manual_data['freq'][manual_mask],
            'Z_real': self._manual_data['Z_real'][manual_mask],
            'Z_imag': self._manual_data['Z_imag'][manual_mask],
        }

        self._base_data = filtered_base
        self._manual_data = filtered_manual
        self._refresh_graph()

    def update_parameters_base(self, freq, Z_real, Z_imag):
        """
        Sets new 'base' data and re-displays both plots.
        """
        self._base_data = {
            'freq': freq, 'Z_real': Z_real, 'Z_imag': Z_imag
        }
        self._refresh_graph()

    def update_parameters_manual(self, freq, Z_real, Z_imag):
        """
        Sets new 'manual' (dynamic) data and refreshes only the dynamic plot.
        """
        self._manual_data = {
            'freq': freq, 'Z_real': Z_real, 'Z_imag': Z_imag
        }
        self._refresh_plot(self._manual_data, self._dynamic_plot)
        
        
    def update_special_points(self, freq_array, z_real_array, z_imag_array):
        # Clear old special items if needed
        for item in getattr(self, '_special_items', []):
            self.removeItem(item)
        self._special_items = []
    
        for i, color in enumerate(['r', 'g', 'b']):  # or pick whatever colors
            f = freq_array[i]
            zr = z_real_array[i]
            zi = z_imag_array[i]
            x, y = self._prepare_xy(np.array([f]), np.array([zr]), np.array([zi]))
    
            plot_item = self.plot(
                x, y,
                pen=None,
                symbol='o',
                symbolSize=8,
                symbolBrush=color,
                symbolPen=color
            )
            self._special_items.append(plot_item)
            

class PhaseGraph(ParentGraph):
    """
    Plots log10(|phase|) vs. frequency, 
    instead of the raw phase in degrees.
    """

    def __init__(self):
        super().__init__()
        self.setTitle("Phase (Log Scale of Degrees)")
        self.setLabel('bottom', "Frequency [Hz]")
        self.setLabel('left', "log10(|Phase|)")

    def _prepare_xy(self, freq, Z_real, Z_imag):
        """
        Convert to phase in degrees, then take log10(|phase|).
        """
        phase_deg = np.degrees(np.arctan2(Z_imag, Z_real))
        # log10 of the absolute value, with a small offset to avoid log(0)
        phase_log = np.log10(np.abs(phase_deg) + 1e-10)
        
        return freq, phase_log


class BodeGraph(ParentGraph):
    """
    Plots the magnitude of impedance (in dB) vs. frequency (Bode plot).
    """

    def __init__(self):
        super().__init__()
        self.setTitle("Bode Graph")
        self.setLabel('bottom', "Frequency [Hz]")
        self.setLabel('left', "Log Magnitude [dB]")

    def _prepare_xy(self, freq, Z_real, Z_imag):
        """
        Convert impedance to magnitude (dB) = 20 * log10(|Z|).
        """
        mag = np.sqrt(Z_real**2 + Z_imag**2)
        mag_db = 20 * np.log10(mag)
        return freq, mag_db


class ColeColeGraph(ParentGraph):
    """
    Plots Cole-Cole (Nyquist) diagram: real(Z) vs. -imag(Z).
    """

    def __init__(self):
        super().__init__()
        
        self.getPlotItem().setAspectLocked(True, 1)
        
        self.setTitle("Cole-Cole Graph")
        self.setLabel('bottom', "Z' [Ohms]")
        self.setLabel('left', "-Z'' [Ohms]")

    def _prepare_xy(self, freq, Z_real, Z_imag):
        """
        Typical Nyquist representation: X = Re(Z), Y = -Im(Z).
        """
        return Z_real, -Z_imag


class WidgetGraphs(QWidget):
    """
    A widget that displays three graphs side by side:
      - A large Cole-Cole graph
      - Two smaller graphs (Bode and Phase) stacked vertically
    """

    def __init__(self):
        super().__init__()

        # Instantiate the 3 graphs
        self._big_graph = ColeColeGraph()
        self._small_graph_1 = BodeGraph()
        self._small_graph_2 = PhaseGraph()

        # Layout for the smaller graphs on the right
        right_layout = QVBoxLayout()
        right_layout.addWidget(self._small_graph_1)
        right_layout.addWidget(self._small_graph_2)

        # Layout for the big graph on the left
        left_layout = QVBoxLayout()
        left_layout.addWidget(self._big_graph)

        # Combine into a main horizontal layout
        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)
        self.setLayout(main_layout)

    def apply_filter_frequency_range(self, f_min, f_max):
        """
        Filters out data outside [f_min, f_max] for all three graphs.
        """
        self._big_graph.filter_frequency_range(f_min, f_max)
        self._small_graph_1.filter_frequency_range(f_min, f_max)
        self._small_graph_2.filter_frequency_range(f_min, f_max)

    def update_graphs(self, freq, Z_real, Z_imag):
        """
        Updates the 'base' (static) data for all three graphs simultaneously.
        """
        self._big_graph.update_parameters_base(freq, Z_real, Z_imag)
        self._small_graph_1.update_parameters_base(freq, Z_real, Z_imag)
        self._small_graph_2.update_parameters_base(freq, Z_real, Z_imag)

    def update_manual_plot(self, calc_result: CalculationResult):
        """
        Updates the 'manual' (dynamic) data for all three graphs.
        """
        # Unpack main arrays
        freq_main   = calc_result.main_freq
        z_real_main = calc_result.main_z_real
        z_imag_main = calc_result.main_z_imag
    
        # Pass them as 'manual/dynamic' data to each graph
        self._big_graph.update_parameters_manual(freq_main, z_real_main, z_imag_main)
        self._small_graph_1.update_parameters_manual(freq_main, z_real_main, z_imag_main)
        self._small_graph_2.update_parameters_manual(freq_main, z_real_main, z_imag_main)
    
        # Unpack the 3 special points
        freq_sp   = calc_result.special_freq
        z_real_sp = calc_result.special_z_real
        z_imag_sp = calc_result.special_z_imag
    
        # Plot those 3 points in each graph. We'll create a new function to handle that:
        self._big_graph.update_special_points(freq_sp, z_real_sp, z_imag_sp)
        self._small_graph_1.update_special_points(freq_sp, z_real_sp, z_imag_sp)
        self._small_graph_2.update_special_points(freq_sp, z_real_sp, z_imag_sp)
    
    
    

    def get_special_points(self):
        return {}

# -----------------------------------------------------------------------
#  Quick test
# -----------------------------------------------------------------------
import sys
import numpy as np
import pyqtgraph as pg

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QSlider, QPushButton
)
from PyQt5.QtCore import Qt

# Import your adapted graph widget and CalculationResult
# from your_file import WidgetGraphs, CalculationResult

def test_widget_graphs():
    app = QApplication(sys.argv)

    # 1) Create a main widget to hold the graphs + sliders + test buttons
    main_widget = QWidget()
    main_layout = QVBoxLayout(main_widget)

    # 2) The composite widget with ColeCole, Bode, Phase
    graph_widget = WidgetGraphs()
    main_layout.addWidget(graph_widget)

    # ---------------------------------------------------------------------
    # Base (green) data: "static" reference
    # ---------------------------------------------------------------------
    base_freq = np.array([1, 10, 100, 1000, 10000])
    base_real = np.array([100, 80, 60, 40, 20])
    base_imag = np.array([-50, -40, -30, -20, -10])

    # Initialize the 'base' lines with green
    graph_widget.update_graphs(base_freq, base_real, base_imag)

    # ---------------------------------------------------------------------
    # Manual (blue) data + 3 special points
    # ---------------------------------------------------------------------
    manual_freq = np.array([1, 10, 100, 1000, 10000])
    manual_real = np.array([90, 70, 50, 30, 10])
    manual_imag = np.array([-45, -35, -25, -15, -5])

    # Three special frequency points
    sp_freq = np.array([5, 50, 500]) 
    sp_real = np.array([88, 48, 12]) 
    sp_imag = np.array([-44, -28, -10])

    # Build a CalculationResult for the "manual" portion
    # (Note: For the 3 special points, we only have 3 data, 
    #  so they’ll be shown as separate colored markers.)
    initial_calc_result = CalculationResult(
        main_freq = manual_freq,
        main_z_real = manual_real,
        main_z_imag = manual_imag,
        special_freq = sp_freq,
        special_z_real = sp_real,
        special_z_imag = sp_imag
    )

    # Pass it to the graph widget’s update_manual_plot (blue + special points)
    graph_widget.update_manual_plot(initial_calc_result)

    # ---------------------------------------------------------------------
    # Create sliders to scale the base & manual data in real-time
    # ---------------------------------------------------------------------
    sliders_layout = QGridLayout()
    main_layout.addLayout(sliders_layout)

    # 5 sliders: freq scale (for *both* base & manual), 
    #            green real, green imag, blue real, blue imag
    freq_slider_label = QLabel("Freq Scale (black):")
    freq_slider = QSlider(Qt.Horizontal)
    freq_slider.setRange(1, 300)
    freq_slider.setValue(100)
    sliders_layout.addWidget(freq_slider_label, 0, 0)
    sliders_layout.addWidget(freq_slider, 0, 1)

    green_real_label = QLabel("Green Z_real:")
    green_real_slider = QSlider(Qt.Horizontal)
    green_real_slider.setRange(1, 300)
    green_real_slider.setValue(100)
    sliders_layout.addWidget(green_real_label, 1, 0)
    sliders_layout.addWidget(green_real_slider, 1, 1)

    green_imag_label = QLabel("Green Z_imag:")
    green_imag_slider = QSlider(Qt.Horizontal)
    green_imag_slider.setRange(1, 300)
    green_imag_slider.setValue(100)
    sliders_layout.addWidget(green_imag_label, 2, 0)
    sliders_layout.addWidget(green_imag_slider, 2, 1)

    blue_real_label = QLabel("Blue Z_real:")
    blue_real_slider = QSlider(Qt.Horizontal)
    blue_real_slider.setRange(1, 300)
    blue_real_slider.setValue(100)
    sliders_layout.addWidget(blue_real_label, 3, 0)
    sliders_layout.addWidget(blue_real_slider, 3, 1)

    blue_imag_label = QLabel("Blue Z_imag:")
    blue_imag_slider = QSlider(Qt.Horizontal)
    blue_imag_slider.setRange(1, 300)
    blue_imag_slider.setValue(100)
    sliders_layout.addWidget(blue_imag_label, 4, 0)
    sliders_layout.addWidget(blue_imag_slider, 4, 1)

    def on_any_slider_changed():
        """
        When any slider moves, rescale base & manual data
        and re-plot them. Then build a new CalculationResult
        for the manual portion (including the special points).
        """
        freq_scale = freq_slider.value() / 100.0

        green_r_scale = green_real_slider.value() / 100.0
        green_i_scale = green_imag_slider.value() / 100.0

        blue_r_scale = blue_real_slider.value() / 100.0
        blue_i_scale = blue_imag_slider.value() / 100.0

        # Scale base (green) data
        base_freq_scaled = base_freq * freq_scale
        base_real_scaled = base_real * green_r_scale
        base_imag_scaled = base_imag * green_i_scale

        # Scale manual (blue) data
        manual_freq_scaled = manual_freq * freq_scale
        manual_real_scaled = manual_real * blue_r_scale
        manual_imag_scaled = manual_imag * blue_i_scale

        # Scale special points
        sp_freq_scaled = sp_freq * freq_scale
        sp_real_scaled = sp_real * blue_r_scale
        sp_imag_scaled = sp_imag * blue_i_scale

        # Update the 'base' line in green
        graph_widget.update_graphs(
            base_freq_scaled,
            base_real_scaled,
            base_imag_scaled
        )

        # Construct a new CalculationResult for the manual portion
        calc_res = CalculationResult(
            main_freq     = manual_freq_scaled,
            main_z_real   = manual_real_scaled,
            main_z_imag   = manual_imag_scaled,
            special_freq  = sp_freq_scaled,
            special_z_real= sp_real_scaled,
            special_z_imag= sp_imag_scaled
        )
        # Pass it to update_manual_plot
        graph_widget.update_manual_plot(calc_res)

    # Connect all sliders
    freq_slider.valueChanged.connect(on_any_slider_changed)
    green_real_slider.valueChanged.connect(on_any_slider_changed)
    green_imag_slider.valueChanged.connect(on_any_slider_changed)
    blue_real_slider.valueChanged.connect(on_any_slider_changed)
    blue_imag_slider.valueChanged.connect(on_any_slider_changed)

    # ---------------------------------------------------------------------
    # 3) Optional: Add test buttons to filter frequency range
    # ---------------------------------------------------------------------
    button_layout = QHBoxLayout()
    main_layout.addLayout(button_layout)

    btn_filter_10_100 = QPushButton("Filter 10..100 Hz")
    button_layout.addWidget(btn_filter_10_100)

    def filter_10_100():
        graph_widget.apply_filter_frequency_range(10, 100)
    btn_filter_10_100.clicked.connect(filter_10_100)

    btn_show_all = QPushButton("Show All Freq")
    button_layout.addWidget(btn_show_all)

    def show_all():
        """
        Reset the original data to undo prior filtering and re-plot.
        """
        graph_widget.update_graphs(base_freq, base_real, base_imag)

        # Also reset manual part
        calc_res = CalculationResult(
            main_freq     = manual_freq,
            main_z_real   = manual_real,
            main_z_imag   = manual_imag,
            special_freq  = sp_freq,
            special_z_real= sp_real,
            special_z_imag= sp_imag
        )
        graph_widget.update_manual_plot(calc_res)

    btn_show_all.clicked.connect(show_all)

    # ---------------------------------------------------------------------
    # Final Setup
    # ---------------------------------------------------------------------
    main_widget.setLayout(main_layout)
    main_widget.resize(900, 700)
    main_widget.setWindowTitle("WidgetGraphs - Test of CalculationResult + Special Points")
    main_widget.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    test_widget_graphs()
