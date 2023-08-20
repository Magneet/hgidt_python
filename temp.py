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

RDS_vtpm_checkbox_var = tk.BooleanVar()
RDS_vtpm_checkbox = ttk.Checkbutton(tab2, text="Add vTPM", variable=RDS_vtpm_checkbox_var)
RDS_vtpm_checkbox.place(x=570, y=70)
ToolTip(RDS_vtpm_checkbox, msg="Check to add a vTPM")

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