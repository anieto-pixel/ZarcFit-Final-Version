# -*- coding: utf-8 -*-
"""
Created on Wed Feb 12 14:03:54 2025

@author: agarcian
"""

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
import scipy.signal as sig
from scipy.signal import hilbert

# ---------------------- 2) Compute Exponential Charging Curve ----------------------

V_max = 5.0    # Final voltage (steady-state)
tau = 0.1      # Time constant
t_array = np.linspace(0, 5 , 2**8)  # Time array (5τ covers ~99.3% of charging)

# Compute exponential charging curve
v_charge = V_max * (np.exp(-t_array / tau))

# -------------------------------------------
#print(len(v_charge))

v_transformed=np.fft.rfft(v_charge) #half a plot

#0.001 from 

# --------------------------------------------

v_charge2 = np.fft.irfft(v_transformed)

# --------------------------------------------
# ------Trying the other way arround-----------------

N=2**8
T=4
dt=T/N
nyquist_f=1/(2*dt)


q = 10**-2
pf = 0.5
pi = 0.5
r = 10.0 

def cpe(freq, q, pf, pi):
    """Returns the impedance of a CPE for a given frequency."""
    if q == 0:
        raise ValueError("Parameter q cannot be zero.")
    if freq < 0:
        raise ValueError("Frequency must be non-negative for CPE model.")
    if freq == 0 and pf > 0:
        raise ValueError("freq=0 and pf>0 results in division by zero in CPE.")
    if freq == 0 and pf < 0:
        raise ValueError("freq=0 and pf<0 is undefined (0 to a negative power).")
    phase_factor = (1j) ** pi
    omega_exp = (2.0 * np.pi * freq) ** pf
    return 1.0 / (q * phase_factor * omega_exp)

def parallel(z1, z2):
    """Returns the impedance of two parallel components."""
    if z1 == 0 or z2 == 0:
        raise ValueError("Cannot take parallel of impedance 0 (=> infinite admittance).")
    return 1.0 / ((1.0 / z1) + (1.0 / z2))

#IDEA 1 OFF, USE LOG SPACING INSTEAD
#freq_even = np.logspace(-2, np.log10(500), int(N/2)) 
freq_even = np.linspace(10**-2, 500, int(N/2))

z_real_func = []
z_imag_func = [] 
zarc_list_func = []  # Store impedance values
       
for freq in freq_even:
    zcpe_func = cpe(freq, q, pf, pi)
    zarc_func = parallel(zcpe_func, r)  # Computed impedance for this freq
    zarc_list_func.append(zarc_func)
    z_real_func.append(zarc_func.real)
    z_imag_func.append(-zarc_func.imag)

# --------------------------------------------
print(len(zarc_list_func))

#IDEA 2 OFF. MODIFICATION: Normalize IFFT properly
#v_maybe = np.fft.irfft(zarc_list_func, n=N)
#v_maybe /= dt  # Normalize by time step
v_maybe=np.fft.irfft(zarc_list_func.copy()) #half a plot

#IDEA3 ON FILTER
b, a = sig.butter(2, 0.45, fs=1)
v_maybe = sig.filtfilt(b, a, v_maybe)

#IDEA4 OFF MODIFICATION: Generate Correct Time Axis
#t_actual = np.linspace(0, T, len(v_maybe))
print(len(v_maybe)) 
t_actual = np.arange(len(v_maybe)) * dt

#MODIFICATION: Compute cumulative integral to get the step response
#Vm = np.sum(v_maybe * dt)  # Compute max voltage for normalization
#dV = v_maybe * dt  # Discrete integration
#v_step_response = np.cumsum(dV)  # Cumulative sum for integral

# Normalize step response
#v_step_response = 1 - v_step_response / Vm  

# --------------------------------------------


jv_maybe = np.fft.irfft(zarc_list_func, n=N)
jv_maybe /= dt  # Normalize by time step

b, a = sig.butter(2, 0.45, fs=1)
jv_maybe = sig.filtfilt(b, a, jv_maybe)

print(len(jv_maybe))

jt_actual = np.linspace(0, T, len(jv_maybe))

Vm = np.sum(jv_maybe * dt)  # Compute max voltage for normalization
dV = jv_maybe * dt  # Discrete integration
v_step_response = np.cumsum(dV)  # Cumulative sum for integral

# Normalize step response
v_step_response = 1 - v_step_response / Vm  

integration_indices = np.where((jt_actual >= 0.45) & (jt_actual <= 1.1))[0]
jt_integrated = jt_actual[integration_indices]
v_integrated = v_step_response[integration_indices]
integrated_area = np.trapz(v_integrated, jt_integrated)

print(f"Integrated Chargeability (0.45s - 1.1s): {integrated_area:.4f}")


# --------------------------------------------



#############################################################################
# ---------------------- 3) PyQtGraph Visualization ----------------------

app = QtWidgets.QApplication([])

# Create the main plotting window
win = pg.GraphicsLayoutWidget(show=True)
win.setWindowTitle("Impedance, Nyquist, and Exponential Charge")
win.resize(1200, 900)  # Adjust window size to fit all plots
win.move(0, 0)

# ----------------- First Row: Nyquist Plot & Exponential Charge Curve -----------------

# Nyquist Plot: Z_real vs Z_imag
p1 = win.addPlot(row=0, col=0, title="Original vs Time")
p1.setLabel('left', "Voltage")
p1.setLabel('bottom', "Time")
p1.showGrid(x=True, y=True)
p1.plot(t_array, v_charge, pen=None, symbol='o', symbolBrush='r')

# Exponential Charge Curve
p2 = win.addPlot(row=0, col=1, title="FFT Output")
p2.setLabel('left', "Imagianry")
p2.setLabel('bottom', "Real")
p2.showGrid(x=True, y=True)
p2.plot(v_transformed.real, v_transformed.imag, pen=None, symbol='o', symbolBrush='b')

# ----------------- Second Row: Additional Example Plots -----------------

# Example Plot 1
p3 = win.addPlot(row=1, col=0, title="Zark Handmade")
p3.setLabel('left', "Impedance")
p3.setLabel('bottom', "freq")
p3.showGrid(x=True, y=True)
p3.plot(freq_even, zarc_list_func, pen=None, symbol='o', symbolBrush='r')

# Example Plot 2
p4 = win.addPlot(row=1, col=1, title="Straigth Inverse Transform")
p4.setLabel('left', "Inverse Transform")
p4.setLabel('bottom', "Mock Time Axis")
p4.showGrid(x=True, y=True)
p4.plot(t_actual, v_maybe, pen='b', symbol='o', symbolBrush='g')
#p4.plot(t_actual, v_step_response, pen='b', symbol='o', symbolBrush='g')

# ----------------- Third Row: More Example Plots -----------------

# Example Plot 3 (Now in row=2)
p5 = win.addPlot(row=2, col=0, title="Example Placeholder Plot 3")
p5.setLabel('left', "Inverse transform")
p5.setLabel('bottom', "Actual t Axis")
p5.showGrid(x=True, y=True)
p5.plot(jt_actual, v_step_response, pen='b', symbol='o', symbolBrush='g')
p5.plot(jt_integrated, v_integrated, pen=pg.mkPen('r', width=2))


# Example Plot 4 (Now in row=2)
p6 = win.addPlot(row=2, col=1, title="Verifying Results")
p6.setLabel('left', "Imag Axis")
p6.setLabel('bottom', "R Axis")
p6.showGrid(x=True, y=True)
p6.plot(t_array, v_charge2, pen=None, symbol='o', symbolBrush='y')

# Start the Qt event loop
app.exec_()


