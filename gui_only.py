import tkinter as tk
from tkinter import ttk
from tktooltip import ToolTip
from tkcalendar import DateEntry
from tktimepicker import SpinTimePickerModern
from tktimepicker import constants

def on_button_click():
    print("Button Clicked!")

def updateTime(time):
    time_lbl.configure(text="{}:{}".format(*time)) # if you are using 24 hours, remove the 3rd flower bracket its for period


root = tk.Tk()
root.title("Horizon Image Deployment Tool")
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
VDI_TimePicker.

# Tab 2 - RDS Farms
tab2 = ttk.Frame(tab_control)
tab_control.add(tab2, text="RDS Farms")

# Place your Tab 2 widgets here
# Example:
RDS_Connect_Button = tk.Button(tab2, text="Connect")
RDS_Connect_Button.place(x=570, y=30, width=160, height=22)
# ... Add other widgets ...

# Tab 3 - Configuration
tab3 = ttk.Frame(tab_control)
tab_control.add(tab3, text="Configuration")

# Place your Tab 3 widgets here
# Example:
config_save_config_button = tk.Button(tab3, text="Save Configuration")
config_save_config_button.place(x=30, y=226, width=160, height=22)
# ... Add other widgets ...

# Handling of tooltips
tooltip_label = ttk.Label(root, background="yellow", relief="solid", padding=(5, 2), justify="left")
tooltip_label.place_forget()


# Start the GUI event loop
root.mainloop()
