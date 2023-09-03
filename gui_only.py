import tkinter as tk
from tkinter import ttk,simpledialog
from tktooltip import ToolTip
from tkcalendar import DateEntry
from tktimepicker import SpinTimePickerModern
from tktimepicker import constants
from datetime import datetime,time as dt_time 
import configparser, os, horizon_functions, logging, sys,warnings, keyring,requests, json, threading,time
from logging.handlers import RotatingFileHandler

application_name = "hgidt"
requests.packages.urllib3.disable_warnings()
#region logging
# we need to have some logging in here 
LOG_FILE = application_name+".log"
# Configure logging with rotating log files
log_handler = RotatingFileHandler(LOG_FILE, maxBytes=1024*1024, backupCount=3)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)
logger = logging.getLogger(application_name)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)


# Custom exception handler
def exception_handler(exc_type, exc_value, exc_traceback):
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

# Set the custom exception handler
# sys.excepthook = exception_handler
#endregion

#region configuration
# Load the config file if one exists
CONFIG_FILE = application_name+'_config.ini'
config = configparser.ConfigParser()
config.read(CONFIG_FILE)

config_url= None
config_password = None

if 'UserInfo' in config:
    config_username = config.get('UserInfo', 'Username')
    config_domain = config.get('UserInfo', 'Domain')
    config_server_name = config.get('UserInfo', 'ServerName')
    config_save_password = config.getboolean('UserInfo', 'Save_Password')
    try:
        config_password = keyring.get_password(application_name, config_username)
        logger.info("Password retreived from credentials store")
    except keyring.errors.PasswordDeleteError:
        logger.error("Password not found or could not be retreived")
else:
    config_username = None
    config_domain = None
    config_server_name = None
    config_save_password = False
if 'Pods' in config:
    config_pods_data = config.get('Pods', 'Pods')
    config_pods = eval(config_pods_data)
else:
    config_pods = []
if 'Connection_Servers' in config:
    config_connection_servers_data = config.get('Connection_Servers', 'Connection_Servers')
    config_connection_servers = eval(config_connection_servers_data)
else:
    config_connection_servers = []


hvconnectionobj = None
onetosixtyfour = list(range(1,65))
memory_start_value = 1024
memory_end_value = 257600
memory_increment = 1024
memory_list = []
current_memory = memory_start_value
current_datetime = datetime.now()

while current_memory <= memory_end_value:
    memory_list.append(current_memory)
    current_memory += memory_increment
logo_image="hgidt_logo.ico"
#endregion

#region Configuration related functions

def build_pod_info(hvconnectionobj):
    federation = horizon_functions.Federation(url=hvconnectionobj.url, access_token=hvconnectionobj.access_token)
    config = horizon_functions.Config(url=hvconnectionobj.url, access_token=hvconnectionobj.access_token)
    monitor = horizon_functions.Monitor(url=hvconnectionobj.url, access_token=hvconnectionobj.access_token) 
    cpa_status = federation.get_cloud_pod_federation()['connection_server_statuses'][0]['status']
    config_pods.clear()
    config_connection_servers.clear()
    if cpa_status == "ENABLED":
        pods = federation.get_pods()
        for pod in pods:
            pod_name = pod['name']
            config_pods.append(pod_name)
            pod_endpoints = federation.get_pod_endpoints(pod_id=pod['id'])
            for pod_endpoint in pod_endpoints:
                conserver_dns = (pod_endpoint['server_address'].replace("https://","")).split(":")[0]
                conserver_name = conserver_dns.split(".")[0]
                conserver_details = {}
                conserver_details['PodName'] = pod_name
                conserver_details['Name'] = conserver_name
                conserver_details['ServerDNS'] = conserver_dns
                config_connection_servers.append(conserver_details)
    else:
        env_details = config.get_environment_properties()
        connection_servers_details = monitor.connection_servers()
        pod_name = env_details['cluster_name']
        # pod["Name"] = pod_name
        config_pods.append(pod_name)
        for conserver in connection_servers_details:
            conserver_name = conserver['name']
            if len(conserver_name.split(".")) > 1:
                conserver_dns = conserver_name.split('.')[0]
            else:
                dns_domain = config_server_name.replace((config_server_name.split(".")[0]), "")
                conserver_dns = conserver_name+dns_domain
            conserver_details = {}
            conserver_details['PodName'] = pod_name
            conserver_details['Name'] = conserver_name
            conserver_details['ServerDNS'] = conserver_dns
            config_connection_servers.append(conserver_details)


# def write_config(username, domain, server_name):
#     config = configparser.ConfigParser()
#     try:
#         config['UserInfo'] = {'Username': username, 'Domain': domain, 'ServerName': server_name}
#         config['Pods'] = {'Pods' : config_pods}
#         config['Connection_Servers'] = {'Connection_Servers' : config_connection_servers}
#         with open(CONFIG_FILE, 'w') as configfile:
#             config.write(configfile)
#     except:
#         logger.error("Configuration could not be saved")
#     try:
#         keyring.set_password(application_name, config_username, config_password)
#         logger.info("Password saved to credentials store")
#     except keyring.errors.PasswordDeleteError:
#         logger.error("Password could not be saved to the credentials store")
    

