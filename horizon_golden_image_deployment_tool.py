import tkinter as tk
from tkinter import ttk, simpledialog
# from tktooltip import ToolTip
from tkcalendar import DateEntry
from datetime import datetime, time as dt_time
import configparser
import os
import horizon_functions
import logging
import keyring
import requests
import threading
import time
import sys
import math
import argparse
import loguru
from ttkthemes import ThemedTk
from loguru import logger
from logging.handlers import RotatingFileHandler

application_name = "hgidt"
requests.packages.urllib3.disable_warnings()
# region arguments and logging

logger.add('hgidt.log', retention="10 days", rotation="50 MB",
           format="{time:YYYY-MM-DD at HH:mm:ss} {level} {message}", level="INFO", enqueue=True, backtrace=True, diagnose=True, catch=True)


# def log_exception(*args):
#     if len(args) == 1:
#         e = args[0]
#         etype, value, tb = type(e), e, e.__traceback__
#     elif len(args) == 3:
#         etype, value, tb = args
#     else:
#         logger.error("Not able to log exception. Wrong number of arguments given. Should either receive 1 argument "
#                      "- an exception, or 3 arguments: exc type, exc value and traceback")
#         return

#     tb_parsed = []
#     for filename, lineno, func, text in traceback.extract_tb(tb):
#         tb_parsed.append(
#             {"filename": filename, "lineno": lineno, "func": func, "text": text})

#     logger.error(
#         "Uncaught exception", extra={
#             "exception": traceback.format_exception_only(etype, value)[0].strip(),
#             "traceback": tb_parsed
#         }
#     )


# # Set the custom exception handler
# sys.excepthook = log_exception

# endregion

# region configuration
# Load the config file if one exists
CONFIG_FILE = application_name+'_config.ini'
config = configparser.ConfigParser()
config.read(CONFIG_FILE)

config_url = None
config_password = None

if 'UserInfo' in config:
    config_username = config.get('UserInfo', 'Username')
    config_domain = config.get('UserInfo', 'Domain')
    config_server_name = config.get('UserInfo', 'ServerName')
    config_save_password = config.getboolean('UserInfo', 'Save_Password')
    try:
        config_password = keyring.get_password(
            application_name, config_username)
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
    config_connection_servers_data = config.get(
        'Connection_Servers', 'Connection_Servers')
    config_connection_servers = eval(config_connection_servers_data)
else:
    config_connection_servers = []


hvconnectionobj = None
onetosixtyfour = list(range(1, 65))
memory_start_value = 1024
memory_end_value = 257600
memory_increment = 1024
memory_list = []
current_memory = memory_start_value
current_datetime = datetime.now()

while current_memory <= memory_end_value:
    memory_list.append(current_memory)
    current_memory += memory_increment
logo_image = "logo.ico"
# endregion

# region Configuration related functions


def build_pod_info(hvconnectionobj):
    federation = horizon_functions.Federation(
        url=hvconnectionobj.url, access_token=hvconnectionobj.access_token)
    config = horizon_functions.Config(
        url=hvconnectionobj.url, access_token=hvconnectionobj.access_token)
    monitor = horizon_functions.Monitor(
        url=hvconnectionobj.url, access_token=hvconnectionobj.access_token)
    cpa_status = federation.get_cloud_pod_federation(
    )['connection_server_statuses'][0]['status']
    config_pods.clear()
    config_connection_servers.clear()
    if cpa_status == "ENABLED":
        pods = federation.get_pods()
        for pod in pods:
            pod_name = pod['name']
            config_pods.append(pod_name)
            pod_endpoints = federation.get_pod_endpoints(pod_id=pod['id'])
            for pod_endpoint in pod_endpoints:
                conserver_dns = (pod_endpoint['server_address'].replace(
                    "https://", "")).split(":")[0]
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
                dns_domain = config_server_name.replace(
                    (config_server_name.split(".")[0]), "")
                conserver_dns = conserver_name+dns_domain
            conserver_details = {}
            conserver_details['PodName'] = pod_name
            conserver_details['Name'] = conserver_name
            conserver_details['ServerDNS'] = conserver_dns
            config_connection_servers.append(conserver_details)


def show_password_dialog():
    password = simpledialog.askstring(
        "Password", "Enter your password:", show='*')
    if password is not None:
        global config_password
        config_password = password
        config_status_label.config(text="Password set")

# endregion

# region functions for button handling of VDI tab


def VDI_secondaryimage_checkbox_callback():
    if VDI_secondaryimage_checkbox_var.get() == True:
        VDI_Secondary_Machine_Options_Combobox.config(state="readonly")
        VDI_Secondary_Machine_Options_Combobox.event_generate(
            "<<ComboboxSelected>>")
        VDI_secondary_image_machine_count_label.config(state="enabled")
    else:
        VDI_secondary_image_machine_count_label.config(
            text=VDI_secondary_image_machine_count_label_default)
        VDI_Secondary_Machine_Options_Combobox.config(state="disabled")
        VDI_machinecount_textbox.config(state="disabled")
        VDI_secondary_image_machine_count_label.config(state="disabled")


def VDI_Secondary_Machine_Options_Combobox_callback(event):
    if VDI_Secondary_Machine_Options_Combobox_var.get() != VDI_Secondary_Machine_Options_Combobox_default_value:
        VDI_machinecount_textbox.config(state="enabled")
        if "Percentage" in VDI_Secondary_Machine_Options_Combobox_var.get():
            VDI_secondary_image_machine_count_label.config(text="Percentage")
        else:
            VDI_secondary_image_machine_count_label.config(
                text="Machine Count")
    else:
        VDI_secondary_image_machine_count_label.config(
            text=VDI_secondary_image_machine_count_label_default)
        VDI_machinecount_textbox.config(state="disabled")
        VDI_secondary_image_machine_count_label.config(state="disabled")


def VDI_Apply_Secondary_Image_button_callback():
    global global_vdi_selected_pool, global_vdi_selected_vm, hvconnectionobj
    if VDI_Secondary_Machine_Options_Combobox_var.get() != VDI_Secondary_Machine_Options_Combobox_default_value:
        pod = global_vdi_selected_pool["pod"]
        hvconnectionobj = connect_pod(pod=pod)
        horizon_inventory = horizon_functions.Inventory(
            url=hvconnectionobj.url, access_token=hvconnectionobj.access_token)
        pool_id = global_vdi_selected_pool['id']
        selected_machine_count = int(VDI_machinecount_textbox.get())
        machinefilter = {}
        machinefilter["type"] = "Equals"
        machinefilter["name"] = "desktop_pool_id"
        machinefilter["value"] = pool_id
        machines = horizon_inventory.get_machines(filter=machinefilter)
        machines = sorted(machines, key=lambda x: x["name"])
        if "Percentage" in VDI_Secondary_Machine_Options_Combobox_var.get():
            machinecount = len(machines)
            selected_machine_count = math.ceil(
                (selected_machine_count / 100) * machinecount)
            selected_machines = [d for d in machines[:selected_machine_count]]
            selected_machine_ids = [item["id"] for item in selected_machines if item["managed_machine_data"]["base_vm_snapshot_id"]
                                    == global_vdi_selected_pool["provisioning_status_data"]["instant_clone_pending_image_snapshot_id"]]
            unselected_machines = [
                d for d in machines[selected_machine_count:]]
            unselected_machine_ids = [item["id"] for item in unselected_machines if item["managed_machine_data"]
                                      ["base_vm_snapshot_id"] != global_vdi_selected_pool["provisioning_settings"]["base_snapshot_id"]]
        else:
            selected_machines = [d for d in machines[:selected_machine_count]]
            selected_machine_ids = [item["id"] for item in selected_machines if item["managed_machine_data"]["base_vm_snapshot_id"]
                                    != global_vdi_selected_pool["provisioning_status_data"]["instant_clone_pending_image_snapshot_id"]]
            unselected_machines = [
                d for d in machines[selected_machine_count:]]
            unselected_machine_ids = [item["id"] for item in unselected_machines if item["managed_machine_data"]
                                      ["base_vm_snapshot_id"] != global_vdi_selected_pool["provisioning_settings"]["base_snapshot_id"]]
        if len(selected_machine_ids) != 0:
            horizon_inventory.apply_pending_desktop_pool_image(
                desktop_pool_id=pool_id, machine_ids=selected_machine_ids, pending_image=True)
        if len(unselected_machine_ids) != 0:
            horizon_inventory.apply_pending_desktop_pool_image(
                desktop_pool_id=pool_id, machine_ids=unselected_machine_ids, pending_image=False)
        VDI_Secondary_Machine_Options_Combobox.config(state="disabled")
        VDI_machinecount_textbox.config(state="disabled")
        VDI_Apply_Golden_Image_button.config(state="disabled")
        VDI_Apply_Secondary_Image_button.config(state="disabled")
        VDI_Cancel_Secondary_Image_button.config(state="disabled")
        VDI_Enable_datetimepicker_checkbox.config(state="disabled")
        VDI_CPUCount_ComboBox.config(state="disabled")
        VDI_cal.config(state="disabled")
        VDI_Golden_Image_Combobox.config(state="disabled")
        VDI_Snapshot_Combobox.config(state="disabled")
        VDI_vtpm_checkbox.config(state="disabled")
        VDI_LofOffPolicy_Combobox.config(state="disabled")
        VDI_Resize_checkbox.config(state="disabled")
        VDI_StopOnError_checkbox.config(state="disabled")
        VDI_secondaryimage_checkbox.config(state="disabled")
        VDI_CoresPerSocket_ComboBox.config(state='disabled')
        VDI_Memory_ComboBox.config(state='disabled')
        VDI_Promote_Secondary_Image_button.config(state="disabled")
        hvconnectionobj.hv_disconnect()
    else:
        VDI_Statusbox_Label.config(text="Select a number of machines first.")


def VDI_Cancel_Secondary_Image_button_callback():
    global global_vdi_selected_pool
    VDI_Secondary_Machine_Options_Combobox.config(state="disabled")
    VDI_machinecount_textbox.config(state="disabled")
    VDI_Apply_Golden_Image_button.config(state="disabled")
    VDI_Apply_Secondary_Image_button.config(state="disabled")
    VDI_Cancel_Secondary_Image_button.config(state="disabled")
    VDI_Enable_datetimepicker_checkbox.config(state="disabled")
    VDI_CPUCount_ComboBox.config(state="disabled")
    VDI_cal.config(state="disabled")
    VDI_Golden_Image_Combobox.config(state="disabled")
    VDI_Snapshot_Combobox.config(state="disabled")
    VDI_vtpm_checkbox.config(state="disabled")
    VDI_LofOffPolicy_Combobox.config(state="disabled")
    VDI_Resize_checkbox.config(state="disabled")
    VDI_StopOnError_checkbox.config(state="disabled")
    VDI_secondaryimage_checkbox.config(state="disabled")
    VDI_CoresPerSocket_ComboBox.config(state='disabled')
    VDI_Memory_ComboBox.config(state='disabled')
    VDI_Promote_Secondary_Image_button.config(state="disabled")
    hvconnectionobj = connect_pod(pod=global_vdi_selected_pool["pod"])
    horizon_inventory = horizon_functions.Inventory(
        url=hvconnectionobj.url, access_token=hvconnectionobj.access_token)
    horizon_inventory.cancel_desktop_pool_push_image(
        desktop_pool_id=global_vdi_selected_pool["id"])
    hvconnectionobj.hv_disconnect()


