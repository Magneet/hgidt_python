from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget,
    QPushButton, QLabel, QComboBox, QLineEdit, QCheckBox,
    QSpinBox, QPlainTextEdit, QDateTimeEdit, QInputDialog
)
from PySide6.QtCore import Qt, QDateTime, QThread, Signal
from PySide6.QtGui import QIcon, QIntValidator
from datetime import datetime
import ast
import configparser
import os
import horizon_functions
import horizon_app
import keyring
import requests
import time
import sys
import math
from loguru import logger


application_name = "hgidt"
requests.packages.urllib3.disable_warnings()
# region arguments and logging

_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"]
_log_handler_id = logger.add('hgidt.log', retention="10 days", rotation="50 MB",
                             format="{time:YYYY-MM-DD at HH:mm:ss} {level} {message}",
                             level="INFO", enqueue=True, backtrace=True, diagnose=True, catch=True)


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
    config_log_level = config.get('UserInfo', 'Log_Level', fallback='INFO')
    config_refresh_vms_snapshots = config.getboolean('UserInfo', 'Refresh_VMs_Snapshots', fallback=False)
    config_local_pod_only = config.getboolean('UserInfo', 'Local_Pod_Only', fallback=False)
    try:
        config_password = keyring.get_password(
            application_name, config_username)
        logger.info("Password retrieved from credentials store")
    except keyring.errors.PasswordDeleteError:
        logger.error("Password not found or could not be retrieved")
else:
    config_username = None
    config_domain = None
    config_server_name = None
    config_save_password = False
    config_log_level = 'INFO'
    config_refresh_vms_snapshots = False
    config_local_pod_only = False

if config_log_level != 'INFO':
    logger.remove(_log_handler_id)
    _log_handler_id = logger.add('hgidt.log', retention="10 days", rotation="50 MB",
                                 format="{time:YYYY-MM-DD at HH:mm:ss} {level} {message}",
                                 level=config_log_level, enqueue=True, backtrace=True,
                                 diagnose=True, catch=True)
if 'Pods' in config:
    config_pods_data = config.get('Pods', 'Pods')
    config_pods = ast.literal_eval(config_pods_data)
else:
    config_pods = []
if 'Connection_Servers' in config:
    config_connection_servers_data = config.get(
        'Connection_Servers', 'Connection_Servers')
    config_connection_servers = ast.literal_eval(config_connection_servers_data)
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
_config_test_worker = None
_connect_worker = None
_vdi_action_worker = None
_rds_action_worker = None

global_desktop_pools = []
global_rds_farms = []
global_base_vms = []
global_base_snapshots = []
global_datacenters = []
global_vcenters = []
global_vdi_selected_pool = {}
global_vdi_selected_vm = {}
global_VDI_selected_snapshot = {}
global_RDS_selected_farm = {}
global_RDS_selected_vm = {}
global_RDS_selected_snapshot = {}
VDI_DesktopPool_Combobox_values = {}
VDI_Golden_Image_Combobox_values = {}
VDI_Snapshot_Combobox_values = {}
RDS_Farm_Combobox_values = {}
RDS_Golden_Image_Combobox_values = {}
RDS_Snapshot_Combobox_values = {}

# Reasons that only matter for RDS farms — not blocking for VDI pools
_VDI_IGNORED_REASONS = {"UNSUPPORTED_OS_FOR_FARM"}
# Reasons that only matter for VDI pools — not blocking for RDS farms
_RDS_IGNORED_REASONS = {"UNSUPPORTED_OS"}


def _vm_has_blocking_reason(vm, ignored_reasons):
    """Return True if the VM has any incompatible reason that is not in ignored_reasons."""
    reasons = vm.get("incompatible_reasons")
    if not reasons:
        return False
    return any(str(r) not in ignored_reasons for r in reasons)

_LOGOFF_POLICIES = ["FORCE_LOGOFF", "WAIT_FOR_LOGOFF"]
_SECONDARY_OPTIONS = ["Select", "Machine Count", "Percentage of Machines"]
VDI_Secondary_Machine_Options_Combobox_default_value = "Select"
VDI_secondary_image_machine_count_label_default = "Count / %"
RDS_Secondary_Machine_Options_Combobox_default_value = "Select"
RDS_secondary_image_machine_count_label_default = "Count / %"
# endregion

# region Configuration related functions


def build_pod_info(hvconnectionobj):
    pods, servers = horizon_app.build_pod_info(hvconnectionobj, config_server_name, local_pod_only=config_local_pod_only)
    config_pods.clear()
    config_pods.extend(pods)
    config_connection_servers.clear()
    config_connection_servers.extend(servers)


def show_password_dialog():
    password, ok = QInputDialog.getText(
        window, "Password", "Enter your password:", QLineEdit.Password)
    if ok and password:
        global config_password
        config_password = password
        config_status_label.setText("Password set")

# endregion

# region functions for button handling of VDI tab


def VDI_secondaryimage_checkbox_callback():
    if VDI_secondaryimage_checkbox.isChecked():
        VDI_Secondary_Machine_Options_Combobox.setEnabled(True)
        VDI_Secondary_Machine_Options_Combobox_callback(None)
        VDI_secondary_image_machine_count_label.setEnabled(True)
    else:
        VDI_secondary_image_machine_count_label.setText(VDI_secondary_image_machine_count_label_default)
        VDI_Secondary_Machine_Options_Combobox.setEnabled(False)
        VDI_machinecount_textbox.setEnabled(False)
        VDI_secondary_image_machine_count_label.setEnabled(False)


def VDI_Secondary_Machine_Options_Combobox_callback(event):
    if VDI_Secondary_Machine_Options_Combobox.currentText() != VDI_Secondary_Machine_Options_Combobox_default_value:
        VDI_machinecount_textbox.setEnabled(True)
        if "Percentage" in VDI_Secondary_Machine_Options_Combobox.currentText():
            VDI_secondary_image_machine_count_label.setText("Percentage")
        else:
            VDI_secondary_image_machine_count_label.setText("Machine Count")
    else:
        VDI_secondary_image_machine_count_label.setText(VDI_secondary_image_machine_count_label_default)
        VDI_machinecount_textbox.setEnabled(False)
        VDI_secondary_image_machine_count_label.setEnabled(False)


def VDI_Apply_Secondary_Image_button_callback():
    global global_vdi_selected_pool, _vdi_action_worker
    secondary_option = VDI_Secondary_Machine_Options_Combobox.currentText()
    if secondary_option == VDI_Secondary_Machine_Options_Combobox_default_value:
        VDI_Statusbox_Label.setText("Select a number of machines first.")
        return
    logger.info(f"Applying secondary image to VDI pool '{global_vdi_selected_pool.get('name')}' using method: {secondary_option}")
    pod = global_vdi_selected_pool["pod"]
    pool_id = global_vdi_selected_pool['id']
    machine_count = int(VDI_machinecount_textbox.text())
    is_percentage = "Percentage" in secondary_option
    pending_snap_id = global_vdi_selected_pool["provisioning_status_data"]["instant_clone_pending_image_snapshot_id"]
    base_snap_id = global_vdi_selected_pool["provisioning_settings"]["base_snapshot_id"]
    _vdi_disable_all_controls()

    def action():
        hvconn = connect_pod(pod=pod)
        inv = horizon_functions.Inventory(url=hvconn.url, access_token=hvconn.access_token)
        machines = sorted(inv.get_machines(filter={"type": "Equals", "name": "desktop_pool_id", "value": pool_id}),
                          key=lambda x: x["name"])
        count = math.ceil((machine_count / 100) * len(machines)) if is_percentage else machine_count
        selected = machines[:count]
        unselected = machines[count:]
        if is_percentage:
            sel_ids = [m["id"] for m in selected if m["managed_machine_data"]["base_vm_snapshot_id"] == pending_snap_id]
        else:
            sel_ids = [m["id"] for m in selected if m["managed_machine_data"]["base_vm_snapshot_id"] != pending_snap_id]
        unsel_ids = [m["id"] for m in unselected if m["managed_machine_data"]["base_vm_snapshot_id"] != base_snap_id]
        if sel_ids:
            inv.apply_pending_desktop_pool_image(desktop_pool_id=pool_id, machine_ids=sel_ids, pending_image=True)
        if unsel_ids:
            inv.apply_pending_desktop_pool_image(desktop_pool_id=pool_id, machine_ids=unsel_ids, pending_image=False)
        hvconn.hv_disconnect()

    _vdi_action_worker = ApiActionWorker(action)
    _vdi_action_worker.status_updated.connect(VDI_Statusbox_Label.setText)
    _vdi_action_worker.start()


def VDI_Cancel_Secondary_Image_button_callback():
    global global_vdi_selected_pool, _vdi_action_worker
    logger.info(f"Cancelling image push for VDI pool '{global_vdi_selected_pool.get('name')}'")
    pod, pool_id = global_vdi_selected_pool["pod"], global_vdi_selected_pool["id"]
    _vdi_disable_all_controls()

    def action():
        hvconn = connect_pod(pod=pod)
        horizon_functions.Inventory(url=hvconn.url, access_token=hvconn.access_token).cancel_desktop_pool_push_image(desktop_pool_id=pool_id)
        hvconn.hv_disconnect()

    _vdi_action_worker = ApiActionWorker(action)
    _vdi_action_worker.status_updated.connect(VDI_Statusbox_Label.setText)
    _vdi_action_worker.start()


def VDI_Promote_Secondary_Image_button_callback():
    global global_vdi_selected_pool, _vdi_action_worker
    logger.info(f"Promoting secondary image for VDI pool '{global_vdi_selected_pool.get('name')}'")
    pod, pool_id = global_vdi_selected_pool["pod"], global_vdi_selected_pool["id"]
    _vdi_disable_all_controls()

    def action():
        hvconn = connect_pod(pod=pod)
        horizon_functions.Inventory(url=hvconn.url, access_token=hvconn.access_token).promote_pending_desktop_pool_image(desktop_pool_id=pool_id)
        hvconn.hv_disconnect()

    _vdi_action_worker = ApiActionWorker(action)
    _vdi_action_worker.status_updated.connect(VDI_Statusbox_Label.setText)
    _vdi_action_worker.start()


