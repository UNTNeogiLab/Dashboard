# -*- coding: utf-8 -*-
"""
Spyder Editor

This script defines functions for initializing data structures
and instruments used for SHG strain imaging microscopy.

"""

from instrumental import instrument, u
from pyvcam import pvc
from pyvcam.camera import Camera
import pyvisa
import numpy as np
from time import sleep
from datetime import datetime
import os
import tifffile
import glob
from tqdm import tqdm
import subprocess
import h5py
import time
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d
import nidaqmx
from nidaqmx.constants import TerminalConfiguration
from instrumental import u
import pickle
import matplotlib.pyplot as plt
import hyperspy.api as hs


# %% InitializeInstruments
def InitializeInstruments():
    """
    Initializes the camera and rotators to the desired names.
    TODO: Figure out how to set the camera to 'quantview' mode.

    Parameters
    ----------
    none
    
    Returns
    -------
    cam : object
        Named pyvcam camera object.
    A : object
        Named Instrumental instrument object.
    B : object
        Named Instrumental instrument object.
    C : object
        Named Instrumental instrument object.

    """
    pvc.init_pvcam()  # Initialize PVCAM
    cam = next(Camera.detect_camera())  # Use generator to find first camera
    cam.open()  # Open the camera.
    if cam.is_open == True:
        print("Camera open")
    else:
        print("Error: camera not found")
    try:
        A = instrument('A')  # try/except is used here to handle
    except:  # a bug in instrumental that requires
        A = instrument('A')  # this line to be run twice
    print("A.serial = " + A.serial)
    try:
        B = instrument('B')
    except:
        B = instrument('B')
    print("B.serial = " + B.serial)
    try:
        C = instrument('C')
    except:
        C = instrument('C')
    print("C.serial = " + C.serial)

    return cam, A, B, C


if __name__ == '__main__':
    cam, rotator_bottom, rotator_top, C = InitializeInstruments()
    # %%

    rm = pyvisa.ResourceManager()
    Pmeter = rm.open_resource('ASRL3::INSTR')
    MaiTai = rm.open_resource('ASRL1::INSTR')


# %% InitializeDateFolder
def InitializeDateFolder(location='E:\\Imaging'):
    """
    Creates a folder named by current date and changes the working directory
    to match. Should be called first.

    Parameters
    ----------
    location : string
        The path of the parent folder the new data folder should be
        generated in.
    Returns
    -------
    newfolder : pathstring
        The path of the generated folder.

    """
    today = datetime.today()
    datefolder = location + '\\' + str(today.date())
    if os.path.exists(datefolder):
        os.chdir(datefolder)
        pass
    else:
        os.mkdir(datefolder)
        os.chdir(datefolder)

    return datefolder


# %%
def InitializeRunFolder(sample, sample_origin, wavelength,
                        power, datefolder, circ_pol=None):
    """
    Creates a folder for an individual strain mapping run.
    TODO: figure out a better way to save the timestamp
    
    Parameters
    ----------
    sample : string
        Identifies the sample.
    sample_origin : string
        Identifies the maker of the sample
    circ_pol : numeric, optional
        Identifies the circular polarization that HalfWaveLoop() will be
        run at.
    datefolder : pathstring
        The parent directory to create runfolder in.

    Returns
    -------
    runfolder : pathstring
        The path of the generated folder.

    """
    now = datetime.now()
    # time = now.strftime("%H.%M")
    if circ_pol == None:
        # runfolder = datefolder + '\\' + sample + '_' + str(wavelength) + 'nm' +f'{power}mW'
        runfolder = datefolder + f'\\{sample}_{wavelength}nm_{power}mW'
    else:
        cp_folder = datefolder + '\\' + sample + '_' + circ_pol
        os.mkdir(cp_folder)
        os.chdir(cp_folder)
    os.mkdir(runfolder)
    os.chdir(runfolder)

    return runfolder


# %%

# %%CloseInstruments
def CloseInstruments(cam, A, B, C):
    cam.close()
    pvc.uninit_pvcam()
    A.close()
    B.close()
    C.close()


