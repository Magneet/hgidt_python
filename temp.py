
RDS_Connect_Button = ttk.Button(tab2, text="Connect", command=generic_Connect_Button_callback)
RDS_Connect_Button.place(x=750, y=30, width=160, height=25)


RDS_Apply_Golden_Image_button = ttk.Button(tab2, state="disabled", text="Deploy Golden Image",command=RDS_Apply_Golden_Image_button_callback)
RDS_Apply_Golden_Image_button.place(x=570, y=510, width=220, height=25)

RDS_Apply_Secondary_Image_button = ttk.Button(tab2, state="disabled", text="Apply Secondary Image", command = RDS_Apply_Secondary_Image_button_callback)
RDS_Apply_Secondary_Image_button.place(x=570, y=456, width=220, height=25)

RDS_Cancel_Secondary_Image_button = ttk.Button(tab2, state="disabled", text="Cancel Image Push", command=RDS_Cancel_Secondary_Image_button_callback)
RDS_Cancel_Secondary_Image_button.place(x=570, y=430, width=220, height=25)

RDS_Promote_Secondary_Image_button = ttk.Button(tab2, state="disabled", text="Promote secondary Image", command=RDS_Promote_Secondary_Image_button_callback)
RDS_Promote_Secondary_Image_button.place(x=570, y=483, width=220, height=25)

# Create Labels
RDS_Statusbox_Label = tk.Label(tab2, borderwidth=1, text="Status: Not Connected", justify="right")
RDS_Statusbox_Label.place(x=430, y=537)


# Create ComboBoxes
RDS_RdsFarm_Combobox_var = tk.StringVar()
RDS_RdsFarm_Combobox = ttk.Combobox(tab2, state="disabled", textvariable=RDS_RdsFarm_Combobox_var)
RDS_RdsFarm_Combobox.place(x=30, y=30, width=220, height=25)
RDS_RdsFarm_Combobox.bind("<<ComboboxSelected>>",RDS_RdsFarm_Combobox_callback)
ToolTip(RDS_RdsFarm_Combobox, msg="Select the Rds Farm to update", delay=0.1)

RDS_Golden_Image_Combobox_var = tk.StringVar()
RDS_Golden_Image_Combobox = ttk.Combobox(tab2, state="disabled", textvariable=RDS_Golden_Image_Combobox_var)
RDS_Golden_Image_Combobox.place(x=270, y=30, width=220, height=25)
RDS_Golden_Image_Combobox.bind("<<ComboboxSelected>>",RDS_Golden_Image_Combobox_callback)
ToolTip(RDS_Golden_Image_Combobox, msg="Select the new source VM", delay=0.1)

RDS_Snapshot_Combobox_var = tk.StringVar()
RDS_Snapshot_Combobox = ttk.Combobox(tab2, state="disabled", textvariable=RDS_Snapshot_Combobox_var)
RDS_Snapshot_Combobox.place(x=510, y=30, width=220, height=25)
RDS_Snapshot_Combobox.bind("<<ComboboxSelected>>",RDS_Snapshot_Combobox_callback)
ToolTip(RDS_Snapshot_Combobox, msg="Select the new source Snapshot", delay=0.1)

RDS_LofOffPolicy_Combobox_var = tk.StringVar()
RDS_LofOffPolicy_Combobox = ttk.Combobox(tab2, state="disabled", values=["FORCE_LOGOFF","WAIT_FOR_LOGOFF"], textvariable=RDS_LofOffPolicy_Combobox_var)
RDS_LofOffPolicy_Combobox_default_value = "WAIT_FOR_LOGOFF"
RDS_LofOffPolicy_Combobox.set(RDS_LofOffPolicy_Combobox_default_value)
RDS_LofOffPolicy_Combobox.place(x=570, y=110, width=160, height=25)
ToolTip(RDS_LofOffPolicy_Combobox, msg="Select the logoff Policy", delay=0.1)

RDS_Memory_ComboBox_var = tk.StringVar()
RDS_Memory_ComboBox = ttk.Combobox(tab2, state="disabled", values=memory_list,textvariable=RDS_Memory_ComboBox_var)
RDS_Memory_ComboBox.place(x=570, y=160, width=160, height=25)
ToolTip(RDS_Memory_ComboBox, msg="Select the new memory size", delay=0.1)

RDS_CPUCount_ComboBox_var = tk.StringVar()
RDS_CPUCount_ComboBox = ttk.Combobox(tab2, state="disabled", values=onetosixtyfour, textvariable=RDS_CPUCount_ComboBox_var)
RDS_CPUCount_ComboBox.place(x=570, y=190, width=160, height=25)
ToolTip(RDS_CPUCount_ComboBox, msg="Select the new CPU count", delay=0.1)

