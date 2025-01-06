# -*- coding: utf-8 -*-
"""
Created on Mon Jan  6 11:05:03 2025

@author: agarcian
"""

#get the variables dictionary

#get or have the model already

#make the fit

#return the fit and the variables

#modle will be passed as a method-variable so it can be passed from outside

import numpy as np
import configparser
import scipy.optimize as opt


class FitCalculator:
    
    def __init__(self):
        self._frequencies = np.array([])
        self._experimental_datapoints = np.array([])
            
    def _equation(self, v, freq):
        
        if len(v) < 3:
            raise ValueError("Insufficient parameters in vector v.")
        else:
            # Corrected variable from 'frequencies' to 'freq'
            result = v[0] * np.sin(v[1] * freq) + 1 + v[2]
            # Alternative equation:
            # result = (v[0]**2) * freq + v[1] * freq + v[2]
            return result

    def _cost_function(self, v):
        # Use instance variables instead of passing them as parameters
        eq_y = np.array([self._equation(v, f) for f in self._frequencies])
        difference_array = (eq_y - self._experimental_datapoints) ** 2
        difference_sum = np.sum(difference_array)
        return difference_sum
        
    ############################  
    # Public Methods   
    ############################  
          
    def fit_model(self, initial_guess, equation=None):
        

        if (self._frequencies.size == 0 or self._experimental_datapoints.size == 0):
            raise ValueError("Frequencies and experimental datapoints must be set before fitting the model.")

        if equation ==None:
            print("You are fitting to the default equation")
            equation=self._equation  # Optionally replace the equation

        
        # Use 'opt.minimize' instead of 'minimize'
        result = opt.minimize(
            self._cost_function,
            x0=initial_guess,
            method='Nelder-Mead'
        )
        
        if not result.success:
            
            print("Optimization failed:", result.message)
            raise RuntimeError("Optimization did not converge.")
        
        best_fit_params = result.x

        return best_fit_params
        
    def set_experimental_values(self, frequencies, experimental_datapoints):
        
        if len(experimental_datapoints) != len(frequencies):
            raise ValueError("Length of experimental datapoints must match length of frequencies.")
        
        else:
            self._frequencies = frequencies
            self._experimental_datapoints = experimental_datapoints
            
        
################################
# TESTING
################################

if __name__ == "__main__":
    
    # Fake data and arbitrary variables for testing
    v1 = 2
    v2 = 0.5
    v3 = 4
    
    frequencies = np.linspace(0, 10, 50)  # 50 frequency points
    experimental_data = v1 * np.sin(v2 * frequencies) + np.random.uniform(0, 2, 50) + v3 * np.random.randn(50)
    
    # Initial guess for parameters (v0, v1, v2)
    initial_guess = [1.0, 1.0, 1.0]  
    
    # Instantiate FitCalculator
    calculator = FitCalculator()
    
    # Set experimental values
    calculator.set_experimental_values(frequencies, experimental_data)
    
    
    # Fit model using Nelder-Mead
    try:
        best_fit_params = calculator.fit_model(initial_guess)
        print("Optimized parameters:", best_fit_params)
        # Compute final cost
        final_cost = calculator._cost_function(best_fit_params)
        print("Final cost:", final_cost)
    except (ValueError, RuntimeError) as e:
        print("An error occurred during fitting:", e)