def VDI_Promote_Secondary_Image_button_callback():
    global global_vdi_selected_pool
    VDI_Secondary_Machine_Options_Combobox.config(state="disabled")
    VDI_machinecount_textbox.config(state="disabled")
    VDI_Apply_Golden_Image_button.config(state="disabled")
    VDI_Apply_Secondary_Image_button.config(state="disabled")
    VDI_Cancel_Secondary_Image_button.config(state="disabled")
    VDI_Enable_datetimepicker_checkbox.config(state="disabled")
    VDI_CPUCount_ComboBox.config(state="disabled")
    VDI_cal.config(state="disabled")
    VDI_Golden_Image_Combobox.config(state="disabled")
    VDI_Snapshot_Combobox.config(state="disabled")
    VDI_vtpm_checkbox.config(state="disabled")
    VDI_LofOffPolicy_Combobox.config(state="disabled")
    VDI_Resize_checkbox.config(state="disabled")
    VDI_StopOnError_checkbox.config(state="disabled")
    VDI_secondaryimage_checkbox.config(state="disabled")
    VDI_CoresPerSocket_ComboBox.config(state='disabled')
    VDI_Memory_ComboBox.config(state='disabled')
    VDI_Promote_Secondary_Image_button.config(state="disabled")
    hvconnectionobj = connect_pod(pod=global_vdi_selected_pool["pod"])
    horizon_inventory = horizon_functions.Inventory(
        url=hvconnectionobj.url, access_token=hvconnectionobj.access_token)
    horizon_inventory.promote_pending_desktop_pool_image(
        desktop_pool_id=global_vdi_selected_pool["id"])
    hvconnectionobj.hv_disconnect()


def VDI_Apply_Golden_Image_button_callback():
    global global_vdi_selected_pool, global_vdi_selected_vm, global_vdi_selected_vm, hvconnectionobj, VDI_vtpm_checkbox_var, VDI_hour_spin, VDI_minute_spin, VDI_cal
    if VDI_Enable_datetimepicker_checkbox_var.get() == True:
        datetime_var = get_selected_datetime(
            VDI_cal, VDI_hour_spin, VDI_minute_spin)
        start_time = datetime.timestamp(datetime_var)*1000
    else:
        start_time = time.time()

    pod = global_vdi_selected_vm["pod"]
    hvconnectionobj = connect_pod(pod=pod)
    horizon_inventory = horizon_functions.Inventory(
        url=hvconnectionobj.url, access_token=hvconnectionobj.access_token)
    pool_id = global_vdi_selected_pool['id']
    parent_vm_id = global_vdi_selected_vm['id']
    snapshot_id = global_VDI_selected_snapshot['id']
    VDI_Resize_checkbox_var_selected = VDI_Resize_checkbox_var.get()
    VDI_CoresPerSocket_ComboBox_var_selected = VDI_CoresPerSocket_ComboBox_var.get()
    VDI_CPUCount_ComboBox_var_selected = VDI_CPUCount_ComboBox_var.get()
    VDI_Memory_ComboBox_var_selected = VDI_Memory_ComboBox_var.get()
    if VDI_Secondary_Machine_Options_Combobox_var.get() != VDI_Secondary_Machine_Options_Combobox_default_value:
        selected_machine_count = int(VDI_machinecount_textbox.get())
        machinefilter = {}
        machinefilter["type"] = "Equals"
        machinefilter["name"] = "desktop_pool_id"
        machinefilter["value"] = pool_id
        machines = horizon_inventory.get_machines(filter=machinefilter)
        machines = sorted(machines, key=lambda x: x["name"])
        if "percent" in VDI_Secondary_Machine_Options_Combobox_var.get():
            machinecount = len(machines)
            selected_machine_count = math.ceil(
                (selected_machine_count / 100) * machinecount)
            machine_ids = [d["id"] for d in machines[:selected_machine_count]]
        else:
            machine_ids = [d["id"] for d in machines[:selected_machine_count]]
    else:
        machine_ids = None
    if VDI_Resize_checkbox_var_selected == True and VDI_CoresPerSocket_ComboBox_var_selected and VDI_CPUCount_ComboBox_var_selected and VDI_Memory_ComboBox_var_selected:
        compute_profile_num_cores_per_socket = VDI_CoresPerSocket_ComboBox_var.get()
        compute_profile_num_cpus = VDI_CPUCount_ComboBox_var.get()
        compute_profile_ram_mb = VDI_Memory_ComboBox_var.get()
    else:
        compute_profile_num_cores_per_socket = None
        compute_profile_num_cpus = None
        compute_profile_ram_mb = None

    horizon_inventory.desktop_pool_push_image(desktop_pool_id=pool_id, parent_vm_id=parent_vm_id, snapshot_id=snapshot_id, machine_ids=machine_ids, compute_profile_ram_mb=compute_profile_ram_mb, compute_profile_num_cpus=compute_profile_num_cpus,
                                              compute_profile_num_cores_per_socket=compute_profile_num_cores_per_socket, add_virtual_tpm=VDI_vtpm_checkbox_var.get(), logoff_policy=VDI_LofOffPolicy_Combobox_var.get(), start_time=start_time, selective_push_image=VDI_secondaryimage_checkbox_var.get())
    VDI_Secondary_Machine_Options_Combobox.config(state="disabled")
    VDI_machinecount_textbox.config(state="disabled")
    VDI_Apply_Golden_Image_button.config(state="disabled")
    VDI_Apply_Secondary_Image_button.config(state="disabled")
    VDI_Cancel_Secondary_Image_button.config(state="disabled")
    VDI_Enable_datetimepicker_checkbox.config(state="disabled")
    VDI_CPUCount_ComboBox.config(state="disabled")
    VDI_cal.config(state="disabled")
    VDI_Golden_Image_Combobox.config(state="disabled")
    VDI_Snapshot_Combobox.config(state="disabled")
    VDI_vtpm_checkbox.config(state="disabled")
    VDI_LofOffPolicy_Combobox.config(state="disabled")
    VDI_Resize_checkbox.config(state="disabled")
    VDI_StopOnError_checkbox.config(state="disabled")
    VDI_secondaryimage_checkbox.config(state="disabled")
    VDI_CoresPerSocket_ComboBox.config(state='disabled')
    VDI_Memory_ComboBox.config(state='disabled')
    VDI_Promote_Secondary_Image_button.config(state="disabled")
    hvconnectionobj.hv_disconnect()


def VDI_DesktopPool_Combobox_callback(event):
    global global_desktop_pools, global_base_vms, VDI_Golden_Image_Combobox__selected_default, VDI_Golden_Image_Combobox_values, global_vdi_selected_pool, global_base_snapshots
    VDI_Secondary_Machine_Options_Combobox.config(state="disabled")
    VDI_machinecount_textbox.config(state="disabled")
    VDI_Apply_Golden_Image_button.config(state="disabled")
    VDI_Apply_Secondary_Image_button.config(state="disabled")
    VDI_Cancel_Secondary_Image_button.config(state="disabled")
    VDI_Enable_datetimepicker_checkbox.config(state="disabled")
    VDI_Promote_Secondary_Image_button.config(state="disabled")
    VDI_CPUCount_ComboBox.config(state="disabled")
    VDI_cal.config(state="disabled")
    VDI_Golden_Image_Combobox.config(state="disabled")
    VDI_Snapshot_Combobox.config(state="disabled")
    VDI_vtpm_checkbox.config(state="disabled")
    VDI_LofOffPolicy_Combobox.config(state="disabled")
    VDI_Resize_checkbox.config(state="disabled")
    VDI_CoresPerSocket_ComboBox.config(state='disabled')
    VDI_CPUCount_ComboBox.config(state='disabled')
    VDI_Memory_ComboBox.config(state='disabled')
    try:
        VDI_Golden_Image_Combobox_values.clear()
    except:
        VDI_Golden_Image_Combobox_values = []
    global_vdi_selected_pool = VDI_DesktopPool_Combobox_values[VDI_DesktopPool_Combobox_var.get(
    )]
    pool_name = global_vdi_selected_pool["name"]
    pool_displayname = global_vdi_selected_pool["display_name"]
    podname = global_vdi_selected_pool['pod']
    if global_vdi_selected_pool["enabled"] == True:
        state = "Enabled"
    else:
        state = "Disabled"
    if global_vdi_selected_pool["enable_provisioning"] == True:
        provisioning_state = "Enabled"
    else:
        provisioning_state = "Disabled"
    vcenter_id = global_vdi_selected_pool['vcenter_id']
    prinary_basevm_id = global_vdi_selected_pool["provisioning_settings"]["parent_vm_id"]
    primary_snapshot_id = global_vdi_selected_pool["provisioning_settings"]["base_snapshot_id"]
    try:
        provisioning_progress = global_vdi_selected_pool[
            "provisioning_status_data"]["instant_clone_pending_image_progress"]
    except:
        provisioning_progress = "N/A"
    tpm_state = global_vdi_selected_pool["provisioning_settings"]["add_virtual_tpm"]
    try:
        deployment_time = datetime.fromtimestamp(
            global_vdi_selected_pool["provisioning_status_data"]["instant_clone_push_image_settings"]["start_time"] / 1000)
    except:
        deployment_time = "N/A"
    primary_basevm_name = [
        item for item in global_base_vms if item["id"] == prinary_basevm_id][0]["name"]
    primary_basesnapshot_name = [
        item for item in global_base_snapshots if item["id"] == primary_snapshot_id][0]["name"]
    try:
        secondary_basevm_id = global_vdi_selected_pool[
            "provisioning_status_data"]["instant_clone_pending_image_parent_vm_id"]
        secondary_basevm_name = [
            item for item in global_base_vms if item["id"] == secondary_basevm_id][0]["name"]
    except:
        secondary_basevm_name = "N/A"
    try:
        secondary_snapshot_id = global_vdi_selected_pool[
            "provisioning_status_data"]["instant_clone_pending_image_snapshot_id"]
        secondary_basesnapshot_name = [
            item for item in global_base_snapshots if item["id"] == secondary_snapshot_id][0]["name"]
    except:
        secondary_basesnapshot_name = "N/A"
    pool_id = global_vdi_selected_pool["id"]
    current_image_state = global_vdi_selected_pool[
        "provisioning_status_data"]["instant_clone_current_image_state"]
    instant_clone_operation = global_vdi_selected_pool[
        "provisioning_status_data"]["instant_clone_operation"]
    try:
        instant_clone_pending_image_state = global_vdi_selected_pool[
            "provisioning_status_data"]["instant_clone_pending_image_state"]
    except:
        instant_clone_pending_image_state = "N/A"
    vdi_textblock_text = f"Desktop Pool Status:\nName: {pool_name}\nDisplay Name: {pool_displayname}\nDesktop Pool State = {state}\nProvisioning State = {provisioning_state}\nCurrent Image State = {current_image_state}\nInstant Clone Operation = {instant_clone_operation}\nImage Deployment time = {deployment_time}\nBase VM = {primary_basevm_name}\nBase Snapshot = {primary_basesnapshot_name}\nSecondary or Pending VM = {secondary_basevm_name}\nSecondary or Pending SNapshot = {secondary_basesnapshot_name}\nPending Image State = {instant_clone_pending_image_state}\nPending Image Progress = {provisioning_progress}"
    VDI_Status_Textblock.delete(1.0, tk.END)
    VDI_Status_Textblock.insert(tk.END, vdi_textblock_text)
    if (instant_clone_operation == "NONE" and instant_clone_pending_image_state == "N/A") or (instant_clone_operation == "NONE" and instant_clone_pending_image_state == "FAILED"):
        optional_golden_images = [item for item in global_base_vms if item["vcenter_id"]
                                  == vcenter_id and "UNSUPPORTED_OS" not in item["incompatible_reasons"]]
        VDI_Golden_Image_Combobox_values = {
            item["name"]: item for item in optional_golden_images}
        VDI_Golden_Image_Combobox__selected_default = optional_golden_images[0]['name']
        VDI_Golden_Image_Combobox['values'] = list(
            VDI_Golden_Image_Combobox_values.keys())
        VDI_Golden_Image_Combobox.set(
            VDI_Golden_Image_Combobox__selected_default)
        VDI_Cancel_Secondary_Image_button.config(state="disabled")
        VDI_Promote_Secondary_Image_button.config(state="disabled")
        VDI_Apply_Golden_Image_button.config(state="disabled")
        VDI_Golden_Image_Combobox.config(state='readonly')
        VDI_secondaryimage_checkbox_callback()
        VDI_Enable_datetimepicker_checkbox_callback()
        VDI_Resize_checkbox_callback()
        VDI_Golden_Image_Combobox.event_generate("<<ComboboxSelected>>")
    elif instant_clone_operation == "NONE" and instant_clone_pending_image_state == "READY_HELD":
        VDI_Cancel_Secondary_Image_button.config(state="enabled")
        VDI_Promote_Secondary_Image_button.config(state="enabled")
        VDI_Apply_Golden_Image_button.config(state="disabled")
        VDI_Apply_Secondary_Image_button.config(state="enabled")
        VDI_Secondary_Machine_Options_Combobox.config(state="readonly")
    elif instant_clone_operation == "SCHEDULE_PUSH_IMAGE" and instant_clone_pending_image_state != "UNPUBLISHING":
        VDI_Cancel_Secondary_Image_button.config(state="enabled")


