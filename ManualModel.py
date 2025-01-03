# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 17:40:39 2024

@author: agarcian
"""

#MM
#This class ahs a level of coupling and specificity for the  name of the variables is not ideal. 
#Maybe I shoudl reconsider and define the slider values and everything here?

import numpy as np
import configparser

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal

from NSlidersWidget import NSlidersWidget
from SubclassesSliderWithTicks import *
from ConfigImporter import *


class ManualModel(QWidget):
    """
    A model class for computing combined impedance data from:
      - Resistor + Inductor in series (R_inf, L_inf).
      - Three Zarc circuits (H, M, L).
      - An optional 'modified Zarc' (E) circuit.

    The results (Z_real, Z_imag) are emitted via the signal `manual_model_updated`.
    """

    manual_model_updated = pyqtSignal(np.ndarray, np.ndarray, np.ndarray)

    def __init__(self, variables_keys, variables_default_values):
        """
        Parameters
        ----------
        variables_keys : list of str
            A list of keys, e.g. ['rinf', 'linf', 'rh', 'fh', 'ph', ...]

        variables_default_values : list of float
            The default values for each key, in the same order.
        """
        super().__init__()
        
        # Store the variable names and defaults
        self._variables_keys = variables_keys
        self._variables_default_values = variables_default_values
        
        # Dictionary storing all slider/settable variable values
        self._variables_dictionary = {
            key: 0.0 for key in variables_keys
        }

        # Default frequency data & placeholders for computed impedances
        self._manual_data = {
            'freq': np.array([1, 10, 100, 1000, 10000]),
            'Z_real': np.array([90, 70, 50, 30, 10]),
            'Z_imag': np.array([-45, -35, -25, -15, -5]),
            'Z_total': np.zeros(5, dtype=complex),  # example placeholder
        }

        self._set_default_values()

    # -----------------------------------------------------------------------
    #  Private Helper Methods
    # -----------------------------------------------------------------------
    def _compute_inductor_and_resistor(self, freq_array, r_key='rinf', l_key='linf'):
        """
        Returns two NumPy arrays (real, imag) for the resistor (r_key) 
        and inductor (l_key) in series: Z = R + j(2πfL).
        """
        r_val = self._variables_dictionary[r_key]
        l_val = self._variables_dictionary[l_key]

        # Z = R + jωL for each frequency
        # => real part = R, imag part = ωL
        # freq_array is length N, so we build length N arrays:
        omega = 2 * np.pi * freq_array
        z_complex = r_val + (1j * omega * l_val)

        return np.real(z_complex), np.imag(z_complex)

    def _zarc_impedance(self, freq, r_val, f_val, pi_val, pf_val):
        """
        Compute the impedance of a single Zarc circuit at one frequency.
        Zarc is (Z_r * Z_cpe) / (Z_r + Z_cpe).

        freq    : float
            A single frequency point.
        r_val   : float
            R in ohms.
        f_val   : float
            The characteristic frequency (f0).
        pi_val  : float
            The exponent for the imaginary base (1j)^pi_val.
        pf_val  : float
            The exponent for the angular frequency term (ω^pf_val).
        """
        # Q = 1 / ( R * (2πf0)^pf_val ) for example
        q_val = 1.0 / (r_val * (2.0 * np.pi * f_val)**pf_val)

        phase_factor = (1j)**pi_val  # e.g. (j)^0.8
        omega_exp = (2.0 * np.pi * freq)**pf_val

        z_cpe = 1.0 / (q_val * phase_factor * omega_exp)  # 1 / (Q * j^p * ω^p)
        z_r = r_val

        return (z_cpe * z_r) / (z_cpe + z_r)

    def _compute_zarc_impedance_for_range(self, r_key, f_key, pi_key, pf_key):
        """
        Loops over self._manual_data['freq'] to compute the real & imaginary 
        parts of a Zarc for each frequency. Returns two arrays: (real, imag).
        """
        freq_array = self._manual_data['freq']
        
        r_val = self._variables_dictionary[r_key]
        f_val = self._variables_dictionary[f_key]
        pi_val = self._variables_dictionary[pi_key]
        pf_val = self._variables_dictionary[pf_key]

        real_parts = []
        imag_parts = []

        for freq in freq_array:
            z_total = self._zarc_impedance(freq, r_val, f_val, pi_val, pf_val)
            real_parts.append(z_total.real)
            imag_parts.append(z_total.imag)

        return np.array(real_parts), np.array(imag_parts)

    def _set_default_values(self):
        """Sets the variables to their default values, then runs the model once."""
        for key, default_val in zip(self._variables_keys, self._variables_default_values):
            self._variables_dictionary[key] = default_val

    # -----------------------------------------------------------------------
    #  Main Calculation Routine
    # -----------------------------------------------------------------------
    def _run_model(self):
        """
        Compute the total impedance as a sum of:
          1. R_inf + L_inf in series,
          2. Zarc H,
          3. Zarc M,
          4. Zarc L,
          5. Zarc E (modified Zarc, optional).
        Then update self._manual_data['Z_real'] and ['Z_imag'].
        """
        freq_array = self._manual_data['freq']

        # 1) Compute resistor + inductor (in series)
        r_i_real, r_i_imag = self._compute_inductor_and_resistor(freq_array, 'rinf', 'linf')

        # 2) Zarc H
        zarc_h_real, zarc_h_imag = self._compute_zarc_impedance_for_range('rh', 'fh', 'ph', 'ph')

        # 3) Zarc M
        zarc_m_real, zarc_m_imag = self._compute_zarc_impedance_for_range('rm', 'fm', 'pm', 'pm')

        # 4) Zarc L
        zarc_l_real, zarc_l_imag = self._compute_zarc_impedance_for_range('rl', 'fl', 'pl', 'pl')

        # 5) Zarc E (modified) 
        #    if you want it actually combined, you'd do the same approach below:
        zarc_e_real, zarc_e_imag = self._compute_zarc_impedance_for_range('re', 'qe', 'pe_i', 'pe_f')

        # Combine them. Example: element-wise sum of real parts & sum of imaginary parts
        # (Adjust if your actual circuit is not purely series addition.)
        total_real = r_i_real + zarc_h_real + zarc_m_real + zarc_l_real
        total_imag = r_i_imag + zarc_h_imag + zarc_m_imag + zarc_l_imag

        # If you also want to include zarc E in that final sum:
        #   total_real += zarc_e_real
        #   total_imag += zarc_e_imag

        # Store final arrays in the data dictionary
        self._manual_data['Z_real'] = total_real
        self._manual_data['Z_imag'] = total_imag

        # (Optionally update self._manual_data['Z_total'] if needed)
        self._manual_data['Z_total'] = total_real + 1j * total_imag

        # Emit the updated data
        self.manual_model_updated.emit(freq_array, total_real, total_imag)

    # -----------------------------------------------------------------------
    #  Public Interface
    # -----------------------------------------------------------------------
    def initialize_frequencies(self, freq_array):
        """
        Allows the user to change the base frequency array (self._manual_data['freq']) 
        and re-run the model from scratch. Also resets defaults if desired.
        """
        self._manual_data['freq'] = freq_array
        self._set_default_values()
        self._run_model()

    def update_variable(self, key, new_value):
        """
        Update a single variable in the model (e.g., 'rh', 'fh', etc.)
        and re-run the calculation, triggering an update signal.
        """
        if key not in self._variables_dictionary:
            raise KeyError(f"Variable '{key}' not found in the model.")

        self._variables_dictionary[key] = new_value
        self._run_model()
    #MM future tail moving thing
    """
    def set_flag_pe_f(turth_value):
        previos_value=self._flag_pe_f
        
        if(turth_value==False):self._flag_pe_f=False
        if(turth_value==True):self._flag_pe_f=True
        if(previos_value!= self._flag_pe_f):self._run_model()
    """
            


#################################################################################################################################              

"""TEST"""
    
if __name__ == "__main__":
    import sys
    import numpy as np
    from PyQt5.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QTableWidget,
        QTableWidgetItem, QHBoxLayout
    )
    from PyQt5.QtCore import Qt
    from ConfigImporter import ConfigImporter
    from NSlidersWidget import NSlidersWidget

    app = QApplication(sys.argv)

    # 1. Load config
    config_file = "config.ini"
    config = ConfigImporter(config_file)

    # 2. Create the ManualModel instance
    manual_model = ManualModel(
        list(config.slider_configurations.keys()),
        config.slider_default_values
    )

    # 3. Create the NSlidersWidget instance
    sliders_widget = NSlidersWidget(
        config.slider_configurations,
        config.slider_default_values
    )

    # 4. Build the main window and main layout
    test_window = QWidget()
    test_window.setWindowTitle("Test ManualModel - Side-by-side Display")
    test_window.setGeometry(100, 100, 1200, 600)  # Make it a bit wider
    main_layout = QVBoxLayout(test_window)  # Vertical layout

    # Place sliders on top
    main_layout.addWidget(sliders_widget)

    # 5. Create the "Variables" table (Variable, Slider Value, Model Value)
    variables_keys = list(manual_model._variables_dictionary.keys())
    table_vars = QTableWidget(len(variables_keys), 3)
    table_vars.setHorizontalHeaderLabels(["Variable", "Slider Value", "Model Value"])

    # Map each variable to a row index
    row_index_map = {}
    for i, key in enumerate(variables_keys):
        row_index_map[key] = i
        # Column 0: Variable name
        table_vars.setItem(i, 0, QTableWidgetItem(key))
        # Columns 1 & 2: initial slider/model values
        slider_val = str(manual_model._variables_dictionary[key])
        table_vars.setItem(i, 1, QTableWidgetItem(slider_val))
        table_vars.setItem(i, 2, QTableWidgetItem(slider_val))

    # 6. Create an Impedance table with 3 columns: Frequency, Z_real, Z_imag
    freq_array = manual_model._manual_data['freq']
    table_imp = QTableWidget(len(freq_array), 3)
    table_imp.setHorizontalHeaderLabels(["Frequency", "Z_real", "Z_imag"])
    
    # Fill initial values
    for i, f in enumerate(freq_array):
        table_imp.setItem(i, 0, QTableWidgetItem(str(f)))
        table_imp.setItem(i, 1, QTableWidgetItem(str(manual_model._manual_data['Z_real'][i])))
        table_imp.setItem(i, 2, QTableWidgetItem(str(manual_model._manual_data['Z_imag'][i])))
    
    # 7. Create a sub-layout to hold the two tables side by side
    tables_layout = QHBoxLayout()
    tables_layout.addWidget(table_vars)
    tables_layout.addWidget(table_imp)

    # Add the sub-layout to the main layout
    main_layout.addLayout(tables_layout)

    # 8. A helper to refresh the impedance table after each slider move
    def update_impedance_table():
        freqs = manual_model._manual_data['freq']
        z_reals = manual_model._manual_data['Z_real']
        z_imags = manual_model._manual_data['Z_imag']
    
        for i in range(len(freqs)):
            table_imp.setItem(i, 0, QTableWidgetItem(str(freqs[i])))
            table_imp.setItem(i, 1, QTableWidgetItem(str(z_reals[i])))
            table_imp.setItem(i, 2, QTableWidgetItem(str(z_imags[i])))

    # 9. Slot to handle slider_value_updated from NSlidersWidget
    def on_slider_value_updated(key, new_value):
        """
        Updates the ManualModel with the new slider value, then
        displays both the slider value and model value in the variables table,
        and refreshes the impedance table.
        """
        manual_model.update_variable(key, new_value)

        # Update the 'Variables' table
        row = row_index_map[key]
        table_vars.setItem(row, 1, QTableWidgetItem(str(new_value)))
        model_val = str(manual_model._variables_dictionary[key])
        table_vars.setItem(row, 2, QTableWidgetItem(model_val))

        # Update the impedance table with new results
        update_impedance_table()

    # 10. Connect NSlidersWidget signal to the slot
    sliders_widget.slider_value_updated.connect(on_slider_value_updated)

    # 11. Show the test window
    test_window.show()
    sys.exit(app.exec_())