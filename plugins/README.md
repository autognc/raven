# Raven Training Plugins
Default training plugins for Raven, and examples for making your own plugins.

## Structure
All plugins are independent and separate Python packages with the following structure:
```
package_name/                   # name of the package, with underscores
    package_name/               # ''
        __init__.py             
        core.py                 # core of plugin - contains command group 
                                    entire plugin flows from
    install.sh                  # install script for the plugin
    requirements.in             # user created requirements file for CPU install
    requirements-gui.in         # user created requirements file for GPU install
    requirements.txt            # pip-compile created requirements file for CPU install
    requirements-gui.txt        # pip-compile created requirements file for GPU install
    setup.py                    # python package setuptools
```
Additional files, directories, and modules can be created as needed. Just be sure to include
an `__init__.py` in every directory you create, and think in modules.

## Requirements Scheme
In order to support both GPU and CPU installs, each plugin will depend on
requirements files rather than packages in `install_requires` in `setup.py`. 
We use [pip-compile](https://github.com/jazzband/pip-tools) to maintain all requirements with
uninstall functionality. Developers should create **two files**:
1. requirements.in
2. requirements-gui.in

These files are manually maintained and include all python packages which the plugin
depends on (such as tensorflow, pytorch, etc). Crucially, they do **not** contain 
these packages' dependencies. `pip-compile` is then used on the `.in` files to create
two files:
1. requirements.txt
2. requirements-gui.txt

Which are created by the command:
```
pip-compile --out-file <prefix>.txt <prefix>.in
```

### install.sh
An `install.sh` script should be written to handle all install logic (including updating pip-compile created requirements files) and ensure 
external dependenices (such as NVIDIA Drivers or additional packages) are met on install. When uninstalling, this script
should **only** handle the uninstall logic for the package itself, not its dependenices. The reason for the difference in 
behavior between install and uninstall is simple: Because many
plugins will have similar dependencies, which themselves share dependencies, we cannot safely remove
all of an individual plugin's dependenices without uninstalling all plugins. What this means for plugins in this directory:
- Plugins can be installed individually using their respective `install.sh` script.
- Plugins can also be installed en masse using `install_all.sh` at the root of this directory.
- Plugins can **exclusively** be uninstalled en masse using `install_all.sh` at the root of this directory.
If you uninstall a plugin individually using its `install.sh` script, you will **only** be uninstalling the plugin itself;
none of its dependencies will be cleaned up. This should be avoided to prevent creating a bloated environment.

All `install.sh` scripts should support two flags:
- `-u`: uninstall. Passed to uninstall the plugin itself.
- `-g`: GPU install. Can be paired with `-u` for uninstalling a GPU install.

### install_all.sh
Installs all plugins in this directory using their `install.sh` scripts. Mostly a convenience item when installing.
When uninstalling, this script should be used **exclusively** in place of any individual plugin's `install.sh` script.
It supports the same two flags as any `install.sh`:
- `-u`: uninstall. Passed to uninstall all plugins, including all plugin dependencies.
- `-g` GPU install. Can be paired with `-g` for uninstalling a GPU install.

`install_all.sh` contains logic to ensure that if any plugins share dependencies with Raven core these dependencies
remain met at the compeition of the pluigin uninstall. This is accomplished by verifying the environment against its
`environment.yml` file once `install.sh -u` script is run for each plugin.

## Making a Plugin

Create a plugin using the following steps:

### 1. Create file structure.
Every Raven training plugin will begin with the following file structure:
```
package_name/                   # name of the package, with underscores
    package_name/               # ''
        __init__.py             
        core.py                 # core of plugin - contains command group 
                                    entire plugin flows from
    install.sh                  # install script for the plugin
    requirements.in             # user created requirements file for CPU install
    requirements-gui.in         # user created requirements file for GPU install
    setup.py 
```

We will go through each of these files individually in the next steps.

#### Inner `package_name/` directory
This directory contains the source code for the plugin itself. Inside are two files:
1. `__init__.py`: empty file which marks this at a python module.
2. `core.py`: core of the plugin where the top level command group is located. Go from the skeleton below:
```css
import click
from raven.train.options import kfold_opt, pass_train
from raven.train.interfaces import TrainInput, TrainOutput

@click.group(help='Top level command group description')
@click.pass_context
@kfold_opt
def <module_name_no_raven>(ctx, kfold):
    pass
    
@<module_name_no_raven>.command()
@pass_train
@click.pass_context
def train(ctx, train: TrainInput):
    # If the context (ctx) has a TrainInput already, it is passed as "train"
    # If it does not, the constructor is called AUTOMATICALLY
    # by Click because the @pass_train decorator is set to ensure
    # object creation, after which the created object is passed as "train"
    # after training, create an instance of TrainOutput and return it
    result = TrainOutput()
    return result               # return result back up the command chain
```
`TrainInput` and `TrainOutput` are described in detail in the [Interfaces](#interfaces) section.

#### `setup.py`
