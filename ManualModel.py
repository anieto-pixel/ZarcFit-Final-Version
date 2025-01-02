# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 17:40:39 2024

@author: agarcian
"""

#MM
#This class ahs a level of coupling and specificity for the  name of the variables is not ideal. 
#Maybe I shoudl reconsider and define the slider values and everything here?

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal
import numpy as np

class ManualModel(QWidget):
    manual_model_updated = pyqtSignal(np.ndarray, np.ndarray, np.ndarray)

    def __init__(self, variables_keys, variables_default_values):
        super().__init__()
        self._variables_dictionary = {key: 0.0 for key in variables_keys}
        self._variables_keys = variables_keys
        self._variables_default_values = variables_default_values

        # Default frequency data
        self._manual_data = {
            'freq': np.array([1, 10, 100, 1000, 10000]),
            'Z_real': np.array([90, 70, 50, 30, 10]),
            'Z_imag': np.array([-45, -35, -25, -15, -5]),
        }

        # Set default values
        self._set_default_values()

    def _calculate_Zarc(self, frec, r, fo, p):
        """
        Calculate the real and imaginary components of impedance for a Zarc circuit.
        """
        omega = 2 * np.pi * frec
        omega_h = 2 * np.pi * fo
        Q = 1 / (omega_h ** p)  # CPE scaling constant approximation

        Z_cpe_mag = 1 / (Q * omega ** p)
        Z_cpe_real = Z_cpe_mag * np.cos(-np.pi * p / 2)
        Z_cpe_imag = Z_cpe_mag * np.sin(-np.pi * p / 2)

        Z_real = 1 / (1 / r + 1 / Z_cpe_real)
        Z_imag = 1 / (1 / Z_cpe_imag)

        return Z_real, Z_imag

    def _run_model(self):
        """
        Updates Z_real and Z_imag based on the current frequencies
        and the sum of the variable dictionary values.
        """
        
        ##MM
        ##I don't like this logic for the upcoming 2 zark elements that are still meant to ge involved
        
        Z_real_combined = []
        Z_imag_combined = []

        # Process high (h), medium (m), and low (l) components
        for prefix in ['h', 'm', 'l']:
            r_key = f"r{prefix}"
            f_key = f"f{prefix}"
            p_key = f"p{prefix}"

            if r_key in self._variables_dictionary and f_key in self._variables_dictionary and p_key in self._variables_dictionary:
                r = self._variables_dictionary[r_key]
                f = self._variables_dictionary[f_key]
                p = self._variables_dictionary[p_key]

                Z_real, Z_imag = zip(*[
                    self._calculate_Zarc(freq, r, f, p)
                    for freq in self._manual_data['freq']
                ])

                Z_real_combined.extend(Z_real)
                Z_imag_combined.extend(Z_imag)

        # Update manual data
        self._manual_data['Z_real'] = np.array(Z_real_combined) #+self._variables_dictionary["rinf"]
        self._manual_data['Z_imag'] = np.array(Z_imag_combined) #+self._variables_dictionary["linf"]

        # Emit the updated data
        self.manual_model_updated.emit(
            self._manual_data['freq'],
            self._manual_data['Z_real'],
            self._manual_data['Z_imag'],
        )

    def _set_default_values(self):
        """
        Sets the variables to the default values.
        """
        for key, default_value in zip(self._variables_keys, self._variables_default_values):
            self._variables_dictionary[key] = default_value

    def initialize_frequencies(self, freq_array):
        """
        Initializes the frequency array and re-runs the model calculations.
        """
        self._manual_data['freq'] = freq_array
        self._set_default_values()  # Optionally reset variables to defaults
        self._run_model()

    def update_variable(self, key, new_value):
        """
        Updates a variable in the dictionary and re-runs the model.
        """
        if key in self._variables_dictionary:
            self._variables_dictionary[key] = new_value
            self._run_model()
        else:
            raise KeyError(f"Variable '{key}' not found in the model.")
            
        #test method
        def print_manual_value(self):
            print(self._manual_data)

