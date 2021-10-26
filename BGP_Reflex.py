from _typeshed import Self
from librouteros import connect
import ast
import json
import firebase_admin
import requests
import paramiko
import os


def db_access():
    secret_file = open(f'secrect.json', 'w')
    secret_file.write(json.dumps(ast.literal_eval(os.environ['firebase_token'])))
    secret_file.close()
    # Fetch the service account key JSON file contents
    cred_path = os.getcwd() + '/secrect.json'
    cred = firebase_admin.credentials.Certificate(cred_path)
    # Initialize the app with a service account, granting admin privileges
    firebase_admin.initialize_app(cred, {
        'databaseURL': f'{os.environ["firebase_url"]}'
    })
    # As an admin, the app has access to read and write all data, regradless of Security Rules
    ref = firebase_admin.db.reference('/')
    ip_addr_list = ref.get()
    return ip_addr_list

class BGP_Reflex:
    def __init__(self) -> None:
        self.mikrotik_username= os.environ['mikrotik_username']
        self.mikrotik_password=os.environ['mikrotik_password']

    def check_availability(self,source_addr, dest_addr):
        api = connect(username=f'{self.mikrotik_username}', password=f'{self.mikrotik_password}', host=f'{self.source_addr}')
        params = {
            'src-address': f'{source_addr}',
            'address': f'{dest_addr}',
            'count': 20
        }
        result = api(cmd='/ping', **params)
        ping_arr = list(result)
        return ping_arr[len(ping_arr)-1]

    def bgp_react(self):
        ping_result = BGP_Reflex.check_availability()
        if ping_result['packet-loss'] >= 20:
            api_server_ip = os.environ['api_server_ip']
            url = f'http://{api_server_ip}:32598/fwb/bgpshutunshut'
            payload = {
                'source_addr': self.source_addr,
                'remote_addr': self.dest_addr,
                'username': self.mikrotik_username,
                'password': self.mikrotik_password,
                'deviceType': self,
                'toShutdown': self,
            }
            requests.post()

# check_availability('41.78.211.50','41.78.211.117')