def VDI_Apply_Golden_Image_button_callback():
    global global_vdi_selected_pool, global_vdi_selected_vm, _vdi_action_worker, VDI_cal
    logger.info(f"Deploying golden image to VDI pool '{global_vdi_selected_pool.get('name')}': "
                f"VM='{global_vdi_selected_vm.get('name')}' snapshot='{global_VDI_selected_snapshot.get('name')}' "
                f"vTPM={VDI_vtpm_checkbox.isChecked()} logoff={VDI_LofOffPolicy_Combobox.currentText()}")
    if VDI_Enable_datetimepicker_checkbox.isChecked():
        datetime_var = get_selected_datetime(VDI_cal)
        start_time = datetime.timestamp(datetime_var) * 1000
        logger.info(f"VDI deployment scheduled for {datetime_var}")
    else:
        start_time = time.time()

    pod = global_vdi_selected_vm["pod"]
    pool_id = global_vdi_selected_pool['id']
    parent_vm_id = global_vdi_selected_vm['id']
    snapshot_id = global_VDI_selected_snapshot['id']
    add_vtpm = VDI_vtpm_checkbox.isChecked()
    logoff_policy = VDI_LofOffPolicy_Combobox.currentText()
    selective = VDI_secondaryimage_checkbox.isChecked()
    resize = VDI_Resize_checkbox.isChecked()
    cores_per_socket = VDI_CoresPerSocket_ComboBox.currentText() if resize else None
    cpu_count = VDI_CPUCount_ComboBox.currentText() if resize else None
    ram_mb = VDI_Memory_ComboBox.currentText() if resize else None
    secondary_option = VDI_Secondary_Machine_Options_Combobox.currentText()
    machine_count = int(VDI_machinecount_textbox.text()) if secondary_option != VDI_Secondary_Machine_Options_Combobox_default_value else None
    is_percentage = "percent" in secondary_option.lower()
    _vdi_disable_all_controls()

    def action():
        hvconn = connect_pod(pod=pod)
        inv = horizon_functions.Inventory(url=hvconn.url, access_token=hvconn.access_token)
        machine_ids = None
        if machine_count is not None:
            machines = sorted(inv.get_machines(filter={"type": "Equals", "name": "desktop_pool_id", "value": pool_id}),
                              key=lambda x: x["name"])
            count = math.ceil((machine_count / 100) * len(machines)) if is_percentage else machine_count
            machine_ids = [d["id"] for d in machines[:count]]
        inv.desktop_pool_push_image(
            desktop_pool_id=pool_id, parent_vm_id=parent_vm_id, snapshot_id=snapshot_id,
            machine_ids=machine_ids,
            compute_profile_ram_mb=int(ram_mb) if ram_mb else None,
            compute_profile_num_cpus=int(cpu_count) if cpu_count else None,
            compute_profile_num_cores_per_socket=int(cores_per_socket) if cores_per_socket else None,
            add_virtual_tpm=add_vtpm, logoff_policy=logoff_policy,
            start_time=start_time, selective_push_image=selective)
        hvconn.hv_disconnect()

    _vdi_action_worker = ApiActionWorker(action)
    _vdi_action_worker.status_updated.connect(VDI_Statusbox_Label.setText)
    _vdi_action_worker.start()


def VDI_DesktopPool_Combobox_callback(event):
    global global_desktop_pools, global_base_vms, VDI_Golden_Image_Combobox__selected_default, VDI_Golden_Image_Combobox_values, global_vdi_selected_pool, global_base_snapshots
    for w in (VDI_Secondary_Machine_Options_Combobox, VDI_machinecount_textbox,
              VDI_Apply_Golden_Image_button, VDI_Apply_Secondary_Image_button,
              VDI_Cancel_Secondary_Image_button, VDI_Enable_datetimepicker_checkbox,
              VDI_Promote_Secondary_Image_button, VDI_CPUCount_ComboBox, VDI_cal,
              VDI_Golden_Image_Combobox, VDI_Snapshot_Combobox, VDI_vtpm_checkbox,
              VDI_LofOffPolicy_Combobox, VDI_Resize_checkbox,
              VDI_CoresPerSocket_ComboBox, VDI_Memory_ComboBox):
        w.setEnabled(False)
    try:
        VDI_Golden_Image_Combobox_values.clear()
    except:
        VDI_Golden_Image_Combobox_values = []
    global_vdi_selected_pool = VDI_DesktopPool_Combobox_values[VDI_DesktopPool_Combobox.currentText()]
    pool_name = global_vdi_selected_pool["name"]
    pool_displayname = global_vdi_selected_pool["display_name"]
    if global_vdi_selected_pool["enabled"]:
        state = "Enabled"
    else:
        state = "Disabled"
    if global_vdi_selected_pool["enable_provisioning"]:
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
    try:
        deployment_time = datetime.fromtimestamp(
            global_vdi_selected_pool["provisioning_status_data"]["instant_clone_push_image_settings"]["start_time"] / 1000)
    except:
        deployment_time = "N/A"
    _vm_match = [item for item in global_base_vms if item["id"] == prinary_basevm_id]
    primary_basevm_name = _vm_match[0]["name"] if _vm_match else f"Unknown ({prinary_basevm_id})"
    _snap_match = [item for item in global_base_snapshots if item["id"] == primary_snapshot_id]
    primary_basesnapshot_name = _snap_match[0]["name"] if _snap_match else f"Unknown ({primary_snapshot_id})"
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
    current_image_state = global_vdi_selected_pool[
        "provisioning_status_data"]["instant_clone_current_image_state"]
    instant_clone_operation = global_vdi_selected_pool[
        "provisioning_status_data"]["instant_clone_operation"]
    try:
        instant_clone_pending_image_state = global_vdi_selected_pool[
            "provisioning_status_data"]["instant_clone_pending_image_state"]
    except:
        instant_clone_pending_image_state = "N/A"
    vdi_textblock_text = (
        f"Desktop Pool Status:\nName: {pool_name}\nDisplay Name: {pool_displayname}\n"
        f"Desktop Pool State = {state}\nProvisioning State = {provisioning_state}\n"
        f"Current Image State = {current_image_state}\nInstant Clone Operation = {instant_clone_operation}\n"
        f"Image Deployment time = {deployment_time}\nBase VM = {primary_basevm_name}\n"
        f"Base Snapshot = {primary_basesnapshot_name}\nSecondary or Pending VM = {secondary_basevm_name}\n"
        f"Secondary or Pending Snapshot = {secondary_basesnapshot_name}\n"
        f"Pending Image State = {instant_clone_pending_image_state}\n"
        f"Pending Image Progress = {provisioning_progress}"
    )
    VDI_Status_Textblock.setPlainText(vdi_textblock_text)
    _update_vdi_provisioning_controls()
    if (instant_clone_operation == "NONE" and instant_clone_pending_image_state == "N/A") or \
            (instant_clone_operation == "NONE" and instant_clone_pending_image_state == "FAILED"):
        for vm in global_base_vms:
            if vm["vcenter_id"] != vcenter_id:
                continue
            snaps = vm.get("snapshotcount", 0)
            if _vm_has_blocking_reason(vm, _VDI_IGNORED_REASONS):
                logger.debug(f"VDI excluded VM '{vm['name']}': incompatible_reasons={vm.get('incompatible_reasons')}")
            elif snaps < 1:
                logger.debug(f"VDI excluded VM '{vm['name']}': snapshotcount={snaps}")
        optional_golden_images = [
            item for item in global_base_vms
            if item["vcenter_id"] == vcenter_id
            and not _vm_has_blocking_reason(item, _VDI_IGNORED_REASONS)
            and item.get("snapshotcount", 0) >= 1
        ]
        if not optional_golden_images:
            vcenter_vms = [v for v in global_base_vms if v["vcenter_id"] == vcenter_id]
            blocked = [v["name"] for v in vcenter_vms if _vm_has_blocking_reason(v, _VDI_IGNORED_REASONS)]
            no_snaps = [v["name"] for v in vcenter_vms if not _vm_has_blocking_reason(v, _VDI_IGNORED_REASONS) and v.get("snapshotcount", 0) < 1]
            logger.info(f"VDI pool '{pool_name}' (vcenter {vcenter_id}): {len(vcenter_vms)} VM(s) found, none eligible. Blocked by reasons: {blocked}. No snapshots: {no_snaps}.")
            return
        logger.debug(f"VDI golden images available for vcenter {vcenter_id}: {[item['name'] for item in optional_golden_images]}")
        VDI_Golden_Image_Combobox_values = {item["name"]: item for item in optional_golden_images}
        _current_vm = next((vm for vm in optional_golden_images if vm['id'] == prinary_basevm_id), None)
        VDI_Golden_Image_Combobox__selected_default = _current_vm['name'] if _current_vm else optional_golden_images[0]['name']
        _vdi_vm_values = list(VDI_Golden_Image_Combobox_values.keys())
        VDI_Golden_Image_Combobox._all_values = _vdi_vm_values
        VDI_Golden_Image_Combobox.blockSignals(True)
        VDI_Golden_Image_Combobox.clear()
        VDI_Golden_Image_Combobox.addItems(_vdi_vm_values)
        VDI_Golden_Image_Combobox.blockSignals(False)
        VDI_Golden_Image_Combobox.setCurrentText(VDI_Golden_Image_Combobox__selected_default)
        VDI_Cancel_Secondary_Image_button.setEnabled(False)
        VDI_Promote_Secondary_Image_button.setEnabled(False)
        VDI_Apply_Golden_Image_button.setEnabled(False)
        VDI_Golden_Image_Combobox.setEnabled(True)
        VDI_secondaryimage_checkbox_callback()
        VDI_Enable_datetimepicker_checkbox_callback()
        VDI_Resize_checkbox_callback()
        VDI_Golden_Image_Combobox_callback(None)
    elif instant_clone_operation == "NONE" and instant_clone_pending_image_state == "READY_HELD":
        VDI_Cancel_Secondary_Image_button.setEnabled(True)
        VDI_Promote_Secondary_Image_button.setEnabled(True)
        VDI_Apply_Golden_Image_button.setEnabled(False)
        VDI_Apply_Secondary_Image_button.setEnabled(True)
        VDI_Secondary_Machine_Options_Combobox.setEnabled(True)
    elif instant_clone_operation == "SCHEDULE_PUSH_IMAGE" and instant_clone_pending_image_state != "UNPUBLISHING":
        VDI_Cancel_Secondary_Image_button.setEnabled(True)


