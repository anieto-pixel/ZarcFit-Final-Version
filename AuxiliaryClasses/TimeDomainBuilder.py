# -*- coding: utf-8 -*-
"""
Created on Wed Mar  5 12:36:22 2025

@author: agarcian
"""
import numpy as np
import scipy.signal as sig
from scipy.interpolate import interp1d
from scipy.interpolate import PchipInterpolator
from PyQt5.QtCore import QCoreApplication, QObject, pyqtSignal
from ModelCircuits import ModelCircuitParent, ModelCircuitParallel, ModelCircuitSeries

    
###############################################################################
# v/t class
###############################################################################
#3ensure that exp dat ahas the right keywords, else have a catch or something
class TimeDomainBuilder(QObject):
    
    def __init__(self, model_circuit) -> None:
        
        super().__init__() 
        self.N = 2 ** 10
        self.T = 4
        self.model_circuit = model_circuit  
        self._integral_variables = {}
        
    #-------------------------------------------    
    #   Public Methods
    #-----------------------------------------------
    def get_integral_variables(self):
        return self._integral_variables
    
    def set_model_circuit(self, model_circuit):
        self.model_circuit=model_circuit

    def run_time_domain(self, params: dict, model_circuit: ModelCircuitParent):
        """
        Calculate time-domain values using a real IFFT.
        """ 
        n_freq = (self.N // 2) #+1
        
        dt = self.T / self.N
        df = 1.0 / self.T

        fmin   = 0
        fmax   = n_freq / self.T
        freq_even = np.linspace(fmin, fmax, int(n_freq + 1))
        freq_even[0] = 0.001

        z_complex = model_circuit.run_rock(params, freq_even)
        t, volt_down, volt_up=self._fourier_transform(z_complex, dt)       
        
        self._integration_variables(t, volt_down)
        
        index = np.searchsorted(t, self.T//2)
        return freq_even[:index+1], t[:index+1], volt_down[:index+1], volt_up[:index+1]

    def transform_to_time_domain(self,experiment_data):
        """
        Transform experimental data to the time domain.
        """
        n_freq = (self.N // 2) #+1
        prune= 10 #will only use every 10th element of the array
                #reason beign extrapolate works poorly with size differences
        dt = self.T / (self.N/prune)
        #df = 1.0 / self.T

        fmin   = 0
        fmax   = n_freq / self.T
        freq_even = np.linspace(fmin, fmax, int(n_freq + 1))
        freq_even[0] = 0.001

        freq_even = freq_even[::prune]
              
        z_interp = self._interpolate_points_for_time_domain(freq_even, experiment_data)
        t, volt_down, volt_up=self._fourier_transform(z_interp, dt)   
        
        index = np.searchsorted(t, self.T//2)
        return freq_even[:index+1], t[:index+1], volt_down[:index+1] 
    
    #--------------------------------------
    #   Private Methods
    #------------------------------------------
    def _interpolate_points_for_time_domain(self, freqs_even: np.ndarray, experiment_data) -> np.ndarray:
        """
        Interpolate measured impedance data for the time-domain transform.
        """
        print("in the method")
        freq   = experiment_data["freq"]
        z_real = experiment_data["Z_real"]
        z_imag = experiment_data["Z_imag"]
    
        print(len(freqs_even))
        print(len(freq))
    
        # Create interpolation functions that extrapolate outside the measured range.
        interp_real = interp1d(freq, z_real, kind="linear", fill_value="extrapolate")
        interp_imag = interp1d(freq, z_imag, kind="linear", fill_value="extrapolate")
    
#        interp_real = PchipInterpolator(freq, z_real, extrapolate=True)
#        interp_imag = PchipInterpolator(freq, z_imag, extrapolate=True)
    
        # Evaluate the interpolants at the uniformly spaced frequencies.
        z_real_interp = interp_real(freqs_even)
        z_imag_interp = interp_imag(freqs_even)

        return z_real_interp + 1j * z_imag_interp

    def _fourier_transform(self, z_complex: np.ndarray, dt: float):
        """
        Build the single-sided array for IRFFT and perform a real IFFT.
        """       
        b, a = sig.butter(2, 0.45) 
        z_inversefft = np.fft.irfft(z_complex)       #to transform the impedance data from the freq domain to the time domain.
                   #largest value is 0.28       
        z_inversefft = sig.filtfilt(b, a, z_inversefft)   #Applies filter
        t = np.arange(len(z_inversefft)) * dt  # constructs time based on N and dt
 
        volt_up = np.concatenate(([0], np.cumsum(z_inversefft)[:-1]))
        
        time_to_plot_in_seconds=2
        
        index = np.searchsorted(t, time_to_plot_in_seconds, side="right")
        volt_down = volt_up[index]-volt_up
        
        return t, volt_down, volt_up

    def _integration_variables(self, t, v_down):
        
        keys=['V(.1ms)',	'V(1ms)', 'V(10)',	'V(100)','V(200)',	'V(400)',	'V(800)',	'V(1.2s)', 'V(1.6s)']
        seconds=[0.0001,	0.001, 0.01,	0.1, 0.2, 0.4, 0.8, 1.2, 1.6]
        
        for key, mili in zip (keys, seconds):
            index = np.searchsorted(t, mili)
            self._integral_variables[key]=v_down[index]
            

###############################################################################
#   Test    
###############################################################################

def manual_test_time_domain_builder():
    # Create dummy experimental data with proper comma-separated values.
    experiment_data = {
        "freq": np.array([
            1.000000e+06, 6.309573e+05, 3.981072e+05, 2.511886e+05, 1.584893e+05,
            1.000000e+05, 6.309573e+04, 3.981072e+04, 2.511886e+04, 1.584893e+04,
            1.000000e+04, 6.309573e+03, 3.981072e+03, 2.511886e+03, 1.584893e+03,
            1.000000e+03, 6.309573e+02, 3.981072e+02, 2.511886e+02, 1.584893e+02,
            1.000000e+02, 6.309573e+01, 3.981072e+01, 2.511886e+01, 1.584893e+01,
            1.000000e+01, 6.309570e+00, 3.981070e+00, 2.511890e+00, 1.584890e+00,
            1.000000e+00, 6.309600e-01, 3.981100e-01, 2.511900e-01, 1.584900e-01,
            1.000000e-01, 6.310000e-02, 3.981000e-02, 2.512000e-02
        ]),
        "Z_real": np.array([
            1.0763e+02, 2.0519e+04, 4.8548e+04, 7.8712e+04, 1.0673e+05, 1.3059e+05,
            1.4836e+05, 1.6278e+05, 1.7341e+05, 1.8115e+05, 1.8669e+05, 1.9064e+05,
            1.9337e+05, 1.9526e+05, 1.9661e+05, 1.9761e+05, 1.9828e+05, 1.9884e+05,
            1.9873e+05, 1.9911e+05, 1.9952e+05, 1.9988e+05, 2.0018e+05, 2.0053e+05,
            2.0080e+05, 2.0110e+05, 2.0137e+05, 2.0170e+05, 2.0195e+05, 2.0226e+05,
            2.0254e+05, 2.0203e+05, 2.0129e+05, 1.9920e+05, 1.9697e+05, 1.9693e+05,
            1.8791e+05, 1.7427e+05, 1.5851e+05
        ]),
        "Z_imag": np.array([
            -45733., -64038., -75276., -78069., -74085., -65870., -55162.,
            -45225., -36187., -28267., -21743., -16562., -12605., -9640.6,
            -7456.1, -5872.2, -4832.8, -4039.6, -3664.1, -3201.4, -2891.4,
            -2671.6, -2484.6, -2362., -2258.3, -2165.2, -2070.5, -1984.7,
            -1891.1, -1813.2, -1698.9, -1635.1, -1541.4, -1485.5, -1316.4,
            -1366.5, -1010.3, -842.82, -271.75
        ]),
    }
    

if __name__ == '__main__':
    manual_test_time_domain_builder()