def VDI_Golden_Image_Combobox_callback(event):
    global global_desktop_pools, global_base_vms, VDI_Snapshot_Combobox__selected_default, global_base_snapshots, VDI_Snapshot_Combobox_values, global_vdi_selected_vm
    try:
        VDI_Snapshot_Combobox_values.clear()
    except:
        VDI_Snapshot_Combobox_values = []
    global_vdi_selected_vm = VDI_Golden_Image_Combobox_values[VDI_Golden_Image_Combobox_var.get(
    )]

    podname = global_vdi_selected_vm['pod']
    vcenter_id = global_vdi_selected_vm['vcenter_id']
    basevm_id = global_vdi_selected_vm['id']
    optional_snapshots = [item for item in global_base_snapshots if item["vcenter_id"]
                          == vcenter_id and item["basevmid"] == basevm_id]
    VDI_Snapshot_Combobox_values = {
        item["name"]: item for item in optional_snapshots}
    VDI_Snapshot_Combobox__selected_default = optional_snapshots[0]['name']
    VDI_Snapshot_Combobox['values'] = list(VDI_Snapshot_Combobox_values.keys())
    VDI_Snapshot_Combobox.config(state='readonly')
    VDI_Snapshot_Combobox.set(VDI_Snapshot_Combobox__selected_default)
    VDI_Snapshot_Combobox.event_generate("<<ComboboxSelected>>")


def VDI_Snapshot_Combobox_callback(event):
    global global_VDI_selected_snapshot, global_vdi_selected_pool
    global_VDI_selected_snapshot = VDI_Snapshot_Combobox_values[VDI_Snapshot_Combobox_var.get(
    )]
    VDI_LofOffPolicy_Combobox.config(state='readonly')
    VDI_Resize_checkbox.config(state="enabled")
    VDI_Enable_datetimepicker_checkbox.config(state='enabled')
    VDI_secondaryimage_checkbox.config(state='enabled')
    VDI_vtpm_checkbox.config(state='enabled')
    VDI_StopOnError_checkbox.config(state='enabled')
    VDI_Apply_Golden_Image_button.config(state='enabled')
    VDI_memsize = None
    VDI_cpucount = None
    VDI_corespersocket = None
    try:
        VDI_memsize = global_vdi_selected_pool['provisioning_settings']['compute_profile_ram_mb']
        VDI_cpucount = global_vdi_selected_pool['provisioning_settings']['compute_profile_num_cpus']
        VDI_corespersocket = global_vdi_selected_pool[
            'provisioning_settings']['compute_profile_num_cores_per_socket']
    except:
        VDI_memsize = None
        VDI_cpucount = None
        VDI_corespersocket = None
    if VDI_memsize is not None and VDI_corespersocket is not None:
        VDI_Resize_checkbox_var.set(True)
        VDI_CoresPerSocket_ComboBox_var.set(VDI_corespersocket)
        VDI_CPUCount_ComboBox_var.set(VDI_cpucount)
        VDI_Memory_ComboBox_var.set(VDI_memsize)
        VDI_Resize_checkbox_callback()


def VDI_Resize_checkbox_callback():
    if VDI_Resize_checkbox_var.get() == True:
        VDI_CoresPerSocket_ComboBox.config(state='readonly')
        VDI_CPUCount_ComboBox.config(state='readonly')
        VDI_Memory_ComboBox.config(state='readonly')
    else:
        VDI_CoresPerSocket_ComboBox.config(state='disabled')
        VDI_CPUCount_ComboBox.config(state='disabled')
        VDI_Memory_ComboBox.config(state='disabled')
        # VDI_Enable_datetimepicker_checkbox


def VDI_Enable_datetimepicker_checkbox_callback():
    if VDI_Enable_datetimepicker_checkbox_var.get() == True:
        VDI_cal.config(state='readonly')
        VDI_minute_spin.config(state='normal')
        VDI_hour_spin.config(state='normal')
    else:
        VDI_cal.config(state='disabled')
        VDI_minute_spin.config(state='disabled')
        VDI_hour_spin.config(state='disabled')
# endregion


# region functions for button handling of RDS tab
def RDS_secondaryimage_checkbox_callback():
    if RDS_secondaryimage_checkbox_var.get() == True:
        RDS_Secondary_Machine_Options_Combobox.config(state="enabled")
        if RDS_Secondary_Machine_Options_Combobox != RDS_Secondary_Machine_Options_Combobox_default_value:
            RDS_machinecount_textbox.config(state="enabled")
    else:
        RDS_Secondary_Machine_Options_Combobox.config(state="disabled")
        RDS_machinecount_textbox.config(state="disabled")


def RDS_Secondary_Machine_Options_Combobox_callback(P):
    if RDS_Secondary_Machine_Options_Combobox_var.get() != RDS_Secondary_Machine_Options_Combobox_default_value:
        RDS_machinecount_textbox.config(state="enabled")
    else:
        RDS_machinecount_textbox.config(state="disabled")


def RDS_Apply_Secondary_Image_button_callback():
    global global_RDS_selected_farm, global_RDS_selected_vm, hvconnectionobj
    if RDS_Secondary_Machine_Options_Combobox_var.get() != RDS_Secondary_Machine_Options_Combobox_default_value:
        pod = global_RDS_selected_farm["pod"]
        hvconnectionobj = connect_pod(pod=pod)
        horizon_inventory = horizon_functions.Inventory(
            url=hvconnectionobj.url, access_token=hvconnectionobj.access_token)
        farm_id = global_RDS_selected_farm['id']
        selected_machine_count = int(RDS_machinecount_textbox.get())
        rdsmachinefilter = {}
        rdsmachinefilter["type"] = "Equals"
        rdsmachinefilter["name"] = "farm_id"
        rdsmachinefilter["value"] = farm_id
        machines = horizon_inventory.get_rds_servers(filter=rdsmachinefilter)
        machines = sorted(machines, key=lambda x: x["name"])
        if "percent" in RDS_Secondary_Machine_Options_Combobox_var.get():
            machinecount = len(machines)
            selected_machine_count = math.ceil(
                (selected_machine_count / 100) * machinecount)
            selected_machines = [d for d in machines[:selected_machine_count]]
            selected_machine_ids = [item["id"] for item in selected_machines if item["base_vm_snapshot_id"] ==
                                    global_RDS_selected_farm["automated_farm_settings"]["provisioning_status_data"]["instant_clone_pending_image_snapshot_id"]]
            unselected_machines = [
                d for d in machines[selected_machine_count:]]
            unselected_machine_ids = [item["id"] for item in unselected_machines if item["base_vm_snapshot_id"]
                                      != global_RDS_selected_farm["automated_farm_settings"]["provisioning_settings"]["base_snapshot_id"]]
        else:
            selected_machines = [d for d in machines[:selected_machine_count]]
            selected_machine_ids = [item["id"] for item in selected_machines if item["base_vm_snapshot_id"] !=
                                    global_RDS_selected_farm["automated_farm_settings"]["provisioning_status_data"]["instant_clone_pending_image_snapshot_id"]]
            unselected_machines = [
                d for d in machines[selected_machine_count:]]
            unselected_machine_ids = [item["id"] for item in unselected_machines if item["base_vm_snapshot_id"]
                                      != global_RDS_selected_farm["automated_farm_settings"]["provisioning_settings"]["base_snapshot_id"]]
        if len(selected_machine_ids) != 0:
            horizon_inventory.apply_pending_rds_farm_image(
                farm_id=farm_id, machine_ids=selected_machine_ids, pending_image=True)
        if len(unselected_machine_ids) != 0:
            horizon_inventory.apply_pending_rds_farm_image(
                farm_id=farm_id, machine_ids=unselected_machine_ids, pending_image=False)
        RDS_Secondary_Machine_Options_Combobox.config(state="disabled")
        RDS_machinecount_textbox.config(state="disabled")
        RDS_Apply_Golden_Image_button.config(state="disabled")
        RDS_Apply_Secondary_Image_button.config(state="disabled")
        RDS_Cancel_Secondary_Image_button.config(state="disabled")
        RDS_Enable_datetimepicker_checkbox.config(state="disabled")
        RDS_CPUCount_ComboBox.config(state="disabled")
        RDS_cal.config(state="disabled")
        RDS_Golden_Image_Combobox.config(state="disabled")
        RDS_Snapshot_Combobox.config(state="disabled")
        RDS_LofOffPolicy_Combobox.config(state="disabled")
        RDS_Resize_checkbox.config(state="disabled")
        RDS_StopOnError_checkbox.config(state="disabled")
        RDS_secondaryimage_checkbox.config(state="disabled")
        RDS_CoresPerSocket_ComboBox.config(state='disabled')
        RDS_Memory_ComboBox.config(state='disabled')
        RDS_Promote_Secondary_Image_button.config(state='disabled')
        hvconnectionobj.hv_disconnect()
    else:
        RDS_Statusbox_Label.config(text="Select a number of machines first.")


def RDS_Cancel_Secondary_Image_button_callback():
    global global_RDS_selected_farm
    RDS_Secondary_Machine_Options_Combobox.config(state="disabled")
    RDS_machinecount_textbox.config(state="disabled")
    RDS_Apply_Golden_Image_button.config(state="disabled")
    RDS_Apply_Secondary_Image_button.config(state="disabled")
    RDS_Cancel_Secondary_Image_button.config(state="disabled")
    RDS_Enable_datetimepicker_checkbox.config(state="disabled")
    RDS_CPUCount_ComboBox.config(state="disabled")
    RDS_cal.config(state="disabled")
    RDS_Golden_Image_Combobox.config(state="disabled")
    RDS_Snapshot_Combobox.config(state="disabled")
    RDS_LofOffPolicy_Combobox.config(state="disabled")
    RDS_Resize_checkbox.config(state="disabled")
    RDS_StopOnError_checkbox.config(state="disabled")
    RDS_secondaryimage_checkbox.config(state="disabled")
    RDS_CoresPerSocket_ComboBox.config(state='disabled')
    RDS_Memory_ComboBox.config(state='disabled')
    RDS_Promote_Secondary_Image_button.config(state='disabled')
    hvconnectionobj = connect_pod(pod=global_RDS_selected_farm["pod"])
    horizon_inventory = horizon_functions.Inventory(
        url=hvconnectionobj.url, access_token=hvconnectionobj.access_token)
    horizon_inventory.cancel_rds_farm_push_image(
        farm_id=global_RDS_selected_farm["id"])
    hvconnectionobj.hv_disconnect()