# def read_config():
#     # Get config from file
#     global config_username, config_password, config_server_name
#     config = configparser.ConfigParser()
#     config.read(CONFIG_FILE)
#     if 'UserInfo' in config:
#         config_username = config.get('UserInfo', 'Username')
#         config_domain = config.get('UserInfo', 'Domain')
#         config_server_name = config.get('UserInfo', 'ServerName')
#         # return config_username, config_domain, config_server_name
#         config_username_textbox.insert(tk.END, config_username)
#         config_domain_textbox.insert(tk.END, config_domain)
#         config_conserver_textbox.insert(tk.END, config_server_name)
#     else:
#         return None
#     # Get password
#     try:
#         global config_password
#         config_password = keyring.get_password(application_name, config_username)
#         logger.info("Password retreived from credentials store")
#     except keyring.errors.PasswordDeleteError:
#         logger.error("Password not found or could not be retreived")


def show_password_dialog():
    password = simpledialog.askstring("Password", "Enter your password:", show='*')
    if password is not None:
        global config_password
        config_password=password
        config_status_label.config(text="Password set")

#endregion

#region functions for button handling of VDI tab

def VDI_Apply_Golden_Image_button():
    global global_vdi_selected_pool, global_vdi_selected_vm, global_vdi_selected_vm, hvconnectionobj, VDI_vtpm_checkbox_var, VDI_hour_spin, VDI_minute_spin, VDI_cal
    if VDI_Enable_datetimepicker_checkbox_var.get() == True:
        datetime_var= get_selected_datetime(VDI_cal,VDI_hour_spin,VDI_minute_spin)
        start_time= datetime.timestamp(datetime_var)*1000
    else:
        start_time = time.time()
    pod = global_vdi_selected_vm["pod"]
    pool_id = global_vdi_selected_pool['id']
    parent_vm_id = global_vdi_selected_vm['id']
    snapshot_id = global_VDI_selected_snapshot['id']
    VDI_Resize_checkbox_var_selected = VDI_Resize_checkbox_var.get()
    VDI_CoresPerSocket_ComboBox_var_selected = VDI_CoresPerSocket_ComboBox_var.get()
    VDI_CPUCount_ComboBox_var_selected = VDI_CPUCount_ComboBox_var.get()
    VDI_Memory_ComboBox_var_selected = VDI_Memory_ComboBox_var.get()
    if VDI_Resize_checkbox_var_selected == True and VDI_CoresPerSocket_ComboBox_var_selected and VDI_CPUCount_ComboBox_var_selected and VDI_Memory_ComboBox_var_selected:
        compute_profile_num_cores_per_socket=VDI_CoresPerSocket_ComboBox_var.get()
        compute_profile_num_cpus = VDI_CPUCount_ComboBox_var.get()
        compute_profile_ram_mb = VDI_Memory_ComboBox_var.get()
    else:
        compute_profile_num_cores_per_socket = None
        compute_profile_num_cpus = None
        compute_profile_ram_mb = None
    hvconnectionobj = connect_pod(pod=pod)
    horizon_inventory=horizon_functions.Inventory(url=hvconnectionobj.url, access_token=hvconnectionobj.access_token)
    horizon_inventory.desktop_pool_push_image(desktop_pool_id=pool_id,parent_vm_id=parent_vm_id,snapshot_id=snapshot_id, compute_profile_ram_mb = compute_profile_ram_mb, compute_profile_num_cpus=compute_profile_num_cpus, compute_profile_num_cores_per_socket=compute_profile_num_cores_per_socket, add_virtual_tpm = VDI_vtpm_checkbox_var.get(), logoff_policy=VDI_LofOffPolicy_Combobox_var.get(), start_time=start_time )
    hvconnectionobj.hv_disconnect()
    

def VDI_DesktopPool_Combobox_callback(event):
    # print(VDI_DesktopPool_Combobox.get())
    global global_desktop_pools, global_base_vms, VDI_Golden_Image_Combobox__selected_default,VDI_Golden_Image_Combobox_values,global_vdi_selected_pool
    try:
        VDI_Golden_Image_Combobox_values.clear()
    except:
        VDI_Golden_Image_Combobox_values = []
    global_vdi_selected_pool = VDI_DesktopPool_Combobox_values[VDI_DesktopPool_Combobox_var.get()]
    podname = global_vdi_selected_pool['pod']
    vcenter_id = global_vdi_selected_pool['vcenter_id']
    optional_golden_images = [item for item in global_base_vms if item["vcenter_id"] == vcenter_id and "UNSUPPORTED_OS" not in item["incompatible_reasons"] ]
    VDI_Golden_Image_Combobox_values = {item["name"]: item for item in optional_golden_images}
    VDI_Golden_Image_Combobox__selected_default = optional_golden_images[0]['name']
    VDI_Golden_Image_Combobox['values'] = list(VDI_Golden_Image_Combobox_values.keys())
    VDI_Golden_Image_Combobox.config(state='readonly')
    VDI_Golden_Image_Combobox.set(VDI_Golden_Image_Combobox__selected_default)
    VDI_Golden_Image_Combobox.event_generate("<<ComboboxSelected>>") 

