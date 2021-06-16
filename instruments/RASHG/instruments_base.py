import param


class instruments_base(param.Parameterized):
    initialized = param.Boolean(default=False, precedence=-1)  # dummy variable to make code work
    type = "base"

    def __init__(self):
        super().__init__()

    def initialize(self):
        pass

    def get_frame(self, xs):
        pass

    def live(self):
        pass

    def widgets(self):
        return self.param

    def start(self):
        pass