def RDS_Promote_Secondary_Image_button_callback():
    global global_RDS_selected_farm
    RDS_Secondary_Machine_Options_Combobox.config(state="disabled")
    RDS_machinecount_textbox.config(state="disabled")
    RDS_Apply_Golden_Image_button.config(state="disabled")
    RDS_Apply_Secondary_Image_button.config(state="disabled")
    RDS_Cancel_Secondary_Image_button.config(state="disabled")
    RDS_Enable_datetimepicker_checkbox.config(state="disabled")
    RDS_CPUCount_ComboBox.config(state="disabled")
    RDS_cal.config(state="disabled")
    RDS_Golden_Image_Combobox.config(state="disabled")
    RDS_Snapshot_Combobox.config(state="disabled")
    RDS_LofOffPolicy_Combobox.config(state="disabled")
    RDS_Resize_checkbox.config(state="disabled")
    RDS_StopOnError_checkbox.config(state="disabled")
    RDS_secondaryimage_checkbox.config(state="disabled")
    RDS_CoresPerSocket_ComboBox.config(state='disabled')
    RDS_Memory_ComboBox.config(state='disabled')
    RDS_Promote_Secondary_Image_button.config(state='disabled')
    hvconnectionobj = connect_pod(pod=global_RDS_selected_farm["pod"])
    horizon_inventory = horizon_functions.Inventory(
        url=hvconnectionobj.url, access_token=hvconnectionobj.access_token)
    horizon_inventory.promote_pending_rds_farm_image(
        farm_id=global_RDS_selected_farm["id"])
    hvconnectionobj.hv_disconnect()


def RDS_Apply_Golden_Image_button_callback():
    global global_RDS_selected_farm, global_RDS_selected_vm, global_RDS_selected_vm, hvconnectionobj, RDS_hour_spin, RDS_minute_spin, RDS_cal
    if RDS_Enable_datetimepicker_checkbox_var.get() == True:
        datetime_var = get_selected_datetime(
            RDS_cal, RDS_hour_spin, RDS_minute_spin)
        next_scheduled_time = datetime.timestamp(datetime_var)*1000
    else:
        next_scheduled_time = time.time()

    pod = global_RDS_selected_vm["pod"]
    hvconnectionobj = connect_pod(pod=pod)
    horizon_inventory = horizon_functions.Inventory(
        url=hvconnectionobj.url, access_token=hvconnectionobj.access_token)
    farm_id = global_RDS_selected_farm['id']
    parent_vm_id = global_RDS_selected_vm['id']
    snapshot_id = global_RDS_selected_snapshot['id']
    RDS_Resize_checkbox_var_selected = RDS_Resize_checkbox_var.get()
    RDS_CoresPerSocket_ComboBox_var_selected = RDS_CoresPerSocket_ComboBox_var.get()
    RDS_CPUCount_ComboBox_var_selected = RDS_CPUCount_ComboBox_var.get()
    RDS_Memory_ComboBox_var_selected = RDS_Memory_ComboBox_var.get()
    if RDS_Secondary_Machine_Options_Combobox_var.get() != RDS_Secondary_Machine_Options_Combobox_default_value:
        selected_machine_count = int(RDS_machinecount_textbox.get())
        machinefilter = {}
        machinefilter["type"] = "Equals"
        machinefilter["name"] = "farm_id"
        machinefilter["value"] = farm_id
        machines = horizon_inventory.get_rds_servers(filter=machinefilter)
        machines = sorted(machines, key=lambda x: x["name"])
        if "percent" in RDS_Secondary_Machine_Options_Combobox_var.get():
            machinecount = len(machines)
            selected_machine_count = math.ceil(
                (selected_machine_count / 100) * machinecount)
            rds_server_ids = [d["id"]
                              for d in machines[:selected_machine_count]]
        else:
            rds_server_ids = [d["id"]
                              for d in machines[:selected_machine_count]]
    else:
        rds_server_ids = None
    if RDS_Resize_checkbox_var_selected == True and RDS_CoresPerSocket_ComboBox_var_selected and RDS_CPUCount_ComboBox_var_selected and RDS_Memory_ComboBox_var_selected:
        compute_profile_num_cores_per_socket = RDS_CoresPerSocket_ComboBox_var.get()
        compute_profile_num_cpus = RDS_CPUCount_ComboBox_var.get()
        compute_profile_ram_mb = RDS_Memory_ComboBox_var.get()
    else:
        compute_profile_num_cores_per_socket = None
        compute_profile_num_cpus = None
        compute_profile_ram_mb = None

    horizon_inventory.rds_farm_schedule_maintenance(farm_id=farm_id, parent_vm_id=parent_vm_id, maintenance_mode="IMMEDIATE", snapshot_id=snapshot_id, rds_server_ids=rds_server_ids, compute_profile_ram_mb=compute_profile_ram_mb, compute_profile_num_cpus=compute_profile_num_cpus,
                                                    compute_profile_num_cores_per_socket=compute_profile_num_cores_per_socket, logoff_policy=RDS_LofOffPolicy_Combobox_var.get(), next_scheduled_time=next_scheduled_time, selective_schedule_maintenance=RDS_secondaryimage_checkbox_var.get())
    RDS_Secondary_Machine_Options_Combobox.config(state="disabled")
    RDS_machinecount_textbox.config(state="disabled")
    RDS_Apply_Golden_Image_button.config(state="disabled")
    RDS_Apply_Secondary_Image_button.config(state="disabled")
    RDS_Cancel_Secondary_Image_button.config(state="disabled")
    RDS_Enable_datetimepicker_checkbox.config(state="disabled")
    RDS_CPUCount_ComboBox.config(state="disabled")
    RDS_cal.config(state="disabled")
    RDS_Golden_Image_Combobox.config(state="disabled")
    RDS_Snapshot_Combobox.config(state="disabled")
    RDS_LofOffPolicy_Combobox.config(state="disabled")
    RDS_Resize_checkbox.config(state="disabled")
    RDS_StopOnError_checkbox.config(state="disabled")
    RDS_secondaryimage_checkbox.config(state="disabled")
    RDS_CoresPerSocket_ComboBox.config(state='disabled')
    RDS_Memory_ComboBox.config(state='disabled')
    RDS_Promote_Secondary_Image_button.config(state='disabled')
    hvconnectionobj.hv_disconnect()


def RDS_Farm_Combobox_callback(event):
    global global_rds_farms, global_base_vms, RDS_Golden_Image_Combobox__selected_default, RDS_Golden_Image_Combobox_values, global_RDS_selected_farm, global_base_snapshots
    RDS_Secondary_Machine_Options_Combobox.config(state="disabled")
    RDS_machinecount_textbox.config(state="disabled")
    RDS_Apply_Golden_Image_button.config(state="disabled")
    RDS_Apply_Secondary_Image_button.config(state="disabled")
    RDS_Cancel_Secondary_Image_button.config(state="disabled")
    RDS_Enable_datetimepicker_checkbox.config(state="disabled")
    RDS_CPUCount_ComboBox.config(state="disabled")
    RDS_cal.config(state="disabled")
    RDS_Golden_Image_Combobox.config(state="disabled")
    RDS_Snapshot_Combobox.config(state="disabled")
    RDS_LofOffPolicy_Combobox.config(state="disabled")
    RDS_Resize_checkbox.config(state="disabled")
    RDS_CoresPerSocket_ComboBox.config(state='disabled')
    RDS_CPUCount_ComboBox.config(state='disabled')
    RDS_Memory_ComboBox.config(state='disabled')
    try:
        RDS_Golden_Image_Combobox_values.clear()
    except:
        RDS_Golden_Image_Combobox_values = []
    global_RDS_selected_farm = RDS_Farm_Combobox_values[RDS_Farm_Combobox_var.get(
    )]
    # print(global_RDS_selected_farm)
    pool_name = global_RDS_selected_farm["name"]
    pool_displayname = global_RDS_selected_farm["display_name"]
    podname = global_RDS_selected_farm['pod']
    if global_RDS_selected_farm["enabled"] == True:
        state = "Enabled"
    else:
        state = "Disabled"
    if global_RDS_selected_farm["automated_farm_settings"]["enable_provisioning"] == True:
        provisioning_state = "Enabled"
    else:
        provisioning_state = "Disabled"
    vcenter_id = global_RDS_selected_farm["automated_farm_settings"]['vcenter_id']
    prinary_basevm_id = global_RDS_selected_farm[
        "automated_farm_settings"]["provisioning_settings"]["parent_vm_id"]
    primary_snapshot_id = global_RDS_selected_farm["automated_farm_settings"][
        "provisioning_settings"]["base_snapshot_id"]

    try:
        provisioning_progress = global_RDS_selected_farm["automated_farm_settings"][
            "provisioning_status_data"]["instant_clone_pending_image_progress"]
    except:
        provisioning_progress = "N/A"
    try:
        deployment_time = datetime.fromtimestamp(
            global_RDS_selected_farm["automated_farm_settings"]["provisioning_status_data"]["instant_clone_push_image_settings"]["start_time"] / 1000)
    except:
        deployment_time = "N/A"
    primary_basevm_name = [
        item for item in global_base_vms if item["id"] == prinary_basevm_id][0]["name"]
    primary_basesnapshot_name = [
        item for item in global_base_snapshots if item["id"] == primary_snapshot_id][0]["name"]
    try:
        secondary_basevm_id = global_RDS_selected_farm["automated_farm_settings"][
            "provisioning_status_data"]["instant_clone_pending_image_parent_vm_id"]
        secondary_basevm_name = [
            item for item in global_base_vms if item["id"] == secondary_basevm_id][0]["name"]
    except:
        secondary_basevm_name = "N/A"
    try:
        secondary_snapshot_id = global_RDS_selected_farm["automated_farm_settings"][
            "provisioning_status_data"]["instant_clone_pending_image_snapshot_id"]
        secondary_basesnapshot_name = [
            item for item in global_base_snapshots if item["id"] == secondary_snapshot_id][0]["name"]
    except:
        secondary_basesnapshot_name = "N/A"
    pool_id = global_RDS_selected_farm["id"]
    current_image_state = global_RDS_selected_farm["automated_farm_settings"][
        "provisioning_status_data"]["instant_clone_current_image_state"]
    instant_clone_operation = global_RDS_selected_farm["automated_farm_settings"][
        "provisioning_status_data"]["instant_clone_operation"]
    try:
        instant_clone_pending_image_state = global_RDS_selected_farm["automated_farm_settings"][
            "provisioning_status_data"]["instant_clone_pending_image_state"]
    except:
        instant_clone_pending_image_state = "N/A"
    RDS_textblock_text = f"Desktop Pool Status:\nName: {pool_name}\nDisplay Name: {pool_displayname}\nDesktop Pool State = {state}\nProvisioning State = {provisioning_state}\nCurrent Image State = {current_image_state}\nInstant Clone Operation = {instant_clone_operation}\nImage Deployment time = {deployment_time}\nBase VM = {primary_basevm_name}\nBase Snapshot = {primary_basesnapshot_name}\nSecondary or Pending VM = {secondary_basevm_name}\nSecondary or Pending SNapshot = {secondary_basesnapshot_name}\nPending Image State = {instant_clone_pending_image_state}\nPending Image Progress = {provisioning_progress}"
    RDS_Status_Textblock.delete(1.0, tk.END)
    RDS_Status_Textblock.insert(tk.END, RDS_textblock_text)
    if (instant_clone_operation == "NONE" and instant_clone_pending_image_state == "N/A") or (instant_clone_operation == "NONE" and instant_clone_pending_image_state == "FAILED"):
        optional_golden_images = [item for item in global_base_vms if item["vcenter_id"]
                                  == vcenter_id and "UNSUPPORTED_OS_FOR_FARM" not in item["incompatible_reasons"]]
        RDS_Golden_Image_Combobox_values = {
            item["name"]: item for item in optional_golden_images}
        RDS_Golden_Image_Combobox__selected_default = optional_golden_images[0]['name']
        RDS_Golden_Image_Combobox['values'] = list(
            RDS_Golden_Image_Combobox_values.keys())
        RDS_Golden_Image_Combobox.set(
            RDS_Golden_Image_Combobox__selected_default)
        RDS_Cancel_Secondary_Image_button.config(state="disabled")
        RDS_Promote_Secondary_Image_button.config(state="disabled")
        RDS_Apply_Golden_Image_button.config(state="disabled")
        RDS_Golden_Image_Combobox.config(state='readonly')
        RDS_secondaryimage_checkbox_callback()
        RDS_Enable_datetimepicker_checkbox_callback()
        RDS_Resize_checkbox_callback()
        RDS_Golden_Image_Combobox.event_generate("<<ComboboxSelected>>")
    elif instant_clone_operation == "NONE" and instant_clone_pending_image_state == "READY_HELD":
        RDS_Cancel_Secondary_Image_button.config(state="enabled")
        RDS_Promote_Secondary_Image_button.config(state="enabled")
        RDS_Apply_Golden_Image_button.config(state="disabled")
        RDS_Apply_Secondary_Image_button.config(state="enabled")
        RDS_Secondary_Machine_Options_Combobox.config(state="enabled")
    elif instant_clone_operation == "SCHEDULE_PUSH_IMAGE" and instant_clone_pending_image_state != "UNPUBLISHING":
        RDS_Cancel_Secondary_Image_button.config(state="enabled")