def VDI_Golden_Image_Combobox_callback(event):
    global global_desktop_pools, global_base_vms, VDI_Snapshot_Combobox__selected_default, global_base_snapshots,VDI_Snapshot_Combobox_values, global_vdi_selected_vm
    try:
        VDI_Snapshot_Combobox_values.clear()
    except:
        VDI_Snapshot_Combobox_values = []
    global_vdi_selected_vm = VDI_Golden_Image_Combobox_values[VDI_Golden_Image_Combobox_var.get()]

    podname = global_vdi_selected_vm['pod']
    vcenter_id = global_vdi_selected_vm['vcenter_id']
    basevm_id = global_vdi_selected_vm['id']
    optional_snapshots = [item for item in global_base_snapshots if item["vcenter_id"] == vcenter_id and item["basevmid"] == basevm_id]
    VDI_Snapshot_Combobox_values = {item["name"]: item for item in optional_snapshots}
    VDI_Snapshot_Combobox__selected_default = optional_snapshots[0]['name']
    VDI_Snapshot_Combobox['values'] = list(VDI_Snapshot_Combobox_values.keys())
    VDI_Snapshot_Combobox.config(state='readonly')
    VDI_Snapshot_Combobox.set(VDI_Snapshot_Combobox__selected_default)
    VDI_Snapshot_Combobox.event_generate("<<ComboboxSelected>>") 

def VDI_Snapshot_Combobox_callback(event):
    global global_VDI_selected_snapshot
    global_VDI_selected_snapshot = VDI_Snapshot_Combobox_values[VDI_Snapshot_Combobox_var.get()]
    VDI_LofOffPolicy_Combobox.config(state='readonly')
    VDI_Resize_checkbox.config(state="enabled")
    VDI_Enable_datetimepicker_checkbox.config(state='enabled')
    VDI_secondaryimage_checkbox.config(state='enabled')
    VDI_vtpm_checkbox.config(state='enabled')
    VDI_StopOnError_checkbox.config(state='enabled')
    VDI_Apply_Golden_Image_button.config(state='enabled')

def VDI_Resize_checkbox_callback():
    if VDI_Resize_checkbox_var.get() == True:
        VDI_CoresPerSocket_ComboBox.config(state='readonly')
        VDI_CPUCount_ComboBox.config(state='readonly')
        VDI_Memory_ComboBox.config(state='readonly')
    else:
        VDI_CoresPerSocket_ComboBox.config(state='disabled')
        VDI_CPUCount_ComboBox.config(state='disabled')
        VDI_Memory_ComboBox.config(state='disabled')
        VDI_Enable_datetimepicker_checkbox

def VDI_Enable_datetimepicker_checkbox_callback():
    if VDI_Enable_datetimepicker_checkbox_var.get() == True:
        VDI_cal.config(state='readonly')
        VDI_minute_spin.config(state='normal')
        VDI_hour_spin.config(state='normal')
    else:
        VDI_cal.config(state='disabled')
        VDI_minute_spin.config(state='disabled')
        VDI_hour_spin.config(state='disabled')
#endregion

#region functions for button handling of configuration tab

def config_reset_stored_password():
    global config_password
    try:
        keyring.delete_password(application_name, config_username)
        logger.info("Password removed from credentials store")
    except keyring.errors.PasswordDeleteError:
        logger.error("Credential not found or could not be deleted")

def config_save_password_checkbox_callback():
    global config_save_password, config_server_name
    if config_save_password_checkbox_var.get() == False:
        config_save_password = False
        config_reset_stored_password()
    else:
        config_save_password = True
    if config_server_name != None:
        config_save_button_callback()

def config_pod_combobox_callback():
    global config_server_name
    config_conserver_combobox.config(foreground='black')
    config_conserver_combobox_selected_name = config_pod_combobox.get()
    config_conserver_combobox_data = [item for item in config_connection_servers if item["PodName"] == config_conserver_combobox_selected_name]
    config_conserver_combobox['values'] = [item["ServerDNS"] for item in config_conserver_combobox_data]
    config_conserver_combobox.current(0)

def config_conserver_combobox_callback():
    global config_server_name
    config_server_name = config_conserver_combobox.get()

def config_save_button_callback():
    logger.info("Saving configuration")
    global config_username, config_domain, config_server_name, config_password
    config_username = config_username_textbox.get()
    config_domain = config_domain_textbox.get()
    config_server_name = config_conserver_combobox.get()
    if config_username == config_username_textbox_default_text or config_domain == config_domain_textbox_default_text or config_server_name == config_conserver_combobox_default_text or config_password == None:
        config_username = None
        config_domain = None
        config_server_name = None
        config_status_label.config(text="Please enter Connection Server, Username and password first.")
    else:
        config = configparser.ConfigParser()
        try:
            config['UserInfo'] = {'Username': config_username, 'Domain': config_domain, 'ServerName': config_server_name, 'Save_Password': str(config_save_password_checkbox_var.get())}
            config['Pods'] = {'Pods' : config_pods}
            config['Connection_Servers'] = {'Connection_Servers' : config_connection_servers}
            with open(CONFIG_FILE, 'w') as configfile:
                config.write(configfile)
        except:
            logger.error("Configuration could not be saved")
        if config_save_password == True:
            try:
                keyring.set_password(application_name, config_username, config_password)
                logger.info("Password saved to credentials store")
            except keyring.errors.PasswordDeleteError:
                logger.error("Password could not be saved to the credentials store")
        config_status_label.config(text="Configuration saved")
        logger.info("Configuration saved")

