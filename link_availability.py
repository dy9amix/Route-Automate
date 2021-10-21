from librouteros import connect
import paramiko
import os

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