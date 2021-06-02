# -*- coding: utf-8 -*-
"""
Created on Sat Mar 21 19:56:08 2020

@author: Mai Tai
"""

import pyvisa
import numpy as np
from instrumental import instrument, u, list_instruments
import time
from datetime import datetime
import pickle
import pprint
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import os
from statistics import stdev
from tqdm import tqdm
from scipy.interpolate import interp1d
import nidaqmx
#%% initialize
if __name__ == '__main__':
    try:
            C = instrument('C')
    except:
            C = instrument('C')
    print("C.serial = " + C.serial)
    #C.offset = Offset*u.degree


    daq = instrument('daq')
    rm = pyvisa.ResourceManager()
    Pmeter = rm.open_resource('ASRL3::INSTR')
    MaiTai = rm.open_resource('ASRL1::INSTR')

#%%
    
def Shutter(op):
    """Helper function for instrumental to avoid clutter and make code 
    more readable
    >>>returns string""" 
    if op == 1:
        MaiTai.write("SHUT 1")
        #tqdm.write("Shutter Opened")
    else:
        MaiTai.write("SHUT 0")
        #tqdm.write("Shutter Closed")
        
def Power(): 
    """Reads power from Gentec TPM300 via VISA commands
    The while loop avoids outputting invalid token
    >>>returns float
    
    to-do: incorporate different power ranges (itteratively check all avaliable
    ranges and chose the best fit. Log this choice)"""
    
    
    while True:
        try:
            Pread = Pmeter.query("*READPOWER:")
            Power = float(Pread.split('e')[0].split('+')[1])
            return Power
        except:
             continue
         
def PowAvg():
    P = []
    for i in range(0,5,1):
        p = Power()
        P.append(p)
        time.sleep(1)
    PowerAvg = np.mean(P)
    PowerStd = np.std(P)
    return PowerAvg, PowerStd
        
        
def MoveWav(position):
    """Helper function for instrumental to avoid clutter and make code 
    more readable
    >>>returns null"""
    MaiTai.write(f"WAV {position}")
    
def ReadWav():
    """Helper function for instrumental to avoid clutter and make code 
    more readable
    >>>returns int"""
    w = int(MaiTai.query("WAV?").split('n')[0])
    return w
    
def Shutter(op):
    """Helper function for instrumental to avoid clutter and make code 
    more readable
    >>>returns string""" 
    if op == 1:
        MaiTai.write("SHUT 1")
        print("Shutter Opened")
    else:
        MaiTai.write("SHUT 0")
        print("Shutter Closed")
        
        
def MoveRot(position, Wait):
    """Helper function for instrumental to avoid clutter and make code 
    more readable
    >>>returns null"""
    C.move_to(position*u.degree, wait = Wait)

def Photodiode(Duration, Fsamp):
    Vlist = []
    Vstdlist = []
    for i in range(0,5):
        V = daq.ai0.read(duration=Duration*u.seconds,fsamp=Fsamp*u.hertz)
        Volts = V['Dev1/ai0'].mean()
        #Vstd = V['Dev1/ai0'].std()
        Vlist.append(Volts)
        #Vstdlist.append(Vstd)
    Voltage = sum(Vlist)/len(Vlist)
    #Vstd = stdev(Vlist,Voltage)*u.volt
    
    return Voltage#, Vstd

#%%
import nidaqmx
from nidaqmx.constants import TerminalConfiguration
from instrumental import u

def PD():
    with nidaqmx.Task() as task:
        ai_channel = task.ai_channels.add_ai_voltage_chan("Dev1/ai0",terminal_config = TerminalConfiguration.RSE)
        r = task.read(number_of_samples_per_channel=100)
        m = np.mean(r)
        delta = np.std(r)
        return m, delta
    
#%%    
def PowerRotLoop(pstart, pstop, pstep, pwait):
    """Main acquisition code to collect power as a function of 
    rotation stage angle. This can be run separately, but is embedded in 
    WavLoop for wavelength dependent calibration
    ************
    pstart = Initial angular position in degrees
    pstop = Final angular position in degrees
    pstep = Angular step size in degrees
    pwait = wait time between steps in seconds
    >>>>>returns P = 2D Array"""
    Shutter(0)
    print("Homing")
    C.home(wait = True)
    time.sleep(5)
    print('Homing finished')
    Pwr = []
    Pwrstd = []
    Pos = []
    Vol = []
    Volstd = []
    Shutter(1)
    for i in np.arange(pstart-pstep,pstop + pstep,pstep):
        if i>=pstart:
            MoveRot(i,True)
            time.sleep(pwait)
            print(str(C.position) + '>>>>>> ' + str(Power()) +' mW')
            Pos.append(float(str(C.position).split(' ')[0]))
            Pwr.append(PowAvg()[0])
            Pwrstd.append(PowAvg()[1])
            V, Vstd = PD()  ###HARDCODED
            Vol.append(float(str(V).split(' ')[0]))
            Volstd.append(float(str(Vstd).split(' ')[0]))
        else:
            MoveRot(i,True)
            time.sleep(pwait)
    P = np.asarray([Pos,Pwr,Pwrstd,Vol, Volstd])
    Shutter(0)
    return P
    
