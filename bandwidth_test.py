import ipaddress
import ssl
import ast
import os
import urllib3
from librouteros import connect
import paramiko
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
from multiprocessing import Process
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import time
import datetime
import requests
import json

ssh_client=paramiko.SSHClient()
urllib3.disable_warnings()
ssl.get_default_verify_paths()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def runInParallel(fns):
  proc = []
  for fn in fns:
    func_vars = fn["args"]
    p = Process(target=fn["name"], args=(*func_vars,))
    p.start()
    proc.append(p)
  for p in proc:
    p.join()

def perform_speedtest(source_ip,dest_ip):
  mikrotik_username= os.environ['mikrotik_username']
  mikrotik_password=os.environ['mikrotik_password']
  api = connect(username=f'{mikrotik_username}', password=f'{mikrotik_password}', host=f'{source_ip}')
  params = {
      'address': f'{dest_ip}',
      'protocol': 'udp',
      'user': f'{mikrotik_username}',
      'password': f'{mikrotik_password}',
      'direction': 'both',
      'duration': 10
  }
  result = api(cmd='/tool/bandwidth-test', **params)
  speedtest_arr = list(result)

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

def send_teams_message():
  teams_webhook = os.environ['teams_webhook_url']
  webhook_url = f"{teams_webhook}"
  headers = {
    "Content-Type":"application/json"
  }
  payload = {
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions",
    "themeColor": "0076D7",
    "summary": f"Speedtest Result for POPs",
    "sections": [{
        "activityTitle": f"Speedtest Result for POPs",
        "activitySubtitle": "Powered by magic",
        "activityImage": "https://img.icons8.com/bubbles/100/000000/fortune-teller.png",
        "facts": [{
            "name":"Message",
            "value":"Speedtest complete. Results can be found at http://192.168.6.253:3000"
        }],
        "markdown": True
    }]
  }
  requests.post(webhook_url, data=json.dumps(payload), headers=headers)

def upload_to_influxdb(values):
  bucket = "Bandwidth"
  org = f"{os.environ['influxdb_organisation_id']}"
  token = f"{os.environ['influxdb_token']}"
  # Store the URL of your InfluxDB instance
  url="https://us-east-1-1.aws.cloud2.influxdata.com"

  client = influxdb_client.InfluxDBClient(
      url=url,
      token=token,
      org=org,
      verify_ssl=False
  )

  write_api = client.write_api(write_options=SYNCHRONOUS)
  p = influxdb_client.Point("POP Bandwidth").tag("POP", f"{values['Name']}").field("Upload", values["Upload"]).field("Download", values['Download'])
  write_api.write(bucket=bucket, org=org, record=p)

def convert_bandwidth(band_val):
  if band_val[len(band_val) - 4] == 'M':
    return float(band_val.split('M')[0])
  elif band_val[len(band_val) - 4] == 'G':
    return float(band_val.split('G')[0])*1000
  elif band_val[len(band_val) - 4] == 'k':
    return float(band_val.split('k')[0])/1000
  else:
    return 0

def check_interface_speed(mkt_ip):
  time.sleep(4)
  mikrotik_username= os.environ['mikrotik_username']
  mikrotik_password=os.environ['mikrotik_password']
  api = connect(username=f'{mikrotik_username}', password=f'{mikrotik_password}', host=f'{mkt_ip}')
  mkt_hostname = list(api.path('system', 'identity'))
  for address in list(api.path('ip', 'address')):
    network_address = address['address']
    if ipaddress.ip_address(f'{mkt_ip}') in ipaddress.ip_network(f'{network_address}', False).hosts():
      interface = address['interface']
      ssh_client.connect(hostname=f'{mkt_ip}',username=f'{mikrotik_username}',password=f'{mikrotik_password}', port=2244)
      stdin,stdout,stderr = ssh_client.exec_command(f"interface monitor-traffic {interface} once")
      lst = stdout.read().decode("utf-8").replace(" ", "").splitlines()
      download_lst = lst[2].split(":")
      upload_lst = lst[8].split(":")
      result_dict = {download_lst[0]: download_lst[1], upload_lst[0]:upload_lst[1]}
      speed_res = {
        "Name": mkt_hostname[0]['name'],
        "Upload": convert_bandwidth(result_dict['tx-bits-per-second']),
        "Download": convert_bandwidth(result_dict["rx-bits-per-second"])
      }
      print(speed_res)
      upload_to_influxdb(speed_res)
      break
    else:
      print(f"Unable to find speedtest interface for {mkt_hostname[0]['name']}")

pop_ips = db_access()
for ip in pop_ips:
  source = pop_ips['NOC']
  destination = pop_ips[ip]
  runInParallel([{'name':perform_speedtest, 'args':[f'{source}',f'{destination}']},
                  {'name':check_interface_speed, 'args':[f'{destination}']}])
send_teams_message()