def VDI_Golden_Image_Combobox_callback(event):
    global global_desktop_pools, global_base_vms, VDI_Snapshot_Combobox__selected_default, global_base_snapshots, VDI_Snapshot_Combobox_values, global_vdi_selected_vm
    try:
        VDI_Snapshot_Combobox_values.clear()
    except:
        VDI_Snapshot_Combobox_values = []
    global_vdi_selected_vm = VDI_Golden_Image_Combobox_values[VDI_Golden_Image_Combobox.currentText()]
    vcenter_id = global_vdi_selected_vm['vcenter_id']
    basevm_id = global_vdi_selected_vm['id']
    optional_snapshots = [item for item in global_base_snapshots if item["vcenter_id"]
                          == vcenter_id and item["basevmid"] == basevm_id
                          and not item.get("incompatible_reasons")]
    VDI_Snapshot_Combobox_values = {item["name"]: item for item in optional_snapshots}
    _pool_vm_id = global_vdi_selected_pool.get("provisioning_settings", {}).get("parent_vm_id")
    _pool_snap_id = global_vdi_selected_pool.get("provisioning_settings", {}).get("base_snapshot_id")
    if global_vdi_selected_vm['id'] == _pool_vm_id and _pool_snap_id:
        _current_snap = next((s for s in optional_snapshots if s['id'] == _pool_snap_id), None)
        VDI_Snapshot_Combobox__selected_default = _current_snap['name'] if _current_snap else optional_snapshots[0]['name']
    else:
        VDI_Snapshot_Combobox__selected_default = optional_snapshots[0]['name']
    _vdi_snap_values = list(VDI_Snapshot_Combobox_values.keys())
    VDI_Snapshot_Combobox._all_values = _vdi_snap_values
    VDI_Snapshot_Combobox.blockSignals(True)
    VDI_Snapshot_Combobox.clear()
    VDI_Snapshot_Combobox.addItems(_vdi_snap_values)
    VDI_Snapshot_Combobox.blockSignals(False)
    VDI_Snapshot_Combobox.setEnabled(True)
    VDI_Snapshot_Combobox.setCurrentText(VDI_Snapshot_Combobox__selected_default)
    VDI_Snapshot_Combobox_callback(None)


def VDI_Snapshot_Combobox_callback(event):
    global global_VDI_selected_snapshot, global_vdi_selected_pool
    global_VDI_selected_snapshot = VDI_Snapshot_Combobox_values[VDI_Snapshot_Combobox.currentText()]
    VDI_LofOffPolicy_Combobox.setEnabled(True)
    VDI_Resize_checkbox.setEnabled(True)
    VDI_Enable_datetimepicker_checkbox.setEnabled(True)
    VDI_secondaryimage_checkbox.setEnabled(True)
    VDI_vtpm_checkbox.setEnabled(True)
    VDI_StopOnError_checkbox.setEnabled(True)
    VDI_Apply_Golden_Image_button.setEnabled(True)
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
        VDI_Resize_checkbox.setChecked(True)
        VDI_CoresPerSocket_ComboBox.setCurrentText(str(VDI_corespersocket))
        VDI_CPUCount_ComboBox.setCurrentText(str(VDI_cpucount))
        VDI_Memory_ComboBox.setCurrentText(str(VDI_memsize))
        VDI_Resize_checkbox_callback()


def VDI_Resize_checkbox_callback():
    enabled = VDI_Resize_checkbox.isChecked()
    VDI_CoresPerSocket_ComboBox.setEnabled(enabled)
    VDI_CPUCount_ComboBox.setEnabled(enabled)
    VDI_Memory_ComboBox.setEnabled(enabled)


def VDI_Enable_datetimepicker_checkbox_callback():
    VDI_cal.setEnabled(VDI_Enable_datetimepicker_checkbox.isChecked())


def _update_vdi_provisioning_controls():
    enabled = global_vdi_selected_pool.get('enable_provisioning', True)
    VDI_Provisioning_Status_Label.setText(f"Provisioning: {'Enabled' if enabled else 'Disabled'}")
    VDI_Toggle_Provisioning_button.setText('Disable Provisioning' if enabled else 'Enable Provisioning')
    VDI_Toggle_Provisioning_button.setEnabled(True)


def VDI_Toggle_Provisioning_button_callback():
    global global_vdi_selected_pool, _vdi_action_worker
    enable = not global_vdi_selected_pool.get('enable_provisioning', True)
    logger.info(f"{'Enabling' if enable else 'Disabling'} provisioning for VDI pool '{global_vdi_selected_pool.get('name')}'")
    pod = global_vdi_selected_pool['pod']
    pool_data = global_vdi_selected_pool.copy()
    VDI_Toggle_Provisioning_button.setEnabled(False)

    def action():
        hvconn = connect_pod(pod=pod)
        horizon_functions.Inventory(url=hvconn.url, access_token=hvconn.access_token).set_desktop_pool_provisioning(pool_data, enable)
        hvconn.hv_disconnect()

    def on_finished():
        global_vdi_selected_pool['enable_provisioning'] = enable
        _update_vdi_provisioning_controls()

    _vdi_action_worker = ApiActionWorker(action)
    _vdi_action_worker.status_updated.connect(VDI_Statusbox_Label.setText)
    _vdi_action_worker.action_finished.connect(on_finished)
    _vdi_action_worker.start()
# endregion


# region functions for button handling of RDS tab
def RDS_secondaryimage_checkbox_callback():
    if RDS_secondaryimage_checkbox.isChecked():
        RDS_Secondary_Machine_Options_Combobox.setEnabled(True)
        RDS_Secondary_Machine_Options_Combobox_callback(None)
        RDS_secondary_image_machine_count_label.setEnabled(True)
    else:
        RDS_secondary_image_machine_count_label.setText(RDS_secondary_image_machine_count_label_default)
        RDS_Secondary_Machine_Options_Combobox.setEnabled(False)
        RDS_machinecount_textbox.setEnabled(False)
        RDS_secondary_image_machine_count_label.setEnabled(False)


def RDS_Secondary_Machine_Options_Combobox_callback(event):
    if RDS_Secondary_Machine_Options_Combobox.currentText() != RDS_Secondary_Machine_Options_Combobox_default_value:
        RDS_machinecount_textbox.setEnabled(True)
        if "Percentage" in RDS_Secondary_Machine_Options_Combobox.currentText():
            RDS_secondary_image_machine_count_label.setText("Percentage")
        else:
            RDS_secondary_image_machine_count_label.setText("Machine Count")
    else:
        RDS_secondary_image_machine_count_label.setText(RDS_secondary_image_machine_count_label_default)
        RDS_machinecount_textbox.setEnabled(False)
        RDS_secondary_image_machine_count_label.setEnabled(False)


def RDS_Apply_Secondary_Image_button_callback():
    global global_RDS_selected_farm, _rds_action_worker
    secondary_option = RDS_Secondary_Machine_Options_Combobox.currentText()
    if secondary_option == RDS_Secondary_Machine_Options_Combobox_default_value:
        RDS_Statusbox_Label.setText("Select a number of machines first.")
        return
    logger.info(f"Applying secondary image to RDS farm '{global_RDS_selected_farm.get('name')}' using method: {secondary_option}")
    pod = global_RDS_selected_farm["pod"]
    farm_id = global_RDS_selected_farm['id']
    machine_count = int(RDS_machinecount_textbox.text())
    is_percentage = "percent" in secondary_option.lower()
    pending_snap_id = global_RDS_selected_farm["automated_farm_settings"]["provisioning_status_data"]["instant_clone_pending_image_snapshot_id"]
    base_snap_id = global_RDS_selected_farm["automated_farm_settings"]["provisioning_settings"]["base_snapshot_id"]
    _rds_disable_all_controls()

    def action():
        hvconn = connect_pod(pod=pod)
        inv = horizon_functions.Inventory(url=hvconn.url, access_token=hvconn.access_token)
        machines = sorted(inv.get_rds_servers(filter={"type": "Equals", "name": "farm_id", "value": farm_id}),
                          key=lambda x: x["name"])
        count = math.ceil((machine_count / 100) * len(machines)) if is_percentage else machine_count
        selected = machines[:count]
        unselected = machines[count:]
        if is_percentage:
            sel_ids = [m["id"] for m in selected if m["base_vm_snapshot_id"] == pending_snap_id]
        else:
            sel_ids = [m["id"] for m in selected if m["base_vm_snapshot_id"] != pending_snap_id]
        unsel_ids = [m["id"] for m in unselected if m["base_vm_snapshot_id"] != base_snap_id]
        if sel_ids:
            inv.apply_pending_rds_farm_image(farm_id=farm_id, machine_ids=sel_ids, pending_image=True)
        if unsel_ids:
            inv.apply_pending_rds_farm_image(farm_id=farm_id, machine_ids=unsel_ids, pending_image=False)
        hvconn.hv_disconnect()

    _rds_action_worker = ApiActionWorker(action)
    _rds_action_worker.status_updated.connect(RDS_Statusbox_Label.setText)
    _rds_action_worker.start()


def RDS_Cancel_Secondary_Image_button_callback():
    global global_RDS_selected_farm, _rds_action_worker
    logger.info(f"Cancelling image push for RDS farm '{global_RDS_selected_farm.get('name')}'")
    pod, farm_id = global_RDS_selected_farm["pod"], global_RDS_selected_farm["id"]
    _rds_disable_all_controls()

    def action():
        hvconn = connect_pod(pod=pod)
        horizon_functions.Inventory(url=hvconn.url, access_token=hvconn.access_token).cancel_rds_farm_push_image(farm_id=farm_id)
        hvconn.hv_disconnect()

    _rds_action_worker = ApiActionWorker(action)
    _rds_action_worker.status_updated.connect(RDS_Statusbox_Label.setText)
    _rds_action_worker.start()


def RDS_Promote_Secondary_Image_button_callback():
    global global_RDS_selected_farm, _rds_action_worker
    logger.info(f"Promoting secondary image for RDS farm '{global_RDS_selected_farm.get('name')}'")
    pod, farm_id = global_RDS_selected_farm["pod"], global_RDS_selected_farm["id"]
    _rds_disable_all_controls()

    def action():
        hvconn = connect_pod(pod=pod)
        horizon_functions.Inventory(url=hvconn.url, access_token=hvconn.access_token).promote_pending_rds_farm_image(farm_id=farm_id)
        hvconn.hv_disconnect()

    _rds_action_worker = ApiActionWorker(action)
    _rds_action_worker.status_updated.connect(RDS_Statusbox_Label.setText)
    _rds_action_worker.start()


