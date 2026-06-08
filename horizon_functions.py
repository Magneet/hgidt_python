import json
import math
import requests
import urllib
import time
from loguru import logger

REQUEST_TIMEOUT = 30
_MAX_RETRIES = 5


def _make_request(func, url: str, **kwargs) -> requests.Response:
    """Wraps a requests call with automatic retry on HTTP 429 (rate-limited).

    Reads X-Rate-Limit-Retry-After-Seconds from the response header to
    determine how long to wait before each retry.
    """
    logger.debug(f"[{func.__name__}] {url}")
    for _ in range(_MAX_RETRIES):
        response = func(url, **kwargs)
        if response.status_code != 429:
            return response
        retry_after = math.ceil(float(response.headers.get('X-Rate-Limit-Retry-After-Seconds', 5)))
        logger.warning(f"Rate limited (429), retrying after {retry_after}s: {url}")
        time.sleep(retry_after)
    return response


def _get(url: str, **kwargs) -> requests.Response:
    return _make_request(requests.get, url, **kwargs)


def _post(url: str, **kwargs) -> requests.Response:
    return _make_request(requests.post, url, **kwargs)


def _put(url: str, **kwargs) -> requests.Response:
    return _make_request(requests.put, url, **kwargs)


def _check_response(response: requests.Response, ok_status: int = 200) -> None:
    """Raise a descriptive Exception for any non-ok response.

    The Horizon REST API returns APIError objects with a single error_message
    string field. Falls back to response.reason if the body is not JSON or
    the field is absent.
    """
    if response.status_code == ok_status:
        return
    msg = response.reason
    try:
        msg = response.json().get("error_message") or response.reason
    except Exception:
        pass
    logger.error(f"API error {response.status_code} for {response.url}: {msg}")
    raise Exception(f"Error {response.status_code}: {msg}")


class Connection:
    """The Connection class is used to handle connections and disconnections to and from the VMware Horizon REST API's"""

    def __init__(self, username: str, password: str, domain: str, url: str):
        """"The default object for the connection class needs to be created using username, password, domain and url in plain text."""
        self.username = username
        self.password = password
        self.domain = domain
        self.url = url
        self.access_token = ""
        self.refresh_token = ""

    def hv_connect(self):
        """Used to authenticate to the VMware Horizon REST API's"""
        logger.info(f"Connecting to {self.url}")
        headers = {
            'accept': '*/*',
            'Content-Type': 'application/json',
        }
        data = {"domain": self.domain, "password": self.password, "username": self.username}
        response = _post(
            f'{self.url}/rest/login', verify=False, timeout=REQUEST_TIMEOUT,
            headers=headers, data=json.dumps(data))
        _check_response(response)
        data = response.json()
        self.access_token = {
            'accept': '*/*',
            'Authorization': 'Bearer ' + data['access_token']
        }
        self.refresh_token = data['refresh_token']
        logger.debug(f"Connected successfully to {self.url}")
        return self

    def hv_disconnect(self):
        """"Used to close close the connection with the VMware Horizon REST API's"""
        logger.debug(f"Disconnecting from {self.url}")
        headers = {
            'accept': '*/*',
            'Content-Type': 'application/json',
        }
        response = _post(
            f'{self.url}/rest/logout', verify=False, timeout=REQUEST_TIMEOUT,
            headers=headers, data=json.dumps({'refresh_token': self.refresh_token}))
        _check_response(response)
        return response.status_code

    def hv_refresh(self):
        """"Used to close close the connection with the VMware Horizon REST API's"""
        headers = {
            'accept': '*/*',
            'Content-Type': 'application/json',
        }
        response = _post(
            f'{self.url}/rest/refresh', verify=False, timeout=REQUEST_TIMEOUT,
            headers=headers, data=json.dumps({'refresh_token': self.refresh_token}))
        _check_response(response)
        return response.status_code


