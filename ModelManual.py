# -*- coding: utf-8 -*-
# manual_model.py

import numpy as np
import logging
import inspect
from PyQt5.QtCore import QObject, pyqtSignal

class ModelManual(QObject):
    """
    This class replicates the circuit calculation by evaluating
    formulas from config.ini (compiled by ConfigImporter).
    Now it also calculates 'secondary variables' that used to be in Main.
    """

    model_manual_updated = pyqtSignal(np.ndarray, np.ndarray, np.ndarray)

    def __init__(self, config_importer):
        """
        :param config_importer: an instance of ConfigImporter
        """
        super().__init__()
        self.config_importer = config_importer

        # We'll store frequencies and results in these arrays
        self._modeled_data = {
            "freq": np.array([1, 10, 100, 1000, 10000]),
            "Z_real": np.zeros(5),
            "Z_imag": np.zeros(5),
        }

        # We'll keep a copy of the secondary variables from the last run
        self._latest_secondaries = {}

    def initialize_frequencies(self, freq_array: np.ndarray):
        """
        Initializes the frequency array used for model calculations.
        """
        self._modeled_data['freq'] = freq_array
        self._modeled_data['Z_real'] = np.zeros_like(freq_array)
        self._modeled_data['Z_imag'] = np.zeros_like(freq_array)

    def run_model(self, v_sliders, v_second=None):
        """
        Evaluate all expressions for each freq using the slider dictionary.
        If v_second is None, we compute the secondary variables ourselves.
        Then we do the final model formula for each freq.
        Finally, we emit model_manual_updated(...) with new Z_real/Z_imag.
        """
        # 1) Compute or update secondary variables
        if v_second is None:
            v_second = self._calculate_secondary_variables(v_sliders)

        # Save for external reference
        self._latest_secondaries = dict(v_second)

        freqs = self._modeled_data["freq"]
        Zr_list = []
        Zi_list = []

        # Combine the user’s slider dictionary with v_second
        base_vars = dict(v_sliders)
        base_vars.update(v_second)

        for f in freqs:
            local_vars = dict(base_vars)
            local_vars["freq"] = float(f)

            # Evaluate Series, Parallel, Model Secondary, Model Tertiary
            self._evaluate_all_expressions(local_vars)

            # Evaluate final formula
            Z_total = self._evaluate_final_formula(local_vars)

            Zr_list.append(Z_total.real)
            Zi_list.append(Z_total.imag)

        # Update the arrays
        self._modeled_data["Z_real"] = np.array(Zr_list)
        self._modeled_data["Z_imag"] = np.array(Zi_list)

        # Emit the new impedance data
        self.model_manual_updated.emit(
            self._modeled_data["freq"],
            self._modeled_data["Z_real"],
            self._modeled_data["Z_imag"]
        )

    def get_latest_secondaries(self):
        """
        Return the most recent dictionary of secondary variables
        that was computed in run_model.
        """
        return dict(self._latest_secondaries)

    # ----------------------------------------------------
    # Private Helpers
    # ----------------------------------------------------
    def _calculate_secondary_variables(self, v_sliders):
        """
        Computes 'series' and 'parallel' secondary variables
        using the expressions from config.ini.
        Returns a dict of newly calculated secondary variables.
        """
        v_second = {}
        config = self.config_importer

        # Convert the slider dict into an ordered list of values
        slider_keys = config.slider_configurations.keys()
        slider_values = [v_sliders[k] for k in slider_keys]

        # 1) Evaluate Series expressions
        for var, func in config.compiled_expressions.items():
            try:
                v_second[var] = func(*slider_values)
            except Exception as e:
                logging.error(f"Error evaluating '{var}': {e}. Assigned 0")
                v_second[var] = 0

        # 2) Evaluate Parallel expressions
        #    Combine slider_values + newly computed series secondaries
        dep_args = slider_values + [
            v_second.get(svar, 0)
            for svar in config.series_secondary_variables.keys()
        ]

        for var, func in config.dependent_compiled_expressions.items():
            try:
                v_second[var] = func(*dep_args)
            except Exception as e:
                logging.error(f"Error evaluating '{var}': {e}. Assigned 0")
                v_second[var] = 0

        return v_second

    def _evaluate_all_expressions(self, local_vars):
        """
        For the given local_vars dict,
        run the series, parallel, model secondary, and model tertiary expressions
        so that final formula can reference them.
        """
        config = self.config_importer

        # 1) Series
        for var_name, func in config.compiled_expressions.items():
            if func is None: 
                continue
            local_vars[var_name] = self._eval_lambda(func, local_vars)

        # 2) Parallel
        for var_name, func in config.dependent_compiled_expressions.items():
            if func is None:
                continue
            local_vars[var_name] = self._eval_lambda(func, local_vars)

        # 3) Model Secondary
        for var_name, func in config.compiled_model_secondary.items():
            if func is None:
                continue
            local_vars[var_name] = self._eval_lambda(func, local_vars)

        # 4) Model Tertiary
        for var_name, func in config.compiled_model_terciary.items():
            if func is None:
                continue
            local_vars[var_name] = self._eval_lambda(func, local_vars)

    def _evaluate_final_formula(self, local_vars):
        """
        Evaluate the final compiled model formula using local_vars.
        """
        config = self.config_importer
        if config.model_final_formula is None:
            logging.error("No final formula compiled!")
            return np.nan + 1j*np.nan
        return self._eval_lambda(config.model_final_formula, local_vars)

    def _eval_lambda(self, func, var_dict):
        """
        Gathers the parameters from var_dict in the correct order,
        then calls func(*args).
        """
        arg_values = []
        for param_name in inspect.signature(func).parameters.keys():
            val = var_dict.get(param_name, 0)
            arg_values.append(val)
        return func(*arg_values)







