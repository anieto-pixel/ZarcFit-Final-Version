# -*- coding: utf-8 -*-
"""
Created on Fri Jan  3 15:42:43 2025

@author: agarcian
"""
import numpy as np
import configparser

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal

# Updated imports (class name changes)
from WidgetSliders import WidgetSliders
from CustomSliders import EPowerSliderWithTicks, DoubleSliderWithTicks
from ConfigImporter import ConfigImporter


class ModelCalculator(QWidget):

    model_calculator_updated = pyqtSignal(np.ndarray, np.ndarray, np.ndarray)
    model_calculator_variables_updated = pyqtSignal(#dictionary or list, to be determined
                                                    )

    def __init__(self, variables_keys, variables_default_values):
        
        super().__init__()

        self._variables_keys = variables_keys
        self._variables_default_values = variables_default_values
        #MM no real need to save default values for this guy

        # Dictionary storing all slider/settable variable values
        self._variables_dictionary = {key: 0.0 for key in variables_keys}

        # Default frequency data & placeholders for computed impedances
        self._manual_data = {
            'freq': np.array([1, 10, 100, 1000, 10000]),
            'Z_real': np.array([90, 70, 50, 30, 10]),
            'Z_imag': np.array([-45, -35, -25, -15, -5]),
        }

        self._reset_values(self._variables_default_values)
        
    # -----------------------------------------------------------------------
    #  Private Helpers
    # -----------------------------------------------------------------------
    
    def _reset_values(self, variables_values):
        """
        Assigns values to each variable and resets the model.
        """
        
        for key, val in zip(self._variables_keys, variables_values):
            self._variables_dictionary[key] = val
            
        ##MM And then right after call run model, or not bother?
        #Can cause issues (small) at initialziaiton if I do but it is covnenient
    
    def _emit_variable_values(self):
        """
        when the values of the variables are changed, it sends a
        dictionary/list of the new values as a signal

        """
        pass
    
    def _run_model(self):
        """
        Generates a more sophisticated model using the variables given.
        Then at the end it emmits it's signal with the "conclussions" of the model'
        
        Interactua con el optimizador de algun modo que no tengo claro
             
        """
        #self._manual_data['Z_real'] = total_real
        #self._manual_data['Z_imag'] = total_imag

        # Emit
        #self.model_calculator_updated.emit(freq_array, total_real, total_imag)
        
        pass
    
    def _square_optimization(self):
        """
        no clue
             
        """
             
        pass
    
    
    
    def return_variables_expanded(self):
        """
        The weird print method I copied from Josh.
        Sends all the information Randy wants printed
        I need to figure out how to send it/print it in the adequate 
        format for the output-er to be able to print it. 
        Not sure of how I am going to handle the 
        """
       

        
        pass

    
            
            
            