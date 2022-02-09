# !/usr/bin/python
"""Main File to embedd and SRT or ASS subtitle file into an MKV file."""
# %%
import matplotlib.pyplot as plt
import numpy as np
from numpy.core.fromnumeric import size


# Get x values of the sine wave

t_max = 3
time = np.arange(0, t_max, 0.01)
time4 = np.arange(0, t_max, 0.25)
time20 = np.arange(0, t_max, 0.05)
f = 1.2
pshift = 0.1*np.pi
amplitude = 1.4* np.sin(f*2*np.pi * time + pshift) + 1.4
amplitude4 = 1.4* np.sin(f*2*np.pi * time4 + pshift) + 1.4
amplitude20 = 1.4* np.sin(f*2*np.pi * time20 + pshift) + 1.4

fig, axes = plt.subplots(1,2, figsize=(15,3))
for ax, t, a in zip(axes, [time4, time20], [amplitude4, amplitude20]):
    ax.plot(time, amplitude)
    ax.plot([0,t_max], [1.4, 1.4], c='r')
    ax.vlines(t, ymin=1.4, ymax=a, color='g')
    ax.plot(t, a, 'o', color='black')

    ax.set_yticks(np.arange(0, 3, 0.2))        
    # Give x axis label for the sine wave plot
    ax.set_xlabel('Time')
    # Give y axis label for the sine wave plot
    ax.set_ylabel('Amplitude [V]')
    ax.grid(True, which='both')

    ax.axhline(y=0, color='k')
plt.savefig("/Users/voelkerb/Desktop/test.pdf", dpi=300)
plt.show()
 