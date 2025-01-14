# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 17:40:39 2024

ModelManual is a widget that calculates combined impedance from:
  - R + jωL (resistor + inductor in series)
  - Zarc circuits (H, M, L)
  - An optional 'modified Zarc' (E) circuit

Emits a signal (modeled_data_updated) whenever it recalculates,
passing the new Z_real and Z_imag arrays.
"""

import numpy as np
import configparser

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal


class Model(QWidget):

    # This signal now carries a dictionary, instead of three np.ndarray
    modeled_data_updated = pyqtSignal(np.ndarray, np.ndarray, np.ndarray)
    modeled_data_variables_updated = pyqtSignal(dict)

    def __init__(self, variables_keys, variables_default_values):
        super().__init__()

        self._variables_keys = variables_keys
        self._variables_default_values = variables_default_values

        # Dictionary storing all slider/settable variable values
        self._variables_dictionary = {key: 0.0 for key in variables_keys}

        # Default frequency data & placeholders for computed impedances
        self._modeled_data = {
            'freq': np.array([1, 10, 100, 1000, 10000]),
            'Z_real': np.array([90, 70, 50, 30, 10]),
            'Z_imag': np.array([-45, -35, -25, -15, -5]),
        }

        self._reset_values(self._variables_default_values)

    # -----------------------------------------------------------------------
    #  Private Helpers
    # -----------------------------------------------------------------------
    def _reset_values(self, variables_values):
        """Assigns default values to each variable (in order) without re-running the model."""
        for key, default_val in zip(self._variables_keys, variables_values):
            self._variables_dictionary[key] = default_val


    # -----------------------------------------------------------------------
    #  Circuit Elements (simulator)
    # -----------------------------------------------------------------------
    """
    Receive Frequency values and the keywords to retrieve the remaining 
    information from the dictionary.
    Return the cmplex impedance of the element
    """
    
    def _inductor(self, freq, l_key):
        l_val = self._variables_dictionary[l_key]
        z_complex = (2 * np.pi * freq) * l_val *1j
        
        return z_complex
        
    def _cpe(self, freq,r_key, f_key, p_i_key, p_f_key):
        r_val = self._variables_dictionary[r_key]
        f_val = self._variables_dictionary[f_key]
        pi_val = self._variables_dictionary[p_i_key]
        pf_val = self._variables_dictionary[p_f_key]
        
        q_val = 1.0 / (r_val * (2.0 * np.pi * f_val)**pf_val)
        phase_factor = (1j)**pi_val
        omega_exp = (2.0 * np.pi * freq)**pf_val
        
        z_complex = 1.0 / (q_val * phase_factor * omega_exp)
        
        return z_complex
    
    def _cpe_q(self, freq, q_key, p_i_key, p_f_key):
        q_val = self._variables_dictionary[q_key]
        pi_val = self._variables_dictionary[p_i_key]
        pf_val = self._variables_dictionary[p_f_key]
        
        phase_factor = (1j)**pi_val
        omega_exp = (2.0 * np.pi * freq)**pf_val
        
        z_complex = 1.0 / (q_val * phase_factor * omega_exp)
        
        return z_complex
    
    def _parallel_circuit(self,z_1, z_2):
        return (z_1 * z_2) / (z_1 + z_2)
  
    # -----------------------------------------------------------------------
    #  Model (simulator)
    # -----------------------------------------------------------------------

    def _model(self,freq):
        pass
        

    def _run_model(self):
        """
        runs the model for every frequency in frequency array
        resets the model
        EMITS signal with the new modeled data
        """
        
        z_real=[]
        z_imag=[]         

        freq_array = self._modeled_data['freq']
        
        for freq in freq_array:
            z_complex=self._model(freq)
            
            z_real.append(np.real(z_complex))
            z_imag.append(np.imag(z_complex))
            
        z_real=np.array( z_real)
        z_imag=np.array(z_imag)
        
        self._modeled_data['Z_real'] =z_real
        self._modeled_data['Z_imag'] =z_imag

        # Emit the updated impedance arrays
        self.modeled_data_updated.emit(freq_array, z_real, z_imag)

    # -----------------------------------------------------------------------
    #  Public Interface
    # -----------------------------------------------------------------------
    
    ##MM maybe delete and limit to the manual model
    def initialize_frequencies(self, freq_array):
        """
        Replaces 'freq' in self._modeled_data, resets default values, and re-runs the model.
        """
        self._modeled_data['freq'] = freq_array
        self._reset_values(self._variables_default_values)
        self._run_model()


    def listen_change_variables_signal(self, dictionary):
        """
        Updates the entire variable dictionary from an external source.
        If the incoming dict's keys don't match this model's keys, raise an error.
        Otherwise, reset self._variables_dictionary to the new values
        """
        # 1) Check key consistency
        if set(dictionary.keys()) != set(self._variables_keys):
            raise ValueError(
                "Incoming dictionary keys do not match the model's variable keys."
            )

        # 2) Update the internal variables to match
        for k in dictionary:
            self._variables_dictionary[k] = dictionary[k]


    def emit_modeled_data_variables_updated(self):
        """
        Emits the entire self._variables_dictionary as a Python dict,
        satisfying the modeled_data_variables_updated signature of type dict.
        """
        # Create a shallow copy or just pass self._variables_dictionary if you prefer
        variables_copy = dict(self._variables_dictionary)
        self.modeled_data_variables_updated.emit(variables_copy)
        
    def print_model_parameters(self):
        """
        Emits the entire self._variables_dictionary as a Python dict,
        satisfying the modeled_data_variables_updated signature of type dict.
        """
        return self._variables_dictionary.values(),self._variables_dictionary.keys()
        




#########################################################################


class ModelManual(Model):

    def __init__(self, variables_keys, variables_default_values):
        super().__init__(variables_keys, variables_default_values)
  
    # -----------------------------------------------------------------------
    #  Model (simulator)
    # -----------------------------------------------------------------------

    def _model(self,freq):
        
        # 1. An inductor and a resistor in series
        inductor=self._inductor(freq, l_key='linf')
        resistor=self._variables_dictionary['rinf']
        
        z1_complex=inductor+resistor
        
        # 2. a parallel CPE-R for high frequency
        
        cpe_h=self._cpe(freq,r_key='rh', f_key='fh', p_i_key='ph', p_f_key='ph')
        resistor_h=self._variables_dictionary['rh']
        
        z2_complex=self._parallel_circuit(cpe_h,resistor_h)
        
        # 3. a parallel CPE-R for medium frequency
        cpe_m=self._cpe(freq,r_key='rm', f_key='fm', p_i_key='pm', p_f_key='pm')
        resistor_m=self._variables_dictionary['rm']
        
        z3_complex=self._parallel_circuit(cpe_m,resistor_m)
        
        # 4. a parallel CPE-R for low frequency
        cpe_l=self._cpe(freq,r_key='rl', f_key='fl', p_i_key='pl', p_f_key='pl')
        resistor_l=self._variables_dictionary['rl']
        
        z4_complex=self._parallel_circuit(cpe_l,resistor_l)
        
        # 5. a modified CPE-R 
        cpe_e=self._cpe_q(freq, q_key='qe', p_i_key='pe_i', p_f_key='pe_f')
        resistor_e=self._variables_dictionary['re']
        
        z5_complex=self._parallel_circuit(cpe_e,resistor_e)
        
        #All of them in series
        z_total_complex = z1_complex + z2_complex + z3_complex + z4_complex + z5_complex
        
        return z_total_complex
    
    # -----------------------------------------------------------------------
    #  Public Interface
    # -----------------------------------------------------------------------

    def update_variable(self, key, new_value):
        """
        Updates one variable in _variables_dictionary, re-runs the model,
        and emits the new data. Also emits modeled_data_variables_updated
        to indicate that variables have changed.
        """
        if key not in self._variables_dictionary:
            raise KeyError(f"Variable '{key}' not found in the model.")

        self._variables_dictionary[key] = new_value
        self.emit_modeled_data_variables_updated()
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
    modeled_data = ModelManual(
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
    variables_keys = list(modeled_data._variables_dictionary.keys())
    table_vars = QTableWidget(len(variables_keys), 3)
    table_vars.setHorizontalHeaderLabels(["Variable", "Slider Value", "Model Value"])

    row_index_map = {}
    for i, key in enumerate(variables_keys):
        row_index_map[key] = i
        table_vars.setItem(i, 0, QTableWidgetItem(key))
        slider_val = str(modeled_data._variables_dictionary[key])
        table_vars.setItem(i, 1, QTableWidgetItem(slider_val))
        table_vars.setItem(i, 2, QTableWidgetItem(slider_val))

    # Impedance table: freq, Z_real, Z_imag
    freq_array = modeled_data._modeled_data['freq']
    table_imp = QTableWidget(len(freq_array), 3)
    table_imp.setHorizontalHeaderLabels(["Frequency", "Z_real", "Z_imag"])

    for i, f in enumerate(freq_array):
        table_imp.setItem(i, 0, QTableWidgetItem(str(f)))
        table_imp.setItem(i, 1, QTableWidgetItem(str(modeled_data._modeled_data['Z_real'][i])))
        table_imp.setItem(i, 2, QTableWidgetItem(str(modeled_data._modeled_data['Z_imag'][i])))

    # Combine tables side by side
    tables_layout = QHBoxLayout()
    tables_layout.addWidget(table_vars)
    tables_layout.addWidget(table_imp)
    main_layout.addLayout(tables_layout)

    def update_impedance_table():
        freqs = modeled_data._modeled_data['freq']
        z_reals = modeled_data._modeled_data['Z_real']
        z_imags = modeled_data._modeled_data['Z_imag']

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
        modeled_data.update_variable(key, new_value)

        row = row_index_map[key]
        table_vars.setItem(row, 1, QTableWidgetItem(str(new_value)))
        model_val = str(modeled_data._variables_dictionary[key])
        table_vars.setItem(row, 2, QTableWidgetItem(model_val))

        # Refresh impedance table
        update_impedance_table()

    sliders_widget.slider_value_updated.connect(on_slider_value_updated)

    test_window.show()

    
    modeled_data.modeled_data_variables_updated.connect(print)
    modeled_data.emit_modeled_data_variables_updated()
    
    sys.exit(app.exec_())