def RDS_Golden_Image_Combobox_callback(event):
    global global_rds_farms, global_base_vms, RDS_Snapshot_Combobox__selected_default, global_base_snapshots, RDS_Snapshot_Combobox_values, global_RDS_selected_vm
    try:
        RDS_Snapshot_Combobox_values.clear()
    except:
        RDS_Snapshot_Combobox_values = []
    global_RDS_selected_vm = RDS_Golden_Image_Combobox_values[RDS_Golden_Image_Combobox_var.get(
    )]

    podname = global_RDS_selected_vm['pod']
    vcenter_id = global_RDS_selected_vm['vcenter_id']
    basevm_id = global_RDS_selected_vm['id']
    optional_snapshots = [item for item in global_base_snapshots if item["vcenter_id"]
                          == vcenter_id and item["basevmid"] == basevm_id]
    RDS_Snapshot_Combobox_values = {
        item["name"]: item for item in optional_snapshots}
    RDS_Snapshot_Combobox__selected_default = optional_snapshots[0]['name']
    RDS_Snapshot_Combobox['values'] = list(RDS_Snapshot_Combobox_values.keys())
    RDS_Snapshot_Combobox.config(state='readonly')
    RDS_Snapshot_Combobox.set(RDS_Snapshot_Combobox__selected_default)
    RDS_Snapshot_Combobox.event_generate("<<ComboboxSelected>>")


def RDS_Snapshot_Combobox_callback(event):
    global global_RDS_selected_snapshot, global_RDS_selected_farm
    global_RDS_selected_snapshot = RDS_Snapshot_Combobox_values[RDS_Snapshot_Combobox_var.get(
    )]

    RDS_LofOffPolicy_Combobox.config(state='readonly')
    RDS_Resize_checkbox.config(state="enabled")
    RDS_Enable_datetimepicker_checkbox.config(state='enabled')
    RDS_secondaryimage_checkbox.config(state='enabled')
    RDS_StopOnError_checkbox.config(state='enabled')
    RDS_Apply_Golden_Image_button.config(state='enabled')
    RDS_memsize = None
    RDS_cpucount = None
    RDS_corespersocket = None
    try:
        RDS_memsize = global_RDS_selected_farm['automated_farm_settings'][
            'provisioning_settings']['compute_profile_ram_mb']
        RDS_cpucount = global_RDS_selected_farm['automated_farm_settings'][
            'provisioning_settings']['compute_profile_num_cpus']
        RDS_corespersocket = global_RDS_selected_farm['automated_farm_settings'][
            'provisioning_settings']['compute_profile_num_cores_per_socket']
    except:
        RDS_memsize = None
        RDS_cpucount = None
        RDS_corespersocket = None
    if RDS_memsize is not None and RDS_corespersocket is not None:
        RDS_Resize_checkbox_var.set(True)
        RDS_CoresPerSocket_ComboBox_var.set(RDS_corespersocket)
        RDS_CPUCount_ComboBox_var.set(RDS_cpucount)
        RDS_Memory_ComboBox_var.set(RDS_memsize)
        RDS_Resize_checkbox_callback()


def RDS_Resize_checkbox_callback():
    if RDS_Resize_checkbox_var.get() == True:
        RDS_CoresPerSocket_ComboBox.config(state='readonly')
        RDS_CPUCount_ComboBox.config(state='readonly')
        RDS_Memory_ComboBox.config(state='readonly')
    else:
        RDS_CoresPerSocket_ComboBox.config(state='disabled')
        RDS_CPUCount_ComboBox.config(state='disabled')
        RDS_Memory_ComboBox.config(state='disabled')


def RDS_Enable_datetimepicker_checkbox_callback():
    if RDS_Enable_datetimepicker_checkbox_var.get() == True:
        RDS_cal.config(state='readonly')
        RDS_minute_spin.config(state='normal')
        RDS_hour_spin.config(state='normal')
    else:
        RDS_cal.config(state='disabled')
        RDS_minute_spin.config(state='disabled')
        RDS_hour_spin.config(state='disabled')
# endregion


# region functions for button handling of configuration tab

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
    config_conserver_combobox_data = [
        item for item in config_connection_servers if item["PodName"] == config_conserver_combobox_selected_name]
    config_conserver_combobox['values'] = [item["ServerDNS"]
                                           for item in config_conserver_combobox_data]
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
        config_status_label.config(
            text="Please enter Connection Server, Username and password first.")
    else:
        config = configparser.ConfigParser()
        try:
            config['UserInfo'] = {'Username': config_username, 'Domain': config_domain,
                                  'ServerName': config_server_name, 'Save_Password': str(config_save_password_checkbox_var.get())}
            config['Pods'] = {'Pods': config_pods}
            config['Connection_Servers'] = {
                'Connection_Servers': config_connection_servers}
            with open(CONFIG_FILE, 'w') as configfile:
                config.write(configfile)
        except:
            logger.error("Configuration could not be saved")
        if config_save_password == True:
            try:
                keyring.set_password(
                    application_name, config_username, config_password)
                logger.info("Password saved to credentials store")
            except keyring.errors.PasswordDeleteError:
                logger.error(
                    "Password could not be saved to the credentials store")
        config_status_label.config(text="Configuration saved")
        logger.info("Configuration saved")


def config_reset_button_callback():
    logger.info("Resetting configuration")
    global config_username, config_domain, config_server_name, config_password, config_url
    config_reset_stored_password()
    del config_password
    config_password = None
    config_save_password_checkbox_var.set(False)
    config_username_textbox.delete(0, tk.END)
    config_username_textbox.insert(
        tk.END, config_username_textbox_default_text)
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

    config_url = None
    config = configparser.ConfigParser()
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    config_status_label.config(
        text="Configuration reset and configuration file deleted.")
    logger.info("Configuration reset")


def config_test_button_callback():
    test_button_thread = threading.Thread(
        target=config_test_button_callback_thread)
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
        config_status_label.config(
            text="Not all information is provided, please check the configuration.")
    elif config_password is None:
        logger.error("No password was set")
        config_status_label.config(text="Please set a password first")
    else:
        logger.info("Testing connection to: "+config_server_name)
        config_url = "https://" + config_server_name
        hvconnectionobj = horizon_functions.Connection(
            username=config_username, domain=config_domain, password=config_password, url=config_url)
        try:
            hvconnectionobj.hv_connect()
            build_pod_info(hvconnectionobj)
            hvconnectionobj.hv_disconnect()
            logger.info("Sucessfully finished testing configuration")
            logger.info("Saving configuration since it works")
            config_save_button_callback()
            config_status_label.config(
                text="Successfully finished testing configuration")
        except Exception as e:
            config_status_label.config(
                text="Error testing the connection, see the log file for details")
            logger.error("Error while testing the credentials")
            logger.error(str(e))

# endregion

# region Various functions


def validate_int_func(P):
    # P is the proposed input

    if P == "" or P.isdigit():
        if len(P) > 3:
            return False
        else:
            return True
    else:
        return False


def get_selected_datetime(cal, hours, minutes):
    date_var = cal.get_date()
    hours_var = int(hours.get())
    minutes_var = int(minutes.get())
    selected_datetime = datetime.combine(
        date_var, dt_time(hours_var, minutes_var))
    return selected_datetime


def generic_Connect_Button_callback():
    generic_connect_thread = threading.Thread(
        target=generic_Connect_Button_callback_thread)
    generic_connect_thread.start()


