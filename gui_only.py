import tkinter as tk
from tkinter import ttk,simpledialog
from tktooltip import ToolTip
from tkcalendar import DateEntry
from tktimepicker import SpinTimePickerModern
from tktimepicker import constants
import configparser, os, horizon_functions, logging, sys
from logging.handlers import RotatingFileHandler

#region logging
# we need to have some logging in here 
LOG_FILE = "hgidt.log"
# Configure logging with rotating log files
log_handler = RotatingFileHandler(LOG_FILE, maxBytes=1024*1024, backupCount=3)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)
logger = logging.getLogger('hgidt')
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)

# Custom exception handler
def exception_handler(exc_type, exc_value, exc_traceback):
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

# Set the custom exception handler
sys.excepthook = exception_handler
#endregion

#region configuration
# Load the config file if one exists
CONFIG_FILE = 'config.ini'
config = configparser.ConfigParser()
config.read(CONFIG_FILE)

config_username = None
config_domain = None
config_server_name = None
config_password = None
config_url= None

if 'UserInfo' in config:
    config_username = config.get('UserInfo', 'Username')
    config_domain = config.get('UserInfo', 'Domain')
    config_server_name = config.get('UserInfo', 'ServerName')
#endregion

#region Configuration related defs

def write_config(username, domain, server_name):
    config = configparser.ConfigParser()
    config['UserInfo'] = {'Username': username, 'Domain': domain, 'ServerName': server_name}
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

def read_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    if 'UserInfo' in config:
        config_username = config.get('UserInfo', 'Username')
        config_domain = config.get('UserInfo', 'Domain')
        config_server_name = config.get('UserInfo', 'ServerName')
        print(config_username)
        print(config_domain)
        print(config_server_name)
        # return config_username, config_domain, config_server_name
        config_username_textbox.insert(tk.END, config_username)
        config_domain_textbox.insert(tk.END, config_domain)
        config_conserver_textbox.insert(tk.END, config_server_name)
    else:
        return None

def reset_config():
    config = configparser.ConfigParser()
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

def show_password_dialog():
    password = simpledialog.askstring("Password", "Enter your password:", show='*')
    if password is not None:
        global config_password
        config_password=password
        config_status_label.config(text="Password set")

#endregion

#region defs for button handling of configuration tab

def config_save_button_callback():
    logger.info("Saving configuration")
    username = config_username_textbox.get()
    domain = config_domain_textbox.get()
    server_name = config_conserver_textbox.get()
    global config_username, config_domain, config_server_name
    if username == config_username_textbox_default_text or domain == config_domain_textbox_default_text or server_name == config_conserver_textbox_default_text:
        config_username = None
        config_domain = None
        config_server_name = None
        config_status_label.config(text="Please enter Connection Server, Username and password first.")
    else:
        write_config(username, domain, server_name)
        config_username = username
        config_domain = domain
        config_server_name = server_name
        config_status_label.config(text="Configuration saved")
        logger.info("Configuration saved")

def config_reset_button_callback():
    logger.info("Resetting configuration")
    reset_config()
    global config_username, config_domain, config_server_name
    config_username_textbox.delete(0, tk.END)
    config_username_textbox.insert(tk.END, config_username_textbox_default_text)
    config_username_textbox.config(foreground='grey')
    config_username = None
    config_domain_textbox.delete(0, tk.END)
    config_domain_textbox.insert(tk.END, config_domain_textbox_default_text)
    config_domain_textbox.config(foreground='grey')
    config_domain = None
    config_conserver_textbox.delete(0, tk.END)
    config_conserver_textbox.insert(tk.END, config_conserver_textbox_default_text)
    config_conserver_textbox.config(foreground='grey')
    config_server_name = None
    config_url=None
    config = configparser.ConfigParser()
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    config_status_label.config(text="Configuration reset and configuration file deleted.")
    logger.info("Configuration reset")

def config_test_button_callback():
    logger.info("Testing configuration")
    config_status_label.config(text="Testing configuration")
    refresh_window()
    config_save_button_callback()
    print(config_username)
    print(config_domain)
    print(config_server_name)
    if config_username is None or config_domain is None or config_server_name is None:
        logger.error("Cannot test due to missing configuration")
        config_status_label.config(text="Not all information is provided, please check the configuration.")
    elif config_password is None:
        logger.error("No password was set")
        config_status_label.config(text="Please set a password first")
    else:
        logger.info("Testing connection to: "+config_server_name)
        config_url = "https://" + config_server_name
        hvconnectionobj = horizon_functions.Connection(username = config_username,domain = config_domain,password = config_password,url = config_url)
        try:
            hvconnectionobj.hv_connect()
            logger.info("Sucessfully finished testing configuration")
            config_status_label.config(text="Successfully finished testing configuration")
        except Exception as e:
            config_status_label.config(text="Error testing the connection, see the log file for details")
            logger.error("Error while testing the credentials")
            logger.error(str(e))

