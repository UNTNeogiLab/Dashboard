# -*- coding: utf-8 -*-
"""
Created on Wed Jun 17 18:11:13 2020

@author: Mai Tai
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d

def Sin2(angle,mag,xoffset, yoffset):
    return mag*np.sin(angle*2*np.pi/360 - xoffset)**2 + yoffset
def PowerFit(datax,datay):
    popt, pcov = curve_fit(Sin2, datax, datay, p0 = [1,1,1],bounds=([0,0,0], [1000, 10, 10]))
    return popt, pcov
def InvSinSqr(y, mag, xoffset, yoffset):
    return np.mod((360/(2*np.pi))*(np.arcsin(np.sqrt(np.abs((y-yoffset)/mag)))+xoffset),180)
def PCFit(file):
    pc = np.load(file, allow_pickle=True)
    wavelengths = pc[:,0]
    PC = []
    PCcov = []
    Angles = []
    xx = np.arange(2,21,1)
    XX = np.linspace(0,30,100)
    
    for i in range(0,len(pc),1):
        params, cov = PowerFit(pc[i,1][0],pc[i,1][1])
        PC.append(params)
        PCcov.append(cov)
        analyticsin = InvSinSqr(XX,*params)
        interpangles = interp1d(XX,analyticsin)
        angles = interpangles(xx)
        Angs = dict(zip(xx,angles))
        Angles.append(Angs)
    PC = np.asarray(PC)
    PCcov = np.asarray(PCcov)
    #Angles = np.asarray(Angles)
    WavPowAng = dict(zip(wavelengths,Angles))
    
    return PC, PCcov, WavPowAng, pc


if __name__ == '__main__':
    PC, PCcov, WavPowAng, pc = PCFit('PowerCalib200626.npy')


    fig, axs = plt.subplots(nrows=2, ncols=2, sharex=False)
    ax1 = axs[0,0]
    ax2 = axs[0,1]
    ax3 = axs[1,0]
    ax4 = axs[1,1]
    X = np.linspace(0,50,51)

    for i in range(0,len(pc),1):
        ax1.errorbar(pc[i,1][0],pc[i,1][1],yerr = pc[i,1][2])
        ax1.set_title(r'Power vs $\theta_{\lambda/2}$')
        ax1.set(xlabel=r'$\theta_{\lambda/2}$ (degrees)',ylabel='Power(mW)')
        ax2.errorbar(pc[i,1][0],pc[i,1][3],yerr = pc[i,1][4])
        ax2.set_title(r'Voltage vs $\theta_{\lambda/2}$')
        ax2.set(xlabel=r'$\theta_{\lambda/2}$ (degrees)',ylabel='Voltage (V)')
        ax3.errorbar(pc[i,1][1],pc[i,1][3], xerr = pc[i,1][2], yerr = pc[i,1][4])
        ax3.set_title(r'Voltage vs Power')
        ax3.set(xlabel='Power(mW)',ylabel='Voltage (V)')
        ax4.plot(X,InvSinSqr(X,*PC[i]))
        ax4.set_title(r'$\theta_{\lambda/2}$ vs. Power (fit)')
        ax4.set(xlabel='Power(mW)',ylabel=r'$\theta_{\lambda/2}$ (degrees)')
    fig.tight_layout()
    