def generic_Connect_Button_callback_thread():
    global hvconnectionobj, global_desktop_pools, global_rds_farms, global_base_vms, global_base_snapshots, global_datacenters, global_vcenters, VDI_DesktopPool_Combobox_values, RDS_Farm_Combobox_values, config_password
    if config_server_name is None and config_password is None:
        logger.info("No Connection server and password found in config")
        VDI_Statusbox_Label.config(
            text="Please configure the connection details first on the Configuration tab")
        RDS_Statusbox_Label.config(
            text="Please configure the connection details first on the Configuration tab")
        refresh_window()
        return
    elif config_server_name is not None and config_password is None:
        logger.info("No password found in config")
        VDI_Statusbox_Label.config(
            text="Please configure the password first on the Configuration tab")
        RDS_Statusbox_Label.config(
            text="Please configure the password first on the Configuration tab")
        refresh_window()
        return
    else:
        VDI_Connect_Button.config(state='disabled')
        RDS_Connect_Button.config(state='disabled')
        VDI_DesktopPool_Combobox.config(state='disabled')
        VDI_Golden_Image_Combobox.config(state='disabled')
        VDI_Snapshot_Combobox.config(state='disabled')
        VDI_Promote_Secondary_Image_button.config(state="disabled")
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
            global_rds_farms = []
            global_desktop_pools = []
            global_base_vms = []
            global_base_snapshots = []
            global_datacenters = []
            global_vcenters = []
            VDI_DesktopPool_Combobox_values = []
            RDS_Farm_Combobox_values = []
        for pod in config_pods:
            logger.info(f'Connecting to Pod: {pod}')
            hvconnectionobj = connect_pod(pod)
            if hvconnectionobj != False:
                horizon_inventory = horizon_functions.Inventory(
                    url=hvconnectionobj.url, access_token=hvconnectionobj.access_token)
                horizon_config = horizon_functions.Config(
                    url=hvconnectionobj.url, access_token=hvconnectionobj.access_token)
                horizon_External = horizon_functions.External(
                    url=hvconnectionobj.url, access_token=hvconnectionobj.access_token)
                vdi_filter = {}
                vdi_filter["type"] = "And"
                vdi_filter["filters"] = []
                vdi_filter1 = {}
                vdi_filter1["type"] = "Equals"
                vdi_filter1["name"] = "source"
                vdi_filter1["value"] = "INSTANT_CLONE"
                vdi_filter2 = {}
                vdi_filter2["type"] = "Equals"
                vdi_filter2["name"] = "type"
                vdi_filter2["value"] = "AUTOMATED"
                vdi_filter["filters"].append(vdi_filter1)
                vdi_filter["filters"].append(vdi_filter2)
                rds_filter = {}
                rds_filter["type"] = "Equals"
                rds_filter["name"] = "automated_farm_settings.image_source"
                rds_filter["value"] = "VIRTUAL_CENTER"
                logger.info(f'Getting Desktop Pools with filter {vdi_filter}')
                desktop_pools = horizon_inventory.get_desktop_pools(
                    filter=vdi_filter)
                for pool in desktop_pools:
                    pool['pod'] = pod
                    logger.info(f'Found Pool: {pool["name"]}')
                global_desktop_pools += desktop_pools
                logger.info(f'Getting RDS Farms with filter {rds_filter}')
                rds_farms = horizon_inventory.get_farms(filter=rds_filter)
                for farm in rds_farms:
                    farm['pod'] = pod
                    logger.info(f'Found: {farm["name"]}')
                global_rds_farms += rds_farms
                logger.info("Getting vCenters")
                vcenters = horizon_config.get_virtual_centers()
                for vcenter in vcenters:
                    vcenter['pod'] = pod
                    logger.info(f'Found vCenter: {vcenter["server_name"]}')
                    logger.info("Getting datacenters")
                    datacenters = horizon_External.get_datacenters(
                        vcenter_id=vcenter['id'])
                    for datacenter in datacenters:
                        datacenter['pod'] = pod
                        logger.info(f'Found Datacenter {datacenter["name"]}')
                        logger.info("Getting Base VMs and snapshots")
                        basevms = horizon_External.get_base_vms(
                            vcenter_id=vcenter['id'], datacenter_id=datacenter['id'], filter_incompatible_vms=True)
                        if isinstance(basevms, list):
                            basevms = basevms
                        else:
                            basevms = [basevms]
                        for basevm in basevms:
                            if 'incompatible_reasons' not in basevm:
                                basevm['incompatible_reasons'] = []
                            basevm['pod'] = pod
                            basesnapshots = horizon_External.get_base_snapshots(
                                vcenter_id=vcenter['id'], base_vm_id=basevm['id'])
                            if len(basesnapshots) is not None:
                                basevm["snapshotcount"] = len(basesnapshots)
                            else:
                                basevm["snapshotcount"] = 0
                            if isinstance(basesnapshots, list):
                                basesnapshots = basesnapshots
                            else:
                                basesnapshots = [basesnapshots]
                            if len(basesnapshots) >= 1:
                                for basesnapshot in basesnapshots:
                                    basesnapshot['basevmid'] = basevm['id']
                                global_base_snapshots += basesnapshots
                        basevms = [
                            item for item in basevms if item["snapshotcount"] >= 1]
                        global_base_vms += basevms
                        logger.info("Done getting Base VMs and snapshots")
                    global_datacenters += datacenter
                global_vcenters += vcenters
                logger.info(f'Disconnecting from Pod: {pod}')
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
                pod_tmp = pool['pod']
                new_name = f'{name} ({pod_tmp}])'
                pool['name'] = new_name
            else:
                vdi_name_dict_mapping.append(name)

        for farm in global_rds_farms:
            name = farm['name']
            if name in rds_name_dict_mapping:
                pod_tmp = farm['pod']
                new_name = f'{name} ({pod_tmp}])'
                farm['name'] = new_name
            else:
                rds_name_dict_mapping.append(name)

        VDI_DesktopPool_Combobox_values = {
            item["name"]: item for item in global_desktop_pools}
        VDI_DesktopPool_Combobox__selected_default = global_desktop_pools[0]['name']
        VDI_DesktopPool_Combobox['values'] = list(
            VDI_DesktopPool_Combobox_values.keys())
        VDI_DesktopPool_Combobox.config(state='readonly')
        VDI_DesktopPool_Combobox.set(
            VDI_DesktopPool_Combobox__selected_default)
        VDI_DesktopPool_Combobox.event_generate("<<ComboboxSelected>>")

        RDS_Farm_Combobox_values = {
            item["name"]: item for item in global_rds_farms}
        RDS_Farm_Combobox__selected_default = global_rds_farms[0]['name']
        RDS_Farm_Combobox['values'] = list(RDS_Farm_Combobox_values.keys())
        RDS_Farm_Combobox.config(state='readonly')
        RDS_Farm_Combobox.set(RDS_Farm_Combobox__selected_default)
        RDS_Farm_Combobox.event_generate("<<ComboboxSelected>>")
        VDI_Connect_Button.config(text="Refresh")
        RDS_Connect_Button.config(text="Refresh")
        VDI_Connect_Button.config(state='normal')
        RDS_Connect_Button.config(state='normal')
        VDI_Statusbox_Label.config(text="Connected")
        RDS_Statusbox_Label.config(text="Connected")


def connect_pod(pod: str):
    global connect_pod_thread_var
    connect_pod_thread_var = []
    connect_pod_thread_tmp = threading.Thread(
        target=connect_pod_thread(pod=pod))
    connect_pod_thread_tmp.start()
    return connect_pod_thread_var


def connect_pod_thread(pod: str):
    global config_server_name, hvconnectionobj, connect_pod_thread_var, config_connection_servers
    con_servers_to_use = [
        item for item in config_connection_servers if item["PodName"] == pod]
    hvconnectionobj = None
    for con_server in con_servers_to_use:
        serverdns = con_server['ServerDNS']
        logger.info("connecting to: "+serverdns)
        config_url = "https://" + serverdns
        hvconnectionobj = horizon_functions.Connection(
            username=config_username, domain=config_domain, password=config_password, url=config_url)
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


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def refresh_window():
    # Redraw the window
    root.update()
    root.update_idletasks()

# def updateTime(time):
#     time_lbl.configure(text="{}:{}".format(*time)) # if you are using 24 hours, remove the 3rd flower bracket its for period


def textbox_handle_focus_in(event, default_text):
    if event.widget.get() == default_text:
        event.widget.delete(0, 'end')
        # Change text color to black when editing
        event.widget.config(foreground='black')


def textbox_handle_focus_out(event, default_text):
    if event.widget.get().strip() == '':
        event.widget.insert(tk.END, default_text)
        # Change text color to grey when not editing
        event.widget.config(foreground='grey')
# endregion


# region Generic tkinter config
# root = tk.Tk()
root = ThemedTk(theme="plastik",themebg=True)
root.title("Horizon Golden Image Deployment Tool")

# Set the custom icon/logo for the taskbar/Dock based on the platform
# root.iconbitmap(logo_image)  # Windows icon file
iconPath = resource_path(logo_image)
root.iconbitmap(iconPath)
# iconimage = tk.PhotoImage(file="logo.ico")
# root.iconphoto(False, iconimage)
validate_int = root.register(validate_int_func)

root.geometry("950x470")

# style = ttk.Style()
# style.map(
#     "TButton", foreground=[('disabled', 'black')]
# )
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

# endregion


# region Tab 1 - VDI Desktop Pools
tab1 = ttk.Frame(tab_control)
tab_control.add(tab1, text="VDI Pools")
# tab1.configure(style='Custom.TFrame')

# Place your Tab 1 widgets here
# Create Buttons
VDI_Connect_Button = ttk.Button(
    tab1, text="Connect", command=generic_Connect_Button_callback)
VDI_Connect_Button.place(x=750, y=35, width=160, height=25)


VDI_Apply_Golden_Image_button = ttk.Button(
    tab1, state="disabled", text="Deploy Golden Image", command=VDI_Apply_Golden_Image_button_callback)
VDI_Apply_Golden_Image_button.place(x=570, y=385, width=160, height=25)

VDI_Apply_Secondary_Image_button = ttk.Button(
    tab1, state="disabled", text="Apply Secondary Image", command=VDI_Apply_Secondary_Image_button_callback)
VDI_Apply_Secondary_Image_button.place(x=570, y=325, width=160, height=25)

VDI_Cancel_Secondary_Image_button = ttk.Button(
    tab1, state="disabled", text="Cancel Image Push", command=VDI_Cancel_Secondary_Image_button_callback)
VDI_Cancel_Secondary_Image_button.place(x=570, y=295, width=160, height=25)

VDI_Promote_Secondary_Image_button = ttk.Button(
    tab1, state="disabled", text="Promote secondary Image", command=VDI_Promote_Secondary_Image_button_callback)
VDI_Promote_Secondary_Image_button.place(x=570, y=355, width=160, height=25)

# Create Labels
VDI_Statusbox_Label = ttk.Label(
    tab1, borderwidth=1, text="Status: Not Connected", anchor="w", justify="right")
VDI_Statusbox_Label.place(x=30, y=385, width=510)

VDI_DesktopPool_Label = ttk.Label(
    tab1, borderwidth=1, text="Desktop Pool", justify="right")
VDI_DesktopPool_Label.place(x=30, y=10)

VDI_Golden_Image_Label = ttk.Label(
    tab1, borderwidth=1, text="Source VM", justify="right")
VDI_Golden_Image_Label.place(x=270, y=10)

VDI_Snapshot_Label = ttk.Label(
    tab1, borderwidth=1, text="Source Snapshot", justify="right")
VDI_Snapshot_Label.place(x=510, y=10)

VDI_hour_label = ttk.Label(tab1, text="Hour:")
VDI_hour_label.place(x=770, y=190)

VDI_minute_label = ttk.Label(tab1, text="Minute:", anchor='w')
VDI_minute_label.place(x=820, y=190)

VDI_CAL_label = ttk.Label(tab1, text="Date:")
VDI_CAL_label.place(x=770, y=145)

VDI_Memory_label = ttk.Label(tab1, text="Memory Size")
VDI_Memory_label.place(x=570, y=135)

VDI_CPUCount_label = ttk.Label(tab1, text="Total Cores Count")
VDI_CPUCount_label.place(x=570, y=185)

VDI_CoresPerSocket_label = ttk.Label(tab1, text="Cores Per Socket")
VDI_CoresPerSocket_label.place(x=570, y=235)

VDI_secondary_image_machine_options_label = ttk.Label(
    tab1, text="Secondary Image Options")
VDI_secondary_image_machine_options_label.place(x=770, y=255)

VDI_secondary_image_machine_count_label = ttk.Label(tab1, state="disabled")
VDI_secondary_image_machine_count_label_default = "Select method first"
VDI_secondary_image_machine_count_label.config(
    text=VDI_secondary_image_machine_count_label_default)
VDI_secondary_image_machine_count_label.place(x=770, y=300)

# Create ComboBoxes
VDI_DesktopPool_Combobox_var = tk.StringVar()
VDI_DesktopPool_Combobox = ttk.Combobox(
    tab1, state="disabled", textvariable=VDI_DesktopPool_Combobox_var)
VDI_DesktopPool_Combobox.place(x=30, y=35, width=220, height=25)
VDI_DesktopPool_Combobox.bind(
    "<<ComboboxSelected>>", VDI_DesktopPool_Combobox_callback)
# ToolTip(VDI_DesktopPool_Combobox,
#         msg="Select the desktop pool to update", delay=0.1)

VDI_Golden_Image_Combobox_var = tk.StringVar()
VDI_Golden_Image_Combobox = ttk.Combobox(
    tab1, state="disabled", textvariable=VDI_Golden_Image_Combobox_var)
