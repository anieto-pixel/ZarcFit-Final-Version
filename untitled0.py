
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
import scipy.signal as sig
from scipy.signal import hilbert


N=2**14
T=4
dt=T/N

q = 0.001 #Farad
pf = 1
pi = pf #in general
r = 1000 #Ohms

nyquist_f=1/(2*dt)
n_freq=(N/2)+1
freq_even = np.linspace(0, n_freq/T, int(n_freq+1))

freq_even[0]=0.001
b, a = sig.butter(2, 0.45, fs=1) #FILTER PARAMETERS

z_real = []
z_imag = [] 
z_absolute = []  # Store impedance values
z_complex =[]

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

for freq in freq_even:
    zcpe = cpe(freq, q, pf, pi)
    zarc = parallel(zcpe, r)
    # Computed impedance for this freq
    z_real.append(zarc.real)
    z_imag.append(-zarc.imag)
    z_absolute.append(np.absolute(zarc))
    z_complex.append(zarc)

z_complex[0]=z_complex[0].real


# -----OPTION 1-----------------------------------

v_maybe=np.fft.irfft(z_complex) #half a plot
v_maybe = sig.filtfilt(b, a, v_maybe)
t_maybe = np.arange(len(v_maybe)) * dt

# ------OPTION 2--------------------------------

dt=T/N
nyquist_f=1/(2*dt)

crit_time=4
Fs = N/(1.1*crit_time) ### maximum frequency in Hz

fmin = 10**-2 ### minimum frequency in Hz
fmax = Fs/2 ## The sampling frequency is twice the nyquist frequency
freqs = np.linspace(fmin,fmax,N)
#crit_time = 5 ## [s] ### The time at which the system is assumed to have reached equilibrium
t_plot = 2 ## [s] ### The extent of the response function to display
t = np.linspace(0,N/Fs,N) ### Compute the time axis
dt = t[1]-t[0] ### time differential for integration   


#print(f"N: {N}")
#print(f"T {T}")
#print(f"Fs {Fs}")

#print(f"np.linspace(0,N/Fs,N)")
#print(f"N/Fs,N {N/Fs},{N}")
#print("********************************")

#print(f"len {len(t)}")
#print("********************************")

#Z = model.locus_wrapper(freqs,model.parameter_values,mode = 'FFT') ## compute the model with only Zarcs
Z=[] 
for freq in freqs:
    zcpe_func = cpe(freq, q, pf, pi)
    zarc_func = parallel(zcpe_func, r)  # Computed impedance for this freq
    Z.append(zarc_func)
    
Z[0]=Z[0].real
  
Z_tilde_unfiltered = np.fft.irfft(Z,len(Z))
Z_tilde_unfiltered /= dt  ### This is now the iFFT of the Impedance, normalized so that the integral over time is the zero
                           ### frequency impedance. Remind me =/ ?
b,a = sig.butter(2,0.45,fs = 1)    
Z_tilde = sig.filtfilt(b,a,Z_tilde_unfiltered)
  
 
w_actual = np.where(t>crit_time)[0][0] #this will error for small N
w_plot = np.where(t>t_plot)[0][0] ## The index which to plot up to
    
t = t[:w_actual]
Z_tilde = Z_tilde[:w_actual]
        
###### This next chunk computes the Voltage normalized by step function current (integral from t to infinity) efficiently

Vm = np.sum(Z_tilde*dt)
dV = Z_tilde*dt
    
partial_sum = 0
V = [partial_sum] 
    
for i in range(len(dV)-1):
    partial_sum += dV[i]
    V.append(partial_sum)
    
V = np.array(V)
 

t_josh=  t[:w_plot] 
v_josh = (1-V[:w_plot]/Vm)[::10]
#    return (t[:w_plot])[::10],(1-V[:w_plot]/Vm)[::10]




#-----------------------------------------


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

p1 = win.addPlot(row=0, col=0, title="Zark Cole")
p1.setLabel('left', "Imag")
p1.setLabel('bottom', "Real")
p1.showGrid(x=True, y=True)
p1.plot(z_real_func, z_imag_func, pen=None, symbol='o', symbolBrush='r')

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
p4.setLabel('bottom', "Time")
p4.showGrid(x=True, y=True)
p4.plot(t_actual, v_maybe, pen='b', symbol='o', symbolBrush='g')
#p4.plot(t_actual, v_step_response, pen='b', symbol='o', symbolBrush='g')

# ----------------- Third Row: More Example Plots -----------------

# Example Plot 3 (Now in row=2)
p5 = win.addPlot(row=2, col=0, title="Mixed version")
p5.setLabel('left', "Inverse transform")
p5.setLabel('bottom', "Time")
p5.showGrid(x=True, y=True)
p5.plot(jt_actual, v_step_response, pen='b', symbol='o', symbolBrush='g')
p5.plot(jt_integrated, v_integrated, pen=pg.mkPen('r', width=2))


# Example Plot 4 (Now in row=2)
p6 = win.addPlot(row=2, col=1, title="Old version (Josh's)")
p6.setLabel('left', "Inverse Transform")
p6.setLabel('bottom', "Time")
p6.showGrid(x=True, y=True)
p6.plot(t, Z_tilde, pen='b', symbol='o', symbolBrush='y')

# Start the Qt event loop
app.exec_()