#endregion

#region Various definitions

def refresh_window():
    # Redraw the window
    root.update()
    root.update_idletasks()

def updateTime(time):
    time_lbl.configure(text="{}:{}".format(*time)) # if you are using 24 hours, remove the 3rd flower bracket its for period

def textbox_handle_focus_in(event,default_text):
    if event.widget.get() == default_text:
        event.widget.delete(0,'end')
        event.widget.config(foreground='black')  # Change text color to black when editing

def textbox_handle_focus_out(event,default_text):
    if event.widget.get().strip() == '':
        event.widget.insert(tk.END, default_text)
        event.widget.config(foreground='grey')  # Change text color to grey when not editing
#endregion

root = tk.Tk()
root.title("Horizon Golden Image Deployment Tool")
root.geometry("800x660")

# Create Canvas
canvas = tk.Canvas(root)
canvas.pack(fill="both", expand=True)

# Create TabControl
tab_control = ttk.Notebook(canvas)
tab_control.pack(fill="both", expand=True)

# Tab 1 - Desktop Pools
tab1 = ttk.Frame(tab_control)
tab_control.add(tab1, text="VDI Pools")

# Place your Tab 1 widgets here
# Create Buttons
VDI_Connect_Button = tk.Button(tab1, text="Connect")
VDI_Connect_Button.place(x=570, y=30, width=160, height=22)

VDI_Apply_Golden_Image_button = tk.Button(tab1, text="Deploy Golden Image")
VDI_Apply_Golden_Image_button.place(x=570, y=510, width=160, height=22)

VDI_Apply_Secondary_Image_button = tk.Button(tab1, text="Apply Secondary Image")
VDI_Apply_Secondary_Image_button.place(x=570, y=456, width=160, height=22)

VDI_Cancel_Secondary_Image_button = tk.Button(tab1, text="Cancel secondary Image")
VDI_Cancel_Secondary_Image_button.place(x=570, y=430, width=160, height=22)

VDI_Promote_Secondary_Image_button = tk.Button(tab1, text="Promote secondary Image")
VDI_Promote_Secondary_Image_button.place(x=570, y=483, width=160, height=22)

# Create Labels
VDI_Statusbox_Label = tk.Label(tab1, borderwidth=1, text="Status: Not Connected", justify="right")
VDI_Statusbox_Label.place(x=430, y=537)

# VDI_timepicker_label = tk.Label(tab1, borderwidth=1, text=":", justify="right")
# VDI_timepicker_label.place(x=615, y=310)

# Create ComboBoxes
VDI_DesktopPool_Combobox = ttk.Combobox(tab1)
VDI_DesktopPool_Combobox.place(x=30, y=30, width=150, height=22)
ToolTip(VDI_DesktopPool_Combobox, msg="Select the desktop pool to update")

VDI_Golden_Image_Combobox = ttk.Combobox(tab1)
VDI_Golden_Image_Combobox.place(x=210, y=30, width=150, height=22)
ToolTip(VDI_Golden_Image_Combobox, msg="Select the new source VM")

VDI_Snapshot_Combobox = ttk.Combobox(tab1)
VDI_Snapshot_Combobox.place(x=390, y=30, width=150, height=22)
ToolTip(VDI_Snapshot_Combobox, msg="Select the new source Snapshot")

VDI_LofOffPolicy_Combobox = ttk.Combobox(tab1)
VDI_LofOffPolicy_Combobox.place(x=570, y=110, width=160, height=22)
ToolTip(VDI_LofOffPolicy_Combobox, msg="Select the logoff Policy")

VDI_Memory_ComboBox = ttk.Combobox(tab1)
VDI_Memory_ComboBox.place(x=570, y=160, width=160, height=22)
ToolTip(VDI_Memory_ComboBox, msg="Select the new memory size")

