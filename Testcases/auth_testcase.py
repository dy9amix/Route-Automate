from librouteros import connect
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import paramiko
import ast
import json
import os

ssh_client=paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def db_access():
    secret_file = open(f'secrect.json', 'w')
    secret_file.write(json.dumps(ast.literal_eval(os.environ['firebase_token'])))
    secret_file.close()
    # Fetch the service account key JSON file contents
    cred_path = os.getcwd() + '/secrect.json'
    cred = credentials.Certificate(cred_path)
    # Initialize the app with a service account, granting admin privileges
    firebase_admin.initialize_app(cred, {
        'databaseURL': f'{os.environ["firebase_url"]}'
    })
    # As an admin, the app has access to read and write all data, regradless of Security Rules
    ref = db.reference('/')
    ip_addr_list = ref.get()
    return ip_addr_list

def test_api_access(ip_addr, usrname, passwd):
    print(f'Testing api access to {ip_addr}')
    api = connect(ip_addr, usrname, passwd)
    hostname = api(cmd='/system/identity/print')
    result = list(hostname)[0]['name']
    return f'API connection to {result} successfull'

def test_ssh_access(ip_addr, usrname, passwd):
    print(f'Testing SSH access to {ip_addr}')
    ssh_client.connect(hostname=f'{ip_addr}',username=f'{usrname}',password=f'{passwd}', port=2244)
    stdin,stdout,stderr = ssh_client.exec_command(f"system identity print")
    result = stdout.read().decode("utf-8").replace(" ", "").splitlines()[0]
    return f'SSH access to {result.split(":")[1]} successful'

pop_ips = db_access()
for ip in pop_ips:
  print(test_api_access(pop_ips[ip],os.environ['mikrotik_username'],os.environ['mikrotik_password']))
  print(test_ssh_access(pop_ips[ip],os.environ['mikrotik_username'],os.environ['mikrotik_password']))