class Federation:
    def __init__(self, url: str, access_token: dict):
        """Default object for the pools class where all Desktop Pool Actions will be performed."""
        self.url = url
        self.access_token = access_token

    def get_cloud_pod_federation(self) -> dict:
        """Retrieves the pod federation details.

        Available for Horizon 8 2012 and later."""
        response = _get(
            f'{self.url}/rest/federation/v1/cpa', verify=False, timeout=REQUEST_TIMEOUT,
            headers=self.access_token)
        _check_response(response)
        return response.json()

    def get_pods(self) -> list:
        """Lists all the pods in the pod federation.

        Available for Horizon 8 2012 and later."""
        response = _get(
            f'{self.url}/rest/federation/v1/pods', verify=False, timeout=REQUEST_TIMEOUT,
            headers=self.access_token)
        _check_response(response)
        return response.json()

    def get_pod(self, pod_id: str) -> dict:
        """Retrieves a given pod from the pod federation.

        Requires pod_id as a string
        Available for Horizon 8 2012 and later."""
        response = _get(
            f'{self.url}/rest/federation/v1/pods/{pod_id}', verify=False, timeout=REQUEST_TIMEOUT,
            headers=self.access_token)
        _check_response(response)
        return response.json()

    def get_pod_endpoints(self, pod_id: str) -> list:
        """Lists all the pod endpoints for the given pod.

        Requires pod_id as a string
        Available for Horizon 8 2012 and later."""
        response = _get(
            f'{self.url}/rest/federation/v1/pods/{pod_id}/endpoints', verify=False,
            timeout=REQUEST_TIMEOUT, headers=self.access_token)
        _check_response(response)
        return response.json()

    def get_pod_endpoint(self, pod_id: str, endpoint_id: str) -> dict:
        """Lists all the pod endpoints for the given pod.

        Requires pod_id and endpoint_id as a string
        Available for Horizon 8 2012 and later."""
        response = _get(
            f'{self.url}/rest/federation/v1/pods/{pod_id}/endpoints/{endpoint_id}',
            verify=False, timeout=REQUEST_TIMEOUT, headers=self.access_token)
        _check_response(response)
        return response.json()


class Monitor:
    def __init__(self, url: str, access_token: dict):
        """Default object for the monitor class used for the monitoring of the various VMware Horiozn services."""
        self.url = url
        self.access_token = access_token

    def connection_servers(self) -> list:
        """Lists monitoring information related to Connection Servers of the environment.

        Available for Horizon 7.10 and later."""
        response = _get(
            f'{self.url}/rest/monitor/v3/connection-servers', verify=False,
            timeout=REQUEST_TIMEOUT, headers=self.access_token)
        _check_response(response)
        return response.json()


class Config:
    def __init__(self, url: str, access_token: dict):
        """Default object for the config class used for the general configuration of VMware Horizon."""
        self.url = url
        self.access_token = access_token

    def get_environment_properties(self) -> dict:
        """Retrieves the environment settings.

        Available for Horizon 7.12 and later."""
        response = _get(
            f'{self.url}/rest/config/v2/environment-properties', verify=False,
            timeout=REQUEST_TIMEOUT, headers=self.access_token)
        _check_response(response)
        return response.json()

    def get_virtual_centers(self) -> list:
        """Lists Virtual Centers configured in the environment.

        Available for Horizon 7.11 and later."""
        response = _get(
            f'{self.url}/rest/config/v6/virtual-centers', verify=False,
            timeout=REQUEST_TIMEOUT, headers=self.access_token)
        _check_response(response)
        return response.json()


