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
        freq   = experiment_data["freq"]
        z_real = experiment_data["Z_real"]
        z_imag = experiment_data["Z_imag"]
    
    
        # Create interpolation functions that extrapolate outside the measured range.
        interp_real = interp1d(freq, z_real, kind="linear", fill_value="extrapolate")
        interp_imag = interp1d(freq, z_imag, kind="linear", fill_value="extrapolate")
    
#        interp_real = PchipInterpolator(freq, z_real, extrapolate=True)
#        interp_imag = PchipInterpolator(freq, z_imag, extrapolate=True)
    
        # Evaluate the interpolants at the uniformly spaced frequencies.
        z_real_interp = interp_real(freqs_even)
        z_imag_interp = interp_imag(freqs_even)

        return z_real_interp + 1j * z_imag_interp
        """
       
        freq   = np.array(experiment_data["freq"])
        z_real = np.array(experiment_data["Z_real"])
        z_imag = np.array(experiment_data["Z_imag"])
    
        # 1) Remove any freq <= 0
        valid_mask = freq > 0
        freq   = freq[valid_mask]
        z_real = z_real[valid_mask]
        z_imag = z_imag[valid_mask]
    
        # 2) Sort by ascending freq
        sort_idx = np.argsort(freq)
        freq   = freq[sort_idx]
        z_real = z_real[sort_idx]
        z_imag = z_imag[sort_idx]
    
        # 3) Remove duplicates (if you have any)
        unique_mask = np.diff(freq, prepend=-np.inf) != 0
        freq   = freq[unique_mask]
        z_real = z_real[unique_mask]
        z_imag = z_imag[unique_mask]
    
        # 4) Create log space for your data
        log_freq_data = np.log10(freq)
        log_freq_even = np.log10(freqs_even)
    
        # 5) Build PCHIP interpolators
        pchip_real = PchipInterpolator(log_freq_data, z_real, extrapolate=True)
        pchip_imag = PchipInterpolator(log_freq_data, z_imag, extrapolate=True)
    
        z_real_interp = pchip_real(log_freq_even)
        z_imag_interp = pchip_imag(log_freq_even)
    
        return z_real_interp + 1j * z_imag_interp
          """      
        
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
            