# %% HalfWaveLoop
def HalfWaveLoop(power, orientation, datefolder, wavelength, sample, sample_origin, cam, rotator_top,
                 rotator_bottom, runfolder, start, stop, step, zfill,
                 delay, exp_time, circ_pol):
    """
    
    Main strain-mapping loop. Rotates pre- and post-sample halfwave plates
    in tandem, taking camera images at each polarization step. Also saves
    metadata.txt in the data folder.

    Parameters
    ----------
    wavelength : numeric
        Measurement wavelength. Metadata parameter.
    sample : string
        Sample name. Metadata parameter.
    sample_origin : string
        Where the sample came from. Metadata parameter.
    cam : object
        pvam Camera object.
    rotator_top : object
        Instrumental K10CR1 object.
    rotator_bottom : object
        Instrumental K10CR1 object.
    start : numeric, optional
        Polarization range start point. For a calibrated run, set to
        the desired offset. Must be a positive value.
    stop : numeric, optional
        Polarization range stop point. 
    step : numeric, optional
        Polarization step size. Lower values yield higher resolution.
    zfill : numeric, optional
        Number of zeros to pad the output filenames
        with. Should be increased for high resolution
        datasets. The default is 3.
    delay : numeric, optional
        The pre-acquisition delay time in seconds.
        Used to give time to turn off light sources
        and vacate the lab. The default is 180.
    exp_time : numeric, optional
        Camera exposure time in ms. The default is 10000.
    circ_pol : numeric, optional
        The circular polarization this run was acquired at. 

    Returns
    -------
    None.

    """
    if orientation == 'parallel':
        sys_offset = 0 * u.degree
        folder = runfolder + '\\' + 'parallel'
        os.mkdir(folder)
        os.chdir(folder)
    elif orientation == 'perpendicular':
        sys_offset = 45 * u.degree
        folder = runfolder + '\\' + 'perpendicular'
        os.mkdir(folder)
        os.chdir(folder)
    # tqdm.write('Homing bottom rotator')
    rotator_bottom.home(wait=True)
    # tqdm.write('Homing top rotator')
    rotator_top.home(wait=True)
    tick = datetime.now()
    stop = start + stop
    sleep(delay)
    step = step * 0.5

    R = tqdm(np.arange(start, stop, step),
             desc=f'{orientation} at {wavelength} nm {power} mW',
             position=0, leave=True)
    # plt.ion()
    # im = plt.imshow(cam.get_frame())
    Volts = []
    Pos = []
    Frames = []
    for i in R:
        position = i * u.degree
        position_top = position - rotator_top.offset + sys_offset
        position_bottom = position - rotator_bottom.offset
        # position_bottom = (360*u.degree)-(position - rotator_bottom.offset)
        strpos = str(2 * i)
        padded = strpos.zfill(zfill)
        name = 'halfwave' + padded
        rotator_top.move_to(position_top, wait=False)
        rotator_bottom.move_to(position_bottom, wait=True)
        frame = cam.get_frame(exp_time=exp_time)
        # im.set_data(frame)
        # plt.pause(0.01)
        volts = PD()[0]
        position = C.position
        Volts.append(volts)
        Pos.append(position)
        Frames.append(frame)
        # np.save(name, frame, allow_pickle=False)
    tock = datetime.now()
    # Frames = np.asarray(Frames).T
    ###
    s = hs.signals.Signal1D(Frames, lazy=True)
    s.axes_manager[0].name = 'Y'
    s.axes_manager[0].units = 'Pixels'
    s.axes_manager[2].name = 'X'
    s.axes_manager[2].units = 'Pixels'
    s.axes_manager[1].name = 'Polarization'
    s.axes_manager[1].scale = step
    s.axes_manager[1].units = 'Degrees'
    s = s.as_signal1D('Polarization')

    #    s.save(f'{wavelength}nm_{power}mW_{orientation}')
    ###moved below
    with h5py.File(datefolder + '\\' + sample + '.hdf5', 'a') as hdf:
        # Note that this does not save in the right structure for hyperspy
        # Hyperspy expects the data to exist in a single multidimensional array
        dset = hdf.create_dataset(f'{wavelength}nm/{power}mW/{orientation}', data=Frames)

    delta = tock - tick
    Wavelength = str(wavelength) + ' nm'
    Vpos = list(map(list, zip(Volts, Pos)))
    np.save('Power_Position', Vpos, allow_pickle=True)
    with open('metadata.txt', mode='w') as f:
        print('Start time: ' + str(tick), file=f)
        print('End time: ' + str(tock), file=f)
        print('Total Acquisition time: ' + str(delta), file=f)
        print('Wavelength: ' + str(Wavelength), file=f)
        print('Exposure time: ' + str(exp_time) + 'ms', file=f)
        print('Sample: ' + str(sample), file=f)
        print('Sample Origin: ' + str(sample_origin), file=f)
        print('Polarization range: ' + str(2 * start) +
              ' to ' + str(2 * stop) + 'deg', file=f)
        print('Polarization resolution: ' + str(2 * step) + 'deg', file=f)
        if circ_pol is not None:
            print('Circular Polarization: ' + str(circ_pol) + 'deg', file=f)
        else:
            pass
    os.chdir(runfolder)
    if os.path.exists(datefolder + '\\hspyfiles'):
        os.chdir(datefolder + '\\hspyfiles')
    else:
        os.mkdir(datefolder + '\\hspyfiles')
        os.chdir(datefolder + '\\hspyfiles')

    s.save(f'{wavelength}nm_{power}mW_{orientation}')

    return folder


