pyinstaller.exe .\horizon_golden_image_deployment_tool.py --noconsole --hiddenimport=requests,tkcalendar,horizon_functions.py,tkinter.tk,tkinter.ttk,tkinter,tkcalendar.dateentry,datetime.datetime,datetime.time,datetime.time,babel.dates,babel.core,babel.localedata,babel.numbers,loguru --name "Horizon Golden Image Deployment Tool" --noconfirm --icon=logo.ico --clean --add-data "logo.ico;." --onefile