import dask.distributed
import param


class GrapherBase(param.Parameterized):
    """base class for graphers"""

    def __init__(self, filename: str, client: dask.distributed.Client):
        super().__init__()

    def widgets(self):
        pass

    def view(self):
        pass

    def close(self):
        pass
