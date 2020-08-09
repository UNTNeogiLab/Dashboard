import os
import argparse


def install(Mamba=False):
    if (Mamba):
        os.system('conda install mamba -c conda-forge')
        if (os.environ['CONDA_DEFAULT_ENV'] != "python"):
            print("Activating environment")
            os.system('conda activate python')
            if (os.environ['CONDA_DEFAULT_ENV'] != "python"):
                print("Failed: Environment doesn't exist")
                print("Creating environment: this will take a while")
                os.chdir("config")
                os.system('mamba env create')
                os.system('conda activate python')
            else:
                print("environment exists")
                os.chdir("config")
                os.system('mamba env update')
        else:
            print("Updating environment")
            os.chdir("config")
            os.system('mamba env update')
        os.chdir("..")
    else:
        if (os.environ['CONDA_DEFAULT_ENV'] != "python"):
            print("Activating environment")
            os.system('conda activate python')
            if (os.environ['CONDA_DEFAULT_ENV'] != "python"):
                print("Failed: Environment doesn't exist")
                print("Creating environment: this will take a while")
                os.system('conda env create -f config/environment.yml')
                os.system('conda activate python')
            else:
                print("environment exists")
                os.system('conda env update --name python --file config/environment.yml')
        else:
            print("Updating environment")
            os.system('conda env update --name python --file config/environment.yml')


def build_Jupyter():
    print("Configuring Jupyter:")
    os.system('jupyter lab workspaces import config/lab.json')
    os.system('jupyter labextension install @pyviz/jupyterlab_pyviz --no-build')
    os.system('jupyter labextension install @bokeh/jupyter_bokeh --no-build')
    os.system('jupyter labextension install @jupyter-widgets/jupyterlab-manager --no-build')
    os.system('jupyter labextension install dask-labextension --no-build')
    os.system('jupyter lab build')


def run_bokeh(ip='', port=5006):
    os.system('panel serve holoviz.ipynb')


def run_jupyter():
    os.system('jupyter lab')


def update(Mamba=False):
    if (Mamba):
        os.chdir("config")
        os.system('mamba env update')
    else:
        os.system('conda env update --name python --file config/environment.yml')


parser = argparse.ArgumentParser(prog='setup',
                                 description='Install and Run python. Only one argument executes in the following order. No arguments will default to running a panel server')
parser.add_argument('--R', dest='R',
                    help='Builds and Runs Bokeh Server using mamba (Doesn\'t install Jupyter components)',
                    action='store_const', const=True, default=False)
parser.add_argument('--J', dest='J', help='Builds and runs Jupter Server using mamba', action='store_const', const=True,
                    default=False)
parser.add_argument('--B', dest='B', help='Installs or Upgrades environment w/ Jupyter components using conda',
                    action='store_const', const=True, default=False)
parser.add_argument('--U', dest='U', help='Updates environment using conda(NOT RECCOMENDED)', action='store_const',
                    const=True, default=False)
parser.add_argument('--M', dest='M', help='Installs or Upgrades environment w/ Jupyter components using mamba',
                    action='store_const', const=True, default=False)
parser.add_argument('--MU', dest='MU', help='Updates environment using mamba(NOT RECCOMENDED)', action='store_const',
                    const=True, default=False)
parser.add_argument('--BJ', dest='BJ', help='Builds Jupyter lab extensions', action='store_const',
                    const=True, default=False)
args = parser.parse_args()
if args.R:
    install(Mamba=True)
    run_bokeh()
elif args.J:
    install(Mamba=True)
    build_Jupyter()
    run_jupyter()
elif args.B:
    install()
    build_Jupyter()
elif args.U:
    update(Mamba=False)
elif args.BJ:
    build_Jupyter()
elif args.M:
    print("Using Mamba")
    install(Mamba=True)
    build_Jupyter()
elif args.MU:
    print("Using Mamba")
    update(Mamba=True)
else:
    print("No arguments given, defaulting to launching panel server")
    install(Mamba=True)
    build_Jupyter()
    run_bokeh()