def RDS_Apply_Golden_Image_button_callback():
    global global_RDS_selected_farm, global_RDS_selected_vm, _rds_action_worker, RDS_cal
    logger.info(f"Deploying golden image to RDS farm '{global_RDS_selected_farm.get('name')}': "
                f"VM='{global_RDS_selected_vm.get('name')}' snapshot='{global_RDS_selected_snapshot.get('name')}' "
                f"logoff={RDS_LofOffPolicy_Combobox.currentText()}")
    if RDS_Enable_datetimepicker_checkbox.isChecked():
        datetime_var = get_selected_datetime(RDS_cal)
        next_scheduled_time = datetime.timestamp(datetime_var) * 1000
        logger.info(f"RDS deployment scheduled for {datetime_var}")
    else:
        next_scheduled_time = time.time()

    pod = global_RDS_selected_vm["pod"]
    farm_id = global_RDS_selected_farm['id']
    parent_vm_id = global_RDS_selected_vm['id']
    snapshot_id = global_RDS_selected_snapshot['id']
    logoff_policy = RDS_LofOffPolicy_Combobox.currentText()
    selective = RDS_secondaryimage_checkbox.isChecked()
    resize = RDS_Resize_checkbox.isChecked()
    cores_per_socket = RDS_CoresPerSocket_ComboBox.currentText() if resize else None
    cpu_count = RDS_CPUCount_ComboBox.currentText() if resize else None
    ram_mb = RDS_Memory_ComboBox.currentText() if resize else None
    secondary_option = RDS_Secondary_Machine_Options_Combobox.currentText()
    machine_count = int(RDS_machinecount_textbox.text()) if secondary_option != RDS_Secondary_Machine_Options_Combobox_default_value else None
    is_percentage = "percent" in secondary_option.lower()
    _rds_disable_all_controls()

    def action():
        hvconn = connect_pod(pod=pod)
        inv = horizon_functions.Inventory(url=hvconn.url, access_token=hvconn.access_token)
        rds_server_ids = None
        if machine_count is not None:
            machines = sorted(inv.get_rds_servers(filter={"type": "Equals", "name": "farm_id", "value": farm_id}),
                              key=lambda x: x["name"])
            count = math.ceil((machine_count / 100) * len(machines)) if is_percentage else machine_count
            rds_server_ids = [d["id"] for d in machines[:count]]
        inv.rds_farm_schedule_maintenance(
            farm_id=farm_id, parent_vm_id=parent_vm_id, maintenance_mode="IMMEDIATE",
            snapshot_id=snapshot_id, rds_server_ids=rds_server_ids,
            compute_profile_ram_mb=int(ram_mb) if ram_mb else None,
            compute_profile_num_cpus=int(cpu_count) if cpu_count else None,
            compute_profile_num_cores_per_socket=int(cores_per_socket) if cores_per_socket else None,
            logoff_policy=logoff_policy, next_scheduled_time=next_scheduled_time,
            selective_schedule_maintenance=selective)
        hvconn.hv_disconnect()

    _rds_action_worker = ApiActionWorker(action)
    _rds_action_worker.status_updated.connect(RDS_Statusbox_Label.setText)
    _rds_action_worker.start()


def RDS_Farm_Combobox_callback(event):
    global global_rds_farms, global_base_vms, RDS_Golden_Image_Combobox__selected_default, RDS_Golden_Image_Combobox_values, global_RDS_selected_farm, global_base_snapshots
    for w in (RDS_Secondary_Machine_Options_Combobox, RDS_machinecount_textbox,
              RDS_Apply_Golden_Image_button, RDS_Apply_Secondary_Image_button,
              RDS_Cancel_Secondary_Image_button, RDS_Enable_datetimepicker_checkbox,
              RDS_CPUCount_ComboBox, RDS_cal, RDS_Golden_Image_Combobox,
              RDS_Snapshot_Combobox, RDS_LofOffPolicy_Combobox, RDS_Resize_checkbox,
              RDS_CoresPerSocket_ComboBox, RDS_Memory_ComboBox,
              RDS_Promote_Secondary_Image_button):
        w.setEnabled(False)
    try:
        RDS_Golden_Image_Combobox_values.clear()
    except:
        RDS_Golden_Image_Combobox_values = []
    global_RDS_selected_farm = RDS_Farm_Combobox_values[RDS_Farm_Combobox.currentText()]
    pool_name = global_RDS_selected_farm["name"]
    pool_displayname = global_RDS_selected_farm["display_name"]
    if global_RDS_selected_farm["enabled"]:
        state = "Enabled"
    else:
        state = "Disabled"
    af = global_RDS_selected_farm.get("automated_farm_settings", {})
    if af.get("enable_provisioning"):
        provisioning_state = "Enabled"
    else:
        provisioning_state = "Disabled"
    vcenter_id = af.get('vcenter_id', '')
    prinary_basevm_id = af.get("provisioning_settings", {}).get("parent_vm_id", '')
    primary_snapshot_id = af.get("provisioning_settings", {}).get("base_snapshot_id", '')
    psd = af.get("provisioning_status_data", {})
    current_image_state = psd.get("instant_clone_current_image_state", "N/A")
    instant_clone_operation = psd.get("instant_clone_operation", "NONE")
    instant_clone_pending_image_state = psd.get("instant_clone_pending_image_state", "N/A")
    provisioning_progress = psd.get("instant_clone_pending_image_progress", "N/A")
    try:
        deployment_time = datetime.fromtimestamp(
            psd["instant_clone_push_image_settings"]["start_time"] / 1000)
    except Exception:
        deployment_time = "N/A"
    _vm_match = [item for item in global_base_vms if item["id"] == prinary_basevm_id]
    primary_basevm_name = _vm_match[0]["name"] if _vm_match else f"Unknown ({prinary_basevm_id})"
    _snap_match = [item for item in global_base_snapshots if item["id"] == primary_snapshot_id]
    primary_basesnapshot_name = _snap_match[0]["name"] if _snap_match else f"Unknown ({primary_snapshot_id})"
    try:
        secondary_basevm_id = psd["instant_clone_pending_image_parent_vm_id"]
        secondary_basevm_name = [
            item for item in global_base_vms if item["id"] == secondary_basevm_id][0]["name"]
    except Exception:
        secondary_basevm_name = "N/A"
    try:
        secondary_snapshot_id = psd["instant_clone_pending_image_snapshot_id"]
        secondary_basesnapshot_name = [
            item for item in global_base_snapshots if item["id"] == secondary_snapshot_id][0]["name"]
    except Exception:
        secondary_basesnapshot_name = "N/A"
    RDS_textblock_text = (
        f"RDS Farm Status:\nName: {pool_name}\nDisplay Name: {pool_displayname}\n"
        f"Farm State = {state}\nProvisioning State = {provisioning_state}\n"
        f"Current Image State = {current_image_state}\nInstant Clone Operation = {instant_clone_operation}\n"
        f"Image Deployment time = {deployment_time}\nBase VM = {primary_basevm_name}\n"
        f"Base Snapshot = {primary_basesnapshot_name}\nSecondary or Pending VM = {secondary_basevm_name}\n"
        f"Secondary or Pending Snapshot = {secondary_basesnapshot_name}\n"
        f"Pending Image State = {instant_clone_pending_image_state}\n"
        f"Pending Image Progress = {provisioning_progress}"
    )
    RDS_Status_Textblock.setPlainText(RDS_textblock_text)
    _update_rds_provisioning_controls()
    if (instant_clone_operation == "NONE" and instant_clone_pending_image_state == "N/A") or \
            (instant_clone_operation == "NONE" and instant_clone_pending_image_state == "FAILED"):
        for vm in global_base_vms:
            if vm["vcenter_id"] != vcenter_id:
                continue
            snaps = vm.get("snapshotcount", 0)
            if _vm_has_blocking_reason(vm, _RDS_IGNORED_REASONS):
                logger.debug(f"RDS excluded VM '{vm['name']}': incompatible_reasons={vm.get('incompatible_reasons')}")
            elif snaps < 1:
                logger.debug(f"RDS excluded VM '{vm['name']}': snapshotcount={snaps}")
        optional_golden_images = [
            item for item in global_base_vms
            if item["vcenter_id"] == vcenter_id
            and not _vm_has_blocking_reason(item, _RDS_IGNORED_REASONS)
            and item.get("snapshotcount", 0) >= 1
        ]
        if not optional_golden_images:
            vcenter_vms = [v for v in global_base_vms if v["vcenter_id"] == vcenter_id]
            blocked = [v["name"] for v in vcenter_vms if _vm_has_blocking_reason(v, _RDS_IGNORED_REASONS)]
            no_snaps = [v["name"] for v in vcenter_vms if not _vm_has_blocking_reason(v, _RDS_IGNORED_REASONS) and v.get("snapshotcount", 0) < 1]
            logger.info(f"RDS farm '{pool_name}' (vcenter {vcenter_id}): {len(vcenter_vms)} VM(s) found, none eligible. Blocked by reasons: {blocked}. No snapshots: {no_snaps}.")
            return
        logger.debug(f"RDS golden images available for vcenter {vcenter_id}: {[item['name'] for item in optional_golden_images]}")
        RDS_Golden_Image_Combobox_values = {item["name"]: item for item in optional_golden_images}
        _current_vm = next((vm for vm in optional_golden_images if vm['id'] == prinary_basevm_id), None)
        RDS_Golden_Image_Combobox__selected_default = _current_vm['name'] if _current_vm else optional_golden_images[0]['name']
        _rds_vm_values = list(RDS_Golden_Image_Combobox_values.keys())
        RDS_Golden_Image_Combobox._all_values = _rds_vm_values
        RDS_Golden_Image_Combobox.blockSignals(True)
        RDS_Golden_Image_Combobox.clear()
        RDS_Golden_Image_Combobox.addItems(_rds_vm_values)
        RDS_Golden_Image_Combobox.blockSignals(False)
        RDS_Golden_Image_Combobox.setCurrentText(RDS_Golden_Image_Combobox__selected_default)
        RDS_Cancel_Secondary_Image_button.setEnabled(False)
        RDS_Promote_Secondary_Image_button.setEnabled(False)
        RDS_Apply_Golden_Image_button.setEnabled(False)
        RDS_Golden_Image_Combobox.setEnabled(True)
        RDS_secondaryimage_checkbox_callback()
        RDS_Enable_datetimepicker_checkbox_callback()
        RDS_Resize_checkbox_callback()
        RDS_Golden_Image_Combobox_callback(None)
    elif instant_clone_operation == "NONE" and instant_clone_pending_image_state == "READY_HELD":
        RDS_Cancel_Secondary_Image_button.setEnabled(True)
        RDS_Promote_Secondary_Image_button.setEnabled(True)
        RDS_Apply_Golden_Image_button.setEnabled(False)
        RDS_Apply_Secondary_Image_button.setEnabled(True)
        RDS_Secondary_Machine_Options_Combobox.setEnabled(True)
    elif instant_clone_operation == "SCHEDULE_PUSH_IMAGE" and instant_clone_pending_image_state != "UNPUBLISHING":
        RDS_Cancel_Secondary_Image_button.setEnabled(True)