VDI_CPUCount_ComboBox = ttk.Combobox(tab1)
VDI_CPUCount_ComboBox.place(x=570, y=190, width=160, height=22)
ToolTip(VDI_CPUCount_ComboBox, msg="Select the new CPU count")

VDI_CoresPerSocket_ComboBox = ttk.Combobox(tab1)
VDI_CoresPerSocket_ComboBox.place(x=570, y=220, width=160, height=22)
ToolTip(VDI_CoresPerSocket_ComboBox, msg="Select the number of cores per socket")

# Create Checkboxes
VDI_secondaryimage_checkbox_var = tk.BooleanVar()
VDI_secondaryimage_checkbox = ttk.Checkbutton(tab1, text="Push as Secondary Image", variable=VDI_secondaryimage_checkbox_var)
VDI_secondaryimage_checkbox.place(x=570, y=342)
ToolTip(VDI_secondaryimage_checkbox, msg="Check to deploy the new golden image as a secondary image")

VDI_StopOnError_checkbox_var = tk.BooleanVar()
VDI_StopOnError_checkbox = ttk.Checkbutton(tab1, text="Stop on error", variable=VDI_StopOnError_checkbox_var)
VDI_StopOnError_checkbox.place(x=570, y=90)
ToolTip(VDI_StopOnError_checkbox, msg="CHeck to make sure deployment of new desktops stops on an error")
VDI_StopOnError_checkbox_var.set(True)

VDI_Resize_checkbox_var = tk.BooleanVar()
VDI_Resize_checkbox = ttk.Checkbutton(tab1, text="Enable Resize Options", variable=VDI_Resize_checkbox_var)
VDI_Resize_checkbox.place(x=570, y=137)
ToolTip(VDI_Resize_checkbox, msg="Check to enable resizing of the Golden Image in the Desktop Pool")

VDI_vtpm_checkbox_var = tk.BooleanVar()
VDI_vtpm_checkbox = ttk.Checkbutton(tab1, text="Add vTPM", variable=VDI_vtpm_checkbox_var)
VDI_vtpm_checkbox.place(x=570, y=70)
ToolTip(VDI_vtpm_checkbox, msg="Check to add a vTPM")

VDI_Enable_datetimepicker_checkbox_var = tk.BooleanVar()
VDI_Enable_datetimepicker_checkbox = ttk.Checkbutton(tab1, text="Schedule deployment", variable=VDI_Enable_datetimepicker_checkbox_var)
VDI_Enable_datetimepicker_checkbox.place(x=570, y=250)
ToolTip(VDI_Enable_datetimepicker_checkbox, msg="Check to enable a scheduled deployment of the new image")

# Create other Widgets
VDI_Status_Textblock = tk.Text(tab1, borderwidth=1, relief="solid", wrap="word")
VDI_Status_Textblock.place(x=30, y=80, height=305, width=510)

VDI_Machines_ListBox = tk.Listbox(tab1, selectmode="multiple")
VDI_Machines_ListBox.place(x=30, y=413, height=150, width=300)

VDI_cal = DateEntry(tab1,bg="darkblue",fg="white",year=2023)
VDI_cal.config(state="disabled")
VDI_cal.place(x=570,y=280)

VDI_TimePicker = SpinTimePickerModern(tab1)
VDI_TimePicker.addAll(constants.HOURS24)  # adds hours clock, minutes and period
VDI_TimePicker.place(x=570,y=310)


#region Tab 2 - RDS Farms
tab2 = ttk.Frame(tab_control)
tab_control.add(tab2, text="RDS Farms")

# Place your Tab 2 widgets here
# create buttons
RDS_Connect_Button = tk.Button(tab2, text="Connect")
RDS_Connect_Button.place(x=570, y=30, width=160, height=22)

RDS_Apply_Golden_Image_button = tk.Button(tab2, text="Deploy Golden Image")
RDS_Apply_Golden_Image_button.place(x=570, y=510, width=160, height=22)

RDS_Apply_Secondary_Image_button = tk.Button(tab2, text="Apply Secondary Image")
RDS_Apply_Secondary_Image_button.place(x=570, y=456, width=160, height=22)

RDS_Cancel_Secondary_Image_button = tk.Button(tab2, text="Cancel secondary Image")
RDS_Cancel_Secondary_Image_button.place(x=570, y=430, width=160, height=22)

RDS_Promote_Secondary_Image_button = tk.Button(tab2, text="Promote secondary Image")
RDS_Promote_Secondary_Image_button.place(x=570, y=483, width=160, height=22)

