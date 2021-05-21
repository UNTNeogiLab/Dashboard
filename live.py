import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
from pyvcam import pvc
from pyvcam.camera import Camera

class Cam:
    def __init__(self):
        self.pvc.init_pvcam()
        self.cam = next(Camera.detect_camera())
        self.cam.open()

    def grab_frame(self, exp_time):
        return frame = self.cam.get_frame(exp_time)

    def live(self,exp_time, itteratons):
        plt.ion()
        ax = plt.subplot(111)
        im = ax.imshow(self.grab_frame(exp_time))
        while i<itterations:
            im.set_data(self.grab_frame(exp_time))
            plt.pause(.01)
            plt.show()
            i+=1
