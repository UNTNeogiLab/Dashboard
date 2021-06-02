from pyvcam import pvc
from pyvcam.camera import Camera
from K10CR1.k10cr1 import K10CR1
import thorpy as apt


def InitializeInstruments():
    """
    Initializes the camera and rotators to the desired names.
    TODO: Figure out how to set the camera to 'quantview' mode.

    Parameters
    ----------

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
    try:
        cam = next(Camera.detect_camera())  # Use generator to find first camera
        cam.open()  # Open the camera.
        if cam.is_open:
            print("Camera open")
    except:
        raise Exception("Error: camera not found")
    Rotational = "K10CR1"
    if Rotational == "K10CR1":
        l = ["55001000", "55114554","55114654"]
        L = [K10CR1(i) for i in l]   # There is no serial number
        for i in L:
            print(f'Homing stage {i}')
            i.home()
    elif Rotational == "thorlabs_apt":
        l = apt.list_available_devices()
        L = [apt.Motor(i[1]) for i in l]
        for i in L:
            i.set_move_home_parameters(2, 1, 10, 0)
            i.set_velocity_parameters(0, 10, 10)
            i.move_home()
    elif Rotational == "thorpy":
        pass

    return cam, *L