def config_reset_button_callback():
    logger.info("Resetting configuration")
    global config_username, config_domain, config_server_name,config_password, config_url
    config_reset_stored_password()
    del config_password
    config_password = None
    config_save_password_checkbox_var.set(False)
    config_username_textbox.delete(0, tk.END)
    config_username_textbox.insert(tk.END, config_username_textbox_default_text)
    config_username_textbox.config(foreground='grey')
    config_username = None
    config_domain_textbox.delete(0, tk.END)
    config_domain_textbox.insert(tk.END, config_domain_textbox_default_text)
    config_domain_textbox.config(foreground='grey')
    config_domain = None
    config_conserver_combobox['values'] = [] 
    config_conserver_combobox.set(config_conserver_combobox_default_text)
    config_conserver_combobox.config(foreground='grey')
    config_pod_combobox['values'] = [] 
    config_pod_combobox.set(config_pod_combobox_default_text)
    config_pod_combobox.config(foreground='grey')
    config_server_name = None
    config_pods.clear()
    config_connection_servers.clear()

    config_url=None
    config = configparser.ConfigParser()
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    config_status_label.config(text="Configuration reset and configuration file deleted.")
    logger.info("Configuration reset")

def config_test_button_callback():
    test_button_thread = threading.Thread(target=config_test_button_callback_thread)
    test_button_thread.start()

def config_test_button_callback_thread():
    logger.info("Testing configuration")
    config_status_label.config(text="Testing configuration")
    refresh_window()
    global config_username, config_domain, config_server_name, config_password
    config_username = config_username_textbox.get()
    config_domain = config_domain_textbox.get()
    config_server_name = config_conserver_combobox.get()
    if config_username is None or config_domain is None or config_server_name is None or config_username == config_username_textbox_default_text or config_domain == config_domain_textbox_default_text or config_server_name == config_conserver_combobox_default_text:
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
            build_pod_info(hvconnectionobj)
            hvconnectionobj.hv_disconnect()
            logger.info("Sucessfully finished testing configuration")
            logger.info("Saving configuration since it works")
            config_save_button_callback()
            config_status_label.config(text="Successfully finished testing configuration")
        except Exception as e:
            config_status_label.config(text="Error testing the connection, see the log file for details")
            logger.error("Error while testing the credentials")
            logger.error(str(e))

#endregion

#region Various functions

def get_selected_datetime(cal,hours,minutes):
    date_var = cal.get_date()
    hours_var = int(hours.get())
    minutes_var = int(minutes.get())
    selected_datetime = datetime.combine(date_var, dt_time(hours_var, minutes_var))
    return selected_datetime

def generic_Connect_Button_callback():
    generic_connect_thread = threading.Thread(target=generic_Connect_Button_callback_thread)
    generic_connect_thread.start()

