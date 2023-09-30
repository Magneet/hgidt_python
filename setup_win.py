from cx_Freeze import setup, Executable
import os.path

PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')

include_files = [os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tk86t.dll'),
                 os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tcl86t.dll'),
                 'logo.ico']

setup(
    name='Horizon Golden Image deployment Tool',
    version='1',
    options={'build_exe': {'include_files': include_files}},
    includes=["tkinter.tktooltip", "tkcalendar", "horizon_functions"],
    executables=[Executable('gui_only.py',
                            icon='hgidt_logo.ico', 
                            base='Win32GUI')]
)
