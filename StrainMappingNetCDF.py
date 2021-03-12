import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import time
import itertools
from  joblib import Parallel, delayed
import multiprocessing as mP
from datetime import timedelta
import os
from scipy import optimize


nCores = mP.cpu_count()


data = xr.open_dataset("RealData.nc")
xyp =data.shg[:,:,0,:, 0, 0]
xyp[np.where(np.isnan(xyp))]=0


phi=np.radians(2*np.linspace(0,xyp[0,0,:].size-1,xyp[0,0,:].size))
# plt.polar(phi,xyp[120,60,:])
def strainfit(phi, a, b, delta, theta):
    return 0.25*(a * np.cos(3*phi- 3*delta) + b * np.cos(2 * theta + phi -
                 3*delta))**2
N = 4
tic = time.time()
print('Start time=' + str(tic))
threshold = np.average(xyp)
def f(v):
    i = v[0]*N
    j = v[1]*N
    t = [v[0],v[1], 0, 0, 0, 0, 0, 0, 0, 0]
    if xyp[i,j,:].mean() > threshold:
        xx = (xyp[i,j,:])
        params, params_covariance = optimize.curve_fit(strainfit, phi, xx,
                                                       maxfev = 1000000,
                                                       p0 = [1,1,1,1],
                                                       method='lm',
                                                       xtol = 1e-9,
                                                       ftol = 1e-9)
        for k in range(4):
            t[k+2] = params[k]
            t[k+6] = params_covariance[k,k]
        print(str(i) + ',' + str(j))
    return t

print('Parallelizing')
paramsarray = np.zeros((xyp.shape[0]//N, xyp.shape[1]//N, 8))
V = itertools.product(range(xyp.shape[0]//N), range(xyp.shape[1]//N) )
A = Parallel(n_jobs=nCores)(delayed(f)(v) for v in V )
print('Collecting')
for a in A:
    for k in range(8):
        paramsarray[a[0],a[1],k] = a[k+2]
print('Saving')
np.save('outfile', paramsarray)
#np.save('outfile', paramsarray)
toc = time.time()
print('Run Time =' + str(timedelta(seconds = toc - tic)) + ' h:min:s')
nan_indices = np.where(np.isnan(xyp))
nan_indices
