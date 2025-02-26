"""
Created on Mon Dec 30 08:27:11 2024

Graphs for impedance data visualization:
  - ParentGraph (base class)
  - PhaseGraph
  - BodeGraph
  - ColeColeGraph
  - TimeGraph
  - WidgetGraphs (displays multiple graphs)
"""

import sys
import copy
import numpy as np
import pyqtgraph as pg
from pyqtgraph import FillBetweenItem
from PyQt5.QtWidgets import QLineEdit
from pyqtgraph import mkPen

from PyQt5.QtWidgets import (
    QApplication, QPushButton, QWidget, QTabWidget, QHBoxLayout,
    QVBoxLayout, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt

# Example import for the type-hinted method below:
# from ModelManual import CalculationResult
# In your real code, ensure CalculationResult is defined or properly imported.
class CalculationResult:
    """Dummy placeholder so this snippet runs independently."""
    def __init__(self):
        self.main_freq = np.array([1, 10, 100])
        self.main_z_real = np.array([100, 80, 60])
        self.main_z_imag = np.array([-50, -40, -30])
            
        self.rock_z_real: np.ndarray = ([100, 80, 60])
        self.rock_z_imag: np.ndarray = ([-48, -32, -28])

        self.special_freq = np.array([10, 50, 90])
        self.special_z_real = np.array([70, 65, 55])
        self.special_z_imag = np.array([-40, -35, -28])
        
        self.special_resistance_frequency: np.ndarray = [0.1]
        self.special_resistance: np.ndarray = [90]

        self.timedomain_freq = np.array([0.01, 4.5, 1.1])
        self.timedomain_time = np.linspace(0, 1, 100)
        self.timedomain_volt = np.sin(2 * np.pi * 10 * self.timedomain_time)

class ParentGraph(pg.PlotWidget):
    """
    A base PlotWidget with methods for:
      - Storing and refreshing 'base' data and 'manual' (dynamic) data
      - Plotting or filtering frequency ranges
      - Overridden methods to transform freq, Z_real, Z_imag into X, Y
    """

    def __init__(self):
        super().__init__()
        self._init_data()
        self._init_ui()
        self._init_signals()
        self._special_items = [] #Special points marker
        
        self.fill_region = None

        # Initial display and auto-scale setup
        self._refresh_graph()
        self.auto_scale_button.setChecked(True)

    #----Public Methods----------
    def filter_frequency_range(self, f_min, f_max):
        """
        Filters base and manual data to only show points within [f_min, f_max].
        Always filter from the original datasets so we can re-expand later.
        """
        base_mask = (
            (self._original_base_data['freq'] >= f_min)
            & (self._original_base_data['freq'] <= f_max)
        )
        self._base_data = {
            'freq': self._original_base_data['freq'][base_mask],
            'Z_real': self._original_base_data['Z_real'][base_mask],
            'Z_imag': self._original_base_data['Z_imag'][base_mask],
        }

        manual_mask = (
            (self._original_manual_data['freq'] >= f_min)
            & (self._original_manual_data['freq'] <= f_max)
        )
        self._manual_data = {
            'freq': self._original_manual_data['freq'][manual_mask],
            'Z_real': self._original_manual_data['Z_real'][manual_mask],
            'Z_imag': self._original_manual_data['Z_imag'][manual_mask],
        }

        self._refresh_graph()

    def update_parameters_base(self, freq, Z_real, Z_imag):
        """
        Sets new 'base' data and re-displays both plots.
        Also updates the originals so filtering includes the new full dataset.
        """
        self.auto_scale_button.setChecked(False)
        self._base_data = {'freq': freq, 'Z_real': Z_real, 'Z_imag': Z_imag}
        self._original_base_data = copy.deepcopy(self._base_data)
        self._refresh_graph()
        self.auto_scale_button.setChecked(True)

    def update_parameters_manual(self, freq, Z_real, Z_imag):
        """
        Sets new 'manual' (dynamic) data and refreshes only the dynamic plot.
        Also updates the originals so filtering includes the new full dataset.
        """
        self._manual_data = {'freq': freq, 'Z_real': Z_real, 'Z_imag': Z_imag}
        self._original_manual_data = copy.deepcopy(self._manual_data)
        self._refresh_plot(self._manual_data, self._dynamic_plot)

    def update_special_points(self, freq_array, z_real_array, z_imag_array):
        """
        Adds or updates special marker points on the graph.
        """
        for item in getattr(self, '_special_items', []):
            self.removeItem(item)
        self._special_items = []

        for i, color in enumerate(['r', 'g', 'b', 'w']):
            x, y = self._prepare_xy(
                np.array([freq_array[i]]),
                np.array([z_real_array[i]]),
                np.array([z_imag_array[i]])
            )
            plot_item = self.plot(
                x, y, pen=None,
                symbol='x', symbolSize=12,
                symbolBrush=color, symbolPen=color
            )
            self._special_items.append(plot_item)

    #----Private Methods----------
    def _init_data(self):
        """Initialize default datasets and related flags."""
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
        # Keep full copies to allow re-expansion after filtering
        self._original_base_data = copy.deepcopy(self._base_data)
        self._original_manual_data = copy.deepcopy(self._manual_data)
        # Flag to avoid recursive auto-ranging calls
        self._auto_range_in_progress = False

    def _init_ui(self):
        """Setup the UI elements."""
        self.setTitle("Parent Graph")
        self.showGrid(x=True, y=True)
        self._create_auto_scale_button()

    # methods related to ploting
    def _refresh_graph(self):
        """Clears and re-displays both the static and dynamic plots."""
        self.clear()


        # Dynamic plot (manual data)
        self._dynamic_plot = self.plot(
            pen=pg.mkPen(color='c', width=4),
            symbol='o',
            symbolSize=10,
            symbolBrush=None
        )
        self._refresh_plot(self._manual_data, self._dynamic_plot)

           # Static plot (base data)
        self._static_plot = self.plot(
            pen='g',  # green line
            symbol='o',
            symbolSize=5,
            symbolBrush='g'
            )
        self._refresh_plot(self._base_data, self._static_plot)




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

    def _prepare_xy(self, freq, z_real, z_imag):
        """
        Transforms impedance data (freq, Z_real, Z_imag) into (x, y) for plotting.
        Default is (Z_real, Z_imag). Subclasses override this if needed.
        """
        return z_real, z_imag
    
    # methods related to escale button
    def _create_auto_scale_button(self):
        """Create and configure the auto-scale button."""
        self.auto_scale_button = QPushButton("", self)
        self.auto_scale_button.setCheckable(True)
        self.auto_scale_button.setGeometry(10, 10, 10, 10)
        self.auto_scale_button.toggled.connect(self._handle_auto_scale_toggle)
        self.auto_scale_button.setStyleSheet("""
            QPushButton { background-color: lightgray; }
            QPushButton:checked { background-color: rgb(102, 178, 255); }
        """)

    def _init_signals(self):
        """Connect signals to their handlers."""
        self.plotItem.getViewBox().sigRangeChanged.connect(self._on_view_range_changed)
        
    def _handle_auto_scale_toggle(self, checked):
        """
        Called when the auto-scale button is toggled.
        If enabled, immediately re-auto-range the view.
        """
        if checked:
            self._apply_auto_scale()

    def _on_view_range_changed(self, view_box, view_range):
        """
        Called when the view's range changes.
        If auto-scale is enabled and this change did not originate
        from our own auto-range call, re-apply auto-range.
        """
        if self.auto_scale_button.isChecked() and not self._auto_range_in_progress:
            self._apply_auto_scale()

    def _apply_auto_scale(self):
        """
        Auto-scales the view based solely on the static (base) plot data.
        """
        x_data, y_data = self._prepare_xy(
            self._base_data['freq'],
            self._base_data['Z_real'],
            self._base_data['Z_imag']
        )
        if x_data.size and y_data.size:
            x_min, x_max = np.min(x_data), np.max(x_data)
            y_min, y_max = np.min(y_data), np.max(y_data)

            self._auto_range_in_progress = True
            self.plotItem.getViewBox().setRange(
                xRange=(x_min, x_max),
                yRange=(y_min, y_max),
                padding=0.1
            )
            self._auto_range_in_progress = False


class PhaseGraph(ParentGraph):
    """
    Plots log10(|phase|) vs. frequency (phase in degrees).
    """
    def __init__(self):
        super().__init__()
        
        self.setTitle("Phase (Log Scale of Degrees)")
        self.setLabel('bottom', "log10(Freq[Hz])")
        self.setLabel('left', "log10(|Phase|)")

        # Fix axes for demonstration
        self.setYRange(-2, 2, padding=0.08)
        self.setXRange(-1.5, 6, padding=0.05)
        self.getViewBox().invertX(True)

    def _prepare_xy(self, freq, z_real, z_imag):
        freq_log = np.log10(freq)
        phase_deg = np.degrees(np.arctan2(z_imag, z_real))
        # Avoid log of zero by adding a small offset
        phase_log = np.log10(np.abs(phase_deg) + 1e-10)
        return freq_log, phase_log


class BodeGraph(ParentGraph):
    """
    Plots the magnitude of impedance in log scale vs. frequency.
    """
    def __init__(self):
        super().__init__()
        self.setTitle("Impedance Magnitude Graph")
        self.setLabel('bottom', "log10(Freq[Hz])")
        self.setLabel('left', "Log10 Magnitude [dB]")

        self.setYRange(3, 7, padding=0.08)
        self.setXRange(-1.5, 6, padding=0.05)
        self.getViewBox().invertX(True)

    def _prepare_xy(self, freq, z_real, z_imag):
        freq_log = np.log10(freq)
        mag = np.sqrt(z_real**2 + z_imag**2)
        # Using log10(magnitude). If you really want dB, use 20*log10(mag).
        mag_db = np.log10(mag)
        return freq_log, mag_db


class ColeColeGraph(ParentGraph):
    """
    Plots a Nyquist diagram: real(Z) vs. -imag(Z),
    with an optional third (secondary) line.
    """
    def __init__(self):
        
        # Initialize secondary manual data and placeholder for plot
        self._secondary_manual_data = {
            'freq': np.array([]),
            'Z_real': np.array([]),
            'Z_imag': np.array([]),
        }
        self._secondary_plot = None
        
        super().__init__()
        
        # Adjust Cole-Cole specific properties
        self.getPlotItem().setAspectLocked(True, 1)
        self.setTitle("Cole-Cole Graph")
        self.setLabel('bottom', "Z' [Ohms]")
        self.setLabel('left', "-Z'' [Ohms]")

    def update_parameters_secondary_manual(self, freq, Z_real, Z_imag):
        """
        Assign new data to the 'third line' (secondary manual data),
        then refresh only that plot.
        """
        self._secondary_manual_data = {
            'freq': freq,
            'Z_real': Z_real,
            'Z_imag': Z_imag
        }
        # If the plot exists, update it; otherwise it will be updated in _refresh_graph
        if self._secondary_plot is not None:
            self._refresh_plot(self._secondary_manual_data, self._secondary_plot)

    def _refresh_graph(self):
        """
        Override the parent method to add a third line after the usual
        base/manual lines have been set up.
        """
        # First, call the parent to plot the base and manual data lines.
        super()._refresh_graph()

        # Now create (or recreate) the third line plot.
        # Example: red line with circle symbols.
        self._secondary_plot = self.plot(
            pen=mkPen(color='#F4C2C2', style=Qt.DashLine),  # Pale pink
            symbol='o',
            symbolSize=6,
            symbolBrush=None
        )
        # Immediately refresh with whatever data is in _secondary_manual_data
        self._refresh_plot(self._secondary_manual_data, self._secondary_plot)

    def _prepare_xy(self, freq, z_real, z_imag):
        """
        Transform data for Cole-Cole plotting: real(Z) vs. -imag(Z).
        """
        return z_real, -z_imag


class TimeGraph(ParentGraph):
    """
    Simple time-domain plot: time vs. voltage.
    Interprets Z_real as time and Z_imag as voltage.
    The Mx, Mt, M0 labels remain pinned in the top-left of the plot view
    (they do NOT move when panning or zooming).
    """
    
    def __init__(self):

        self._init_child_attributes()
        
        super().__init__()
        self._configure_plot()
        self._setup_text_items()
        self._refresh_graph()
    
    def _init_child_attributes(self):
        """Initialize attributes specific to the time graph."""
        self.mx = None
        self.mt = None
        self.m0 = None

        # Create TextItems; they are not added to the ViewBox until later.
        self.mx_text = pg.TextItem(color='w', anchor=(0, 0))
        self.mt_text = pg.TextItem(color='w', anchor=(0, 0))
        self.m0_text = pg.TextItem(color='w', anchor=(0, 0))
    
    def _configure_plot(self):
        """Configure the plot title and axis labels."""
        self.setTitle("Time Domain Graph")
        self.setLabel('bottom', "Time [s]")
        self.setLabel('left', "Voltage")
    
    def _setup_text_items(self):
        """
        Make each label a child of the ViewBox in device coordinates so that they stay
        in the same screen location regardless of panning or zooming.
        """
        vb = self.plotItem.vb
        self.mx_text.setParentItem(vb)
        self.mt_text.setParentItem(vb)
        self.m0_text.setParentItem(vb)
        
        # Position the text items in the top-left corner (device coordinates)
        self.mx_text.setPos(300, 10)
        self.mt_text.setPos(300, 30)  # Stack below Mx
        self.m0_text.setPos(300, 50)  # Stack below Mt
    
    def _prepare_xy(self, freq, z_real, z_imag):
        """Interpret Z_real as time, Z_imag as voltage."""
        return z_real, z_imag

    def update_parameters_base(self, freq, z_real, z_imag):
        super().update_parameters_base(freq, z_real, z_imag)
        self._refresh_graph()

    def update_parameters_manual(self, freq, z_real, z_imag):
        super().update_parameters_manual(freq, z_real, z_imag)
        self._refresh_graph()

    def _refresh_graph(self):
        """
        Draw the green (base) + blue (manual) lines via the parent,
        then compute Mx/Mt/M0 and update the text items' content.
        The text items are pinned to the top-left in device coords, so we do NOT change their positions here.
        """
        # 1) Let the parent draw its curves.
        super()._refresh_graph()

        # 2) Get manual data (blue curve)
        t = self._manual_data['Z_real']  # Here, Z_real is used as time.
        v = self._manual_data['Z_imag']  # Z_imag is the voltage.

        if t.size == 0 or v.size == 0:
            return

        # 3) Shade the region [0.45, 1.1]
        t_start, t_end = 0.45, 1.1
        mask = (t >= t_start) & (t <= t_end)
        if np.any(mask):
            self.plot(
                t[mask], v[mask],
                pen=pg.mkPen('b', width=0),
                fillLevel=0,
                brush=pg.mkBrush(0, 0, 255, 80)  # Semi-transparent blue.
            )

        # 4) Compute chargeability M-values (mV/V)
        Vp = np.interp(0.0, t, v)  # Voltage at t=0.
        if abs(Vp) < 1e-12:
            self.mx = 0.0
            self.mt = 0.0
            self.m0 = 0.0
        else:
            integral_mx = self._integrate_chargeability(t, v, 0.45, 1.1)
            integral_mt = self._integrate_chargeability(t, v, 0.0, 2.0)
            v_at_0p01   = np.interp(0.01, t, v) if np.any(t >= 0.01) else 0.0

            self.mx = 1000.0 * (integral_mx / Vp)
            self.mt = 1000.0 * (integral_mt / Vp)
            self.m0 = 1000.0 * (v_at_0p01 / Vp)

        # 5) Update text items with the computed values.
        self.mx_text.setText(f"Mx = {self.mx:.1f}")
        self.mt_text.setText(f"Mt = {self.mt:.1f}")
        self.m0_text.setText(f"M0 = {self.m0:.3f}")

        # 6) Auto-range the plot.
        self.plotItem.getViewBox().autoRange()

    def _integrate_chargeability(self, t, v, tmin, tmax):
        """
        Compute the integral of v(t) between tmin and tmax using the trapezoidal rule.
        """
        mask = (t >= tmin) & (t <= tmax)
        if not np.any(mask):
            return 0.0
        return np.trapz(y=v[mask], x=t[mask])
    
    def get_special_values(self):
        """
        Return a dictionary of the special values: Mx, Mt, and M0.
        """
        return {'mx': self.mx, 'mt': self.mt, 'm0': self.m0}


class WidgetGraphs(QWidget):
    """
    A widget that displays multiple graphs in a split/tabbed layout:
      - A tabbed area with:
          * Cole-Cole (Nyquist) graph
          * Time-Domain graph
      - To the right, a vertical stack of:
          * Bode graph
          * Phase graph
    """

    def __init__(self):
        super().__init__()
        self._init_graphs()
        self._init_ui()

    def _init_graphs(self):
        """
        Initializes internal graph widgets.
        """
        self._big_graph = ColeColeGraph()
        self._small_graph_1 = BodeGraph()
        self._small_graph_2 = PhaseGraph()
        self._tab_graph = TimeGraph()

    def _init_ui(self):
        """
        Initializes and sets up the UI layout.
        """
        # Create the tab widget
        self._tab_widget = QTabWidget()
        self._tab_widget.addTab(self._big_graph, "Cole Graph")
        self._tab_widget.addTab(self._tab_graph, "T.Domain Graph")
        self._tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._tab_widget.setStyleSheet("QTabWidget::pane { border: none; }")

        # Determine tab bar height for alignment
        tab_bar_height = self._tab_widget.tabBar().sizeHint().height()

        # Create the left panel (tabbed area)
        left_panel = self._create_left_panel()

        # Create the right panel (two smaller graphs)
        right_panel = self._create_right_panel(tab_bar_height)

        # Put everything in a horizontal layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)

        self.setLayout(main_layout)

    def _create_left_panel(self):
        """
        Creates the left panel containing the QTabWidget inside a QFrame.
        """
        frame = self._create_frame()
        layout = self._create_vbox_layout(frame, margins=(0, 0, 0, 0))
        layout.addWidget(self._tab_widget)
        return frame

    def _create_right_panel(self, tab_bar_height):
        """
        Creates the right panel containing the two smaller graphs.
        """
        frame = self._create_frame()
        layout = self._create_vbox_layout(frame, margins=(0, tab_bar_height, 0, 0))
        layout.addWidget(self._small_graph_1)
        layout.addWidget(self._small_graph_2)
        return frame

    @staticmethod
    def _create_frame():
        """
        Creates and returns a styled QFrame.
        """
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFrameShadow(QFrame.Raised)
        return frame

    @staticmethod
    def _create_vbox_layout(parent, margins=(0, 0, 0, 0)):
        """
        Creates and returns a QVBoxLayout with the specified margins.
        """
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(*margins)
        layout.setSpacing(0)
        return layout

    def update_front_graphs(self, freq, z_real, z_imag):
        """
        Updates the base (static) data for the Cole, Bode, Phase graphs.
        """
        self._big_graph.update_parameters_base(freq, z_real, z_imag)
        self._small_graph_1.update_parameters_base(freq, z_real, z_imag)
        self._small_graph_2.update_parameters_base(freq, z_real, z_imag)

    def update_timedomain_graph(self, freq, time, voltage):
        """
        Updates the base (static) data for the time-domain graph.
        """
        self._tab_graph.update_parameters_base(freq, time, voltage)

    def update_manual_plot(self, calc_result: CalculationResult):
        """
        Updates all graphs with the 'manual' (dynamic) data from a CalculationResult.
        """
        freq_main = calc_result.main_freq
        z_real_main = calc_result.main_z_real
        z_imag_main = calc_result.main_z_imag
        
        z_rock_real = calc_result.rock_z_real
        z_rock_imag = calc_result.rock_z_imag

        # Update manual parameters for Cole/Bode/Phase
        self._big_graph.update_parameters_manual(freq_main, z_real_main, z_imag_main)
        self._small_graph_1.update_parameters_manual(freq_main, z_real_main, z_imag_main)
        self._small_graph_2.update_parameters_manual(freq_main, z_real_main, z_imag_main)
        
        # Update secondary manual parameters for Cole
        self._big_graph.update_parameters_secondary_manual(freq_main, z_rock_real, z_rock_imag)

        # Add special markers
        freq_sp = calc_result.special_freq
        z_real_sp = calc_result.special_z_real
        z_imag_sp = calc_result.special_z_imag
        
        self._big_graph.update_special_points(freq_sp, z_real_sp, z_imag_sp)
        self._small_graph_1.update_special_points(freq_sp, z_real_sp, z_imag_sp)
        self._small_graph_2.update_special_points(freq_sp, z_real_sp, z_imag_sp)

        # Update time-domain graph with manual data
        self._tab_graph.update_parameters_manual(
            calc_result.timedomain_freq,
            calc_result.timedomain_time,
            calc_result.timedomain_volt
        )

    def apply_filter_frequency_range(self, f_min, f_max):
        """
        Filters out data outside [f_min, f_max] for all graphs.
        """
        self._big_graph.filter_frequency_range(f_min, f_max)
        self._small_graph_1.filter_frequency_range(f_min, f_max)
        self._small_graph_2.filter_frequency_range(f_min, f_max)
        
    def get_graphs_parameters(self):
        
        graphs_parameters= self._tab_graph.get_special_values()
        
        return graphs_parameters
    

# -----------------------------------------------------------------------
#  Quick Test
# -----------------------------------------------------------------------

import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QSlider, QLabel
)
from PyQt5.QtCore import Qt

