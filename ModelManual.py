# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 17:40:39 2024

ModelManual is a widget that calculates combined impedance from:
  - R + jωL (resistor + inductor in series)
  - Zarc circuits (H, M, L)
  - An optional 'modified Zarc' (E) circuit

Emits a signal (model_manual_updated) whenever it recalculates,
passing the new Z_real and Z_imag arrays.
"""

import numpy as np
import configparser

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal

# Updated imports (class name changes)
from WidgetSliders import WidgetSliders
from CustomSliders import EPowerSliderWithTicks, DoubleSliderWithTicks
from ConfigImporter import ConfigImporter


class ModelManual(QWidget):
    """
    A model class for computing combined impedance data from:
      - Resistor + Inductor in series (rinf, linf).
      - Three Zarc circuits (H, M, L).
      - An optional 'modified Zarc' (E) circuit.

    The results (Z_real, Z_imag) are emitted via the signal `model_manual_updated`.
    """

    model_manual_updated = pyqtSignal(np.ndarray, np.ndarray, np.ndarray)

    def __init__(self, variables_keys, variables_default_values):
        """
        Parameters
        ----------
        variables_keys : list of str
            For instance ['rinf', 'linf', 'rh', 'fh', 'ph', 'rm', ...]
        variables_default_values : list of float
            Default numeric values corresponding to each key.
        """
        super().__init__()

        self._variables_keys = variables_keys
        self._variables_default_values = variables_default_values

        # Dictionary storing all slider/settable variable values
        self._variables_dictionary = {key: 0.0 for key in variables_keys}

        # Default frequency data & placeholders for computed impedances
        self._manual_data = {
            'freq': np.array([1, 10, 100, 1000, 10000]),
            'Z_real': np.array([90, 70, 50, 30, 10]),
            'Z_imag': np.array([-45, -35, -25, -15, -5]),
        }

        self._set_default_values()

    # -----------------------------------------------------------------------
    #  Private Helpers
    # -----------------------------------------------------------------------
    def _set_default_values(self):
        """Assigns default values to each variable and resets the model."""
        for key, default_val in zip(self._variables_keys, self._variables_default_values):
            self._variables_dictionary[key] = default_val

    
    def _compute_inductor_and_resistor(self, freq_array, r_key='rinf', l_key='linf'):
        """
        Returns arrays (real, imag) for resistor (r_key) + jωL (l_key).
        """
        r_val = self._variables_dictionary[r_key]
        l_val = self._variables_dictionary[l_key]
        omega = 2 * np.pi * freq_array
        z_complex = r_val + (1j * omega * l_val)  # R + jωL
        return np.real(z_complex), np.imag(z_complex)

    def _zarc_impedance(self, freq, r_val, f_val, pi_val, pf_val):
        """
        Computes Zarc = (Z_r * Z_cpe) / (Z_r + Z_cpe) at a single freq.
        """
        # Example: Q = 1 / (R * (2πf0)^pf_val)
        q_val = 1.0 / (r_val * (2.0 * np.pi * f_val)**pf_val)
        phase_factor = (1j)**pi_val
        omega_exp = (2.0 * np.pi * freq)**pf_val

        z_cpe = 1.0 / (q_val * phase_factor * omega_exp)
        z_r = r_val
        return (z_cpe * z_r) / (z_cpe + z_r)

    def _compute_zarc_impedance_for_range(self, r_key, f_key, pi_key, pf_key):
        """
        Loops over self._manual_data['freq'] to compute real & imag parts.
        """
        freq_array = self._manual_data['freq']
        r_val = self._variables_dictionary[r_key]
        f_val = self._variables_dictionary[f_key]
        pi_val = self._variables_dictionary[pi_key]
        pf_val = self._variables_dictionary[pf_key]

        real_parts, imag_parts = [], []
        for freq in freq_array:
            z_total = self._zarc_impedance(freq, r_val, f_val, pi_val, pf_val)
            real_parts.append(z_total.real)
            imag_parts.append(z_total.imag)

        return np.array(real_parts), np.array(imag_parts)

    # -----------------------------------------------------------------------
    #  Main Calculation Routine
    # -----------------------------------------------------------------------
    def _run_model(self):
        """
        1. R_inf + L_inf in series
        2. Zarc H, Zarc M, Zarc L
        3. Zarc E (modified)
        Summation of real and imaginary parts. Then emits model_manual_updated.
        """
        freq_array = self._manual_data['freq']

        # (1) R+L
        r_i_real, r_i_imag = self._compute_inductor_and_resistor(freq_array, 'rinf', 'linf')

        # (2) H
        zarc_h_real, zarc_h_imag = self._compute_zarc_impedance_for_range('rh', 'fh', 'ph', 'ph')
        # (3) M
        zarc_m_real, zarc_m_imag = self._compute_zarc_impedance_for_range('rm', 'fm', 'pm', 'pm')
        # (4) L
        zarc_l_real, zarc_l_imag = self._compute_zarc_impedance_for_range('rl', 'fl', 'pl', 'pl')
        # (5) E
        zarc_e_real, zarc_e_imag = self._compute_zarc_impedance_for_range('re', 'qe', 'pe_i', 'pe_f')

        # Summation (or whatever your circuit requires)
        total_real = (r_i_real + zarc_h_real + zarc_m_real + zarc_l_real + zarc_e_real)
        total_imag = (r_i_imag + zarc_h_imag + zarc_m_imag + zarc_l_imag + zarc_e_imag)

        self._manual_data['Z_real'] = total_real
        self._manual_data['Z_imag'] = total_imag

        # Emit
        self.model_manual_updated.emit(freq_array, total_real, total_imag)

    # -----------------------------------------------------------------------
    #  Public Interface
    # -----------------------------------------------------------------------
    def initialize_frequencies(self, freq_array):
        """
        Replaces 'freq' in self._manual_data. Then resets defaults and re-runs the model.
        """
        self._manual_data['freq'] = freq_array
        self._set_default_values()
        self._run_model()

    def update_variable(self, key, new_value):
        """
        Updates one variable in _variables_dictionary, re-runs the model,
        and emits the new data.
        """
        if key not in self._variables_dictionary:
            raise KeyError(f"Variable '{key}' not found in the model.")

        self._variables_dictionary[key] = new_value
        self._run_model()


# -----------------------------------------------------------------------
#  TEST
# -----------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import numpy as np
    from PyQt5.QtWidgets import (
        QApplication, QWidget, QVBoxLayout,
        QTableWidget, QTableWidgetItem, QHBoxLayout
    )
    from PyQt5.QtCore import Qt
    from ConfigImporter import ConfigImporter
    # Renamed from NSlidersWidget → WidgetSliders
    from WidgetSliders import WidgetSliders

    app = QApplication(sys.argv)

    # 1. Load config
    config_file = "config.ini"
    config = ConfigImporter(config_file)

    # 2. Create an instance of ModelManual
    model_manual = ModelManual(
        list(config.slider_configurations.keys()),
        config.slider_default_values
    )

    # 3. Create the WidgetSliders instance
    sliders_widget = WidgetSliders(
        config.slider_configurations,
        config.slider_default_values
    )

    # Build a test window
    test_window = QWidget()
    test_window.setWindowTitle("Test ModelManual - Side-by-side Display")
    test_window.setGeometry(100, 100, 1200, 600)

    main_layout = QVBoxLayout(test_window)

    # Place sliders on top
    main_layout.addWidget(sliders_widget)

    # Variables table
    variables_keys = list(model_manual._variables_dictionary.keys())
    table_vars = QTableWidget(len(variables_keys), 3)
    table_vars.setHorizontalHeaderLabels(["Variable", "Slider Value", "Model Value"])

    row_index_map = {}
    for i, key in enumerate(variables_keys):
        row_index_map[key] = i
        table_vars.setItem(i, 0, QTableWidgetItem(key))
        slider_val = str(model_manual._variables_dictionary[key])
        table_vars.setItem(i, 1, QTableWidgetItem(slider_val))
        table_vars.setItem(i, 2, QTableWidgetItem(slider_val))

    # Impedance table: freq, Z_real, Z_imag
    freq_array = model_manual._manual_data['freq']
    table_imp = QTableWidget(len(freq_array), 3)
    table_imp.setHorizontalHeaderLabels(["Frequency", "Z_real", "Z_imag"])

    for i, f in enumerate(freq_array):
        table_imp.setItem(i, 0, QTableWidgetItem(str(f)))
        table_imp.setItem(i, 1, QTableWidgetItem(str(model_manual._manual_data['Z_real'][i])))
        table_imp.setItem(i, 2, QTableWidgetItem(str(model_manual._manual_data['Z_imag'][i])))

    # Combine tables side by side
    tables_layout = QHBoxLayout()
    tables_layout.addWidget(table_vars)
    tables_layout.addWidget(table_imp)
    main_layout.addLayout(tables_layout)

    def update_impedance_table():
        freqs = model_manual._manual_data['freq']
        z_reals = model_manual._manual_data['Z_real']
        z_imags = model_manual._manual_data['Z_imag']

        # If freq array changed size, adjust the table row count
        table_imp.setRowCount(len(freqs))

        for i in range(len(freqs)):
            table_imp.setItem(i, 0, QTableWidgetItem(str(freqs[i])))
            table_imp.setItem(i, 1, QTableWidgetItem(str(z_reals[i])))
            table_imp.setItem(i, 2, QTableWidgetItem(str(z_imags[i])))

    def on_slider_value_updated(key, new_value):
        """
        Called when a slider changes. Updates ModelManual & table.
        """
        model_manual.update_variable(key, new_value)

        row = row_index_map[key]
        table_vars.setItem(row, 1, QTableWidgetItem(str(new_value)))
        model_val = str(model_manual._variables_dictionary[key])
        table_vars.setItem(row, 2, QTableWidgetItem(model_val))

        # Refresh impedance table
        update_impedance_table()

    sliders_widget.slider_value_updated.connect(on_slider_value_updated)

    test_window.show()
    sys.exit(app.exec_())