import json, requests, urllib
from typing import get_args

class Connection:
    """The Connection class is used to handle connections and disconnections to and from the VMware Horizon REST API's"""
    def __init__(self, username: str, password: str, domain: str, url:str):
        """"The default object for the connection class needs to be created using username, password, domain and url in plain text."""
        self.username = username
        self.password = password
        self.domain = domain
        self.url = url
        self.access_token = ""
        self.refresh_token = ""

    def hv_connect(self):
        """Used to authenticate to the VMware Horizon REST API's"""
        headers = {
            'accept': '*/*',
            'Content-Type': 'application/json',
        }

        data = {"domain": self.domain, "password": self.password, "username": self.username}
        json_data = json.dumps(data)

        response = requests.post(f'{self.url}/rest/login', verify=False, headers=headers, data=json_data)
        if response.status_code == 400:
            error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {error_message}")
        elif response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        else:
            try:
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise Exception("Error: " + str(e))
            else:
                data = response.json()
                self.access_token = {
                    'accept': '*/*',
                    'Authorization': 'Bearer ' + data['access_token']
                }
                self.refresh_token = data['refresh_token']
                return self

    def hv_disconnect(self):
        """"Used to close close the connection with the VMware Horizon REST API's"""
        headers = {
            'accept': '*/*',
            'Content-Type': 'application/json',
        }
        data = {'refresh_token': self.refresh_token}
        json_data = json.dumps(data)
        response = requests.post(f'{self.url}/rest/logout', verify=False, headers=headers, data=json_data)
        if response.status_code == 400:
            error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {error_message}")
        elif response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        else:
            try:
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise Exception("Error: " + str(e))
            else:
                return response.status_code
            
    def hv_refresh(self):
        """"Used to close close the connection with the VMware Horizon REST API's"""
        headers = {
            'accept': '*/*',
            'Content-Type': 'application/json',
        }
        data = {'refresh_token': self.refresh_token}
        json_data = json.dumps(data)
        response = requests.post(f'{self.url}/rest/refresh', verify=False, headers=headers, data=json_data)
        if response.status_code == 400:
            error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {error_message}")
        elif response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        else:
            try:
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise Exception("Error: " + str(e))
            else:
                return response.status_code

class Federation:
    def __init__(self, url: str, access_token: dict):
        """Default object for the pools class where all Desktop Pool Actions will be performed."""
        self.url = url
        self.access_token = access_token

    def get_cloud_pod_federation(self) -> dict:
        """Retrieves the pod federation details.

        Available for Horizon 8 2012 and later."""
        response = requests.get(f'{self.url}/rest/federation/v1/cpa', verify=False,  headers=self.access_token)
        if response.status_code == 400:
            error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {error_message}")
        if response.status_code == 404:
            error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {error_message}")
        elif response.status_code == 403:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        elif response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        else:
            try:
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise "Error: " + str(e)
            else:
                return response.json()

    def get_pods(self) -> list:
        """Lists all the pods in the pod federation.

        Available for Horizon 8 2012 and later."""
        response = requests.get(f'{self.url}/rest/federation/v1/pods', verify=False,  headers=self.access_token)
        if response.status_code == 400:
            if "error_messages" in response.json():
                error_message = (response.json())["error_messages"]
            else:
                error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {error_message}")
        if response.status_code == 404:
            error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {error_message}")
        elif response.status_code == 403:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        elif response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        else:
            try:
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise "Error: " + str(e)
            else:
                return response.json()

    def get_pod(self, pod_id:str) -> dict:
        """Retrieves a given pod from the pod federation.

        Requires pod_id as a string
        Available for Horizon 8 2012 and later."""
        response = requests.get(f'{self.url}/rest/federation/v1/pods/{pod_id}', verify=False,  headers=self.access_token)
        if response.status_code == 400:
            if "error_messages" in response.json():
                error_message = (response.json())["error_messages"]
            else:
                error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {error_message}")
        if response.status_code == 404:
            error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {error_message}")
        elif response.status_code == 403:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        elif response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        else:
            try:
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise "Error: " + str(e)
            else:
                return response.json()
            
    def get_pod_endpoints(self, pod_id:str) -> list:
        """Lists all the pod endpoints for the given pod.

        Requires pod_id as a string
        Available for Horizon 8 2012 and later."""
        response = requests.get(f'{self.url}/rest/federation/v1/pods/{pod_id}/endpoints', verify=False,  headers=self.access_token)
        if response.status_code == 400:
            if "error_messages" in response.json():
                error_message = (response.json())["error_messages"]
            else:
                error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {error_message}")
        if response.status_code == 404:
            error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {error_message}")
        elif response.status_code == 403:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        elif response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        else:
            try:
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise "Error: " + str(e)
            else:
                return response.json()

    def get_pod_endpoint(self, pod_id:str, endpoint_id:str) -> dict:
        """Lists all the pod endpoints for the given pod.

        Requires pod_id and endpoint_id as a string
        Available for Horizon 8 2012 and later."""
        response = requests.get(f'{self.url}/rest/federation/v1/pods/{pod_id}/endpoints/{endpoint_id}', verify=False,  headers=self.access_token)
        if response.status_code == 400:
            if "error_messages" in response.json():
                error_message = (response.json())["error_messages"]
            else:
                error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {error_message}")
        if response.status_code == 404:
            error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {error_message}")
        elif response.status_code == 403:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        elif response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        else:
            try:
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise "Error: " + str(e)
            else:
                return response.json()

