# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 17:40:39 2024

@author: agarcian
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QPainter, QFont, QColor 

import numpy as np

class ManualModel():
    
    manual_model_updated = pyqtSignal(np.ndarray, np.ndarray)

    
    def __init__(self, slider_configurations, ):
        super().__init__()
        #make a dictionary with this variables
        self._variables_dictionary = {
            
            }
        
        #define a signal that indicates that the model has been updated
        #that re-sends the Z' and Z'' of it
        
        
        
        self._linf=None
        self._rinf=None
        
        self._rh=None
        self._fh=None
        self._ph=None
        
        self._rm=None
        self._fm=None
        self._pm=None
        
        self._rl=None
        self._fl=None
        self._pl=None
        
        self._re=None
        self._qe=None
        self._pe_f=None
        self._pe_i=None


        #resultados de los calculos. default frequencies? 
        #frequencies subidas desde input file? probablemente si
        self._manual_data = {
            'freq': np.array([1, 10, 100, 1000, 10000]),
            'Z_real': np.array([90, 70, 50, 30, 10]),
            'Z_imag': np.array([-45, -35, -25, -15, -5]),
        } #not sure of how the frequency would go here
        
    def _run_model():
        #Runs the pretend model and the equations it implies
        #sends signal?
        pass
        
        
    #public method
    def update_variable(key, new_value):
        #you give it a keyword and it updates the matching variable
        #to the new value
        #it calls to recalculate the model
        
        pass
    