def RDS_Golden_Image_Combobox_callback(event):
    global global_rds_farms, global_base_vms, RDS_Snapshot_Combobox__selected_default, global_base_snapshots, RDS_Snapshot_Combobox_values, global_RDS_selected_vm
    try:
        RDS_Snapshot_Combobox_values.clear()
    except:
        RDS_Snapshot_Combobox_values = []
    global_RDS_selected_vm = RDS_Golden_Image_Combobox_values[RDS_Golden_Image_Combobox.currentText()]
    vcenter_id = global_RDS_selected_vm['vcenter_id']
    basevm_id = global_RDS_selected_vm['id']
    optional_snapshots = [item for item in global_base_snapshots if item["vcenter_id"]
                          == vcenter_id and item["basevmid"] == basevm_id
                          and not item.get("incompatible_reasons")]
    RDS_Snapshot_Combobox_values = {item["name"]: item for item in optional_snapshots}
    _farm_vm_id = global_RDS_selected_farm.get("automated_farm_settings", {}).get("provisioning_settings", {}).get("parent_vm_id")
    _farm_snap_id = global_RDS_selected_farm.get("automated_farm_settings", {}).get("provisioning_settings", {}).get("base_snapshot_id")
    if global_RDS_selected_vm['id'] == _farm_vm_id and _farm_snap_id:
        _current_snap = next((s for s in optional_snapshots if s['id'] == _farm_snap_id), None)
        RDS_Snapshot_Combobox__selected_default = _current_snap['name'] if _current_snap else optional_snapshots[0]['name']
    else:
        RDS_Snapshot_Combobox__selected_default = optional_snapshots[0]['name']
    _rds_snap_values = list(RDS_Snapshot_Combobox_values.keys())
    RDS_Snapshot_Combobox._all_values = _rds_snap_values
    RDS_Snapshot_Combobox.blockSignals(True)
    RDS_Snapshot_Combobox.clear()
    RDS_Snapshot_Combobox.addItems(_rds_snap_values)
    RDS_Snapshot_Combobox.blockSignals(False)
    RDS_Snapshot_Combobox.setEnabled(True)
    RDS_Snapshot_Combobox.setCurrentText(RDS_Snapshot_Combobox__selected_default)
    RDS_Snapshot_Combobox_callback(None)


def RDS_Snapshot_Combobox_callback(event):
    global global_RDS_selected_snapshot, global_RDS_selected_farm
    global_RDS_selected_snapshot = RDS_Snapshot_Combobox_values[RDS_Snapshot_Combobox.currentText()]
    RDS_LofOffPolicy_Combobox.setEnabled(True)
    RDS_Resize_checkbox.setEnabled(True)
    RDS_Enable_datetimepicker_checkbox.setEnabled(True)
    RDS_secondaryimage_checkbox.setEnabled(True)
    RDS_StopOnError_checkbox.setEnabled(True)
    RDS_Apply_Golden_Image_button.setEnabled(True)
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
        RDS_Resize_checkbox.setChecked(True)
        RDS_CoresPerSocket_ComboBox.setCurrentText(str(RDS_corespersocket))
        RDS_CPUCount_ComboBox.setCurrentText(str(RDS_cpucount))
        RDS_Memory_ComboBox.setCurrentText(str(RDS_memsize))
        RDS_Resize_checkbox_callback()


def RDS_Resize_checkbox_callback():
    enabled = RDS_Resize_checkbox.isChecked()
    RDS_CoresPerSocket_ComboBox.setEnabled(enabled)
    RDS_CPUCount_ComboBox.setEnabled(enabled)
    RDS_Memory_ComboBox.setEnabled(enabled)


def RDS_Enable_datetimepicker_checkbox_callback():
    RDS_cal.setEnabled(RDS_Enable_datetimepicker_checkbox.isChecked())


def _update_rds_provisioning_controls():
    af = global_RDS_selected_farm.get('automated_farm_settings', {})
    enabled = af.get('enable_provisioning', True)
    RDS_Provisioning_Status_Label.setText(f"Provisioning: {'Enabled' if enabled else 'Disabled'}")
    RDS_Toggle_Provisioning_button.setText('Disable Provisioning' if enabled else 'Enable Provisioning')
    RDS_Toggle_Provisioning_button.setEnabled(True)


def RDS_Toggle_Provisioning_button_callback():
    global global_RDS_selected_farm, _rds_action_worker
    af = global_RDS_selected_farm.get('automated_farm_settings', {})
    enable = not af.get('enable_provisioning', True)
    logger.info(f"{'Enabling' if enable else 'Disabling'} provisioning for RDS farm '{global_RDS_selected_farm.get('name')}'")
    pod = global_RDS_selected_farm['pod']
    farm_data = global_RDS_selected_farm.copy()
    RDS_Toggle_Provisioning_button.setEnabled(False)

    def action():
        hvconn = connect_pod(pod=pod)
        horizon_functions.Inventory(url=hvconn.url, access_token=hvconn.access_token).set_farm_provisioning(farm_data, enable)
        hvconn.hv_disconnect()

    def on_finished():
        global_RDS_selected_farm['automated_farm_settings']['enable_provisioning'] = enable
        _update_rds_provisioning_controls()

    _rds_action_worker = ApiActionWorker(action)
    _rds_action_worker.status_updated.connect(RDS_Statusbox_Label.setText)
    _rds_action_worker.action_finished.connect(on_finished)
    _rds_action_worker.start()
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
    if not config_save_password_checkbox.isChecked():
        config_save_password = False
        config_reset_stored_password()
    else:
        config_save_password = True
    if config_server_name is not None:
        config_save_button_callback()


def config_loglevel_combobox_callback(event):
    global _log_handler_id, config_log_level
    config_log_level = config_loglevel_combobox.currentText()
    logger.remove(_log_handler_id)
    _log_handler_id = logger.add('hgidt.log', retention="10 days", rotation="50 MB",
                                 format="{time:YYYY-MM-DD at HH:mm:ss} {level} {message}",
                                 level=config_log_level, enqueue=True, backtrace=True,
                                 diagnose=True, catch=True)
    logger.info(f"Log level changed to {config_log_level}")


def config_pod_combobox_callback():
    global config_server_name
    config_conserver_combobox_selected_name = config_pod_combobox.currentText()
    config_conserver_combobox_data = [
        item for item in config_connection_servers if item["PodName"] == config_conserver_combobox_selected_name]
    config_conserver_combobox.blockSignals(True)
    config_conserver_combobox.clear()
    config_conserver_combobox.addItems(
        [item["ServerDNS"] for item in config_conserver_combobox_data])
    config_conserver_combobox.blockSignals(False)
    if config_conserver_combobox.count() > 0:
        config_conserver_combobox.setCurrentIndex(0)


def config_conserver_combobox_callback():
    global config_server_name
    config_server_name = config_conserver_combobox.currentText()


def config_save_button_callback():
    logger.info("Saving configuration")
    global config_username, config_domain, config_server_name, config_password
    config_username = config_username_textbox.text()
    config_domain = config_domain_textbox.text()
    old_server_name = config_server_name
    config_server_name = config_conserver_combobox.currentText()
    if not config_username or not config_domain or not config_server_name or config_password is None:
        config_username = None
        config_domain = None
        config_server_name = None
        config_status_label.setText(
            "Please enter Connection Server, Username and password first.")
    else:
        config = configparser.ConfigParser()
        try:
            config['UserInfo'] = {'Username': config_username, 'Domain': config_domain,
                                  'ServerName': config_server_name, 'Save_Password': str(config_save_password_checkbox.isChecked()),
                                  'Log_Level': config_log_level,
                                  'Refresh_VMs_Snapshots': str(config_refresh_vms_snapshots_checkbox.isChecked()),
                                  'Local_Pod_Only': str(config_local_pod_only_checkbox.isChecked())}
            config['Pods'] = {'Pods': config_pods}
            config['Connection_Servers'] = {
                'Connection_Servers': config_connection_servers}
            with open(CONFIG_FILE, 'w') as configfile:
                config.write(configfile)
        except:
            logger.error("Configuration could not be saved")
        if config_save_password:
            try:
                keyring.set_password(
                    application_name, config_username, config_password)
                logger.info("Password saved to credentials store")
            except keyring.errors.PasswordDeleteError:
                logger.error(
                    "Password could not be saved to the credentials store")
        config_status_label.setText("Configuration saved")
        logger.info("Configuration saved")
        if old_server_name != config_server_name and VDI_Connect_Button.text() == "Refresh":
            _reset_to_disconnected_state()


def config_reset_button_callback():
    logger.info("Resetting configuration")
    global config_username, config_domain, config_server_name, config_password, config_url
    config_reset_stored_password()
    del config_password
    config_password = None
    config_save_password_checkbox.setChecked(False)
    config_username_textbox.clear()
    config_username = None
    config_domain_textbox.clear()
    config_domain = None
    config_conserver_combobox.blockSignals(True)
    config_conserver_combobox.clear()
    config_conserver_combobox.lineEdit().clear()
    config_conserver_combobox.blockSignals(False)
    config_pod_combobox.clear()
    config_pod_combobox.setEnabled(False)
    config_server_name = None
    config_pods.clear()
    config_connection_servers.clear()
    config_url = None
    config = configparser.ConfigParser()
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    config_loglevel_combobox.setCurrentText('INFO')
    config_loglevel_combobox_callback(None)
    config_status_label.setText(
        "Configuration reset and configuration file deleted.")
    logger.info("Configuration reset")


class ConfigTestWorker(QThread):
    status_updated = Signal(str)
    save_requested = Signal()

    def __init__(self, username, domain, server_name, password):
        super().__init__()
        self._username = username
        self._domain = domain
        self._server_name = server_name
        self._password = password

    def run(self):
        logger.info("Testing configuration")
        self.status_updated.emit("Testing configuration")
        config_url = "https://" + self._server_name
        hvconnectionobj = horizon_functions.Connection(
            username=self._username, domain=self._domain,
            password=self._password, url=config_url)
        try:
            hvconnectionobj.hv_connect()
            build_pod_info(hvconnectionobj)
            hvconnectionobj.hv_disconnect()
            logger.info("Successfully finished testing configuration")
            logger.info("Saving configuration since it works")
            self.save_requested.emit()
            self.status_updated.emit("Successfully finished testing configuration")
        except Exception as e:
            self.status_updated.emit(
                "Error testing the connection, see the log file for details")
            logger.error("Error while testing the credentials")
            logger.error(str(e))


def config_test_button_callback():
    global config_username, config_domain, config_server_name, _config_test_worker
    config_username = config_username_textbox.text()
    config_domain = config_domain_textbox.text()
    config_server_name = config_conserver_combobox.currentText()
    if not config_username or not config_domain or not config_server_name:
        logger.error("Cannot test due to missing configuration")
        config_status_label.setText(
            "Not all information is provided, please check the configuration.")
        return
    if config_password is None:
        logger.error("No password was set")
        config_status_label.setText("Please set a password first")
        return
    _config_test_worker = ConfigTestWorker(
        config_username, config_domain, config_server_name, config_password)
    _config_test_worker.status_updated.connect(config_status_label.setText)
    _config_test_worker.save_requested.connect(config_save_button_callback)
    _config_test_worker.start()

# endregion

# region Various functions


def get_selected_datetime(cal):
    return cal.dateTime().toPython()


class ConnectWorker(QThread):
    status_updated = Signal(str)
    data_loaded = Signal(dict)

    def __init__(self, include_vms_snapshots=True):
        super().__init__()
        self._include_vms_snapshots = include_vms_snapshots

    def run(self):
        data = horizon_app.load_environment_data(
            config_pods, config_connection_servers,
            config_username, config_domain, config_password,
            on_status=lambda msg: self.status_updated.emit(msg),
            include_vms_snapshots=self._include_vms_snapshots)
        self.data_loaded.emit(data)


