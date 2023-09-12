import json, requests, urllib, time
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
        if isinstance(results, list):
            results = results
        else:
            results = [results]
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
        if isinstance(results, list):
            results = results
        else:
            results = [results]
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

    def desktop_pool_push_image(self, desktop_pool_id:str, start_time:str=None,compute_profile_num_cores_per_socket:int=None,compute_profile_num_cpus:int=None,compute_profile_ram_mb:int=None,machine_ids:list=None, im_stream_id:str=None,im_tag_id:str=None,parent_vm_id:str=None,snapshot_id:str=None,logoff_policy:str="WAIT_FOR_LOGOFF", stop_on_first_error:bool=True,selective_push_image:bool=False, add_virtual_tpm:bool=False):
        """Schedule/reschedule a request to update the image in an instant clone desktop pool
        """
        headers = self.access_token
        headers["Content-Type"] = 'application/json'
        data = {}
        data["add_virtual_tpm"] = add_virtual_tpm
        if compute_profile_num_cores_per_socket != None:
            data["compute_profile_num_cores_per_socket"] = int(compute_profile_num_cores_per_socket)
        if compute_profile_num_cpus != None:
            data["compute_profile_num_cpus"] = int(compute_profile_num_cpus)
        if compute_profile_ram_mb != None:
            data["compute_profile_ram_mb"] = int(compute_profile_ram_mb)
        if im_stream_id != None and im_tag_id !=None:
            data["im_stream_id"] = im_stream_id
            data["im_tag_id"] = im_tag_id
        data["logoff_policy"] = logoff_policy
        if machine_ids != None:
            data["machine_ids"] = machine_ids
        if parent_vm_id != None and snapshot_id !=None:
            data["parent_vm_id"] = parent_vm_id
        data["selective_push_image"] = selective_push_image
        if parent_vm_id != None and snapshot_id !=None:
            data["snapshot_id"] = snapshot_id
        if start_time != None:
            data["start_time"]= start_time
        else:
            data["start_time"]= time.time()
        data["stop_on_first_error"] = stop_on_first_error
        json_data = json.dumps(data)
        response = requests.post(f'{self.url}/rest/inventory/v2/desktop-pools/{desktop_pool_id}/action/schedule-push-image', verify=False,  headers=headers, data = json_data)
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

    def cancel_desktop_pool_push_image(self, desktop_pool_id:str):
        """Promotes pending image.

        Available for Horizon 8 2012 and later."""
        response = requests.post(f'{self.url}/rest/inventory/v1/desktop-pools/{desktop_pool_id}/action/cancel-scheduled-push-image', verify=False,  headers=self.access_token)
        if response.status_code == 400:
            error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {error_message}")
        if response.status_code == 404:
            error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {error_message}")
        elif response.status_code == 403:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        elif response.status_code != 204:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        else:
            try:
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise "Error: " + str(e)

    def promote_pending_desktop_pool_image(self, desktop_pool_id:str):
        """Cancels push of new golden image.

        """
        response = requests.post(f'{self.url}/rest/inventory/v1/desktop-pools/{desktop_pool_id}/action/promote-pending-image', verify=False,  headers=self.access_token)
        if response.status_code == 400:
            error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {error_message}")
        if response.status_code == 404:
            error_message = (response.json())["error_message"]
            raise Exception(f"Error {response.status_code}: {error_message}")
        elif response.status_code == 403:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        elif response.status_code != 204:
            raise Exception(f"Error {response.status_code}: {response.reason}")
        else:
            try:
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise "Error: " + str(e)

    def apply_pending_desktop_pool_image(self, desktop_pool_id:str, machine_ids:list,pending_image:bool):
        """Cancels push of new golden image.

        """
        headers = self.access_token
        headers["Content-Type"] = 'application/json'
        if pending_image == True:
            pending_image="true"
        else:
            pending_image="false"
        params = {
            'pending_image': pending_image
        }
        response = requests.post(f'{self.url}/rest/inventory/v1/desktop-pools/{desktop_pool_id}/action/apply-image?', verify=False,  headers=headers, json=machine_ids, params=params)
        if response.status_code == 400:
            error_message = (response.json())["Bad Request"]
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

    def get_machines(self, maxpagesize:int=100, filter:dict="") -> list:
        """Lists the Machines in the environment.

        For information on filtering see https://vdc-download.vmware.com/vmwb-repository/dcr-public/f92cce4b-9762-4ed0-acbd-f1d0591bd739/235dc19c-dabd-43f2-8d38-8a7a333e914e/HorizonServerRESTPaginationAndFilterGuide.doc
        """

        def int_get_machines(self, page:int, maxpagesize: int, filter:dict="") ->list:
            if filter != "":
                filter_url = urllib.parse.quote(json.dumps(filter,separators=(', ', ':')))
                add_filter = f"{filter_url}"
                response = requests.get(f'{self.url}/rest/inventory/v3/machines?filter={add_filter}&page={page}&size={maxpagesize}', verify=False, headers=self.access_token)
            else:
                response = requests.get(f'{self.url}/rest/inventory/v3/machines?page={page}&size={maxpagesize}', verify=False, headers=self.access_token)
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
                    return response
        if maxpagesize > 1000:
            maxpagesize = 1000
        page = 1
        response = int_get_machines(self,page = page, maxpagesize= maxpagesize,filter = filter)
        results = response.json()
        while 'HAS_MORE_RECORDS' in response.headers:
            page += 1
            response = int_get_machines(self,page = page, maxpagesize= maxpagesize, filter = filter)
            results += response.json()
        return results

    def get_rds_servers(self, maxpagesize:int=100, filter:dict="") -> list:
        """Lists the RDS Servers in the environment.

        For information on filtering see https://vdc-download.vmware.com/vmwb-repository/dcr-public/f92cce4b-9762-4ed0-acbd-f1d0591bd739/235dc19c-dabd-43f2-8d38-8a7a333e914e/HorizonServerRESTPaginationAndFilterGuide.doc
        Available for Horizon 8 2012 and later."""

        def int_get_rds_servers(self, page:int, maxpagesize: int, filter:list="") ->list:
            if filter != "":
                add_filter = urllib.parse.quote(json.dumps(filter,separators=(', ', ':')))
                response = requests.get(f'{self.url}/rest/inventory/v1/rds-servers?filter={add_filter}&page={page}&size={maxpagesize}', verify=False, headers=self.access_token)
            else:
                response = requests.get(f'{self.url}/rest/inventory/v1/rds-servers?page={page}&size={maxpagesize}', verify=False, headers=self.access_token)
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
        response = int_get_rds_servers(self,page = page, maxpagesize= maxpagesize,filter = filter)
        results = response.json()
        while 'HAS_MORE_RECORDS' in response.headers:
            page += 1
            response = int_get_rds_servers(self,page = page, maxpagesize= maxpagesize, filter = filter)
            results += response.json()
        return results

    def get_rds_server(self, rds_server_id:str) -> dict:
        """Gets the RDS Server information.

        Available for Horizon 8 2012 and later."""
        response = requests.get(f'{self.url}/rest/inventory/v1/rds-servers/{rds_server_id}', verify=False,  headers=self.access_token)
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

    def rds_farm_schedule_maintenance(self, farm_id:str, next_scheduled_time:str=None,compute_profile_num_cores_per_socket:int=None,compute_profile_num_cpus:int=None,compute_profile_ram_mb:int=None,rds_server_ids:list=None, im_stream_id:str=None,im_tag_id:str=None,parent_vm_id:str=None,snapshot_id:str=None,logoff_policy:str="WAIT_FOR_LOGOFF", stop_on_first_error:bool=True,selective_schedule_maintenance:bool=False,maintenance_mode:str="IMMEDIATE", maintenance_period:str=None,maintenance_period_frequency:int=None,maintenance_start_index:int=None,maintenance_start_time:str=None):
        """Schedule/reschedule a request to update the image in an instant clone RDS Farm
        """
        headers = self.access_token
        headers["Content-Type"] = 'application/json'
        data = {}
        if compute_profile_num_cores_per_socket != None:
            data["compute_profile_num_cores_per_socket"] = int(compute_profile_num_cores_per_socket)
        if compute_profile_num_cpus != None:
            data["compute_profile_num_cpus"] = int(compute_profile_num_cpus)
        if compute_profile_ram_mb != None:
            data["compute_profile_ram_mb"] = int(compute_profile_ram_mb)
        if im_stream_id != None and im_tag_id !=None:
            data["im_stream_id"] = im_stream_id
            data["im_tag_id"] = im_tag_id
        data["logoff_policy"] = logoff_policy
        data["maintenance_mode"] = maintenance_mode

        if next_scheduled_time != None:
            data["next_scheduled_time"]= next_scheduled_time
        else:
            data["next_scheduled_time"]= time.time()
        if parent_vm_id != None and snapshot_id !=None:
            data["parent_vm_id"] = parent_vm_id
        if rds_server_ids != None:
            data["rds_server_ids"] = rds_server_ids
        if maintenance_mode == "RECURRING ":
            data["recurring_maintenance_settings"]["maintenance_period"] = maintenance_period
            data["recurring_maintenance_settings"]["maintenance_period_frequency"] = maintenance_period_frequency
            data["recurring_maintenance_settings"]["start_index"] = maintenance_start_index
            data["recurring_maintenance_settings"]["start_time"] = maintenance_start_time
        data["selective_schedule_maintenance"] = selective_schedule_maintenance
        if parent_vm_id != None and snapshot_id !=None:
            data["snapshot_id"] = snapshot_id
        data["stop_on_first_error"] = stop_on_first_error
        json_data = json.dumps(data)
        response = requests.post(f'{self.url}/rest/inventory/v2/farms/{farm_id}/action/schedule-maintenance', verify=False,  headers=headers, data = json_data)
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
                results=response.json()
                if isinstance(results, list):
                    results = results
                else:
                    results = [results]
                return results

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
                results=response.json()
                if isinstance(results, list):
                    results = results
                else:
                    results = [results]
                return results

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
                results=response.json()
                if isinstance(results, list):
                    results = results
                else:
                    results = [results]
                return results