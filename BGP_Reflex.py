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

def check_availability(source_addr, dest_addr):
    mikrotik_username= os.environ['mikrotik_username']
    mikrotik_password=os.environ['mikrotik_password']
    api = connect(username=f'{mikrotik_username}', password=f'{mikrotik_password}', host=f'{source_ip}')
    params = {
        'src-address': f'{source_addr}',
        'address': f'{dest_addr}',
        'count': 20
    }
    result = api(cmd='/ping', **params)
    ping_arr = list(result)
    print(ping_arr[len(ping_arr)-1] )



check_availability('41.78.211.50','41.78.211.117')