VDI_Golden_Image_Combobox.place(x=270, y=35, width=220, height=25)
VDI_Golden_Image_Combobox.bind(
    "<<ComboboxSelected>>", VDI_Golden_Image_Combobox_callback)
# ToolTip(VDI_Golden_Image_Combobox, msg="Select the new source VM", delay=0.1)

VDI_Snapshot_Combobox_var = tk.StringVar()
VDI_Snapshot_Combobox = ttk.Combobox(
    tab1, state="disabled", textvariable=VDI_Snapshot_Combobox_var)
VDI_Snapshot_Combobox.place(x=510, y=35, width=220, height=25)
VDI_Snapshot_Combobox.bind("<<ComboboxSelected>>",
                           VDI_Snapshot_Combobox_callback)
# ToolTip(VDI_Snapshot_Combobox, msg="Select the new source Snapshot", delay=0.1)

VDI_LofOffPolicy_Combobox_var = tk.StringVar()
VDI_LofOffPolicy_Combobox = ttk.Combobox(tab1, state="disabled", values=[
                                         "FORCE_LOGOFF", "WAIT_FOR_LOGOFF"], textvariable=VDI_LofOffPolicy_Combobox_var)
VDI_LofOffPolicy_Combobox_default_value = "WAIT_FOR_LOGOFF"
VDI_LofOffPolicy_Combobox.set(VDI_LofOffPolicy_Combobox_default_value)
VDI_LofOffPolicy_Combobox.place(x=570, y=80, width=160, height=25)
# ToolTip(VDI_LofOffPolicy_Combobox, msg="Select the logoff Policy", delay=0.1)

VDI_Memory_ComboBox_var = tk.StringVar()
VDI_Memory_ComboBox = ttk.Combobox(
    tab1, state="disabled", values=memory_list, textvariable=VDI_Memory_ComboBox_var)
VDI_Memory_ComboBox.place(x=570, y=155, width=160, height=25)
# ToolTip(VDI_Memory_ComboBox, msg="Select the new memory size", delay=0.1)

VDI_CPUCount_ComboBox_var = tk.StringVar()
VDI_CPUCount_ComboBox = ttk.Combobox(
    tab1, state="disabled", values=onetosixtyfour, textvariable=VDI_CPUCount_ComboBox_var)
VDI_CPUCount_ComboBox.place(x=570, y=205, width=160, height=25)
# ToolTip(VDI_CPUCount_ComboBox, msg="Select the new CPU count", delay=0.1)

VDI_CoresPerSocket_ComboBox_var = tk.StringVar()
VDI_CoresPerSocket_ComboBox = ttk.Combobox(
    tab1, state="disabled", values=onetosixtyfour, textvariable=VDI_CoresPerSocket_ComboBox_var)
VDI_CoresPerSocket_ComboBox.place(x=570, y=255, width=160, height=25)
# ToolTip(VDI_CoresPerSocket_ComboBox,
# msg="Select the number of cores per socket", delay=0.1)

VDI_Secondary_Machine_Options_Combobox_var = tk.StringVar()
VDI_Secondary_Machine_Options_Combobox = ttk.Combobox(tab1, state="disabled", values=[
                                                      "Don't deploy to machines", "Percentage of machines", "Number of machines"], textvariable=VDI_Secondary_Machine_Options_Combobox_var)
VDI_Secondary_Machine_Options_Combobox_default_value = "Don't deploy to machines"
VDI_Secondary_Machine_Options_Combobox.set(
    VDI_Secondary_Machine_Options_Combobox_default_value)
VDI_Secondary_Machine_Options_Combobox.bind(
    "<<ComboboxSelected>>", VDI_Secondary_Machine_Options_Combobox_callback)
VDI_Secondary_Machine_Options_Combobox.place(
    x=770, y=275, height=25, width=160)
# ToolTip(VDI_Secondary_Machine_Options_Combobox,
#         msg="Select selection type of secondary machines", delay=0.1)

# Create Checkboxes
VDI_secondaryimage_checkbox_var = tk.BooleanVar()
VDI_secondaryimage_checkbox = ttk.Checkbutton(tab1, state="disabled", text="Push as Secondary Image",
                                              variable=VDI_secondaryimage_checkbox_var, command=VDI_secondaryimage_checkbox_callback)
VDI_secondaryimage_checkbox.place(x=750, y=235, height=25)
# ToolTip(VDI_secondaryimage_checkbox,
#         msg="Check to deploy the new golden image as a secondary image", delay=0.1)

VDI_StopOnError_checkbox_var = tk.BooleanVar()
VDI_StopOnError_checkbox = ttk.Checkbutton(
    tab1, state="disabled", text="Stop on error", variable=VDI_StopOnError_checkbox_var)
VDI_StopOnError_checkbox.place(x=750, y=100, height=25)
# ToolTip(VDI_StopOnError_checkbox,
# msg="CHeck to make sure deployment of new desktops stops on an error", delay=0.1)
VDI_StopOnError_checkbox_var.set(True)

VDI_Resize_checkbox_var = tk.BooleanVar()
VDI_Resize_checkbox = ttk.Checkbutton(tab1, state="disabled", text="Enable Resize Options",
                                      variable=VDI_Resize_checkbox_var, command=VDI_Resize_checkbox_callback)
VDI_Resize_checkbox.place(x=570, y=110, height=25)
# ToolTip(VDI_Resize_checkbox,
#         msg="Check to enable resizing of the Golden Image in the Desktop Pool", delay=0.1)
VDI_Resize_checkbox_var.set(False)

VDI_vtpm_checkbox_var = tk.BooleanVar()
VDI_vtpm_checkbox = ttk.Checkbutton(
    tab1, state="disabled", text="Add vTPM", variable=VDI_vtpm_checkbox_var)
VDI_vtpm_checkbox.place(x=750, y=80, height=25)
# ToolTip(VDI_vtpm_checkbox, msg="Check to add a vTPM", delay=0.1)

VDI_Enable_datetimepicker_checkbox_var = tk.BooleanVar()
VDI_Enable_datetimepicker_checkbox = ttk.Checkbutton(tab1, state="disabled", text="Schedule deployment",
                                                     variable=VDI_Enable_datetimepicker_checkbox_var, command=VDI_Enable_datetimepicker_checkbox_callback)
VDI_Enable_datetimepicker_checkbox.place(x=750, y=120, height=25)
# ToolTip(VDI_Enable_datetimepicker_checkbox,
#         msg="Check to enable a scheduled deployment of the new image", delay=0.1)

# Create other Widgets
VDI_Status_Textblock = tk.Text(
    tab1, borderwidth=1, relief="solid", wrap="word", state="normal")
VDI_Status_Textblock.place(x=30, y=80, height=300, width=510)
VDI_Status_Textblock.insert(tk.END, "No Info yet")

# VDI_Machines_ListBox = tk.Listbox(tab1, selectmode="multiple")
# VDI_Machines_ListBox.place(x=30, y=413, height=150, width=300)


VDI_cal = DateEntry(tab1, bg="darkblue", fg="white", year=current_datetime.year,
                    month=current_datetime.month, day=current_datetime.day)
# VDI_cal = Calendar(tab1,bg="darkblue",fg="white", selectmode="day", year=current_datetime.year, month=current_datetime.month, day=current_datetime.day)
VDI_cal.config(state="disabled")
VDI_cal.place(x=770, y=165)

VDI_hour_spin = ttk.Spinbox(
    tab1, from_=0, to=23, width=2, value=current_datetime.hour, state="disabled")
VDI_hour_spin.place(x=775, y=210)


VDI_minute_spin = ttk.Spinbox(
    tab1, from_=0, to=59, width=2, value=current_datetime.minute, state="disabled")
VDI_minute_spin.place(x=825, y=210)

VDI_machinecount_textbox = ttk.Entry(
    tab1, validate="key", validatecommand=(validate_int, "%P"), state="readonly")
VDI_machinecount_textbox.place(x=770, y=320, height=25, width=30)
# ToolTip(VDI_machinecount_textbox,
#         msg="ENter number or percentage of machines to apply the secondary image to", delay=0.1)

# endregion


# region Tab 2 - RDS Farms
tab2 = ttk.Frame(tab_control)
tab_control.add(tab2, text="RDS Farms")
# tab2.configure(style='Custom.TFrame')

# Place your Tab 2 widgets here
# create buttons

RDS_Connect_Button = ttk.Button(
    tab2, text="Connect", command=generic_Connect_Button_callback)
RDS_Connect_Button.place(x=750, y=35, width=160, height=25)


RDS_Apply_Golden_Image_button = ttk.Button(
    tab2, state="disabled", text="Deploy Golden Image", command=RDS_Apply_Golden_Image_button_callback)
RDS_Apply_Golden_Image_button.place(x=570, y=385, width=160, height=25)

RDS_Apply_Secondary_Image_button = ttk.Button(
    tab2, state="disabled", text="Apply Secondary Image", command=RDS_Apply_Secondary_Image_button_callback)
RDS_Apply_Secondary_Image_button.place(x=570, y=325, width=160, height=25)

RDS_Cancel_Secondary_Image_button = ttk.Button(
    tab2, state="disabled", text="Cancel Image Push", command=RDS_Cancel_Secondary_Image_button_callback)
RDS_Cancel_Secondary_Image_button.place(x=570, y=295, width=160, height=25)

RDS_Promote_Secondary_Image_button = ttk.Button(
    tab2, state="disabled", text="Promote secondary Image", command=RDS_Promote_Secondary_Image_button_callback)
RDS_Promote_Secondary_Image_button.place(x=570, y=483, width=220, height=25)

# Create Labels
RDS_Statusbox_Label = ttk.Label(
    tab2, borderwidth=1, text="Status: Not Connected", anchor="w", justify="right")
RDS_Statusbox_Label.place(x=30, y=385, width=510)

RDS_DesktopPool_Label = ttk.Label(
    tab2, borderwidth=1, text="RDS Farm", justify="right")
RDS_DesktopPool_Label.place(x=30, y=10)

RDS_Golden_Image_Label = ttk.Label(
    tab2, borderwidth=1, text="Source VM", justify="right")
RDS_Golden_Image_Label.place(x=270, y=10)

RDS_Snapshot_Label = ttk.Label(
    tab2, borderwidth=1, text="Source Snapshot", justify="right")
RDS_Snapshot_Label.place(x=510, y=10)

RDS_hour_label = ttk.Label(tab2, text="Hour:")
RDS_hour_label.place(x=770, y=190)

RDS_minute_label = ttk.Label(tab2, text="Minute:", anchor='w')
RDS_minute_label.place(x=820, y=190)

RDS_CAL_label = ttk.Label(tab2, text="Date:")
RDS_CAL_label.place(x=770, y=145)

RDS_Memory_label = ttk.Label(tab2, text="Memory Size")
RDS_Memory_label.place(x=570, y=135)

RDS_CPUCount_label = ttk.Label(tab2, text="Total Cores Count")
RDS_CPUCount_label.place(x=570, y=185)

RDS_CoresPerSocket_label = ttk.Label(tab2, text="Cores Per Socket")
RDS_CoresPerSocket_label.place(x=570, y=235)

RDS_secondary_image_machine_options_label = ttk.Label(
    tab2, text="Secondary Image Options")
RDS_secondary_image_machine_options_label.place(x=770, y=255)

RDS_secondary_image_machine_count_label = ttk.Label(tab2, state="disabled")
RDS_secondary_image_machine_count_label_default = "Select method first"
RDS_secondary_image_machine_count_label.config(
    text=RDS_secondary_image_machine_count_label_default)
RDS_secondary_image_machine_count_label.place(x=770, y=300)