def generic_Connect_Button_callback_thread():
    global hvconnectionobj, global_desktop_pools, global_rds_farms, global_base_vms, global_base_snapshots, global_datacenters, global_vcenters,VDI_DesktopPool_Combobox_values,RDS_Farm_Combobox_values,config_password
    if config_server_name is None and config_password is None:
        VDI_Statusbox_Label.config(text="Please configure the connection details first on the Configuration tab")
        RDS_Statusbox_Label.config(text="Please configure the connection details first on the Configuration tab")
        refresh_window()
        return
    elif config_server_name is not None and config_password is None:
        VDI_Statusbox_Label.config(text="Please configure the password first on the Configuration tab")
        RDS_Statusbox_Label.config(text="Please configure the password first on the Configuration tab")
        refresh_window()
        return
    else:
        VDI_DesktopPool_Combobox.config(state='disabled')
        VDI_Golden_Image_Combobox.config(state='disabled')
        VDI_Snapshot_Combobox.config(state='disabled')
        VDI_Statusbox_Label.config(text="Connecting")
        RDS_Statusbox_Label.config(text="Connecting")
        refresh_window()
        try:
            global_rds_farms.clear()
            global_desktop_pools.clear()
            global_base_vms.clear()
            global_base_snapshots.clear()
            global_datacenters.clear()
            global_vcenters.clear()
            VDI_DesktopPool_Combobox_values.clear()
            RDS_Farm_Combobox_values.clear()
        except:
            global_rds_farms=[]
            global_desktop_pools=[]
            global_base_vms=[]
            global_base_snapshots=[]
            global_datacenters=[]
            global_vcenters=[]
            VDI_DesktopPool_Combobox_values = []
            RDS_Farm_Combobox_values = []
        for pod in config_pods:
            # thread_connect = threading.Thread(target=connect_pod(pod))
            # thread_connect.start()
            hvconnectionobj = connect_pod(pod)
            if hvconnectionobj != False:
                horizon_inventory=horizon_functions.Inventory(url=hvconnectionobj.url, access_token=hvconnectionobj.access_token)
                horizon_config = horizon_functions.Config(url=hvconnectionobj.url, access_token=hvconnectionobj.access_token)
                horizon_External = horizon_functions.External(url=hvconnectionobj.url, access_token=hvconnectionobj.access_token)
                vdi_filter = {}
                vdi_filter["type"] = "And"
                vdi_filter["filters"] = []
                vdi_filter1={}
                vdi_filter1["type"] = "Equals"
                vdi_filter1["name"] = "source"
                vdi_filter1["value"] = "INSTANT_CLONE"
                vdi_filter2={}
                vdi_filter2["type"] = "Equals"
                vdi_filter2["name"] = "type"
                vdi_filter2["value"] = "AUTOMATED"
                vdi_filter["filters"].append(vdi_filter1)
                vdi_filter["filters"].append(vdi_filter2)
                rds_filter = {}
                rds_filter["type"] = "Equals"
                rds_filter["name"] = "automated_farm_settings.image_source"
                rds_filter["value"] = "VIRTUAL_CENTER"
                desktop_pools=horizon_inventory.get_desktop_pools(filter=vdi_filter)
                for pool in desktop_pools:
                    pool['pod'] = pod
                global_desktop_pools+=desktop_pools

                rds_farms=horizon_inventory.get_farms(filter=rds_filter)
                for farm in rds_farms:
                    farm['pod'] = pod
                global_rds_farms+=rds_farms

                vcenters = horizon_config.get_virtual_centers()
                for vcenter in vcenters:
                    vcenter['pod'] = pod
                    datacenters = horizon_External.get_datacenters(vcenter_id=vcenter['id'])
                    for datacenter in datacenters:
                        datacenter['pod'] = pod
                        basevms = horizon_External.get_base_vms(vcenter_id=vcenter['id'], datacenter_id=datacenter['id'],filter_incompatible_vms=True)
                        for basevm in basevms:
                            basevm['pod'] = pod
                            basesnapshots = horizon_External.get_base_snapshots(vcenter_id=vcenter['id'],base_vm_id=basevm['id'])
                            if len(basesnapshots) < 1:
                                basevms.remove(basevm)
                            else:
                                for basesnapshot in basesnapshots:
                                    basesnapshot['basevmid'] = basevm['id']
                                global_base_snapshots+=basesnapshots
                        global_base_vms+=basevms
                    global_datacenters+=datacenter
                global_vcenters+=vcenters
                hvconnectionobj.hv_disconnect()
        try:
            vdi_name_dict_mapping.clear()
            rds_name_dict_mapping.clear()
        except:
            vdi_name_dict_mapping = []
            rds_name_dict_mapping = []

        for pool in global_desktop_pools:
            name = pool['name']
            if name in vdi_name_dict_mapping:
                pod_tmp=pool['pod']
                new_name = f'{name} ({pod_tmp}])'
                pool['name'] = new_name
            else:
                vdi_name_dict_mapping.append(name)

        for farm in global_rds_farms:
            name = farm['name']
            if name in rds_name_dict_mapping:
                pod_tmp=farm['pod']
                new_name = f'{name} ({pod_tmp}])'
                farm['name'] = new_name
            else:
                rds_name_dict_mapping.append(name)
            # print(name_dict_mapping)
            # print(pool['name'])
        VDI_DesktopPool_Combobox_values = {item["name"]: item for item in global_desktop_pools}
        VDI_DesktopPool_Combobox__selected_default = global_desktop_pools[0]['name']
        VDI_DesktopPool_Combobox['values'] = list(VDI_DesktopPool_Combobox_values.keys())
        VDI_DesktopPool_Combobox.config(state='readonly')
        VDI_DesktopPool_Combobox.set(VDI_DesktopPool_Combobox__selected_default)
        VDI_DesktopPool_Combobox.event_generate("<<ComboboxSelected>>") 
        
        RDS_Farm_Combobox_values = {item["name"]: item for item in global_rds_farms}
        RDS_Farm_Combobox__selected_default = global_rds_farms[0]['name']
        RDS_Farm_Combobox['values'] = list(RDS_Farm_Combobox_values.keys())
        RDS_Farm_Combobox.config(state='readonly')
        RDS_Farm_Combobox.set(RDS_Farm_Combobox__selected_default)
        RDS_Farm_Combobox.event_generate("<<ComboboxSelected>>") 
        
        VDI_Connect_Button.config(text="Refresh")
        RDS_Connect_Button.config(text="Refresh")
        VDI_Statusbox_Label.config(text="Connected")
        RDS_Statusbox_Label.config(text="Connected")

def connect_pod(pod:str):
    global connect_pod_thread_var
    connect_pod_thread_var = []
    connect_pod_thread_tmp = threading.Thread(target=connect_pod_thread(pod=pod))
    connect_pod_thread_tmp.start()
    return connect_pod_thread_var

def connect_pod_thread(pod:str):
    global config_server_name, hvconnectionobj, connect_pod_thread_var,config_connection_servers
    con_servers_to_use = [item for item in config_connection_servers if item["PodName"] == pod]
    hvconnectionobj = None
    for con_server in con_servers_to_use:
        serverdns = con_server['ServerDNS']
        logger.info("connecting to: "+serverdns)
        config_url = "https://" + serverdns
        hvconnectionobj = horizon_functions.Connection(username = config_username,domain = config_domain,password = config_password,url = config_url)
        try:
            hvconnectionobj.hv_connect()
            logger.info("Connected to: "+serverdns)
            config_server_name = serverdns
            connect_pod_thread_var = hvconnectionobj
            break
        except Exception as e:
            logger.error("Failed to connect to: "+serverdns)
            logger.error(str(e))
            connect_pod_thread_var = False

