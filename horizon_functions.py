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