from cx_Freeze import setup, Executable
import os.path
import keyring


PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')

include_files = [os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tk86t.dll'),
                 os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tcl86t.dll'),
                 'logo.ico']

company_name = 'Retouw'
product_name = 'Horizon Golden Image Deployment Tool'

bdist_msi_options = {
    'upgrade_code': '{666243A-DC3A-11E2-B341-002219E9901E}',
    'add_to_path': False,
    'initial_target_dir': r'[ProgramFilesFolder]\%s\%s' % (company_name, product_name),
    # 'includes': ['atexit', 'PySide.QtNetwork'], # <-- this causes error
}


setup(
    name='Horizon Golden Image deployment Tool',
    version='1',
    description='Tool to apply Golden Images on VMware Horizon',
    author='Wouter Kursten',
    author_email='wouter@retouw.nl',
    options={'build_exe': {'include_files': include_files},
             'build_msi': bdist_msi_options},
    includes=["tkcalendar", "horizon_functions"],
    executables=[Executable('horizon_golden_image_deployment_tool.py',
                            icon='hgidt_logo.ico',
                            base='Win32GUI',
                            shortcut_name="hgidt",
                            shortcut_dir="DesktopFolder")]
)
