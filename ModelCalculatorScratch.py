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

import sys
import numpy as np
import scipy.optimize as opt

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt

import pyqtgraph as pg


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
"""
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

"""

#this test is garbaje, I need to redo the entire thing
class FitCalculatorTest(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fit Calculator")
        self.resize(800, 600)

        # Initialize FitCalculator
        self.calculator = FitCalculator()

        # Initialize UI components
        self.init_ui()

        # Generate and set experimental data
        self.generate_experimental_data()

        # Perform initial fit and plot
        self.perform_fit_and_plot()

    def init_ui(self):
        """
        Initializes the user interface components.
        """
        layout = QVBoxLayout()

        # Initialize PyQtGraph PlotWidget
        self.plot_widget = pg.PlotWidget(title="Experimental Data vs. Fit Model")
        self.plot_widget.setLabel('left', 'Experimental Data')
        self.plot_widget.setLabel('bottom', 'Frequency')
        self.plot_widget.addLegend()

        # Add PlotWidget to the layout
        layout.addWidget(self.plot_widget)

        # Initialize Re-Fit button
        self.refit_button = QPushButton("Re-Fit")
        self.refit_button.setFixedHeight(40)
        self.refit_button.clicked.connect(self.on_refit)

        # Add button to the layout
        layout.addWidget(self.refit_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def generate_experimental_data(self):
        """
        Generates synthetic experimental data for testing.
        """
        # True parameters
        self.v1_true = 2
        self.v2_true = 0.5
        self.v3_true = 4

        # Generate frequencies
        self.frequencies = np.linspace(0, 10, 50)  # 50 frequency points

        # Generate experimental data with noise
        self.experimental_data = (
            self.v1_true * np.sin(self.v2_true * self.frequencies) +
            np.random.uniform(0, 2, 50) +
            self.v3_true * np.random.randn(50)
        )

        # Set experimental values in FitCalculator
        self.calculator.set_experimental_values(self.frequencies, self.experimental_data)

        # Plot experimental data
        self.plot_widget.plot(
            self.frequencies, self.experimental_data,
            pen=pg.mkPen(color='b', width=2),
            name="Experimental Data"
        )

    def perform_fit_and_plot(self):
        """
        Performs the fitting process and plots the fit results.
        """
        # Initial guess for parameters (v0, v1, v2)
        initial_guess = [1.0, 1.0, 1.0]

        try:
            # Perform the fit
            best_fit_params = self.calculator.fit_model(initial_guess)
            print("Optimized parameters:", best_fit_params)

            # Compute final cost
            final_cost = self.calculator._cost_function(best_fit_params)
            print("Final cost:", final_cost)

            # Generate fit data using the optimized parameters
            fit_data = self.calculator._equation(best_fit_params, self.frequencies)

            # Plot fit data
            self.plot_widget.plot(
                self.frequencies, fit_data,
                pen=pg.mkPen(color='r', width=2),
                name="Fit Model"
            )

        except (ValueError, RuntimeError) as e:
            QMessageBox.critical(self, "Fitting Error", str(e))

    def on_refit(self):
        """
        Slot for handling Re-Fit button clicks.
        """
        # Clear previous fit data (assuming it's the second plot)
        self.plot_widget.clearPlots()

        # Re-plot experimental data
        self.plot_widget.plot(
            self.frequencies, self.experimental_data,
            pen=pg.mkPen(color='b', width=2),
            name="Experimental Data"
        )

        # Perform fit and plot again
        self.perform_fit_and_plot()


################################
# TESTING
################################

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Instantiate and show the FitCalculatorWidget
    window = FitCalculatorTest()
    window.show()

    sys.exit(app.exec_())