class ApiActionWorker(QThread):
    status_updated = Signal(str)
    action_finished = Signal()

    def __init__(self, action_fn):
        super().__init__()
        self._action_fn = action_fn

    def run(self):
        try:
            self._action_fn()
        except Exception as e:
            logger.error(f"Action failed: {e}")
            self.status_updated.emit(str(e))
        self.action_finished.emit()


def generic_Connect_Button_callback():
    global _connect_worker
    if config_server_name is None and config_password is None:
        logger.info("No Connection server and password found in config")
        VDI_Statusbox_Label.setText("Please configure the connection details first on the Configuration tab")
        RDS_Statusbox_Label.setText("Please configure the connection details first on the Configuration tab")
        return
    elif config_server_name is not None and config_password is None:
        logger.info("No password found in config")
        VDI_Statusbox_Label.setText("Please configure the password first on the Configuration tab")
        RDS_Statusbox_Label.setText("Please configure the password first on the Configuration tab")
        return

    VDI_Connect_Button.setEnabled(False)
    RDS_Connect_Button.setEnabled(False)
    VDI_DesktopPool_Combobox.setEnabled(False)
    VDI_Golden_Image_Combobox.setEnabled(False)
    VDI_Snapshot_Combobox.setEnabled(False)
    VDI_Promote_Secondary_Image_button.setEnabled(False)
    VDI_Statusbox_Label.setText("Connecting")
    RDS_Statusbox_Label.setText("Connecting")

    is_refresh = VDI_Connect_Button.text() == "Refresh"
    include_vms = not is_refresh or config_refresh_vms_snapshots_checkbox.isChecked()
    _connect_worker = ConnectWorker(include_vms_snapshots=include_vms)
    _connect_worker.status_updated.connect(_on_connect_status)
    _connect_worker.data_loaded.connect(_on_connect_finished)
    _connect_worker.start()


def _on_connect_status(msg):
    VDI_Statusbox_Label.setText(msg)
    RDS_Statusbox_Label.setText(msg)


def _on_connect_finished(data):
    global global_desktop_pools, global_rds_farms, global_base_vms, global_base_snapshots, global_datacenters, global_vcenters, VDI_DesktopPool_Combobox_values, RDS_Farm_Combobox_values

    global_desktop_pools = data['desktop_pools']
    global_rds_farms = data['rds_farms']
    if data.get('include_vms_snapshots', True):
        global_base_vms = data['base_vms']
        global_base_snapshots = data['base_snapshots']
        global_datacenters = data['datacenters']
        global_vcenters = data['vcenters']

    vdi_name_dict_mapping = []
    rds_name_dict_mapping = []

    for pool in global_desktop_pools:
        name = pool['name']
        if name in vdi_name_dict_mapping:
            pool['name'] = f'{name} ({pool["pod"]})'
        else:
            vdi_name_dict_mapping.append(name)

    for farm in global_rds_farms:
        name = farm['name']
        if name in rds_name_dict_mapping:
            farm['name'] = f'{name} ({farm["pod"]})'
        else:
            rds_name_dict_mapping.append(name)

    VDI_DesktopPool_Combobox_values = {item["name"]: item for item in global_desktop_pools}
    if global_desktop_pools:
        VDI_DesktopPool_Combobox__selected_default = global_desktop_pools[0]['name']
        _vdi_pool_names = list(VDI_DesktopPool_Combobox_values.keys())
        VDI_DesktopPool_Combobox._all_values = _vdi_pool_names
        VDI_DesktopPool_Combobox.blockSignals(True)
        VDI_DesktopPool_Combobox.clear()
        VDI_DesktopPool_Combobox.addItems(_vdi_pool_names)
        VDI_DesktopPool_Combobox.blockSignals(False)
        VDI_DesktopPool_Combobox.setEnabled(True)
        VDI_DesktopPool_Combobox.setCurrentText(VDI_DesktopPool_Combobox__selected_default)
        VDI_DesktopPool_Combobox_callback(None)
        VDI_Statusbox_Label.setText("Connected")
    else:
        VDI_Statusbox_Label.setText("Connected - no instant-clone VDI pools found")

    RDS_Farm_Combobox_values = {item["name"]: item for item in global_rds_farms}
    if global_rds_farms:
        RDS_Farm_Combobox__selected_default = global_rds_farms[0]['name']
        _rds_farm_names = list(RDS_Farm_Combobox_values.keys())
        RDS_Farm_Combobox._all_values = _rds_farm_names
        RDS_Farm_Combobox.blockSignals(True)
        RDS_Farm_Combobox.clear()
        RDS_Farm_Combobox.addItems(_rds_farm_names)
        RDS_Farm_Combobox.blockSignals(False)
        RDS_Farm_Combobox.setEnabled(True)
        RDS_Farm_Combobox.setCurrentText(RDS_Farm_Combobox__selected_default)
        RDS_Farm_Combobox_callback(None)
        RDS_Statusbox_Label.setText("Connected")
    else:
        RDS_Statusbox_Label.setText("Connected - no instant-clone RDS farms found")

    VDI_Connect_Button.setText("Refresh")
    RDS_Connect_Button.setText("Refresh")
    VDI_Connect_Button.setEnabled(True)
    RDS_Connect_Button.setEnabled(True)


def connect_pod(pod: str):
    global config_server_name
    conn, server_dns = horizon_app.connect_to_pod(
        pod, config_connection_servers, config_username, config_domain, config_password)
    if conn is not False and server_dns:
        config_server_name = server_dns
    return conn


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def _reset_to_disconnected_state():
    global global_desktop_pools, global_rds_farms, global_base_vms, global_base_snapshots
    global global_datacenters, global_vcenters
    global global_vdi_selected_pool, global_vdi_selected_vm, global_VDI_selected_snapshot
    global global_RDS_selected_farm, global_RDS_selected_vm, global_RDS_selected_snapshot
    global VDI_DesktopPool_Combobox_values, VDI_Golden_Image_Combobox_values, VDI_Snapshot_Combobox_values
    global RDS_Farm_Combobox_values, RDS_Golden_Image_Combobox_values, RDS_Snapshot_Combobox_values

    global_desktop_pools.clear()
    global_rds_farms.clear()
    global_base_vms.clear()
    global_base_snapshots.clear()
    global_datacenters.clear()
    global_vcenters.clear()
    global_vdi_selected_pool = {}
    global_vdi_selected_vm = {}
    global_VDI_selected_snapshot = {}
    global_RDS_selected_farm = {}
    global_RDS_selected_vm = {}
    global_RDS_selected_snapshot = {}
    VDI_DesktopPool_Combobox_values = {}
    VDI_Golden_Image_Combobox_values = {}
    VDI_Snapshot_Combobox_values = {}
    RDS_Farm_Combobox_values = {}
    RDS_Golden_Image_Combobox_values = {}
    RDS_Snapshot_Combobox_values = {}

    for cb in (VDI_DesktopPool_Combobox, VDI_Golden_Image_Combobox, VDI_Snapshot_Combobox,
               RDS_Farm_Combobox, RDS_Golden_Image_Combobox, RDS_Snapshot_Combobox):
        cb.blockSignals(True)
        cb.clear()
        cb.blockSignals(False)

    _vdi_disable_all_controls()
    _rds_disable_all_controls()

    VDI_Connect_Button.setText("Connect")
    VDI_Connect_Button.setEnabled(True)
    RDS_Connect_Button.setText("Connect")
    RDS_Connect_Button.setEnabled(True)

    VDI_Statusbox_Label.setText("")
    RDS_Statusbox_Label.setText("")
    VDI_Provisioning_Status_Label.setText("Provisioning: N/A")
    RDS_Provisioning_Status_Label.setText("Provisioning: N/A")


def _vdi_disable_all_controls():
    for widget in (
        VDI_Secondary_Machine_Options_Combobox, VDI_machinecount_textbox,
        VDI_Apply_Golden_Image_button, VDI_Apply_Secondary_Image_button,
        VDI_Cancel_Secondary_Image_button, VDI_Promote_Secondary_Image_button,
        VDI_Enable_datetimepicker_checkbox, VDI_CPUCount_ComboBox, VDI_cal,
        VDI_Golden_Image_Combobox, VDI_Snapshot_Combobox, VDI_vtpm_checkbox,
        VDI_LofOffPolicy_Combobox, VDI_Resize_checkbox, VDI_StopOnError_checkbox,
        VDI_secondaryimage_checkbox, VDI_CoresPerSocket_ComboBox, VDI_Memory_ComboBox,
        VDI_Toggle_Provisioning_button,
    ):
        widget.setEnabled(False)


def _rds_disable_all_controls():
    for widget in (
        RDS_Secondary_Machine_Options_Combobox, RDS_machinecount_textbox,
        RDS_Apply_Golden_Image_button, RDS_Apply_Secondary_Image_button,
        RDS_Cancel_Secondary_Image_button, RDS_Promote_Secondary_Image_button,
        RDS_Enable_datetimepicker_checkbox, RDS_CPUCount_ComboBox, RDS_cal,
        RDS_Golden_Image_Combobox, RDS_Snapshot_Combobox,
        RDS_LofOffPolicy_Combobox, RDS_Resize_checkbox, RDS_StopOnError_checkbox,
        RDS_secondaryimage_checkbox, RDS_CoresPerSocket_ComboBox, RDS_Memory_ComboBox,
        RDS_Toggle_Provisioning_button,
    ):
        widget.setEnabled(False)


def bind_combobox_search(combobox):
    combobox._all_values = []
    combobox.setEditable(True)
    combobox.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

    def on_text_edited(text):
        typed = text.lower()
        filtered = (
            [v for v in combobox._all_values if typed in v.lower()]
            if typed else list(combobox._all_values)
        )
        combobox.blockSignals(True)
        current = combobox.lineEdit().text()
        combobox.clear()
        combobox.addItems(filtered)
        combobox.blockSignals(False)
        combobox.lineEdit().setText(current)

    combobox.lineEdit().textEdited.connect(on_text_edited)
# endregion


# region Foundation - PySide6
app = QApplication(sys.argv)
app.setStyle("Fusion")

window = QMainWindow()
window.setWindowTitle("Horizon Golden Image Deployment Tool")
iconPath = resource_path(logo_image)
window.setWindowIcon(QIcon(iconPath))
window.setFixedSize(1100, 470)

tab_widget = QTabWidget()
window.setCentralWidget(tab_widget)
# endregion


# region Tab 1 - VDI Desktop Pools
tab1 = QWidget()
tab_widget.addTab(tab1, "VDI Pools")

