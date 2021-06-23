import numpy as np
from neogiinstruments import MaiTai,ESP300,Photodiode
from time import sleep
import matplotlib.pyplot as plt
ESP300 = ESP300()
ESP300.Home(1)
print('homing...')
sleep(10)
V = []
StDev = []
pos = []
for i in range(10):
    ESP300.moveRel(1,.1+i)
    sleep(.51)
    v = Photodiode()
    V.append(v[0])
    StDev.append(v[1])
    pos.append(i)
    print(i)

plt.plot(pos,V)
