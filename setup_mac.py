from cx_Freeze import setup, Executable
import os.path

PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
tcldir= '/opt/homebrew/Cellar/tcl-tk/8.6.13_5/lib'
os.environ['TCL_LIBRARY'] = os.path.join(tcldir, 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(tcldir, 'tk8.6')

include_files = [os.path.join(tcldir, 'libtcl8.6.dylib'),
                 os.path.join(tcldir, 'libtcl8.6.dylib'),
                 'logo.ico']

target = Executable(
    script="horizon_golden_image_deployment_tool.py",
    icon="hgidt_logo.icns",
    base=None
    )

setup(
    name='Horizon Golden Image Deployment Tool',
    version='1',
    options={'build_exe': {'include_files': include_files}},
    includes=[ "horizon_functions","babel","babel.numbers","requests","loguru"],
    executables=[target]
)