# Top row
VDI_Connect_Button = QPushButton("Connect", tab1)
VDI_Connect_Button.setGeometry(10, 10, 120, 25)
VDI_Connect_Button.clicked.connect(generic_Connect_Button_callback)

VDI_Statusbox_Label = QLabel("", tab1)
VDI_Statusbox_Label.setGeometry(140, 12, 395, 20)

# Pool / Image / Snapshot selectors
QLabel("Desktop Pool", tab1).setGeometry(10, 45, 180, 20)
VDI_DesktopPool_Combobox = QComboBox(tab1)
VDI_DesktopPool_Combobox.setGeometry(10, 65, 360, 25)
VDI_DesktopPool_Combobox.setEnabled(False)
bind_combobox_search(VDI_DesktopPool_Combobox)
VDI_DesktopPool_Combobox.currentIndexChanged.connect(
    lambda _: VDI_DesktopPool_Combobox_callback(None))

QLabel("Golden Image", tab1).setGeometry(10, 100, 180, 20)
VDI_Golden_Image_Combobox = QComboBox(tab1)
VDI_Golden_Image_Combobox.setGeometry(10, 120, 360, 25)
VDI_Golden_Image_Combobox.setEnabled(False)
bind_combobox_search(VDI_Golden_Image_Combobox)
VDI_Golden_Image_Combobox.activated.connect(
    lambda _: VDI_Golden_Image_Combobox_callback(None))

QLabel("Snapshot", tab1).setGeometry(10, 155, 180, 20)
VDI_Snapshot_Combobox = QComboBox(tab1)
VDI_Snapshot_Combobox.setGeometry(10, 175, 360, 25)
VDI_Snapshot_Combobox.setEnabled(False)
bind_combobox_search(VDI_Snapshot_Combobox)
VDI_Snapshot_Combobox.currentIndexChanged.connect(
    lambda _: VDI_Snapshot_Combobox_callback(None))

# Options row: logoff policy, vtpm, stop on error
QLabel("Log Off Policy", tab1).setGeometry(10, 210, 120, 20)
VDI_vtpm_checkbox = QCheckBox("Add vTPM", tab1)
VDI_vtpm_checkbox.setGeometry(145, 208, 100, 20)
VDI_vtpm_checkbox.setEnabled(False)
VDI_StopOnError_checkbox = QCheckBox("Stop on Error", tab1)
VDI_StopOnError_checkbox.setGeometry(255, 208, 110, 20)
VDI_StopOnError_checkbox.setEnabled(False)

VDI_LofOffPolicy_Combobox = QComboBox(tab1)
VDI_LofOffPolicy_Combobox.setGeometry(10, 230, 130, 25)
VDI_LofOffPolicy_Combobox.addItems(_LOGOFF_POLICIES)
VDI_LofOffPolicy_Combobox.setEnabled(False)

# Resize row
VDI_Resize_checkbox = QCheckBox("Resize VM", tab1)
VDI_Resize_checkbox.setGeometry(10, 265, 90, 20)
VDI_Resize_checkbox.setEnabled(False)
VDI_Resize_checkbox.toggled.connect(lambda _: VDI_Resize_checkbox_callback())

QLabel("Cores/Socket", tab1).setGeometry(105, 265, 90, 20)
QLabel("CPU Count", tab1).setGeometry(210, 265, 80, 20)
QLabel("Memory MB", tab1).setGeometry(305, 265, 80, 20)

VDI_CoresPerSocket_ComboBox = QComboBox(tab1)
VDI_CoresPerSocket_ComboBox.setGeometry(105, 285, 95, 25)
VDI_CoresPerSocket_ComboBox.addItems([str(x) for x in onetosixtyfour])
VDI_CoresPerSocket_ComboBox.setEnabled(False)

VDI_CPUCount_ComboBox = QComboBox(tab1)
VDI_CPUCount_ComboBox.setGeometry(210, 285, 85, 25)
VDI_CPUCount_ComboBox.addItems([str(x) for x in onetosixtyfour])
VDI_CPUCount_ComboBox.setEnabled(False)

VDI_Memory_ComboBox = QComboBox(tab1)
VDI_Memory_ComboBox.setGeometry(305, 285, 110, 25)
VDI_Memory_ComboBox.addItems([str(x) for x in memory_list])
VDI_Memory_ComboBox.setEnabled(False)

# Secondary image + schedule row
VDI_secondaryimage_checkbox = QCheckBox("Secondary Image", tab1)
VDI_secondaryimage_checkbox.setGeometry(10, 320, 130, 20)
VDI_secondaryimage_checkbox.setEnabled(False)
VDI_secondaryimage_checkbox.toggled.connect(lambda _: VDI_secondaryimage_checkbox_callback())

VDI_Enable_datetimepicker_checkbox = QCheckBox("Schedule", tab1)
VDI_Enable_datetimepicker_checkbox.setGeometry(265, 320, 90, 20)
VDI_Enable_datetimepicker_checkbox.setEnabled(False)
VDI_Enable_datetimepicker_checkbox.toggled.connect(
    lambda _: VDI_Enable_datetimepicker_checkbox_callback())

# Secondary options row
VDI_Secondary_Machine_Options_Combobox = QComboBox(tab1)
VDI_Secondary_Machine_Options_Combobox.setGeometry(10, 345, 185, 25)
VDI_Secondary_Machine_Options_Combobox.addItems(_SECONDARY_OPTIONS)
VDI_Secondary_Machine_Options_Combobox.setEnabled(False)
VDI_Secondary_Machine_Options_Combobox.currentIndexChanged.connect(
    lambda _: VDI_Secondary_Machine_Options_Combobox_callback(None))

VDI_secondary_image_machine_count_label = QLabel(VDI_secondary_image_machine_count_label_default, tab1)
VDI_secondary_image_machine_count_label.setGeometry(205, 347, 65, 20)
VDI_secondary_image_machine_count_label.setEnabled(False)

VDI_machinecount_textbox = QLineEdit(tab1)
VDI_machinecount_textbox.setGeometry(278, 345, 55, 25)
VDI_machinecount_textbox.setValidator(QIntValidator(0, 999))
VDI_machinecount_textbox.setEnabled(False)

VDI_cal = QDateTimeEdit(tab1)
VDI_cal.setGeometry(345, 345, 185, 25)
VDI_cal.setCalendarPopup(True)
VDI_cal.setDateTime(QDateTime.currentDateTime())
VDI_cal.setEnabled(False)

# Action buttons
VDI_Apply_Golden_Image_button = QPushButton("Apply Image", tab1)
VDI_Apply_Golden_Image_button.setGeometry(10, 400, 120, 25)
VDI_Apply_Golden_Image_button.setEnabled(False)
VDI_Apply_Golden_Image_button.clicked.connect(VDI_Apply_Golden_Image_button_callback)

VDI_Cancel_Secondary_Image_button = QPushButton("Cancel Image", tab1)
VDI_Cancel_Secondary_Image_button.setGeometry(140, 400, 120, 25)
VDI_Cancel_Secondary_Image_button.setEnabled(False)
VDI_Cancel_Secondary_Image_button.clicked.connect(VDI_Cancel_Secondary_Image_button_callback)

VDI_Promote_Secondary_Image_button = QPushButton("Promote Image", tab1)
VDI_Promote_Secondary_Image_button.setGeometry(270, 400, 120, 25)
VDI_Promote_Secondary_Image_button.setEnabled(False)
VDI_Promote_Secondary_Image_button.clicked.connect(VDI_Promote_Secondary_Image_button_callback)

VDI_Apply_Secondary_Image_button = QPushButton("Apply Secondary", tab1)
VDI_Apply_Secondary_Image_button.setGeometry(400, 400, 120, 25)
VDI_Apply_Secondary_Image_button.setEnabled(False)
VDI_Apply_Secondary_Image_button.clicked.connect(VDI_Apply_Secondary_Image_button_callback)

# Status textblock (right side)
VDI_Status_Textblock = QPlainTextEdit(tab1)
VDI_Status_Textblock.setGeometry(545, 10, 540, 355)
VDI_Status_Textblock.setReadOnly(True)

# Provisioning status + toggle (right panel, same row as action buttons)
VDI_Provisioning_Status_Label = QLabel("Provisioning: N/A", tab1)
VDI_Provisioning_Status_Label.setGeometry(545, 402, 200, 20)

VDI_Toggle_Provisioning_button = QPushButton("Enable Provisioning", tab1)
VDI_Toggle_Provisioning_button.setGeometry(752, 396, 330, 25)
VDI_Toggle_Provisioning_button.setEnabled(False)
VDI_Toggle_Provisioning_button.clicked.connect(VDI_Toggle_Provisioning_button_callback)
# endregion


# region Tab 2 - RDS Farms
tab2 = QWidget()
tab_widget.addTab(tab2, "RDS Farms")

# Top row
RDS_Connect_Button = QPushButton("Connect", tab2)
RDS_Connect_Button.setGeometry(10, 10, 120, 25)
RDS_Connect_Button.clicked.connect(generic_Connect_Button_callback)

RDS_Statusbox_Label = QLabel("", tab2)
RDS_Statusbox_Label.setGeometry(140, 12, 395, 20)

# Farm / Image / Snapshot selectors
QLabel("RDS Farm", tab2).setGeometry(10, 45, 180, 20)
RDS_Farm_Combobox = QComboBox(tab2)
RDS_Farm_Combobox.setGeometry(10, 65, 360, 25)
RDS_Farm_Combobox.setEnabled(False)
bind_combobox_search(RDS_Farm_Combobox)
RDS_Farm_Combobox.currentIndexChanged.connect(
    lambda _: RDS_Farm_Combobox_callback(None))

QLabel("Golden Image", tab2).setGeometry(10, 100, 180, 20)
RDS_Golden_Image_Combobox = QComboBox(tab2)
RDS_Golden_Image_Combobox.setGeometry(10, 120, 360, 25)
RDS_Golden_Image_Combobox.setEnabled(False)
bind_combobox_search(RDS_Golden_Image_Combobox)
RDS_Golden_Image_Combobox.activated.connect(
    lambda _: RDS_Golden_Image_Combobox_callback(None))

QLabel("Snapshot", tab2).setGeometry(10, 155, 180, 20)
RDS_Snapshot_Combobox = QComboBox(tab2)
RDS_Snapshot_Combobox.setGeometry(10, 175, 360, 25)
RDS_Snapshot_Combobox.setEnabled(False)
bind_combobox_search(RDS_Snapshot_Combobox)
RDS_Snapshot_Combobox.currentIndexChanged.connect(
    lambda _: RDS_Snapshot_Combobox_callback(None))

# Options row: logoff policy, stop on error
QLabel("Log Off Policy", tab2).setGeometry(10, 210, 120, 20)
RDS_StopOnError_checkbox = QCheckBox("Stop on Error", tab2)
RDS_StopOnError_checkbox.setGeometry(145, 208, 110, 20)
RDS_StopOnError_checkbox.setEnabled(False)