RDS_CoresPerSocket_ComboBox_var = tk.StringVar()
RDS_CoresPerSocket_ComboBox = ttk.Combobox(tab2, state="disabled", values=onetosixtyfour,textvariable=RDS_CoresPerSocket_ComboBox_var)
RDS_CoresPerSocket_ComboBox.place(x=570, y=220, width=160, height=25)
ToolTip(RDS_CoresPerSocket_ComboBox, msg="Select the number of cores per socket", delay=0.1)

RDS_Secondary_Machine_Options_Combobox_var = tk.StringVar()
RDS_Secondary_Machine_Options_Combobox= ttk.Combobox(tab2, state="disabled", values=["Don't deploy to machines", "First xx percent of machines", "First xx amount of machines"], textvariable=RDS_Secondary_Machine_Options_Combobox_var)
RDS_Secondary_Machine_Options_Combobox_default_value = "Don't deploy to machines"
RDS_Secondary_Machine_Options_Combobox.set(RDS_Secondary_Machine_Options_Combobox_default_value)
RDS_Secondary_Machine_Options_Combobox.bind("<<ComboboxSelected>>",RDS_Secondary_Machine_Options_Combobox_callback)
RDS_Secondary_Machine_Options_Combobox.place(x=30, y=413, height=25, width=300)
ToolTip(RDS_Secondary_Machine_Options_Combobox, msg="Select selection type of secondary machines", delay=0.1)

# Create Checkboxes
RDS_secondaryimage_checkbox_var = tk.BooleanVar()
RDS_secondaryimage_checkbox = ttk.Checkbutton(tab2, state="disabled", text="Push as Secondary Image", variable=RDS_secondaryimage_checkbox_var, command=RDS_secondaryimage_checkbox_callback)
RDS_secondaryimage_checkbox.place(x=570, y=390)
ToolTip(RDS_secondaryimage_checkbox, msg="Check to deploy the new golden image as a secondary image", delay=0.1)

RDS_StopOnError_checkbox_var = tk.BooleanVar()
RDS_StopOnError_checkbox = ttk.Checkbutton(tab2, state="disabled", text="Stop on error", variable=RDS_StopOnError_checkbox_var)
RDS_StopOnError_checkbox.place(x=570, y=90)
ToolTip(RDS_StopOnError_checkbox, msg="CHeck to make sure deployment of new desktops stops on an error", delay=0.1)
RDS_StopOnError_checkbox_var.set(True)

RDS_Resize_checkbox_var = tk.BooleanVar()
RDS_Resize_checkbox = ttk.Checkbutton(tab2, state="disabled" ,text="Enable Resize Options", variable=RDS_Resize_checkbox_var, command=RDS_Resize_checkbox_callback)
RDS_Resize_checkbox.place(x=570, y=137)
ToolTip(RDS_Resize_checkbox, msg="Check to enable resizing of the Golden Image in the Rds Farm", delay=0.1)
RDS_Resize_checkbox_var.set(False)

RDS_Enable_datetimepicker_checkbox_var = tk.BooleanVar()
RDS_Enable_datetimepicker_checkbox = ttk.Checkbutton(tab2, state="disabled", text="Schedule deployment", variable=RDS_Enable_datetimepicker_checkbox_var, command=RDS_Enable_datetimepicker_checkbox_callback)
RDS_Enable_datetimepicker_checkbox.place(x=570, y=250)
ToolTip(RDS_Enable_datetimepicker_checkbox, msg="Check to enable a scheduled deployment of the new image", delay=0.1)

# Create other Widgets
RDS_Status_Textblock = tk.Text(tab2, borderwidth=1, relief="solid", wrap="word", state="normal")
RDS_Status_Textblock.place(x=30, y=80, height=305, width=510)
RDS_Status_Textblock.insert(tk.END, "No Info yet")

RDS_cal = DateEntry(tab2,bg="darkblue",fg="white", year=current_datetime.year, month=current_datetime.month, day=current_datetime.day)
RDS_cal.config(state="disabled")
RDS_cal.place(x=570,y=280)

RDS_hour_label = ttk.Label(tab2, text="Hour:")
RDS_hour_label.place(x=570, y=310)
RDS_hour_spin = tk.Spinbox(tab2, from_=0, to=23, width=2, value=current_datetime.hour, state="disabled")
RDS_hour_spin.place(x=570, y=340)

RDS_minute_label = ttk.Label(tab2, text="Minute:", anchor='w')
RDS_minute_label.place(x=650, y=310)
RDS_minute_spin = tk.Spinbox(tab2, from_=0, to=59, width=2, value=current_datetime.minute, state="disabled")
RDS_minute_spin.place(x=650, y=340)

RDS_machinecount_textbox = ttk.Entry(tab2, validate="key", validatecommand=(validate_int, "%P"), state="disabled")
RDS_machinecount_textbox.place(x=30, y=450, height=25, width=60)
ToolTip(RDS_machinecount_textbox, msg="ENter number or percentage of machines to apply the secondary image to", delay=0.1)