def refresh_window():
    # Redraw the window
    root.update()
    root.update_idletasks()

# def updateTime(time):
#     time_lbl.configure(text="{}:{}".format(*time)) # if you are using 24 hours, remove the 3rd flower bracket its for period

def textbox_handle_focus_in(event,default_text):
    if event.widget.get() == default_text:
        event.widget.delete(0,'end')
        event.widget.config(foreground='black')  # Change text color to black when editing

def textbox_handle_focus_out(event,default_text):
    if event.widget.get().strip() == '':
        event.widget.insert(tk.END, default_text)
        event.widget.config(foreground='grey')  # Change text color to grey when not editing
#endregion

# region Generic tkinter config
root = tk.Tk()
root.title("Horizon Golden Image Deployment Tool")

# Set the custom icon/logo for the taskbar/Dock based on the platform
root.iconbitmap(logo_image)  # Windows icon file


root.geometry("1024x660")

style = ttk.Style()
# style.configure("Centered.TButton", padding=(10, 5))
# style.configure('Custom.TFrame', background="ghost white")

# root.tk_setPalette(background="ghost white", foreground='black', activeBackground="ghost white", activeForeground='black')
# root.option_add('*TFrame*background', "ghost white")
# root.option_add('*TFrame*foreground', 'black')

# Create Canvas
canvas = tk.Canvas(root)
canvas.pack(fill="both", expand=True)
# canvas.configure(bg='blue')

# Create TabControl
tab_control = ttk.Notebook(canvas)
tab_control.pack(fill="both", expand=True)

#endregion


# region Tab 1 - VDI Desktop Pools
tab1 = ttk.Frame(tab_control)
tab_control.add(tab1, text="VDI Pools")
# tab1.configure(style='Custom.TFrame')

# Place your Tab 1 widgets here
# Create Buttons
VDI_Connect_Button = ttk.Button(tab1, text="Connect", command=generic_Connect_Button_callback)
VDI_Connect_Button.place(x=750, y=30, width=160, height=25)


VDI_Apply_Golden_Image_button = ttk.Button(tab1, state="disabled", text="Deploy Golden Image",command=VDI_Apply_Golden_Image_button)
VDI_Apply_Golden_Image_button.place(x=570, y=510, width=220, height=25)

VDI_Apply_Secondary_Image_button = ttk.Button(tab1, state="disabled", text="Apply Secondary Image")
VDI_Apply_Secondary_Image_button.place(x=570, y=456, width=220, height=25)

VDI_Cancel_Secondary_Image_button = ttk.Button(tab1, state="disabled", text="Cancel secondary Image")
VDI_Cancel_Secondary_Image_button.place(x=570, y=430, width=220, height=25)

VDI_Promote_Secondary_Image_button = ttk.Button(tab1, state="disabled", text="Promote secondary Image")
VDI_Promote_Secondary_Image_button.place(x=570, y=483, width=220, height=25)

# Create Labels
VDI_Statusbox_Label = tk.Label(tab1, borderwidth=1, text="Status: Not Connected", justify="right")
VDI_Statusbox_Label.place(x=430, y=537)


# Create ComboBoxes
VDI_DesktopPool_Combobox_var = tk.StringVar()
VDI_DesktopPool_Combobox = ttk.Combobox(tab1, state="disabled", textvariable=VDI_DesktopPool_Combobox_var)
VDI_DesktopPool_Combobox.place(x=30, y=30, width=220, height=25)
VDI_DesktopPool_Combobox.bind("<<ComboboxSelected>>",VDI_DesktopPool_Combobox_callback)
ToolTip(VDI_DesktopPool_Combobox, msg="Select the desktop pool to update", delay=0.1)

VDI_Golden_Image_Combobox_var = tk.StringVar()
VDI_Golden_Image_Combobox = ttk.Combobox(tab1, state="disabled", textvariable=VDI_Golden_Image_Combobox_var)
VDI_Golden_Image_Combobox.place(x=270, y=30, width=220, height=25)
VDI_Golden_Image_Combobox.bind("<<ComboboxSelected>>",VDI_Golden_Image_Combobox_callback)
ToolTip(VDI_Golden_Image_Combobox, msg="Select the new source VM", delay=0.1)

VDI_Snapshot_Combobox_var = tk.StringVar()
VDI_Snapshot_Combobox = ttk.Combobox(tab1, state="disabled", textvariable=VDI_Snapshot_Combobox_var)
VDI_Snapshot_Combobox.place(x=510, y=30, width=220, height=25)
VDI_Snapshot_Combobox.bind("<<ComboboxSelected>>",VDI_Snapshot_Combobox_callback)
ToolTip(VDI_Snapshot_Combobox, msg="Select the new source Snapshot", delay=0.1)

VDI_LofOffPolicy_Combobox_var = tk.StringVar()
VDI_LofOffPolicy_Combobox = ttk.Combobox(tab1, state="disabled", values=["FORCE_LOGOFF","WAIT_FOR_LOGOFF"], textvariable=VDI_LofOffPolicy_Combobox_var)
VDI_LofOffPolicy_Combobox_default_value = "WAIT_FOR_LOGOFF"
VDI_LofOffPolicy_Combobox.set(VDI_LofOffPolicy_Combobox_default_value)
VDI_LofOffPolicy_Combobox.place(x=570, y=110, width=160, height=25)
ToolTip(VDI_LofOffPolicy_Combobox, msg="Select the logoff Policy", delay=0.1)

