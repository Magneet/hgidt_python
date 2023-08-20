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
            
