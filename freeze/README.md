Building Windows Installer
==========================

This folders cotnains all necessary files and instructions for building
installer for ged2doc on Windows platform.


Install Python and all packages
-------------------------------

Download and install any reasonable Python distribution, Python3 is
preferred because it has `pip` bundled already. Make sure that Python
is in your PATH and install packages::

    pip install ged2doc
    pip install cx_Freeze

`cx_Freeze` may not be compatible with latest `setuptools` versions, if
you run resulting ged2doc executable and see error like::

    ImportError: The 'six' package is required; ...

then you need to downgrade setuptools, version 19.2 is known to work::

    pip install setuptools==19.2


Checkout ged2doc
----------------

Get ged2doc from github (you need git installed obviously)::

    git clone https://github.com/andy-z/ged2doc.git


Build executable
----------------

Freezing ged2doc as a standalone executable, make sure that Python is in
the PATH::

    cd ged2doc
    python freeze\setup.py build_exe

Resulting binaries and all other needed files will appear in the folder
`build\exe.win32-3.6` (assuming you installed 32-bit Python 3.6).


Build installer
---------------

`freeze` folder has a script for Inno Setup, check that all paths
in that script are valid (SourceDir, other paths are relative to `freeze`
folder and should be stable) and also verify that version is correct.
Inno Setup should be installed, start Inno Setup Compiler and open
the script, then compile the script which should produce installed
in the `dist` folder with the name like `ged2doc-setup-0.1.10.exe`.