# Create ComboBoxes
RDS_Farm_Combobox_var = tk.StringVar()
RDS_Farm_Combobox = ttk.Combobox(
    tab2, state="disabled", textvariable=RDS_Farm_Combobox_var)
RDS_Farm_Combobox.place(x=30, y=35, width=220, height=25)
RDS_Farm_Combobox.bind("<<ComboboxSelected>>", RDS_Farm_Combobox_callback)
# ToolTip(RDS_Farm_Combobox, msg="Select the Rds Farm to update", delay=0.1)

RDS_Golden_Image_Combobox_var = tk.StringVar()
RDS_Golden_Image_Combobox = ttk.Combobox(
    tab2, state="disabled", textvariable=RDS_Golden_Image_Combobox_var)
RDS_Golden_Image_Combobox.place(x=270, y=35, width=220, height=25)
RDS_Golden_Image_Combobox.bind(
    "<<ComboboxSelected>>", RDS_Golden_Image_Combobox_callback)
# ToolTip(RDS_Golden_Image_Combobox, msg="Select the new source VM", delay=0.1)

RDS_Snapshot_Combobox_var = tk.StringVar()
RDS_Snapshot_Combobox = ttk.Combobox(
    tab2, state="disabled", textvariable=RDS_Snapshot_Combobox_var)
RDS_Snapshot_Combobox.place(x=510, y=35, width=220, height=25)
RDS_Snapshot_Combobox.bind("<<ComboboxSelected>>",
                           RDS_Snapshot_Combobox_callback)
# ToolTip(RDS_Snapshot_Combobox, msg="Select the new source Snapshot", delay=0.1)

RDS_LofOffPolicy_Combobox_var = tk.StringVar()
RDS_LofOffPolicy_Combobox = ttk.Combobox(tab2, state="disabled", values=[
                                         "FORCE_LOGOFF", "WAIT_FOR_LOGOFF"], textvariable=RDS_LofOffPolicy_Combobox_var)
RDS_LofOffPolicy_Combobox_default_value = "WAIT_FOR_LOGOFF"
RDS_LofOffPolicy_Combobox.set(RDS_LofOffPolicy_Combobox_default_value)
RDS_LofOffPolicy_Combobox.place(x=570, y=80, width=160, height=25)
# ToolTip(RDS_LofOffPolicy_Combobox, msg="Select the logoff Policy", delay=0.1)

RDS_Memory_ComboBox_var = tk.StringVar()
RDS_Memory_ComboBox = ttk.Combobox(
    tab2, state="disabled", values=memory_list, textvariable=RDS_Memory_ComboBox_var)
RDS_Memory_ComboBox.place(x=570, y=155, width=160, height=25)
# ToolTip(RDS_Memory_ComboBox, msg="Select the new memory size", delay=0.1)

RDS_CPUCount_ComboBox_var = tk.StringVar()
RDS_CPUCount_ComboBox = ttk.Combobox(
    tab2, state="disabled", values=onetosixtyfour, textvariable=RDS_CPUCount_ComboBox_var)
RDS_CPUCount_ComboBox.place(x=570, y=205, width=160, height=25)
# ToolTip(RDS_CPUCount_ComboBox, msg="Select the new CPU count", delay=0.1)

RDS_CoresPerSocket_ComboBox_var = tk.StringVar()
RDS_CoresPerSocket_ComboBox = ttk.Combobox(
    tab2, state="disabled", values=onetosixtyfour, textvariable=RDS_CoresPerSocket_ComboBox_var)
RDS_CoresPerSocket_ComboBox.place(x=570, y=255, width=160, height=25)
# ToolTip(RDS_CoresPerSocket_ComboBox,
# msg="Select the number of cores per socket", delay=0.1)

RDS_Secondary_Machine_Options_Combobox_var = tk.StringVar()
RDS_Secondary_Machine_Options_Combobox = ttk.Combobox(tab2, state="disabled", values=[
                                                      "Don't deploy to machines", "First xx percent of machines", "First xx amount of machines"], textvariable=RDS_Secondary_Machine_Options_Combobox_var)
RDS_Secondary_Machine_Options_Combobox_default_value = "Don't deploy to machines"
RDS_Secondary_Machine_Options_Combobox.set(
    RDS_Secondary_Machine_Options_Combobox_default_value)
RDS_Secondary_Machine_Options_Combobox.bind(
    "<<ComboboxSelected>>", RDS_Secondary_Machine_Options_Combobox_callback)
RDS_Secondary_Machine_Options_Combobox.place(
    x=770, y=275, height=25, width=160)
# ToolTip(RDS_Secondary_Machine_Options_Combobox,
#         msg="Select selection type of secondary machines", delay=0.1)

# Create Checkboxes
RDS_secondaryimage_checkbox_var = tk.BooleanVar()
RDS_secondaryimage_checkbox = ttk.Checkbutton(tab2, state="disabled", text="Push as Secondary Image",
                                              variable=RDS_secondaryimage_checkbox_var, command=RDS_secondaryimage_checkbox_callback)
RDS_secondaryimage_checkbox.place(x=750, y=235, height=25)
# ToolTip(RDS_secondaryimage_checkbox,
#         msg="Check to deploy the new golden image as a secondary image", delay=0.1)

RDS_StopOnError_checkbox_var = tk.BooleanVar()
RDS_StopOnError_checkbox = ttk.Checkbutton(
    tab2, state="disabled", text="Stop on error", variable=RDS_StopOnError_checkbox_var)
RDS_StopOnError_checkbox.place(x=750, y=100, height=25)
# ToolTip(RDS_StopOnError_checkbox,
#         msg="CHeck to make sure deployment of new desktops stops on an error", delay=0.1)
RDS_StopOnError_checkbox_var.set(True)

RDS_Resize_checkbox_var = tk.BooleanVar()
RDS_Resize_checkbox = ttk.Checkbutton(tab2, state="disabled", text="Enable Resize Options",
                                      variable=RDS_Resize_checkbox_var, command=RDS_Resize_checkbox_callback)
RDS_Resize_checkbox.place(x=570, y=110, height=25)
# ToolTip(RDS_Resize_checkbox,
#         msg="Check to enable resizing of the Golden Image in the Rds Farm", delay=0.1)
RDS_Resize_checkbox_var.set(False)

RDS_Enable_datetimepicker_checkbox_var = tk.BooleanVar()
RDS_Enable_datetimepicker_checkbox = ttk.Checkbutton(tab2, state="disabled", text="Schedule deployment",
                                                     variable=RDS_Enable_datetimepicker_checkbox_var, command=RDS_Enable_datetimepicker_checkbox_callback)
RDS_Enable_datetimepicker_checkbox.place(x=750, y=120, height=25)
# ToolTip(RDS_Enable_datetimepicker_checkbox,
#         msg="Check to enable a scheduled deployment of the new image", delay=0.1)

# Create other Widgets
RDS_Status_Textblock = tk.Text(
    tab2, borderwidth=1, relief="solid", wrap="word", state="normal")
RDS_Status_Textblock.place(x=30, y=80, height=300, width=510)
RDS_Status_Textblock.insert(tk.END, "No Info yet")

RDS_cal = DateEntry(tab2, bg="darkblue", fg="white", year=current_datetime.year,
                    month=current_datetime.month, day=current_datetime.day)
RDS_cal.config(state="disabled")
RDS_cal.place(x=770, y=165)

RDS_hour_spin = ttk.Spinbox(
    tab2, from_=0, to=23, width=2, value=current_datetime.hour, state="disabled")
RDS_hour_spin.place(x=775, y=210)

RDS_minute_spin = ttk.Spinbox(
    tab2, from_=0, to=59, width=2, value=current_datetime.minute, state="disabled")
RDS_minute_spin.place(x=825, y=210)

RDS_machinecount_textbox = ttk.Entry(
    tab2, validate="key", validatecommand=(validate_int, "%P"), state="readonly")
RDS_machinecount_textbox.place(x=770, y=320, height=25, width=30)
# ToolTip(RDS_machinecount_textbox,
#         msg="ENter number or percentage of machines to apply the secondary image to", delay=0.1)

# endregion


# region Tab 3 - Configuration
tab3 = ttk.Frame(tab_control)
tab_control.add(tab3, text="Configuration")
# tab3.configure(style='Custom.TFrame')

# Place your Tab 3 widgets here
# Create Buttons

config_get_password_button = ttk.Button(
    tab3, text="Get Password", command=show_password_dialog)
config_get_password_button.place(x=30, y=150)

config_save_button = ttk.Button(
    tab3, text="Save Configuration", command=config_save_button_callback)
config_save_button.place(x=30, y=226)

config_reset_button = ttk.Button(
    tab3, text="Reset Configuration", command=config_reset_button_callback)
config_reset_button.place(x=30, y=198)

config_test_credential_button = ttk.Button(
    tab3, text="Test Credentials", command=config_test_button_callback)
config_test_credential_button.place(x=30, y=255)

config_username_textbox = ttk.Entry(tab3)
config_username_textbox_default_text = "UserName"
if config_username is not None:
    config_username_textbox.insert(tk.END, config_username)
    config_username_textbox.config(foreground='black')
else:
    config_username_textbox.insert(
        tk.END, config_username_textbox_default_text)
    config_username_textbox.config(foreground='grey')
config_username_textbox.bind(
    "<FocusIn>", lambda event, var=config_username_textbox_default_text: textbox_handle_focus_in(event, var))
config_username_textbox.bind("<FocusOut>", lambda event,
                             var=config_username_textbox_default_text: textbox_handle_focus_out(event, var))
config_username_textbox.place(x=30, y=100, width=150)

config_domain_textbox = ttk.Entry(tab3)
config_domain_textbox_default_text = "Domain"
if config_domain is not None:
    config_domain_textbox.insert(tk.END, config_domain)
    config_domain_textbox.config(foreground='black')
else:
    config_domain_textbox.insert(tk.END, config_domain_textbox_default_text)
    config_domain_textbox.config(foreground='grey')
config_domain_textbox.bind("<FocusIn>", lambda event,
                           var=config_domain_textbox_default_text: textbox_handle_focus_in(event, var))
config_domain_textbox.bind("<FocusOut>", lambda event,
                           var=config_domain_textbox_default_text: textbox_handle_focus_out(event, var))
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
if len(config_pods) >= 1:
    config_pod_combobox['values'] = config_pods
    config_pod_combobox.current(0)
else:
    config_pod_combobox.set(config_pod_combobox_default_text)
    config_pod_combobox.state(["disabled"])

config_conserver_combobox = ttk.Combobox(tab3)
config_conserver_combobox.place(x=30, y=50, width=200)
config_conserver_combobox_default_text = "Enter Connectionserver DNS"
if len(config_pods) >= 1:
    config_pod_combobox_callback()
else:
    config_conserver_combobox.set(config_conserver_combobox_default_text)
config_conserver_combobox.bind(
    "<FocusIn>", lambda event, var=config_conserver_combobox_default_text: textbox_handle_focus_in(event, var))
config_conserver_combobox.bind(
    "<FocusOut>", lambda event, var=config_conserver_combobox_default_text: textbox_handle_focus_out(event, var))

# Create CheckBox
config_save_password_checkbox_var = tk.BooleanVar()
config_save_password_checkbox = ttk.Checkbutton(
    tab3, text="Save Password", variable=config_save_password_checkbox_var, command=config_save_password_checkbox_callback)
config_save_password_checkbox.place(x=30, y=175)
config_save_password_checkbox_var.set(config_save_password)

# endregion

# Handling of tooltips
# tooltip_label = ttk.Label(root, background="yellow", relief="solid", padding=(5, 2), justify="left")
# tooltip_label.place_forget()

tab_control.select(tab1)

# Start the GUI event loop
root.mainloop()