class Monitor:
    def __init__(self, url: str, access_token: dict):
        """Default object for the monitor class used for the monitoring of the various VMware Horiozn services."""
        self.url = url
        self.access_token = access_token

    def connection_servers(self) -> list:
        """Lists monitoring information related to Connection Servers of the environment.

        Available for Horizon 7.10 and later."""
        response = requests.get(f'{self.url}/rest/monitor/v2/connection-servers', verify=False,  headers=self.access_token)
        if response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        else:
            try:
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise "Error: " + str(e)
            else:
                return response.json()

class Config:
    def __init__(self, url: str, access_token: dict):
        """Default object for the config class used for the general configuration of VMware Horizon."""
        self.url = url
        self.access_token = access_token
        
    def get_environment_properties(self) -> dict:
        """Retrieves the environment settings.

        Available for Horizon 7.12 and later."""
        response = requests.get(f'{self.url}/rest/config/v2/environment-properties', verify=False,  headers=self.access_token)
        if response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        else:
            try:
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise "Error: " + str(e)
            else:
                return response.json()

    def get_virtual_centers(self) -> list:
        """Lists Virtual Centers configured in the environment.

        Available for Horizon 7.11 and later."""
        response = requests.get(f'{self.url}/rest/config/v2/virtual-centers', verify=False,  headers=self.access_token)
        if response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        else:
            try:
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise "Error: " + str(e)
            else:
                return response.json()

class Inventory:
    def __init__(self, url: str, access_token: dict):
        """Default object for the pools class where all Desktop Pool Actions will be performed."""
        self.url = url
        self.access_token = access_token
        
    def get_desktop_pools(self, maxpagesize:int=100, filter:dict="") -> list:
        """Returns a list of dictionaries with all available Desktop Pools. 

        For information on filtering see https://vdc-download.vmware.com/vmwb-repository/dcr-public/f92cce4b-9762-4ed0-acbd-f1d0591bd739/235dc19c-dabd-43f2-8d38-8a7a333e914e/HorizonServerRESTPaginationAndFilterGuide.doc
        Available for Horizon 8 2111 and later."""

        def int_get_desktop_pools(self, page:int, maxpagesize: int, filter:list="") ->list:
            if filter != "":
                filter_url = urllib.parse.quote(json.dumps(filter,separators=(', ', ':')))
                add_filter = f"?filter={filter_url}"
                response = requests.get(f'{self.url}/rest/inventory/v6/desktop-pools{add_filter}&page={page}&size={maxpagesize}', verify=False, headers=self.access_token)
            else:
                response = requests.get(f'{self.url}/rest/inventory/v6/desktop-pools?page={page}&size={maxpagesize}', verify=False, headers=self.access_token)
            if response.status_code == 400:
                if "error_messages" in response.json():
                    error_message = (response.json())["error_messages"]
                else:
                    error_message = (response.json())["error_message"]
                raise Exception(f"Error {response.status_code}: {error_message}")
            elif response.status_code != 200:
                raise Exception(f"Error {response.status_code}: {response.reason}")
            else:
                try:
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    raise "Error: " + str(e)
                else:
                    return response
        if maxpagesize > 1000:
            maxpagesize = 1000
        page = 1
        response = int_get_desktop_pools(self,page = page, maxpagesize= maxpagesize,filter = filter)
        results = response.json()
        while 'HAS_MORE_RECORDS' in response.headers:
            page += 1
            response = int_get_desktop_pools(self,page = page, maxpagesize= maxpagesize, filter = filter)
            results += response.json()
        return results

    def get_desktop_pool(self, desktop_pool_id: str) -> dict:
        """Gets the Desktop Pool information.

        Requires id of a desktop pool
        Available for Horizon 8 2111 and later."""
        response = requests.get(f'{self.url}/rest/inventory/v6/desktop-pools/{desktop_pool_id}', verify=False,  headers=self.access_token)
        if response.status_code == 400:
            error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {error_message}")
        elif response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        else:
            try:
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise "Error: " + str(e)
            else:
                return response.json()
            
    def get_farms(self, maxpagesize:int=100, filter:dict="") -> list:
        """Lists the Farms in the environment.

        For information on filtering see https://vdc-download.vmware.com/vmwb-repository/dcr-public/f92cce4b-9762-4ed0-acbd-f1d0591bd739/235dc19c-dabd-43f2-8d38-8a7a333e914e/HorizonServerRESTPaginationAndFilterGuide.doc
        Available for Horizon 8 2111 and later."""

        def int_get_farms_v3(self, page:int, maxpagesize: int, filter:list="") ->list:
            if filter != "":
                filter_url = urllib.parse.quote(json.dumps(filter,separators=(', ', ':')))
                add_filter = f"?filter={filter_url}"
                response = requests.get(f'{self.url}/rest/inventory/v4/farms{add_filter}&page={page}&size={maxpagesize}', verify=False, headers=self.access_token)
            else:
                response = requests.get(f'{self.url}/rest/inventory/v4/farms?page={page}&size={maxpagesize}', verify=False, headers=self.access_token)
            if response.status_code == 400:
                if "error_messages" in response.json():
                    error_message = (response.json())["error_messages"]
                else:
                    error_message = (response.json())["error_message"]
                raise Exception(f"Error {response.status_code}: {error_message}")
            elif response.status_code != 200:
                raise Exception(f"Error {response.status_code}: {response.reason}")
            else:
                try:
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    raise "Error: " + str(e)
                else:
                    return response
        if maxpagesize > 1000:
            maxpagesize = 1000
        page = 1
        response = int_get_farms_v3(self,page = page, maxpagesize= maxpagesize,filter = filter)
        results = response.json()
        while 'HAS_MORE_RECORDS' in response.headers:
            page += 1
            response = int_get_farms_v3(self,page = page, maxpagesize= maxpagesize, filter = filter)
            results += response.json()
        return results

    def get_farm(self, farm_id:str) -> dict:
        """Gets the Farm information.

        Requires id of a RDS Farm
        Available for Horizon 8 2103 and later."""
        response = requests.get(f'{self.url}/rest/inventory/v4/farms/{farm_id}', verify=False,  headers=self.access_token)
        if response.status_code == 400:
            error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {error_message}")
        elif response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        else:
            try:
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise "Error: " + str(e)
            else:
                return response.json()            

