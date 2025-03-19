from cx_Freeze import Executable, setup

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"excludes": ["tkinter"]}

setup(
    name="ged2doc",
    version="0.5.1",
    description="ged2doc command line tool",
    options={"build_exe": build_exe_options},
    executables=[Executable("freeze\\freeze_main.py", targetName="ged2doc.exe", shortcutName="ged2doc")],
)
