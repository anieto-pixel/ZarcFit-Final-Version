# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 17:40:39 2024

@author: agarcian
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal
import numpy as np

class ManualModel(QWidget):
    # Signal emitted every time the model is run
    manual_model_updated = pyqtSignal(np.ndarray, np.ndarray, np.ndarray)

    def __init__(self, variables_keys):
        super().__init__()
        # Initialize a dictionary with variables
        self._variables_dictionary = {key: 0.0 for key in variables_keys}

        # Default frequency data (can be replaced with input file frequencies)
        self._manual_data = {
            'freq': np.array([1, 10, 100, 1000, 10000]),
            'Z_real': np.array([90, 70, 50, 30, 10]),
            'Z_imag': np.array([-45, -35, -25, -15, -5]),
        }

    def initialize_frequencies(self, freq_array):
        """
        Initializes the frequency array and re-runs the model calculations.
        """
        
        self._manual_data['freq'] = freq_array
        self._run_model()

    def _run_model(self):
        """
        Updates Z_real and Z_imag based on the current frequencies
        and the sum of the variable dictionary values.
        """
        
        total_offset = sum(self._variables_dictionary.values())
        self._manual_data['Z_real'] = self._manual_data['freq'] + total_offset
        self._manual_data['Z_imag'] = self._manual_data['freq'] + total_offset

        # Emit the updated data
        self.manual_model_updated.emit(
            self._manual_data['freq'],
            self._manual_data['Z_real'],
            self._manual_data['Z_imag'],
        )

    def update_variable(self, key, new_value):
        """
        Updates a variable in the dictionary and re-runs the model.
        """
        if key in self._variables_dictionary:
            self._variables_dictionary[key] = new_value
            self._run_model()
        else:
            raise KeyError(f"Variable '{key}' not found in the model.")

    