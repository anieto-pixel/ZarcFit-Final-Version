# -*- coding: utf-8 -*-
"""
Created on Wed Feb 12 14:03:54 2025

@author: agarcian
"""

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets

# ---------------------- 1) Define the v/t plot of a RCPE ----------------------
q = 10**-2
pf = 0.5
pi = 0.5
r = 10.0  # Example resistor value in ohms
N = 100

# Compute capacitance (CPE behaves as capacitor when pf=1)
c = q  # Since pf = 1, CPE acts as a capacitor with C = Q
tau = r * c  # Time constant of the RC circuit
v0 = 1.0  # Initial voltage (assumed)


# Generate time values
t = np.linspace(0, 1, N)  # Simulate for 1 second
v_t = v0 * np.exp(-t / tau)  # Exponential decay equation

# ---------------------- 2) transform back and forth ----------------------
v_transformed=np.fft.rfft(v_t)

#v_charge2 = np.fft.irfft(v_transformed)

#Since t spans 5 * tau with N samples
fs = N / (v0 * tau)  # Sampling frequency (assuming uniform time step)
freqs_voltage = np.fft.rfftfreq(N, d=1/fs)

# ---------------------- 3) Compute zarcs, they should look the same ----------------------
# Generate frequencies

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

# Compute impedance data for the Nyquist plot
z_real_v = []
z_imag_v = [] 
zarc_list_v = []  # Store impedance values

print(f"freq_voltage{freqs_voltage[1:]}")
for freq in freqs_voltage[1:]:
    zcpe_v = cpe(freq, q, pf, pi)
    zarc_v = parallel(zcpe_v, r)  # Computed impedance for this freq
    zarc_list_v.append(zarc_v)
    z_real_v.append(zarc_v.real)
    z_imag_v.append(-zarc_v.imag)
    
z_real_func = []
z_imag_func = [] 
zarc_list_func = []  # Store impedance values
       
#freq_even = np.logspace(10, 500., N)
freq_even = np.linspace(10, 500.,int(N/2))
print(f"freq_even:{freq_even}")
for freq in freq_even:
    zcpe_func = cpe(freq, q, pf, pi)
    zarc_func = parallel(zcpe_func, r)  # Computed impedance for this freq
    zarc_list_func.append(zarc_func)
    z_real_func.append(zarc_func.real)
    z_imag_func.append(-zarc_func.imag)

# ---------------------- 2) Compute Exponential Charging Curve ----------------------

# --------------------------------------------


# --------------------------------------------




# --------------------------------------------



#############################################################################
# ---------------------- 3) PyQtGraph Visualization ----------------------

app = QtWidgets.QApplication([])

# Create the main plotting window
win = pg.GraphicsLayoutWidget(show=True)
win.setWindowTitle("Impedance, Nyquist, and Exponential Charge")
win.resize(1200, 900)  # Adjust window size to fit all plots

# ----------------- First Row: Nyquist Plot & Exponential Charge Curve -----------------

# Nyquist Plot: Z_real vs Z_imag
p1 = win.addPlot(row=0, col=0, title="Zarc")
p1.setLabel('left', "time")
p1.setLabel('bottom', "Voltage")
p1.showGrid(x=True, y=True)
p1.plot(t, v_t, pen=None, symbol='o', symbolBrush='r')


# Exponential Charge Curve
p2 = win.addPlot(row=0, col=1, title="Exponential Charging Curve")
p2.setLabel('left', "Real")
p2.setLabel('bottom', "Imag")
p2.showGrid(x=True, y=True)
p2.plot(z_real_v, z_imag_v, pen='b')

# ----------------- Second Row: Additional Example Plots -----------------

# Example Plot 1
p3 = win.addPlot(row=1, col=0, title="rffted voltage")
p3.setLabel('left', "Real")
p3.setLabel('bottom', "Imag")
p3.showGrid(x=True, y=True)
p3.plot(z_real_func, z_imag_func, pen=None, symbol='o', symbolBrush='r')

# Example Plot 2
p4 = win.addPlot(row=1, col=1, title="irffted rffted voltage")
p4.setLabel('left', "Y Axis")
p4.setLabel('bottom', "X Axis")
p4.showGrid(x=True, y=True)
#p4.plot(t, v_charge2, pen=None, symbol='o', symbolBrush='b')

# ----------------- Third Row: More Example Plots -----------------

# Example Plot 3 (Now in row=2)
p5 = win.addPlot(row=2, col=0, title="Example Placeholder Plot 3")
p5.setLabel('left', "Y Axis")
p5.setLabel('bottom', "X Axis")
p5.showGrid(x=True, y=True)
#p5.plot(z_real_v, z_imag_v, pen=None, symbol='o', symbolBrush='g')

# Example Plot 4 (Now in row=2)
p6 = win.addPlot(row=2, col=1, title="Example Placeholder Plot 4")
p6.setLabel('left', "Y Axis")
p6.setLabel('bottom', "X Axis")
p6.showGrid(x=True, y=True)
#p6.plot([1,2,3], [3,1,2], pen=None, symbol='o', symbolBrush='y')

# Start the Qt event loop
app.exec_()