# %%ClusterSync
def ClusterSync(datefolder):
    """
    Syncs data to the cluster.
    TODO: figure out how to make the 'rsync' string more readable/maintainable,
    and how to pass the desired data location.
    Parameters
    ------
    datefolder : TYPE, optional
        DESCRIPTION. The default is datefolder.
    runfolder : TYPE, optional
        DESCRIPTION. The default is runfolder.

    Returns
    -------
    None.

    """
    today = datefolder
    shell = 'C:\Program Files (x86)\Mobatek\MobaXterm\MobaXterm.exe'
    kill = '-exitwhendone'
    tab = '-newtab'
    rsync = ('rsync --chmod=Du=rwx,Dgo=rwx,Fu=rw,Fog=rw -aHXxv --numeric-ids --delete --progress -e' +
             ' \'/bin/ssh -x -T -c arcfour -o Compression=no\'' +
             ' /drives/e/Imaging/' + str(today) +
             ' bms0248@talon3.hpc.unt.edu:/storage/scratch2/share/pi_an0047/autoupload/')
    subprocess.call([shell, kill, tab, rsync])


# %%TiffSave
def TiffSave(runfolder):
    """
    Generates a TIFF stack from a folder of numpy arrays for quick analysis
    in ImageJ.

    Parameters
    ----------
    runfolder : pathstring
        The folder containing numpy arrays to be concatenated as a 
        Tiff stack.

    Returns
    -------
    None.

    """
    os.chdir(runfolder)
    filelist = glob.glob(runfolder + '\\*.npy')
    filelist = sorted(filelist)
    datacube = np.array([np.load(fname) for fname in filelist])
    tifffile.imsave('out.tiff', datacube)


# %% CheckRotators

def CheckRotators(A, B, C):
    """
    Verifies physical position of half wave plate rotation mounts and assigns
    initialized rotators to the correct variables for HalfWaveLoop().

    Parameters
    ----------
    A : object
        Instrumental K10CR1 object.
    B : object
        Instrumental K10CR1 object.
    C : object
        Instrumental K10CR1 object.

    Returns
    -------
    rotator_top : object
        Instrumental K10CR1 object.
    rotator_bottom : object
        Instrumental K10CR1 object.
    cp_post : object
        Instrumental K10CR1 object.

    """
    response = ''
    while response != 'y':
        response = input("Are the rotator locations unchanged? Enter " +
                         "'y' to continue, 'n' to manually set rotator_top " +
                         "and rotator_bottom\n" +
                         '>>>')
        rotator_top = input("Enter name (A, B, or C) of post-sample half-wave"
                            + " rotator:\n" +
                            ">>>")
        if rotator_top == 'A':
            rotator_top = A
        elif rotator_top == 'B':
            rotator_top = B
        elif rotator_top == 'C':
            rotator_top = C
        else:
            pass
        rotator_bottom = input("Enter name (A, B, or C) of pre-sample " +
                               "half-wave rotator:\n" +
                               ">>>")
        if rotator_bottom == 'A':
            rotator_bottom = A
        elif rotator_bottom == 'B':
            rotator_bottom = B
        elif rotator_bottom == 'C':
            rotator_bottom = C
        else:
            pass
        cp_post = input("Enter name (A, B, or C) of post-sample " +
                        "quarter-wave rotator:\n" +
                        ">>>")
        if cp_post == 'A':
            cp_post = A
        elif cp_post == 'B':
            cp_post = B
        elif cp_post == 'C':
            cp_post = C
        else:
            pass
    return rotator_top, rotator_bottom, cp_post


# %%


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


def PD():
    with nidaqmx.Task() as task:
        ai_channel = task.ai_channels.add_ai_voltage_chan("Dev1/ai0", terminal_config=TerminalConfiguration.RSE)
        r = task.read(number_of_samples_per_channel=100)
        m = np.mean(r)
        delta = np.std(r)
        return m, delta


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
        # tqdm.write("Shutter Opened")
    else:
        MaiTai.write("SHUT 0")
        # tqdm.write("Shutter Closed")