class Inventory:
    def __init__(self, url: str, access_token: dict):
        """Default object for the pools class where all Desktop Pool Actions will be performed."""
        self.url = url
        self.access_token = access_token

    def get_desktop_pools(self, maxpagesize: int = 1000, filter: dict = "") -> list:
        """Returns a list of dictionaries with all available Desktop Pools.

        For information on filtering see https://vdc-download.vmware.com/vmwb-repository/dcr-public/f92cce4b-9762-4ed0-acbd-f1d0591bd739/235dc19c-dabd-43f2-8d38-8a7a333e914e/HorizonServerRESTPaginationAndFilterGuide.doc
        Available for Horizon 8 2111 and later."""

        def int_get_desktop_pools(page: int) -> requests.Response:
            if filter != "":
                filter_url = urllib.parse.quote(json.dumps(filter, separators=(', ', ':')))
                url = f'{self.url}/rest/inventory/v8/desktop-pools?filter={filter_url}&page={page}&size={maxpagesize}'
            else:
                url = f'{self.url}/rest/inventory/v8/desktop-pools?page={page}&size={maxpagesize}'
            response = _get(url, verify=False, timeout=REQUEST_TIMEOUT, headers=self.access_token)
            _check_response(response)
            return response

        maxpagesize = min(maxpagesize, 1000)
        page = 1
        response = int_get_desktop_pools(page)
        results = response.json()
        while 'HAS_MORE_RECORDS' in response.headers:
            page += 1
            response = int_get_desktop_pools(page)
            results += response.json()
        return results if isinstance(results, list) else [results]

    def get_desktop_pool(self, desktop_pool_id: str) -> dict:
        """Gets the Desktop Pool information.

        Requires id of a desktop pool
        Available for Horizon 8 2111 and later."""
        response = _get(
            f'{self.url}/rest/inventory/v8/desktop-pools/{desktop_pool_id}', verify=False,
            timeout=REQUEST_TIMEOUT, headers=self.access_token)
        _check_response(response)
        return response.json()

    def get_farms(self, maxpagesize: int = 1000, filter: dict = "") -> list:
        """Lists the Farms in the environment.

        For information on filtering see https://vdc-download.vmware.com/vmwb-repository/dcr-public/f92cce4b-9762-4ed0-acbd-f1d0591bd739/235dc19c-dabd-43f2-8d38-8a7a333e914e/HorizonServerRESTPaginationAndFilterGuide.doc
        Available for Horizon 8 2111 and later."""

        def int_get_farms(page: int) -> requests.Response:
            if filter != "":
                filter_url = urllib.parse.quote(json.dumps(filter, separators=(', ', ':')))
                url = f'{self.url}/rest/inventory/v7/farms?filter={filter_url}&page={page}&size={maxpagesize}'
            else:
                url = f'{self.url}/rest/inventory/v7/farms?page={page}&size={maxpagesize}'
            response = _get(url, verify=False, timeout=REQUEST_TIMEOUT, headers=self.access_token)
            _check_response(response)
            return response

        maxpagesize = min(maxpagesize, 1000)
        page = 1
        response = int_get_farms(page)
        results = response.json()
        while 'HAS_MORE_RECORDS' in response.headers:
            page += 1
            response = int_get_farms(page)
            results += response.json()
        return results if isinstance(results, list) else [results]

    def get_farm(self, farm_id: str) -> dict:
        """Gets the Farm information.

        Requires id of a RDS Farm
        Available for Horizon 8 2103 and later."""
        response = _get(
            f'{self.url}/rest/inventory/v7/farms/{farm_id}', verify=False,
            timeout=REQUEST_TIMEOUT, headers=self.access_token)
        _check_response(response)
        return response.json()

    def desktop_pool_push_image(self, desktop_pool_id: str, start_time: str = None, compute_profile_num_cores_per_socket: int = None, compute_profile_num_cpus: int = None, compute_profile_ram_mb: int = None, machine_ids: list = None, im_stream_id: str = None, im_tag_id: str = None, parent_vm_id: str = None, snapshot_id: str = None, logoff_policy: str = "WAIT_FOR_LOGOFF", stop_on_first_error: bool = True, selective_push_image: bool = False, add_virtual_tpm: bool = False):
        """Schedule/reschedule a request to update the image in an instant clone desktop pool"""
        headers = self.access_token
        headers["Content-Type"] = 'application/json'
        data = {}
        data["add_virtual_tpm"] = add_virtual_tpm
        if compute_profile_num_cores_per_socket is not None:
            data["compute_profile_num_cores_per_socket"] = int(compute_profile_num_cores_per_socket)
        if compute_profile_num_cpus is not None:
            data["compute_profile_num_cpus"] = int(compute_profile_num_cpus)
        if compute_profile_ram_mb is not None:
            data["compute_profile_ram_mb"] = int(compute_profile_ram_mb)
        if im_stream_id is not None and im_tag_id is not None:
            data["im_stream_id"] = im_stream_id
            data["im_tag_id"] = im_tag_id
        data["logoff_policy"] = logoff_policy
        if machine_ids is not None:
            data["machine_ids"] = machine_ids
        if parent_vm_id is not None and snapshot_id is not None:
            data["parent_vm_id"] = parent_vm_id
            data["snapshot_id"] = snapshot_id
        data["selective_push_image"] = selective_push_image
        data["start_time"] = start_time if start_time is not None else time.time()
        data["stop_on_first_error"] = stop_on_first_error
        response = _post(
            f'{self.url}/rest/inventory/v2/desktop-pools/{desktop_pool_id}/action/schedule-push-image',
            verify=False, timeout=REQUEST_TIMEOUT, headers=headers, data=json.dumps(data))
        _check_response(response)

    def cancel_desktop_pool_push_image(self, desktop_pool_id: str):
        """Cancels pending image.

        Available for Horizon 8 2012 and later."""
        response = _post(
            f'{self.url}/rest/inventory/v1/desktop-pools/{desktop_pool_id}/action/cancel-scheduled-push-image',
            verify=False, timeout=REQUEST_TIMEOUT, headers=self.access_token)
        _check_response(response, ok_status=204)

    def promote_pending_desktop_pool_image(self, desktop_pool_id: str):
        """promotes secondary image."""
        response = _post(
            f'{self.url}/rest/inventory/v1/desktop-pools/{desktop_pool_id}/action/promote-pending-image',
            verify=False, timeout=REQUEST_TIMEOUT, headers=self.access_token)
        _check_response(response, ok_status=204)

    def apply_pending_desktop_pool_image(self, desktop_pool_id: str, machine_ids: list, pending_image: bool):
        """applies secondary image to selected machines."""
        headers = self.access_token
        headers["Content-Type"] = 'application/json'
        params = {'pending_image': "true" if pending_image else "false"}
        response = _post(
            f'{self.url}/rest/inventory/v1/desktop-pools/{desktop_pool_id}/action/apply-image?',
            verify=False, timeout=REQUEST_TIMEOUT, headers=headers, json=machine_ids, params=params)
        _check_response(response)

    def get_machines(self, maxpagesize: int = 1000, filter: dict = "") -> list:
        """Lists the Machines in the environment.

        For information on filtering see https://vdc-download.vmware.com/vmwb-repository/dcr-public/f92cce4b-9762-4ed0-acbd-f1d0591bd739/235dc19c-dabd-43f2-8d38-8a7a333e914e/HorizonServerRESTPaginationAndFilterGuide.doc
        """

        def int_get_machines(page: int) -> requests.Response:
            if filter != "":
                filter_url = urllib.parse.quote(json.dumps(filter, separators=(', ', ':')))
                url = f'{self.url}/rest/inventory/v5/machines?filter={filter_url}&page={page}&size={maxpagesize}'
            else:
                url = f'{self.url}/rest/inventory/v5/machines?page={page}&size={maxpagesize}'
            response = _get(url, verify=False, timeout=REQUEST_TIMEOUT, headers=self.access_token)
            _check_response(response)
            return response

        maxpagesize = min(maxpagesize, 1000)
        page = 1
        response = int_get_machines(page)
        results = response.json()
        while 'HAS_MORE_RECORDS' in response.headers:
            page += 1
            response = int_get_machines(page)
            results += response.json()
        return results

    def get_rds_servers(self, maxpagesize: int = 1000, filter: dict = "") -> list:
        """Lists the RDS Servers in the environment.

        For information on filtering see https://vdc-download.vmware.com/vmwb-repository/dcr-public/f92cce4b-9762-4ed0-acbd-f1d0591bd739/235dc19c-dabd-43f2-8d38-8a7a333e914e/HorizonServerRESTPaginationAndFilterGuide.doc
        Available for Horizon 8 2012 and later."""

        def int_get_rds_servers(page: int) -> requests.Response:
            if filter != "":
                filter_url = urllib.parse.quote(json.dumps(filter, separators=(', ', ':')))
                url = f'{self.url}/rest/inventory/v2/rds-servers?filter={filter_url}&page={page}&size={maxpagesize}'
            else:
                url = f'{self.url}/rest/inventory/v2/rds-servers?page={page}&size={maxpagesize}'
            response = _get(url, verify=False, timeout=REQUEST_TIMEOUT, headers=self.access_token)
            _check_response(response)
            return response

        maxpagesize = min(maxpagesize, 1000)
        page = 1
        response = int_get_rds_servers(page)
        results = response.json()
        while 'HAS_MORE_RECORDS' in response.headers:
            page += 1
            response = int_get_rds_servers(page)
            results += response.json()
        return results

    def get_rds_server(self, rds_server_id: str) -> dict:
        """Gets the RDS Server information.

        Available for Horizon 8 2012 and later."""
        response = _get(
            f'{self.url}/rest/inventory/v2/rds-servers/{rds_server_id}', verify=False,
            timeout=REQUEST_TIMEOUT, headers=self.access_token)
        _check_response(response)
        return response.json()

    def rds_farm_schedule_maintenance(self, farm_id: str, next_scheduled_time: str = None, compute_profile_num_cores_per_socket: int = None, compute_profile_num_cpus: int = None, compute_profile_ram_mb: int = None, rds_server_ids: list = None, im_stream_id: str = None, im_tag_id: str = None, parent_vm_id: str = None, snapshot_id: str = None, logoff_policy: str = "WAIT_FOR_LOGOFF", stop_on_first_error: bool = True, selective_schedule_maintenance: bool = False, maintenance_mode: str = "IMMEDIATE", maintenance_period: str = None, maintenance_period_frequency: int = None, maintenance_start_index: int = None, maintenance_start_time: str = None):
        """Schedule/reschedule a request to update the image in an instant clone RDS Farm"""
        headers = self.access_token
        headers["Content-Type"] = 'application/json'
        data = {}
        if compute_profile_num_cores_per_socket is not None:
            data["compute_profile_num_cores_per_socket"] = int(compute_profile_num_cores_per_socket)
        if compute_profile_num_cpus is not None:
            data["compute_profile_num_cpus"] = int(compute_profile_num_cpus)
        if compute_profile_ram_mb is not None:
            data["compute_profile_ram_mb"] = int(compute_profile_ram_mb)
        if im_stream_id is not None and im_tag_id is not None:
            data["im_stream_id"] = im_stream_id
            data["im_tag_id"] = im_tag_id
        data["logoff_policy"] = logoff_policy
        data["maintenance_mode"] = maintenance_mode
        data["next_scheduled_time"] = next_scheduled_time if next_scheduled_time is not None else time.time()
        if parent_vm_id is not None and snapshot_id is not None:
            data["parent_vm_id"] = parent_vm_id
            data["snapshot_id"] = snapshot_id
        if rds_server_ids is not None:
            data["rds_server_ids"] = rds_server_ids
        if maintenance_mode == "RECURRING":
            data["recurring_maintenance_settings"] = {
                "maintenance_period": maintenance_period,
                "maintenance_period_frequency": maintenance_period_frequency,
                "start_index": maintenance_start_index,
                "start_time": maintenance_start_time,
            }
        data["selective_schedule_maintenance"] = selective_schedule_maintenance
        data["stop_on_first_error"] = stop_on_first_error
        response = _post(
            f'{self.url}/rest/inventory/v2/farms/{farm_id}/action/schedule-maintenance',
            verify=False, timeout=REQUEST_TIMEOUT, headers=headers, data=json.dumps(data))
        _check_response(response)

    def cancel_rds_farm_push_image(self, farm_id: str):
        """Cancels pending rds image.

        Available for Horizon 8 2012 and later."""
        headers = self.access_token
        headers["Content-Type"] = 'application/json'
        response = _post(
            f'{self.url}/rest/inventory/v1/farms/{farm_id}/action/cancel-scheduled-maintenance',
            verify=False, timeout=REQUEST_TIMEOUT,
            json={'maintenance_mode': 'IMMEDIATE'}, headers=headers)
        _check_response(response, ok_status=204)

    def promote_pending_rds_farm_image(self, farm_id: str):
        """promotes secondary rds image."""
        response = _post(
            f'{self.url}/rest/inventory/v1/farms/{farm_id}/action/promote-pending-image',
            verify=False, timeout=REQUEST_TIMEOUT, headers=self.access_token)
        _check_response(response, ok_status=204)

    def apply_pending_rds_farm_image(self, farm_id: str, machine_ids: list, pending_image: bool):
        """applies secondary image to selected rds machines."""
        headers = self.access_token
        headers["Content-Type"] = 'application/json'
        params = {'pending_image': "true" if pending_image else "false"}
        response = _post(
            f'{self.url}/rest/inventory/v1/farms/{farm_id}/action/apply-image?',
            verify=False, timeout=REQUEST_TIMEOUT, headers=headers, json=machine_ids, params=params)
        _check_response(response)

    def set_desktop_pool_provisioning(self, pool_data: dict, enable: bool):
        """Enables or disables provisioning for a desktop pool."""
        spec = {
            'cloud_assigned': pool_data.get('cloud_assigned', False),
            'cloud_managed': pool_data.get('cloud_managed', False),
            'display_assigned_machine_name': pool_data.get('display_assigned_machine_name', False),
            'display_machine_alias': pool_data.get('display_machine_alias', False),
            'display_name': pool_data.get('display_name', ''),
            'enable_client_restrictions': pool_data.get('enable_client_restrictions', False),
            'enabled': pool_data.get('enabled', True),
            'enable_provisioning': enable,
        }
        self.update_desktop_pool(spec, pool_data['id'])

    def set_farm_provisioning(self, farm_data: dict, enable: bool):
        """Enables or disables provisioning for an RDS farm."""
        af = farm_data.get('automated_farm_settings', {})
        spec = {
            'access_group_id': farm_data.get('access_group_id', ''),
            'display_name': farm_data.get('display_name', ''),
            'display_protocol_settings': farm_data.get('display_protocol_settings', {}),
            'enabled': farm_data.get('enabled', True),
            'load_balancer_settings': farm_data.get('load_balancer_settings', {}),
            'server_error_threshold': farm_data.get('server_error_threshold', 0),
            'session_settings': farm_data.get('session_settings', {}),
            'use_custom_script_for_load_balancing': farm_data.get('use_custom_script_for_load_balancing', False),
            'automated_farm_settings': {**af, 'enable_provisioning': enable},
        }
        self.update_farm(spec, farm_data['id'])

    def update_desktop_pool(self, pool_data: dict, desktop_pool_id: str):
        """Updates a Desktop Pool's configuration.

        Requires pool_data as a dict (DesktopPoolUpdateSpecV3).
        Available for Horizon 8 2111 and later."""
        headers = {**self.access_token, "Content-Type": "application/json"}
        response = _put(
            f'{self.url}/rest/inventory/v8/desktop-pools/{desktop_pool_id}',
            verify=False, timeout=REQUEST_TIMEOUT, headers=headers, data=json.dumps(pool_data))
        _check_response(response, ok_status=204)

    def update_farm(self, farm_data: dict, farm_id: str):
        """Updates a Farm's configuration.

        Requires farm_data as a dict (FarmUpdateSpecV5).
        Available for Horizon 8 2111 and later."""
        headers = {**self.access_token, "Content-Type": "application/json"}
        response = _put(
            f'{self.url}/rest/inventory/v7/farms/{farm_id}',
            verify=False, timeout=REQUEST_TIMEOUT, headers=headers, data=json.dumps(farm_data))
        _check_response(response, ok_status=204)


