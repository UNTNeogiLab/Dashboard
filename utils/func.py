'''from sys import executable, argv
from subprocess import check_output
from PyQt5.QtWidgets import QFileDialog, QApplicat
import os
def gui_fname(directory='./'):
    """Open a file dialog, starting in the given directory, and return
    the chosen filename"""
    # run this exact file in a separate process, and grab the result
    file = check_output([executable, __file__, directory])
    return file.strip()

if __name__ == "__main__":
    directory = argv[1]
    app = QApplication([directory])
    fname = QFileDialog.getOpenFileName(None, "Select a file...",
            directory, filter="All files (*)")
    print(fname[0])
def getflies():
    return os.listdir("data")
'''
#APPARENTLY I GOT TO WRITE MY OWN FUNCTIONS NOW
import numpy as np
def Max(data):
    return np.atleast_1d(np.max(data).values)[0]
def Min(data):
    return np.atleast_1d(np.min(data).values)[0]
def colormap(data):
    return range(round(Max(data)),round(Min(data)))