VDI_Memory_ComboBox_var = tk.StringVar()


VDI_Memory_ComboBox = ttk.Combobox(tab1, state="disabled", values=memory_list,textvariable=VDI_Memory_ComboBox_var)
VDI_Memory_ComboBox.place(x=570, y=160, width=160, height=25)
ToolTip(VDI_Memory_ComboBox, msg="Select the new memory size", delay=0.1)

VDI_CPUCount_ComboBox_var = tk.StringVar()
VDI_CPUCount_ComboBox = ttk.Combobox(tab1, state="disabled", values=onetosixtyfour, textvariable=VDI_CPUCount_ComboBox_var)
VDI_CPUCount_ComboBox.place(x=570, y=190, width=160, height=25)
ToolTip(VDI_CPUCount_ComboBox, msg="Select the new CPU count", delay=0.1)

VDI_CoresPerSocket_ComboBox_var = tk.StringVar()
VDI_CoresPerSocket_ComboBox = ttk.Combobox(tab1, state="disabled", values=onetosixtyfour,textvariable=VDI_CoresPerSocket_ComboBox_var)
VDI_CoresPerSocket_ComboBox.place(x=570, y=220, width=160, height=25)
ToolTip(VDI_CoresPerSocket_ComboBox, msg="Select the number of cores per socket", delay=0.1)

# Create Checkboxes
VDI_secondaryimage_checkbox_var = tk.BooleanVar()
VDI_secondaryimage_checkbox = ttk.Checkbutton(tab1, state="disabled", text="Push as Secondary Image", variable=VDI_secondaryimage_checkbox_var)
VDI_secondaryimage_checkbox.place(x=570, y=390)
ToolTip(VDI_secondaryimage_checkbox, msg="Check to deploy the new golden image as a secondary image", delay=0.1)

VDI_StopOnError_checkbox_var = tk.BooleanVar()
VDI_StopOnError_checkbox = ttk.Checkbutton(tab1, state="disabled", text="Stop on error", variable=VDI_StopOnError_checkbox_var)
VDI_StopOnError_checkbox.place(x=570, y=90)
ToolTip(VDI_StopOnError_checkbox, msg="CHeck to make sure deployment of new desktops stops on an error", delay=0.1)
VDI_StopOnError_checkbox_var.set(True)

VDI_Resize_checkbox_var = tk.BooleanVar()
VDI_Resize_checkbox = ttk.Checkbutton(tab1, state="disabled" ,text="Enable Resize Options", variable=VDI_Resize_checkbox_var, command=VDI_Resize_checkbox_callback)
VDI_Resize_checkbox.place(x=570, y=137)
ToolTip(VDI_Resize_checkbox, msg="Check to enable resizing of the Golden Image in the Desktop Pool", delay=0.1)
VDI_Resize_checkbox_var.set(False)

VDI_vtpm_checkbox_var = tk.BooleanVar()
VDI_vtpm_checkbox = ttk.Checkbutton(tab1, state="disabled", text="Add vTPM", variable=VDI_vtpm_checkbox_var)
VDI_vtpm_checkbox.place(x=570, y=70)
ToolTip(VDI_vtpm_checkbox, msg="Check to add a vTPM", delay=0.1)

VDI_Enable_datetimepicker_checkbox_var = tk.BooleanVar()
VDI_Enable_datetimepicker_checkbox = ttk.Checkbutton(tab1, state="disabled", text="Schedule deployment", variable=VDI_Enable_datetimepicker_checkbox_var, command=VDI_Enable_datetimepicker_checkbox_callback)
VDI_Enable_datetimepicker_checkbox.place(x=570, y=250)
ToolTip(VDI_Enable_datetimepicker_checkbox, msg="Check to enable a scheduled deployment of the new image", delay=0.1)

# Create other Widgets
VDI_Status_Textblock = tk.Text(tab1, borderwidth=1, relief="solid", wrap="word")
VDI_Status_Textblock.place(x=30, y=80, height=305, width=510)

VDI_Machines_ListBox = tk.Listbox(tab1, selectmode="multiple")
VDI_Machines_ListBox.place(x=30, y=413, height=150, width=300)

VDI_cal = DateEntry(tab1,bg="darkblue",fg="white", year=current_datetime.year, month=current_datetime.month, day=current_datetime.day)
# VDI_cal = Calendar(tab1,bg="darkblue",fg="white", selectmode="day", year=current_datetime.year, month=current_datetime.month, day=current_datetime.day)
VDI_cal.config(state="disabled")
VDI_cal.place(x=570,y=280)


VDI_hour_label = ttk.Label(tab1, text="Hour:")
VDI_hour_label.place(x=570, y=310)
VDI_hour_spin = tk.Spinbox(tab1, from_=0, to=23, width=2, value=current_datetime.hour, state="disabled")
VDI_hour_spin.place(x=570, y=340)

VDI_minute_label = ttk.Label(tab1, text="Minute:", anchor='w')
VDI_minute_label.place(x=650, y=310)
VDI_minute_spin = tk.Spinbox(tab1, from_=0, to=59, width=2, value=current_datetime.minute, state="disabled")
VDI_minute_spin.place(x=650, y=340)