# Create Labels
RDS_Statusbox_Label = tk.Label(tab2, borderwidth=1, text="Status: Not Connected", justify="right")
RDS_Statusbox_Label.place(x=430, y=537)

# RDS_timepicker_label = tk.Label(tab2, borderwidth=1, text=":", justify="right")
# RDS_timepicker_label.place(x=615, y=310)

# Create ComboBoxes
RDS_DesktopPool_Combobox = ttk.Combobox(tab2)
RDS_DesktopPool_Combobox.place(x=30, y=30, width=150, height=22)
ToolTip(RDS_DesktopPool_Combobox, msg="Select the desktop pool to update")

RDS_Golden_Image_Combobox = ttk.Combobox(tab2)
RDS_Golden_Image_Combobox.place(x=210, y=30, width=150, height=22)
ToolTip(RDS_Golden_Image_Combobox, msg="Select the new source VM")

RDS_Snapshot_Combobox = ttk.Combobox(tab2)
RDS_Snapshot_Combobox.place(x=390, y=30, width=150, height=22)
ToolTip(RDS_Snapshot_Combobox, msg="Select the new source Snapshot")

RDS_LofOffPolicy_Combobox = ttk.Combobox(tab2)
RDS_LofOffPolicy_Combobox.place(x=570, y=110, width=160, height=22)
ToolTip(RDS_LofOffPolicy_Combobox, msg="Select the logoff Policy")

RDS_Memory_ComboBox = ttk.Combobox(tab2)
RDS_Memory_ComboBox.place(x=570, y=160, width=160, height=22)
ToolTip(RDS_Memory_ComboBox, msg="Select the new memory size")

RDS_CPUCount_ComboBox = ttk.Combobox(tab2)
RDS_CPUCount_ComboBox.place(x=570, y=190, width=160, height=22)
ToolTip(RDS_CPUCount_ComboBox, msg="Select the new CPU count")

RDS_CoresPerSocket_ComboBox = ttk.Combobox(tab2)
RDS_CoresPerSocket_ComboBox.place(x=570, y=220, width=160, height=22)
ToolTip(RDS_CoresPerSocket_ComboBox, msg="Select the number of cores per socket")

# Create Checkboxes
RDS_secondaryimage_checkbox_var = tk.BooleanVar()
RDS_secondaryimage_checkbox = ttk.Checkbutton(tab2, text="Push as Secondary Image", variable=RDS_secondaryimage_checkbox_var)
RDS_secondaryimage_checkbox.place(x=570, y=342)
ToolTip(RDS_secondaryimage_checkbox, msg="Check to deploy the new golden image as a secondary image")

RDS_StopOnError_checkbox_var = tk.BooleanVar()
RDS_StopOnError_checkbox = ttk.Checkbutton(tab2, text="Stop on error", variable=RDS_StopOnError_checkbox_var)
RDS_StopOnError_checkbox.place(x=570, y=90)
ToolTip(RDS_StopOnError_checkbox, msg="CHeck to make sure deployment of new desktops stops on an error")
RDS_StopOnError_checkbox_var.set(True)

RDS_Resize_checkbox_var = tk.BooleanVar()
RDS_Resize_checkbox = ttk.Checkbutton(tab2, text="Enable Resize Options", variable=RDS_Resize_checkbox_var)
RDS_Resize_checkbox.place(x=570, y=137)
ToolTip(RDS_Resize_checkbox, msg="Check to enable resizing of the Golden Image in the Desktop Pool")

RDS_Enable_datetimepicker_checkbox_var = tk.BooleanVar()
RDS_Enable_datetimepicker_checkbox = ttk.Checkbutton(tab2, text="Schedule deployment", variable=RDS_Enable_datetimepicker_checkbox_var)
RDS_Enable_datetimepicker_checkbox.place(x=570, y=250)
ToolTip(RDS_Enable_datetimepicker_checkbox, msg="Check to enable a scheduled deployment of the new image")

# Create other Widgets
RDS_Status_Textblock = tk.Text(tab2, borderwidth=1, relief="solid", wrap="word")
RDS_Status_Textblock.place(x=30, y=80, height=305, width=510)

RDS_Machines_ListBox = tk.Listbox(tab2, selectmode="multiple")
RDS_Machines_ListBox.place(x=30, y=413, height=150, width=300)