def MoveRot(position, Rot=C):
    """Helper function for instrumental to avoid clutter and make code 
    more readable
    >>>returns null"""
    Rot.move_to(position * u.degree)


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

    print("Homing")
    C.home(wait=True)
    time.sleep(5)
    print('Homing finished')
    Pwr = []
    Pos = []
    for i in np.arange(pstart, pstop + pstep, pstep):
        MoveRot(i)
        time.sleep(pwait)
        print(str(C.position) + '>>>>>> ' + str(Power()) + ' mW')
        Pos.append(float(str(C.position).split(' ')[0]))
        Pwr.append(Power())
        P = np.asarray([Pos, Pwr])
    return P


def WavLoop(wavstart, wavstop, wavstep, wavwait,
            wpstart, wpstop, wpstep, wpwait,
            filename):
    """Main acquisiton code used to collect wavelength dependent calibration.
    First, the laser wavelength is set to wavstart. Then, PowerRotLoop is 
    called to collect Power vs Angle for said wavelength. The laser
    wavelength is then set to the next step.
    
    *************
    Figure out the inputs yourself, it's pretty self exxplanitory.
    
    ********
    >>>>>returns W = a list of 2D arrays """
    print('Starting Wavelength Loop')
    if (950 >= wavstart >= 750 and 950 >= wavstop >= 750):
        MoveWav(wavstart)
        time.sleep(wavwait * 2)
        W = []
        for w in np.arange(wavstart, wavstop + wavstep, wavstep):
            MoveWav(w)
            time.sleep(wavwait)
            wavelength = ReadWav()
            print(f'Starting Power Loop at {wavelength}nm')
            Pwr = PowerRotLoop(wpstart, wpstop, wpstep, wpwait)
            W.append([wavelength, Pwr])
        np.save(f'{filename}', W, allow_pickle=True)
        return W
    else:
        print('Wavelengths out of range')


# %% Save Function
def SaveAsFiles(filename):
    A = np.load(filename, allow_pickle=True)
    B = [np.transpose(A[i, 1]) for i in np.arange(0, A[:, 0].size, 1)]
    cwd = os.getcwd()
    today = datetime.today()
    path = 'PowerCalibration' + str(today.date())
    os.mkdir(path)
    os.chdir(path)
    [np.savetxt(f'{A[i, 0]}.csv', B[i], delimiter=',') for i in np.arange(len(B))]
    os.chdir(cwd)

    # %%
    # =============================================================================
    # def Sin2(angle,mag,xoffset, yoffset):
    #     return mag*np.sin(angle*2*np.pi/360 - xoffset)**2 + yoffset
    # def PowerFit(data):
    #     popt, pcov = curve_fit(Sin2, data[0], data[1])
    #     return popt, pcov
    #
    # =============================================================================
    # %%
    # =============================================================================
    # def InvSineSqr(y,y0,xc,w,A):
    #     return xc + (w/(np.pi))*np.arcsin(np.sqrt((y - y0)/A))
    # =============================================================================

    # %%Notes
    """Parameters for WavLoop shoiuld be ~ (750,950,2,60,0,44,2,5,'filename')
        for this to run in ~8hrs
        Further testing is needed to determine optimal parameters"""

    # %%%%%%%%%%%%%%%%%%%%%%%


def Sin2(angle, mag, xoffset, yoffset):
    return mag * np.sin(angle * 2 * np.pi / 360 - xoffset) ** 2 + yoffset


def PowerFit(datax, datay):
    popt, pcov = curve_fit(Sin2, datax, datay, p0=[1, 1, 1], bounds=([0, 0, 0], [1000, 10, 10]))
    return popt, pcov


def InvSinSqr(y, mag, xoffset, yoffset):
    return np.mod((360 / (2 * np.pi)) * (np.arcsin(np.sqrt(np.abs((y - yoffset) / mag))) + xoffset), 180)


def PCFit(file):
    pc = np.load(file, allow_pickle=True)
    wavelengths = pc[:, 0]
    PC = []
    PCcov = []
    Angles = []
    xx = np.arange(2, 21, 1)
    XX = np.linspace(0, 30, 100)

    for i in range(0, len(pc), 1):
        params, cov = PowerFit(pc[i, 1][0], pc[i, 1][1])
        PC.append(params)
        PCcov.append(cov)
        analyticsin = InvSinSqr(XX, *params)
        interpangles = interp1d(XX, analyticsin)
        angles = interpangles(xx)
        Angs = dict(zip(xx, angles))
        Angles.append(Angs)
    PC = np.asarray(PC)
    PCcov = np.asarray(PCcov)
    # Angles = np.asarray(Angles)
    WavPowAng = dict(zip(wavelengths, Angles))

    return PC, PCcov, WavPowAng, pc