# VDI_TimePicker = SpinTimePickerModern(tab1)
# VDI_TimePicker.addAll(constants.HOURS24)  # adds hours clock, minutes and period
# VDI_TimePicker.place(x=570,y=310)

#endregion


#region Tab 2 - RDS Farms
tab2 = ttk.Frame(tab_control)
tab_control.add(tab2, text="RDS Farms")
# tab2.configure(style='Custom.TFrame')

# Place your Tab 2 widgets here
# create buttons
RDS_Connect_Button = ttk.Button(tab2, text="Connect", command=generic_Connect_Button_callback)
RDS_Connect_Button.place(x=570, y=30, width=160, height=25)

RDS_Apply_Golden_Image_button = ttk.Button(tab2, text="Deploy Golden Image")
RDS_Apply_Golden_Image_button.place(x=570, y=510, width=160, height=25)

RDS_Apply_Secondary_Image_button = ttk.Button(tab2, text="Apply Secondary Image")
RDS_Apply_Secondary_Image_button.place(x=570, y=456, width=160, height=25)

RDS_Cancel_Secondary_Image_button = ttk.Button(tab2, text="Cancel secondary Image")
RDS_Cancel_Secondary_Image_button.place(x=570, y=430, width=160, height=25)

RDS_Promote_Secondary_Image_button = ttk.Button(tab2, text="Promote secondary Image")
RDS_Promote_Secondary_Image_button.place(x=570, y=483, width=160, height=25)

# Create Labels
RDS_Statusbox_Label = tk.Label(tab2, borderwidth=1, text="Status: Not Connected", justify="right")
RDS_Statusbox_Label.place(x=430, y=537)

# RDS_timepicker_label = tk.Label(tab2, borderwidth=1, text=":", justify="right")
# RDS_timepicker_label.place(x=615, y=310)

# Create ComboBoxes
RDS_Farm_Combobox = ttk.Combobox(tab2, state="disabled")
RDS_Farm_Combobox.place(x=30, y=30, width=150, height=25)
ToolTip(RDS_Farm_Combobox, msg="Select the desktop pool to update")

RDS_Golden_Image_Combobox = ttk.Combobox(tab2, state="disabled")
RDS_Golden_Image_Combobox.place(x=210, y=30, width=150, height=25)
ToolTip(RDS_Golden_Image_Combobox, msg="Select the new source VM")

RDS_Snapshot_Combobox = ttk.Combobox(tab2, state="disabled")
RDS_Snapshot_Combobox.place(x=390, y=30, width=150, height=25)
ToolTip(RDS_Snapshot_Combobox, msg="Select the new source Snapshot")

RDS_LofOffPolicy_Combobox = ttk.Combobox(tab2, state="disabled")
RDS_LofOffPolicy_Combobox.place(x=570, y=110, width=160, height=25)
ToolTip(RDS_LofOffPolicy_Combobox, msg="Select the logoff Policy")

RDS_Memory_ComboBox = ttk.Combobox(tab2 , state="disabled")
RDS_Memory_ComboBox.place(x=570, y=160, width=160, height=25)
ToolTip(RDS_Memory_ComboBox, msg="Select the new memory size")

RDS_CPUCount_ComboBox = ttk.Combobox(tab2, state="disabled")
RDS_CPUCount_ComboBox.place(x=570, y=190, width=160, height=25)
ToolTip(RDS_CPUCount_ComboBox, msg="Select the new CPU count")

RDS_CoresPerSocket_ComboBox = ttk.Combobox(tab2, state="disabled")
RDS_CoresPerSocket_ComboBox.place(x=570, y=220, width=160, height=25)
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
# tab3.configure(style='Custom.TFrame')

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
config_pod_combobox_default_text = "Test the connection first"
if len(config_pods) >= 1 :
    config_pod_combobox['values'] = config_pods
    config_pod_combobox.current(0)
else:
    config_pod_combobox.set(config_pod_combobox_default_text)
    config_pod_combobox.state(["disabled"])

config_conserver_combobox = ttk.Combobox(tab3)
config_conserver_combobox.place(x=30, y=50, width=200)
config_conserver_combobox_default_text = "Enter Connectionserver DNS"
if len(config_pods) >= 1 :
    config_pod_combobox_callback()
else:
    config_conserver_combobox.set(config_conserver_combobox_default_text)
config_conserver_combobox.bind("<FocusIn>", lambda event, var=config_conserver_combobox_default_text: textbox_handle_focus_in(event, var))
config_conserver_combobox.bind("<FocusOut>" , lambda event, var=config_conserver_combobox_default_text: textbox_handle_focus_out(event, var))

# Create CheckBox
config_save_password_checkbox_var = tk.BooleanVar()
config_save_password_checkbox = ttk.Checkbutton(tab3, text="Save Password", variable=config_save_password_checkbox_var, command=config_save_password_checkbox_callback)
config_save_password_checkbox.place(x=30, y=175)
config_save_password_checkbox_var.set(config_save_password)

#endregion

# Handling of tooltips
# tooltip_label = ttk.Label(root, background="yellow", relief="solid", padding=(5, 2), justify="left")
# tooltip_label.place_forget()

tab_control.select(tab1)

# Start the GUI event loop
root.mainloop()