RDS_LofOffPolicy_Combobox = QComboBox(tab2)
RDS_LofOffPolicy_Combobox.setGeometry(10, 230, 130, 25)
RDS_LofOffPolicy_Combobox.addItems(_LOGOFF_POLICIES)
RDS_LofOffPolicy_Combobox.setEnabled(False)

# Resize row
RDS_Resize_checkbox = QCheckBox("Resize VM", tab2)
RDS_Resize_checkbox.setGeometry(10, 265, 90, 20)
RDS_Resize_checkbox.setEnabled(False)
RDS_Resize_checkbox.toggled.connect(lambda _: RDS_Resize_checkbox_callback())

QLabel("Cores/Socket", tab2).setGeometry(105, 265, 90, 20)
QLabel("CPU Count", tab2).setGeometry(210, 265, 80, 20)
QLabel("Memory MB", tab2).setGeometry(305, 265, 80, 20)

RDS_CoresPerSocket_ComboBox = QComboBox(tab2)
RDS_CoresPerSocket_ComboBox.setGeometry(105, 285, 95, 25)
RDS_CoresPerSocket_ComboBox.addItems([str(x) for x in onetosixtyfour])
RDS_CoresPerSocket_ComboBox.setEnabled(False)

RDS_CPUCount_ComboBox = QComboBox(tab2)
RDS_CPUCount_ComboBox.setGeometry(210, 285, 85, 25)
RDS_CPUCount_ComboBox.addItems([str(x) for x in onetosixtyfour])
RDS_CPUCount_ComboBox.setEnabled(False)

RDS_Memory_ComboBox = QComboBox(tab2)
RDS_Memory_ComboBox.setGeometry(305, 285, 110, 25)
RDS_Memory_ComboBox.addItems([str(x) for x in memory_list])
RDS_Memory_ComboBox.setEnabled(False)

# Secondary image + schedule row
RDS_secondaryimage_checkbox = QCheckBox("Secondary Image", tab2)
RDS_secondaryimage_checkbox.setGeometry(10, 320, 130, 20)
RDS_secondaryimage_checkbox.setEnabled(False)
RDS_secondaryimage_checkbox.toggled.connect(lambda _: RDS_secondaryimage_checkbox_callback())

RDS_Enable_datetimepicker_checkbox = QCheckBox("Schedule", tab2)
RDS_Enable_datetimepicker_checkbox.setGeometry(265, 320, 90, 20)
RDS_Enable_datetimepicker_checkbox.setEnabled(False)
RDS_Enable_datetimepicker_checkbox.toggled.connect(
    lambda _: RDS_Enable_datetimepicker_checkbox_callback())

# Secondary options row
RDS_Secondary_Machine_Options_Combobox = QComboBox(tab2)
RDS_Secondary_Machine_Options_Combobox.setGeometry(10, 345, 185, 25)
RDS_Secondary_Machine_Options_Combobox.addItems(_SECONDARY_OPTIONS)
RDS_Secondary_Machine_Options_Combobox.setEnabled(False)
RDS_Secondary_Machine_Options_Combobox.currentIndexChanged.connect(
    lambda _: RDS_Secondary_Machine_Options_Combobox_callback(None))

RDS_secondary_image_machine_count_label = QLabel(RDS_secondary_image_machine_count_label_default, tab2)
RDS_secondary_image_machine_count_label.setGeometry(205, 347, 65, 20)
RDS_secondary_image_machine_count_label.setEnabled(False)

RDS_machinecount_textbox = QLineEdit(tab2)
RDS_machinecount_textbox.setGeometry(278, 345, 55, 25)
RDS_machinecount_textbox.setValidator(QIntValidator(0, 999))
RDS_machinecount_textbox.setEnabled(False)

RDS_cal = QDateTimeEdit(tab2)
RDS_cal.setGeometry(345, 345, 185, 25)
RDS_cal.setCalendarPopup(True)
RDS_cal.setDateTime(QDateTime.currentDateTime())
RDS_cal.setEnabled(False)

# Action buttons
RDS_Apply_Golden_Image_button = QPushButton("Apply Image", tab2)
RDS_Apply_Golden_Image_button.setGeometry(10, 400, 120, 25)
RDS_Apply_Golden_Image_button.setEnabled(False)
RDS_Apply_Golden_Image_button.clicked.connect(RDS_Apply_Golden_Image_button_callback)

RDS_Cancel_Secondary_Image_button = QPushButton("Cancel Image", tab2)
RDS_Cancel_Secondary_Image_button.setGeometry(140, 400, 120, 25)
RDS_Cancel_Secondary_Image_button.setEnabled(False)
RDS_Cancel_Secondary_Image_button.clicked.connect(RDS_Cancel_Secondary_Image_button_callback)

RDS_Promote_Secondary_Image_button = QPushButton("Promote Image", tab2)
RDS_Promote_Secondary_Image_button.setGeometry(270, 400, 120, 25)
RDS_Promote_Secondary_Image_button.setEnabled(False)
RDS_Promote_Secondary_Image_button.clicked.connect(RDS_Promote_Secondary_Image_button_callback)

RDS_Apply_Secondary_Image_button = QPushButton("Apply Secondary", tab2)
RDS_Apply_Secondary_Image_button.setGeometry(400, 400, 120, 25)
RDS_Apply_Secondary_Image_button.setEnabled(False)
RDS_Apply_Secondary_Image_button.clicked.connect(RDS_Apply_Secondary_Image_button_callback)

# Status textblock (right side)
RDS_Status_Textblock = QPlainTextEdit(tab2)
RDS_Status_Textblock.setGeometry(545, 10, 540, 355)
RDS_Status_Textblock.setReadOnly(True)

# Provisioning status + toggle (right panel, same row as action buttons)
RDS_Provisioning_Status_Label = QLabel("Provisioning: N/A", tab2)
RDS_Provisioning_Status_Label.setGeometry(545, 402, 200, 20)

RDS_Toggle_Provisioning_button = QPushButton("Enable Provisioning", tab2)
RDS_Toggle_Provisioning_button.setGeometry(752, 396, 330, 25)
RDS_Toggle_Provisioning_button.setEnabled(False)
RDS_Toggle_Provisioning_button.clicked.connect(RDS_Toggle_Provisioning_button_callback)
# endregion


# region Tab 3 - Configuration
tab3 = QWidget()
tab_widget.addTab(tab3, "Configuration")

# Buttons
config_get_password_button = QPushButton("Get Password", tab3)
config_get_password_button.setGeometry(30, 200, 150, 25)
config_get_password_button.clicked.connect(show_password_dialog)

config_reset_button = QPushButton("Reset Configuration", tab3)
config_reset_button.setGeometry(30, 323, 150, 25)
config_reset_button.clicked.connect(config_reset_button_callback)

config_save_button = QPushButton("Save Configuration", tab3)
config_save_button.setGeometry(30, 353, 150, 25)
config_save_button.clicked.connect(config_save_button_callback)

config_test_credential_button = QPushButton("Test Credentials", tab3)
config_test_credential_button.setGeometry(30, 383, 150, 25)
config_test_credential_button.clicked.connect(config_test_button_callback)

# Labels
config_conserver_label = QLabel("Connection Server", tab3)
config_conserver_label.setGeometry(30, 20, 180, 20)

config_pod_label = QLabel("Pod", tab3)
config_pod_label.setGeometry(270, 20, 180, 20)

config_username_label = QLabel("Username", tab3)
config_username_label.setGeometry(30, 80, 150, 20)

config_domain_label = QLabel("Domain", tab3)
config_domain_label.setGeometry(30, 140, 150, 20)

config_loglevel_label = QLabel("Log Level", tab3)
config_loglevel_label.setGeometry(270, 80, 150, 20)

config_status_label = QLabel("Status: N/A", tab3)
config_status_label.setGeometry(30, 418, 400, 20)

# Text inputs
config_username_textbox = QLineEdit(tab3)
config_username_textbox.setGeometry(30, 105, 150, 25)
config_username_textbox.setPlaceholderText("UserName")
if config_username is not None:
    config_username_textbox.setText(config_username)

config_domain_textbox = QLineEdit(tab3)
config_domain_textbox.setGeometry(30, 165, 150, 25)
config_domain_textbox.setPlaceholderText("Domain")
if config_domain is not None:
    config_domain_textbox.setText(config_domain)

# ComboBoxes
config_loglevel_combobox = QComboBox(tab3)
config_loglevel_combobox.setGeometry(270, 105, 120, 25)
config_loglevel_combobox.addItems(_LOG_LEVELS)
config_loglevel_combobox.setCurrentText(config_log_level)
config_loglevel_combobox.activated.connect(
    lambda _: config_loglevel_combobox_callback(None))

config_pod_combobox = QComboBox(tab3)
config_pod_combobox.setGeometry(270, 45, 200, 25)
if len(config_pods) >= 1:
    config_pod_combobox.addItems(config_pods)
    config_pod_combobox.setCurrentIndex(0)
else:
    config_pod_combobox.setEnabled(False)
config_pod_combobox.activated.connect(lambda _: config_pod_combobox_callback())

config_conserver_combobox = QComboBox(tab3)
config_conserver_combobox.setGeometry(30, 45, 200, 25)
config_conserver_combobox.setEditable(True)
config_conserver_combobox.lineEdit().setPlaceholderText("Enter Connectionserver DNS")
if len(config_pods) >= 1:
    config_pod_combobox_callback()
config_conserver_combobox.currentTextChanged.connect(
    lambda _: config_conserver_combobox_callback())

# Checkboxes
config_save_password_checkbox = QCheckBox("Save Password", tab3)
config_save_password_checkbox.move(30, 235)
config_save_password_checkbox.adjustSize()
config_save_password_checkbox.setChecked(config_save_password)
config_save_password_checkbox.toggled.connect(
    lambda _: config_save_password_checkbox_callback())

config_refresh_vms_snapshots_checkbox = QCheckBox("Refresh Golden Images & Snapshots on Refresh", tab3)
config_refresh_vms_snapshots_checkbox.move(30, 263)
config_refresh_vms_snapshots_checkbox.adjustSize()
config_refresh_vms_snapshots_checkbox.setChecked(config_refresh_vms_snapshots)
config_refresh_vms_snapshots_checkbox.toggled.connect(config_save_button_callback)

config_local_pod_only_checkbox = QCheckBox("Local Pod Only (skip multi-pod federation discovery)", tab3)
config_local_pod_only_checkbox.move(30, 291)
config_local_pod_only_checkbox.adjustSize()
config_local_pod_only_checkbox.setChecked(config_local_pod_only)
config_local_pod_only_checkbox.toggled.connect(config_save_button_callback)

# endregion

tab_widget.setCurrentIndex(0)
window.show()
sys.exit(app.exec())