class External:
    def __init__(self, url: str, access_token: dict):
        """Default object for the External class for resources that are external to Horizon environment."""
        self.url = url
        self.access_token = access_token

    def get_datacenters(self, vcenter_id: str) -> list:
        """Lists all the datacenters of a vCenter.

        Requires vcenter_id
        Available for Horizon 7.12 and later."""

        response = requests.get(f'{self.url}/rest/external/v1/datacenters?vcenter_id={vcenter_id}', verify=False,  headers=self.access_token)
        if response.status_code == 400:
            error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {error_message}")
        elif response.status_code == 404:
            error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {response}")
        elif response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        else:
            try:
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise "Error: " + str(e)
            else:
                return response.json()

    def get_base_vms(self, vcenter_id : str,filter_incompatible_vms: bool="", datacenter_id:str="" ) -> list:
        """Lists all the VMs from a vCenter or a datacenter in that vCenter which may be suitable as snapshots for instant/linked clone desktop or farm creation.

        Requires vcenter_id, optionally datacenter id and since Horizon 2012 filter_incompatible_vms was added (defaults to false)
        Available for Horizon 7.12 and later and Horizon 8 2012 for filter_incompatible_vms."""

        if (filter_incompatible_vms == True or filter_incompatible_vms == False) and datacenter_id != "":
            response = requests.get(f'{self.url}/rest/external/v1/base-vms?datacenter_id={datacenter_id}&filter_incompatible_vms={filter_incompatible_vms}&vcenter_id={vcenter_id}', verify=False,  headers=self.access_token)
        elif (filter_incompatible_vms != True or filter_incompatible_vms != False) and datacenter_id != "":
            response = requests.get(f'{self.url}/rest/external/v1/base-vms?filter_incompatible_vms={filter_incompatible_vms}&vcenter_id={vcenter_id}', verify=False,  headers=self.access_token)
        elif datacenter_id != "":
            response = requests.get(f'{self.url}/rest/external/v1/base-vms?datacenter_id={datacenter_id}&vcenter_id={vcenter_id}', verify=False,  headers=self.access_token)
        else:
            response = requests.get(f'{self.url}/rest/external/v1/base-vms?vcenter_id={vcenter_id}', verify=False,  headers=self.access_token)
        if response.status_code == 400:
            error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {error_message}")
        elif response.status_code == 404:
            error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {response}")
        elif response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        else:
            try:
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise "Error: " + str(e)
            else:
                return response.json()

    def get_base_snapshots(self, vcenter_id : str, base_vm_id:str ) -> list:
        """Lists all the VM snapshots from the vCenter for a given VM.

        Requires vcenter_id and base_vm_id
        Available for Horizon 8 2006."""

        response = requests.get(f'{self.url}/rest/external/v2/base-snapshots?base_vm_id={base_vm_id}&vcenter_id={vcenter_id}', verify=False,  headers=self.access_token)

        if response.status_code == 400:
            error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {error_message}")
        elif response.status_code == 404:
            error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {response}")
        elif response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        else:
            try:
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise "Error: " + str(e)
            else:
                return response.json()