###############################################################################
# TestWidget
###############################################################################
class TestWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manual Test: Blue & Pink lines move (ColeColeGraph)")

        # 1) Create the main "WidgetGraphs" container
        self.graphs = WidgetGraphs()

        # 2) Create sliders & labels for parameters
        params = [("param1", 20), ("param2", 10), ("param3", 5)]
        self.sliders, self.labels = {}, {}
        slider_layout = QVBoxLayout()
        for name, init_val in params:
            label = QLabel(f"{name}: {init_val}")
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 100)  # slider from 0..100
            slider.setValue(init_val)
            slider.valueChanged.connect(self._update_blue_line)

            self.labels[name] = label
            self.sliders[name] = slider

            slider_layout.addWidget(label)
            slider_layout.addWidget(slider)

        # 3) Put everything in the main layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.graphs, stretch=1)
        main_layout.addLayout(slider_layout)
        self.setLayout(main_layout)

        # 4) Generate & set up the base (green) data once
        self.base_data = self._generate_base_data()
        freq, z_real, z_imag, time, volt = self.base_data
        self.graphs.update_front_graphs(freq, z_real, z_imag)    # Cole/Bode/Phase
        self.graphs.update_timedomain_graph(freq, time, volt)    # TimeGraph

        # 5) Initial draw of the manual lines (blue & pink)
        self._update_blue_line()

    @staticmethod
    def _generate_base_data(num_points=50):
        """
        Creates some 'base' data for testing.
        """
        freq = np.logspace(0, 5, num_points)   # 1 .. 100000
        z_real = 50 + 10 * np.sqrt(freq)       # some made-up data
        z_imag = -5 * np.log10(freq + 1)
        time = np.linspace(0, 1, 200)          # 0..1
        volt = 0.5 * np.sin(2 * np.pi * 5 * time)
        return freq, z_real, z_imag, time, volt

    @staticmethod
    def _generate_manual_data(base_data, param1, param2, param3):
        """
        Generates the 'manual' (blue) line data from the base data,
        with transformations to make changes clearly visible.
        """
        freq, z_real, z_imag, time, volt = base_data

        # Increase factor & offset so changes are obvious:
        # param1 (0..100) => factor ~ [1..6], param2 => offset up to ~50, etc.
        factor = 1 + param1 / 20.0
        offset_z = param2 * 0.5
        offset_v = param3 / 20.0

        freq_out = freq
        z_real_out = factor * (z_real + offset_z)
        z_imag_out = factor * (z_imag + offset_z)
        volt_out = factor * volt + offset_v

        return freq_out, z_real_out, z_imag_out, time, volt_out

    def _update_blue_line(self):
        """
        1) Re-compute the 'manual' (blue) data from sliders,
        2) Update it in all relevant graphs,
        3) Generate & update the 'secondary' pink line in ColeColeGraph.
        """
        # -- Read slider values --
        p1 = self.sliders["param1"].value()
        p2 = self.sliders["param2"].value()
        p3 = self.sliders["param3"].value()

        # -- Update labels --
        for name, val in zip(["param1", "param2", "param3"], (p1, p2, p3)):
            self.labels[name].setText(f"{name}: {val}")

        # -- 1) Update the BLUE line --
        freq, z_real, z_imag, time, volt = self._generate_manual_data(
            self.base_data, p1, p2, p3
        )

        # Update the 'blue line' (manual) in Cole/Bode/Phase
        self.graphs._big_graph.update_parameters_manual(freq, z_real, z_imag)
        self.graphs._small_graph_1.update_parameters_manual(freq, z_real, z_imag)
        self.graphs._small_graph_2.update_parameters_manual(freq, z_real, z_imag)

        # Update the 'blue line' in the TimeDomain
        self.graphs._tab_graph.update_parameters_manual(freq, time, volt)

        # -- 2) Update the PINK (secondary) line in ColeColeGraph --
        # Create a bigger shift so the pink line is clearly different:
        freq2 = freq * (1.2 + p1 / 15.0)
        z_real2 = z_real + 30 + 2 * p2
        z_imag2 = z_imag - 30 - 2 * p3

        # This method is only valid on ColeColeGraph
        self.graphs._big_graph.update_parameters_secondary_manual(
            freq2, z_real2, z_imag2
        )

###############################################################################
#  MAIN
###############################################################################
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    # Make sure we have a QApplication instance
    app = QApplication(sys.argv)

    # Create and show the test widget
    tester = TestWidget()
    tester.show()

    sys.exit(app.exec_())