# =============================================================================
# def PCFit(file):
#     pc = np.load(file, allow_pickle=True)
#     PC = []
#     PCcov = []
#     Angles = []
#     xx = np.arange(2,22,2)
#     for i in range(0,len(pc),1):
#         params, cov = PowerFit(pc[i,1][0],pc[i,1][1])
#         PC.append(params)
#         PCcov.append(cov)
#         angles = InvSinSqr(xx,*params)
#         Angles.append(angles)
#     PC = np.asarray(PC)
#     return PC, PCcov, Angles
# =============================================================================

def V2P(wavelength, voltage, pc):
    def Line(x, m, b):
        return m * x + b

    def FitV2P(x, y):
        fit, fitcov = curve_fit(Line, x, y)
        return fit, fitcov

    F = []
    Fcov = []
    for i in range(0, len(pc), 1):
        f, fcov = FitV2P(pc[i, 1][1], pc[i, 1][3])
        F.append(f)
        Fcov.append(fcov)
    F = np.asarray(F)
    M = F[:, 0]
    B = F[:, 1]
    mW = (voltage - B[int((wavelength - 780) / 2)]) / M[int((wavelength - 780) / 2)]
    return mW


def SetPower(power, wavelength, wavelength_start_calib, wavelength_step_calib, PC):
    MoveRot(InvSinSqr(power, *PC[int((wavelength - wavelength_start_calib) / wavelength_step_calib)]))


def LiveCam(cam, exptime, itter):
    import matplotlib.pyplot as plt
    plt.ion()
    i = 1
    cam.start_live(exp_time=exptime)
    im = plt.imshow(cam.get_live_frame())
    while i < itter:
        im.set_data(cam.get_live_frame())
        i = i + 1
        plt.pause(.01)
    cam.stop_live()


def WavelengthRASHG(wav_start, wav_stop, wav_step,
                    wav_wait, res, exp, sample, sample_origin, Tiff=False):
    '''
    CALIBRATION FILE HARDCODED
    
    
    '''
    PC, PCcov, WavPowAng, pc = PCFit(
        'C:/Users/Mai Tai/Desktop/Python Code/PowerCalib200626.npy')  ###Check End of File as well

    cam.roi = (900, 1550, 650, 1500)  # x1,x2,y1,y2
    # cam.roi = (10,20,10,20)

    datefolder = InitializeDateFolder()

    MoveWav(wav_start)
    time.sleep(wav_wait)
    tictic = datetime.now
    pbar = tqdm(np.arange(wav_start, wav_stop + wav_step, wav_step), desc='Total', position=0)

    for wav in pbar:
        TIME = []
        tic = datetime.now()
        for power in range(10, 20, 5):
            runfolder = InitializeRunFolder(sample, sample_origin,
                                            f'{wav}', power, datefolder)
            Shutter(0)
            SetPower(power, wav, 780, 2, PC)  ###hard coded
            # MoveRot(InvSinSqr(power,*PC[int((wav-wav_start)/wav_step)]))
            MoveWav(wav)
            time.sleep(wav_wait)

            Shutter(1)

            HalfWaveLoop(power, 'parallel', datefolder, wav,
                         sample, sample_origin, cam,
                         rotator_top, rotator_bottom, runfolder,
                         start=0, stop=180, step=res, zfill=5,
                         delay=0, exp_time=exp,
                         circ_pol=None)

            HalfWaveLoop(power, 'perpendicular', datefolder, wav,
                         sample, sample_origin, cam,
                         rotator_top, rotator_bottom, runfolder,
                         start=0, stop=180, step=res, zfill=5,
                         delay=0, exp_time=exp,
                         circ_pol=None)
            ClusterSync(datefolder)
        toc = datetime.now()
        time_delta = toc - tic
        delta = str(time_delta)
        TIME.append([wav, delta])
    MaiTai.write('OFF')
    toctoc = datetime.now
    # te = toctoc-tictic
    # print(f'MaiTai off a {toctoc} \n Time elapsed = {te}')


if __name__ == '__main__':
    PC, PCcov, WavPowAng, pc = PCFit(
        'C:/Users/Mai Tai/Desktop/Python Code/PowerCalib200617.npy')
    # WavelengthRASHG(5, 780, 920, 2, 60, 2, 1000, 'MoS2_hierres_wav', 'Y+V', False)
