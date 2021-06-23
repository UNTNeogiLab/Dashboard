from K10CR1.k10cr1 import K10CR1
import elliptec


def find_ports(type):
    if type == "K10CR1":
        return ["55001000", "55114554", "55114654"]
    elif type == "elliptec":
        return elliptec.find_ports()
    # more or less documentation on finding the rotators


class rotator():
    def __init__(self, i, type="K10CR1"):
        self.type = type
        if type == "K10CR1":
            self.rotator = K10CR1(i)
            self.home()

        elif type == "elliptec":
            ports = elliptec.find_ports()
            for port in ports:
                if port.serial_number == i:
                    self.rotator = elliptec.Motor(port.device)
        '''
        elif type == "thorlabs_apt":
            rotator = apt.Motor(i[1])
            rotator.set_move_home_parameters(2, 1, 10, 0)
            rotator.set_velocity_parameters(0, 10, 10)
            rotator.move_home()
            return rotator
        '''

    def home(self):
        if self.type == "K10CR1":
            self.rotator.home()
        elif self.type == "elliptec":
            self.degree = 0
            self.rotator.do_("home")
    def move_abs(self,value):
        if self.type == "K10CR1":
            self.rotator.move_abs(value)
        elif self.type == "elliptec":
            val_dif = (value - self.degree)%360
            val = self.rotator.deg_to_hex(abs(val_dif))
            self.rotator.set_('stepsize',val)
            if val_dif > 0:
                self.rotator.do_("forward")
                self.degree = (self.degree + val_dif)%360
            elif val_dif < 0:
                self.rotator.do_("backward")
                self.degree = (self.degree + val_dif)%360
            else:
                print("No change, moving 0 degrees")