class External:
    def __init__(self, url: str, access_token: dict):
        """Default object for the External class for resources that are external to Horizon environment."""
        self.url = url
        self.access_token = access_token

    def get_datacenters(self, vcenter_id: str) -> list:
        """Lists all the datacenters of a vCenter.

        Requires vcenter_id
        Available for Horizon 7.12 and later."""
        response = _get(
            f'{self.url}/rest/external/v1/datacenters?vcenter_id={vcenter_id}', verify=False,
            timeout=REQUEST_TIMEOUT, headers=self.access_token)
        _check_response(response)
        results = response.json()
        return results if isinstance(results, list) else [results]

    def get_base_vms(self, vcenter_id: str, filter_incompatible_vms: bool = None, datacenter_id: str = "") -> list:
        """Lists all the VMs from a vCenter or a datacenter in that vCenter which may be suitable as snapshots for instant/linked clone desktop or farm creation.

        Requires vcenter_id, optionally datacenter_id and since Horizon 2012 filter_incompatible_vms (defaults to None / not sent).
        Available for Horizon 7.12 and later and Horizon 8 2012 for filter_incompatible_vms."""
        params = {"vcenter_id": vcenter_id}
        if isinstance(filter_incompatible_vms, bool):
            params["filter_incompatible_vms"] = "true" if filter_incompatible_vms else "false"
        if datacenter_id:
            params["datacenter_id"] = datacenter_id
        url = f'{self.url}/rest/external/v3/base-vms?' + urllib.parse.urlencode(params)
        response = _get(url, verify=False, timeout=REQUEST_TIMEOUT, headers=self.access_token)
        _check_response(response)
        results = response.json()
        return results if isinstance(results, list) else [results]

    def get_base_snapshots(self, vcenter_id: str, base_vm_id: str) -> list:
        """Lists all the VM snapshots from the vCenter for a given VM.

        Requires vcenter_id and base_vm_id
        Available for Horizon 8 2006."""
        response = _get(
            f'{self.url}/rest/external/v2/base-snapshots?base_vm_id={base_vm_id}&vcenter_id={vcenter_id}',
            verify=False, timeout=REQUEST_TIMEOUT, headers=self.access_token)
        _check_response(response)
        results = response.json()
        return results if isinstance(results, list) else [results]

    def get_network_labels(self, vcenter_id: str, host_or_cluster_id: str,
                           network_type: str = "") -> list:
        """Retrieves all network labels (portgroups) on the given host or cluster.

        Requires vcenter_id and host_or_cluster_id.
        Optional network_type: NETWORK, OPAQUE_NETWORK, DISTRUBUTED_VIRTUAL_PORT_GROUP.
        Available for Horizon 8 2006 and later."""
        params = f"host_or_cluster_id={host_or_cluster_id}&vcenter_id={vcenter_id}"
        if network_type:
            params += f"&network_type={network_type}"
        response = _get(
            f'{self.url}/rest/external/v1/network-labels?{params}',
            verify=False, timeout=REQUEST_TIMEOUT, headers=self.access_token)
        _check_response(response)
        results = response.json()
        return results if isinstance(results, list) else [results]

    def get_network_interface_cards(self, vcenter_id: str, base_vm_id: str,
                                    base_snapshot_id: str) -> list:
        """Returns network interface cards suitable for configuration on a desktop pool/farm.

        Requires vcenter_id, base_vm_id and base_snapshot_id.
        Available for Horizon 8 2006 and later."""
        response = _get(
            f'{self.url}/rest/external/v1/network-interface-cards'
            f'?base_snapshot_id={base_snapshot_id}&base_vm_id={base_vm_id}&vcenter_id={vcenter_id}',
            verify=False, timeout=REQUEST_TIMEOUT, headers=self.access_token)
        _check_response(response)
        results = response.json()
        return results if isinstance(results, list) else [results]