#---------------------------------------------------------
#   TEST
#---------------------------------------------------------
def test_all_sliders_influence(self):
    """
    Manual test to ensure that changing each of the 15 slider variables
    alters the model output in some way. If any variable has zero effect,
    we log a warning.
    """
    import numpy as np

    # 1) Define a baseline dictionary for all 15 sliders.
    #    (Adjust these baseline values as needed.)
    v_sliders_baseline = {
        "Linf": -6.0,   # e.g. 10^-6
        "Rinf": 10.0,
        "Rh":   50.0,
        "Fh":   100.0,
        "Ph":   0.8,
        "Rm":   20.0,
        "Fm":   200.0,
        "Pm":   0.9,
        "Rl":   30.0,
        "Fl":   1.0,
        "Pl":   0.7,
        "Re":   25.0,
        "Qe":   1e-4,
        "Pe_f": 0.8,
        "Pe_i": 0.0,
    }

    # 2) Run the model once to get a baseline
    self.run_model(v_sliders_baseline)
    freq_baseline = self._modeled_data["freq"].copy()
    Zr_baseline   = self._modeled_data["Z_real"].copy()
    Zi_baseline   = self._modeled_data["Z_imag"].copy()

    # Just a helper function to apply a small tweak
    def tweak_value(val):
        # If val is zero, bump it to 0.1
        # Else multiply by 1.1 for a ~10% tweak
        return 0.1 if abs(val) < 1e-12 else val * 1.1

    all_sliders = list(v_sliders_baseline.keys())

    # 3) For each slider, tweak it and see if results change
    for slider_name in all_sliders:
        # Copy baseline
        v_changed = dict(v_sliders_baseline)
        # Tweak that one slider
        v_changed[slider_name] = tweak_value(v_changed[slider_name])

        # Re-run the model
        self.run_model(v_changed)
        Zr_new = self._modeled_data["Z_real"].copy()
        Zi_new = self._modeled_data["Z_imag"].copy()

        # 4) Compare new results with baseline
        #    We'll check if they are identical (within a small epsilon).
        #    If all points are basically the same, warn about no effect.
        same_real = np.allclose(Zr_baseline, Zr_new, atol=1e-14, rtol=1e-5)
        same_imag = np.allclose(Zi_baseline, Zi_new, atol=1e-14, rtol=1e-5)

        if same_real and same_imag:
            logging.warning(
                f"[Test] Changing slider '{slider_name}' produced NO change "
                f"in Z_real or Z_imag!"
            )
        else:
            logging.info(
                f"[Test] Changing slider '{slider_name}' did affect the results as expected."
            )

    # Optionally: restore the baseline model or do other cleanup
    self.run_model(v_sliders_baseline)
    
    
    
    
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

