# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 17:40:39 2024


Emits a signal (model_manual_updated) whenever it recalculates,
passing the new Z_real and Z_imag arrays.
"""

import numpy as np
import configparser
import logging
import inspect

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QObject, pyqtSignal


class ModelManual(QObject):
    """
    A model class for computing combined impedance data from:
      - Resistor + Inductor in series (rinf, linf).
      - Three Zarc circuits (H, M, L).
      - An optional 'modified Zarc' (E) circuit.

    The results (Z_real, Z_imag) are emitted via the signal `model_manual_updated`.
    Additionally, changes to the internal variables can be emitted via 
    `model_manual_variables_updated` as a dictionary.
    """

    # Signals
    model_manual_updated = pyqtSignal(np.ndarray, np.ndarray, np.ndarray)

    def __init__(self, model_formula):
        super().__init__()
        self._model_formula = model_formula

        # Default frequency data & placeholders for computed impedances
        self._modeled_data = {
            'freq': np.array([1, 10, 100, 1000, 10000]),
            'Z_real': np.array([90, 70, 50, 30, 10]),
            'Z_imag': np.array([-45, -35, -25, -15, -5]),
        }

      
        
   # -----------------------------------------------------------------------
   #  Public Interface
   # -----------------------------------------------------------------------

    def initialize_frequencies(self, key, np_array):
          """
          Replaces 'freq' in self._modeled_data, resets default values, and re-runs the model.
          """
          #MM not a fan of error handling here
          if key not in self._modeled_data:
            logging.error(f"Key '{key}' not found in modeled data.")
            return
          
          self._modeled_data[key] = np_array
        


    def run_model(self, v_sliders, v_second):
        print(f"R_h: {v_sliders['Rh']}, F_h: {v_sliders['Fh']}, P_h: {v_sliders['Ph']}")
        
        """
        Evaluate the model_formula for each frequency and update impedance results.
        """
        if self._modeled_data["freq"] is None:
            logging.warning("No frequency data available to iterate over.")
            return

        if self._model_formula is None:
            logging.error("model_formula is not compiled.")
            return

        # Initialize result lists
        modeling_results_real = []
        modeling_results_imag = []

        for freq in self._modeled_data["freq"]:
            try:
                # Prepare arguments
                args = {
                    "freq": freq,
                    **v_sliders,
                    **v_second
                }
                param_values = [
                    args.get(param, np.nan)
                    for param in inspect.signature(self._model_formula).parameters.keys()
                ]

                # Evaluate the formula
                result = self._model_formula(*param_values)

                modeling_results_real.append(result.real)
                modeling_results_imag.append(result.imag)

            except Exception as e:
                logging.error(f"Error evaluating model_formula for freq={freq}: {e}")
                modeling_results_real.append(np.nan)
                modeling_results_imag.append(np.nan)

        # Update results in modeled data
        self._modeled_data['Z_real'] = np.array(modeling_results_real)
        self._modeled_data['Z_imag'] = np.array(modeling_results_imag)

        # Emit updated signal
        self.model_manual_updated.emit(
            self._modeled_data["freq"],
            self._modeled_data['Z_real'],
            self._modeled_data['Z_imag']
        )
        
        
# -----------------------------------------------------------------------
# MANUAL  TEST
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

    from ConfigImporter import ConfigImporter
    from WidgetSliders import WidgetSliders
    from ModelManual import ModelManual

    app = QApplication(sys.argv)

    # ----------------------------------------------------
    # 1. Load config
    # ----------------------------------------------------
    config_file = "config.ini"
    config = ConfigImporter(config_file)

    # ----------------------------------------------------
    # 2. Create an instance of ModelManual
    # ----------------------------------------------------
    model_manual = ModelManual(config.serial_model_compiled_formula)

    # ----------------------------------------------------
    # 3. Create the WidgetSliders instance
    # ----------------------------------------------------
    sliders_widget = WidgetSliders(
        config.slider_configurations,
        config.slider_default_values
    )

    # ----------------------------------------------------
    # Frequency/Impedance Table
    # ----------------------------------------------------
    #freq_array = np.logspace(0, 5, 500)  # 1 Hz to 100 kHz
    freq_array = np.array([1, 10, 100, 1000, 10000])
    
    model_manual.initialize_frequencies("freq", freq_array)

    table_imp = QTableWidget(len(freq_array), 3)
    table_imp.setHorizontalHeaderLabels(["Frequency (Hz)", "Z_real", "Z_imag"])
    for i, freq in enumerate(freq_array):
        table_imp.setItem(i, 0, QTableWidgetItem(f"{freq:.4g}"))
        table_imp.setItem(i, 1, QTableWidgetItem("--"))
        table_imp.setItem(i, 2, QTableWidgetItem("--"))

    # ----------------------------------------------------
    # Nyquist Plot
    # ----------------------------------------------------
    plot_widget = pg.PlotWidget(title="Nyquist Plot (Z_real vs. Z_imag)")
    plot_widget.setLabel("left", "Z_imag")
    plot_widget.setLabel("bottom", "Z_real")
    curve = plot_widget.plot([], [], pen=None, symbol='o', symbolSize=6, symbolBrush='b')

    # ----------------------------------------------------
    # Build the Test Window
    # ----------------------------------------------------
    test_window = QWidget()
    test_window.setWindowTitle("Test ModelManual - Side-by-side Display")
    test_window.setGeometry(0, 0, 1200, 1000)

    main_layout = QVBoxLayout(test_window)


    # ----------------------------------------------------
    # Layout for Tables and Plot
    # ----------------------------------------------------
    h_layout = QHBoxLayout()
    h_layout.addWidget(table_imp)
    h_layout.addWidget(plot_widget)
    main_layout.addLayout(h_layout)
    main_layout.addWidget(sliders_widget)

    # ----------------------------------------------------
    # Update Functions
    # ----------------------------------------------------
    def update_impedance_table_and_plot(freqs, z_reals, z_imags):
        print("Z_real:", z_reals)  # Debugging real values
        print("Z_imag:", z_imags)  # Debugging imaginary values
    
        # Update table
        table_imp.setRowCount(len(freqs))
        for i, (f, re, im) in enumerate(zip(freqs, z_reals, z_imags)):
            table_imp.setItem(i, 0, QTableWidgetItem(f"{f:.4g}"))
            table_imp.setItem(i, 1, QTableWidgetItem(f"{re:.4g}"))
            table_imp.setItem(i, 2, QTableWidgetItem(f"{im:.4g}"))
    
        # Update Nyquist plot
        curve.setData(z_reals, -z_imags)
    
    model_manual.model_manual_updated.connect(update_impedance_table_and_plot)

    # ----------------------------------------------------
    # Slider Callback
    # ----------------------------------------------------
    v_sliders = {k: slider.get_value() for k, slider in sliders_widget.sliders.items()}  # Initial values

    def calculate_v_second(v_sliders):
        
        v_second = {}
        slider_keys = config.slider_configurations.keys()
        slider_values = [v_sliders[key] for key in slider_keys]

        # Compute independent secondary variables (SeriesSecondaryVariables)
        for var, func in config.compiled_expressions.items():
            try:
                v_second[var] = func(*slider_values)
            except Exception as e:
                logging.error(f"Error evaluating '{var}': {e}")
                v_second[var] = None  # Continue processing other expressions

        # Prepare arguments for dependent expressions
        dependent_args = slider_values + [
            v_second.get(var, 0) if v_second.get(var) is not None else 0 
            for var in config.series_secondary_variables.keys()
        ]

        # Compute dependent secondary variables (ParallelModelSecondaryVariables)
        for var, func in config.dependent_compiled_expressions.items():
            try:
                v_second[var] = func(*dependent_args)
            except Exception as e:
                logging.error(f"Error evaluating '{var}': {e}")
                v_second[var] = None  # Continue processing other expressions

        logging.info("Secondary variables calculated successfully.")
        # At this point, self.v_second contains all secondary variables with computed values
        return v_second

    def on_slider_value_updated(key, new_value):
        """
        Update v_sliders with the new slider value, calculate v_second,
        and trigger ModelManual's run_model.
        """
        global v_sliders
        v_sliders[key] = new_value
        v_second = calculate_v_second(v_sliders)
        model_manual.run_model(v_sliders, v_second)

    sliders_widget.slider_value_updated.connect(on_slider_value_updated)

    # ----------------------------------------------------
    # Initial Run
    # ----------------------------------------------------
    v_second = calculate_v_second(v_sliders)
    model_manual.run_model(v_sliders, v_second)

    # ----------------------------------------------------
    # Show Window
    # ----------------------------------------------------
    test_window.show()
    sys.exit(app.exec_())

