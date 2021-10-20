from librouteros import connect
import paramiko

def check_availability(source_addr, dest_addr):
    api = connect(username='backup', password='N3tb@ckup', host=f'{source_addr}')
    params = {
        'src-address': f'{source_addr}',
        'address': f'{dest_addr}',
        'count': 20
    }
    result = api(cmd='/ping', **params)
    ping_arr = list(result)
    print(ping_arr[len(ping_arr)-1]  )

check_availability('41.78.211.50','41.78.211.117')