def WavLoop(wavstart,wavstop,wavstep,wavwait,
            wpstart, wpstop, wpstep, wpwait, 
            filename):
    """Main acquisiton code used to collect wavelength dependent calibration.
    First, the laser wavelength is set to wavstart. Then, PowerRotLoop is 
    called to collect Power vs Angle for said wavelength. The laser
    wavelength is then set to the next step.
    
    *************
    Figure out the inputs yourself, it's pretty self explantory.
    
    ********
    >>>>>returns W = a list of 2D arrays """
    print('Starting Wavelength Loop')
    
    def Sin2(angle,mag,xoffset, yoffset):
        return mag*np.sin(angle*2*np.pi/360 - xoffset)**2 + yoffset
    def PowerFit(datax,datay):
        popt, pcov = curve_fit(Sin2, datax, datay, p0 = [1,1,1])
        return popt, pcov
    def InvSinSqr(y, mag, xoffset, yoffset):
        return (360/(2*np.pi))*(np.arcsin(-np.sqrt((y-yoffset)/mag))+xoffset)

    
    if (950 >= wavstart >= 750 and 950 >= wavstop >= 750):
        MoveWav(wavstart)
        time.sleep(wavwait*2)
        W = []
        for w in np.arange(wavstart,wavstop+wavstep,wavstep):
            MoveWav(w)
            time.sleep(wavwait)
            wavelength = ReadWav()
            print (f'Starting Power Loop at {wavelength}nm')
            Pwr = PowerRotLoop(wpstart, wpstop, wpstep, wpwait)
            W.append([wavelength, Pwr])
        W = np.asarray(W)
        np.save(f'{filename}',W, allow_pickle = True)
        #PvA = PowerFit(W)

        return W
    else:
        print('Wavelengths out of range')
        
#%% Save Function
def SaveAsFiles(filename):

    A = np.load(filename, allow_pickle=True) 
    B = [np.transpose(A[i,1]) for i in np.arange(0,A[:,0].size,1)]
    cwd = os.getcwd()
    today = datetime.today()
    path = 'PowerCalibration' + str(today.date())
    os.mkdir(path)
    os.chdir(path)
    [np.savetxt(f'{A[i,0]}.csv',B[i], delimiter=',') for i in np.arange(len(B))]
    os.chdir(cwd)
         
    
    
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

# =============================================================================
# def Sin2(angle,mag,xoffset, yoffset):
#     return mag*np.sin(angle*2*np.pi/360 - xoffset)**2 + yoffset
# def PowerFit(datax,datay):
#     popt, pcov = curve_fit(Sin2, datax, datay, p0 = [1,1,1])
#     return popt, pcov
# # =============================================================================
# # def InvSinSqrPos(y, mag, xoffset, yoffset):
# #     return (360/(2*np.pi))*(np.arcsin(np.sqrt((y-yoffset)/mag))+xoffset)
# # def InvSinSqrNeg(y, mag, xoffset, yoffset):
# #     return (360/(2*np.pi))*(np.arcsin(-np.sqrt((y-yoffset)/mag))+xoffset)
# # =============================================================================
# 
# 
# def PCFit(file):
#     pc = np.load(file, allow_pickle=True)
#     wavelengths = pc[:,0]
#     PC = []
#     PCcov = []
#     Angles = []
#     xx = np.arange(2,21,1)
#     XX = np.arange(0,50,.01)
#     
#     for i in range(0,len(pc),1):
#         params, cov = PowerFit(pc[i,1][0],pc[i,1][1])
#         PC.append(params)
#         PCcov.append(cov)
#         analyticsin = Sin2(XX,*params)
#         interpangles = interp1d(XX,analyticsin)
#         angles = interpangles(xx)
#         Angs = dict(zip(xx,angles))
#         Angles.append(Angs)
#     PC = np.asarray(PC)
#     PCcov = np.asarray(PCcov)
#     #Angles = np.asarray(Angles)
#     WavPowAng = dict(zip(wavelengths,Angles))
#     
#     return PC, PCcov, WavPowAng
#     
# =============================================================================
# =============================================================================
# #%%    
# def Sin2(angle,mag,xoffset, yoffset):
#     return mag*np.sin(angle*2*np.pi/360 - xoffset)**2 + yoffset
# # =============================================================================
# # def PowerFit(xdata, ydata):
# #     popt, pcov = curve_fit(Sin2, data[0], data[1])
# #     return popt, pcov
# # =============================================================================
# 
# #%%
# def InvSineSqr(y,y0,xc,w,A):
#     return xc + (w/(4*np.pi))*np.arcsin(np.sqrt((y - y0)/A))
# =============================================================================

#%%Notes
    """Parameters for WavLoop shoiuld be ~ (780,920,2,60,0,10,1,5,'filename')
        for this to run in ~xxxhrs(last =6hrs)
        Further testing is needed to determine optimal parameters"""