RDS_cal = DateEntry(tab2,bg="darkblue",fg="white",year=2023)
RDS_cal.config(state="disabled")
RDS_cal.place(x=570,y=280)

RDS_TimePicker = SpinTimePickerModern(tab2)
RDS_TimePicker.addAll(constants.HOURS24)  # adds hours clock, minutes and period
RDS_TimePicker.place(x=570,y=310)

#endregion


#region Tab 3 - Configuration
tab3 = ttk.Frame(tab_control)
tab_control.add(tab3, text="Configuration")

# Place your Tab 3 widgets here
# Create Buttons

config_get_password_button = ttk.Button(tab3, text="Get Password", command=show_password_dialog)
config_get_password_button.place(x=30, y=150)

config_save_button = ttk.Button(tab3, text="Save Configuration",command=config_save_button_callback)
config_save_button.place(x=30, y=226)

config_reset_button = ttk.Button(tab3, text="Reset Configuration",command=config_reset_button_callback)
config_reset_button.place(x=30, y=198)

config_test_credential_button = ttk.Button(tab3, text="Test Credentials",command=config_test_button_callback)
config_test_credential_button.place(x=30, y=255)

# Create TextBoxes
config_conserver_textbox = ttk.Entry(tab3)
config_conserver_textbox_default_text= "Enter Connectionserver DNS"
if config_server_name is not None:
    config_conserver_textbox.insert(tk.END, config_server_name)
    config_conserver_textbox.config(foreground='black')
else:
    config_conserver_textbox.insert(tk.END, config_conserver_textbox_default_text)
    config_conserver_textbox.config(foreground='grey')
config_conserver_textbox.bind("<FocusIn>", lambda event, var=config_conserver_textbox_default_text: textbox_handle_focus_in(event, var))
config_conserver_textbox.bind("<FocusOut>" , lambda event, var=config_conserver_textbox_default_text: textbox_handle_focus_out(event, var))
config_conserver_textbox.place(x=30, y=50, width=200)

config_username_textbox = ttk.Entry(tab3)
config_username_textbox_default_text= "UserName"
if config_username is not None:
    config_username_textbox.insert(tk.END, config_username)
    config_username_textbox.config(foreground='black')
else:
    config_username_textbox.insert(tk.END, config_username_textbox_default_text)
    config_username_textbox.config(foreground='grey')
config_username_textbox.bind("<FocusIn>", lambda event, var=config_username_textbox_default_text: textbox_handle_focus_in(event, var))
config_username_textbox.bind("<FocusOut>" , lambda event, var=config_username_textbox_default_text: textbox_handle_focus_out(event, var))
config_username_textbox.place(x=30, y=100, width=150)

config_domain_textbox = ttk.Entry(tab3)
config_domain_textbox_default_text= "Domain"
if config_domain is not None:
    config_domain_textbox.insert(tk.END, config_domain)
    config_domain_textbox.config(foreground='black')
else:
    config_domain_textbox.insert(tk.END, config_domain_textbox_default_text)
    config_domain_textbox.config(foreground='grey')
config_domain_textbox.bind("<FocusIn>", lambda event, var=config_domain_textbox_default_text: textbox_handle_focus_in(event, var))
config_domain_textbox.bind("<FocusOut>" , lambda event, var=config_domain_textbox_default_text: textbox_handle_focus_out(event, var))
config_domain_textbox.place(x=30, y=125, width=150)

# Create Labels
config_conserver_label = ttk.Label(tab3, text="Connection Server")
config_conserver_label.place(x=30, y=20)

config_pod_label = ttk.Label(tab3, text="Pod")
config_pod_label.place(x=270, y=20)

config_status_label = ttk.Label(tab3, text="Status: N/A")
config_status_label.place(x=30, y=290)

# Create ComboBoxes
config_pod_combobox = ttk.Combobox(tab3)
config_pod_combobox.place(x=270, y=50, width=200)

config_conserver_combobox = ttk.Combobox(tab3)
config_conserver_combobox.place(x=510, y=50, width=200)

# Create CheckBox
config_ignore_cert_errors_checkbox = ttk.Checkbutton(tab3, text="Ignore Certificate Errors")
config_ignore_cert_errors_checkbox.place(x=30, y=175)
#endregion

# Handling of tooltips
tooltip_label = ttk.Label(root, background="yellow", relief="solid", padding=(5, 2), justify="left")
tooltip_label.place_forget()

# Start the GUI event loop
root.mainloop()
