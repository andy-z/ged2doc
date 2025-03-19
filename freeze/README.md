Building Windows Installer
==========================

This folders contains all necessary files and instructions for building
installer for ged2doc on Windows platform.


Install Python and all packages
-------------------------------

Download and install any reasonable Python distribution, Python3.11+ is
preferred. Make sure that Python is in your PATH and create a virtual
environment::

    cd ...somewhere
    python -m venv venv-gedcom
    venv-gedcom\Scripts\activate.bat  # if in "command" shell

Then install packages::

    pip install ged2doc
    pip install cx_Freeze

Alternatively checkout latest `ged4py`/`ged2doc` and install those.

Checkout ged2doc
----------------

Get `ged2doc` repository from github (you need git installed obviously)::

    git clone https://github.com/andy-z/ged2doc.git


Build executable
----------------

Freezing ged2doc as a standalone executable, make sure that `cxfreeze` is in
the PATH::

    cd ged2doc
    rmdir /s build\exe.win-amd64-3.12
    cxfreeze build_exe

Resulting binaries and all other needed files will appear in the folder
`build\exe.win-amd64-3.12` (assuming you installed 64-bit Python 3.12).


Build installer
---------------

`freeze` folder has a script for `Inno Setup`, check that all paths
in that script are valid (SourceDir, other paths are relative to `freeze`
folder and should be stable) and also verify that version is correct.
Inno Setup should be installed, start Inno Setup Compiler and open
the script, then compile the script which should produce installed
in the `dist` folder with the name like `ged2doc-setup-0.6.1.exe`.
