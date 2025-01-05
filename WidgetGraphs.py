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
        x, y = self._prepare_xy(data_dict['freq'], data_dict['Z_real'], data_dict['Z_imag'])
        if plot_item:
            plot_item.setData(x, y)

    def _refresh_graph(self):
        """Clears and re-displays both the static and dynamic plots."""
        self.clear()

        # Static plot (base data)
        self._static_plot = self.plot(
            pen=None, symbol='o', symbolSize=8, symbolBrush='g'
        )  # green dots
        self._refresh_plot(self._base_data, self._static_plot)

        # Dynamic plot (manual data)
        self._dynamic_plot = self.plot(
            pen=None, symbol='x', symbolSize=8, symbolBrush='b'
        )  # blue x
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


class PhaseGraph(ParentGraph):
    """
    Plots phase (in degrees) vs. frequency.
    """

    def __init__(self):
        super().__init__()
        self.setTitle("Phase")
        self.setLabel('bottom', "Frequency [Hz]")
        self.setLabel('left', "Phase [degrees]")

    def _prepare_xy(self, freq, Z_real, Z_imag):
        """
        Convert impedance to phase (arctan(Z_imag / Z_real)), in degrees, vs. freq.
        """
        phase_deg = np.degrees(np.arctan2(Z_imag, Z_real))
        return freq, phase_deg


class BodeGraph(ParentGraph):
    """
    Plots the magnitude of impedance (in dB) vs. frequency (Bode plot).
    """

    def __init__(self):
        super().__init__()
        self.setTitle("Bode Graph")
        self.setLabel('bottom', "Frequency [Hz]")
        self.setLabel('left', "Magnitude [dB]")

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

    def update_manual_plot(self, freq, Z_real, Z_imag):
        """
        Updates the 'manual' (dynamic) data for all three graphs.
        """
        self._big_graph.update_parameters_manual(freq, Z_real, Z_imag)
        self._small_graph_1.update_parameters_manual(freq, Z_real, Z_imag)
        self._small_graph_2.update_parameters_manual(freq, Z_real, Z_imag)


# -----------------------------------------------------------------------
#  Quick test
# -----------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    widget = WidgetGraphs()
    widget.resize(600, 400)
    widget.show()

    # Example: set new base data or apply a frequency filter
    # widget.apply_filter_frequency_range(10, 100)

    sys.exit(app.exec_())