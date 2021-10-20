import ipaddress
import ssl
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
api = connect(username='admin', password='!@#Supp0rt1', host='192.168.6.1')

mikrotik_ips = {
    "VI POP": "41.78.211.30",
    "IKOTA POP": "197.234.34.1",
    "LEKKI POP" : "192.168.27.1",
    "TANGO POP": "197.234.38.1",
    "IJORA POP": "192.168.4.52",
    "CRESTVIEW POP": "197.234.57.1",
    "MEDALLION POP" : "192.168.35.1",
    "ABUJA POP" : "41.78.209.11",
    "CRESTVIEW": "197.234.57.1",
    "RACKCENTER": "197.234.51.2",
    "SAKA 18": "192.168.5.4",
    "SAKA 25": "192.168.5.17",
    "ABUJA": "41.78.209.11",
    "PORT HARCOURT": "197.234.32.2"
}

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
    api = connect(username='backup', password='N3tb@ckup', host=f'{source_ip}')
    params = {
        'address': f'{dest_ip}',
        'protocol': 'udp',
        'user': 'backup',
        'password': 'N3tb@ckup',
        'direction': 'both',
        'duration': 10
    }
    result = api(cmd='/tool/bandwidth-test', **params)
    speedtest_arr = list(result)

def db_access():
    # Fetch the service account key JSON file contents
    cred_path = os.getcwd() + '/coollink-routing-automation-firebase-adminsdk-fveid-a72cbfd68c.json'
    cred = credentials.Certificate(cred_path)
    # Initialize the app with a service account, granting admin privileges
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://coollink-routing-automation-default-rtdb.europe-west1.firebasedatabase.app/'
    })
    # As an admin, the app has access to read and write all data, regradless of Security Rules
    ref = db.reference('/')
    ip_addr_list = ref.get()
    return ip_addr_list

def send_teams_message(message):
  webhook_url = "https://coollinkng0.webhook.office.com/webhookb2/b3918fce-f6ff-4d87-90d0-3139268b7667@ad7e4552-adb0-4afd-88ea-a790cf18973d/IncomingWebhook/17a9cfc229de42b2a9c5a442ab8b4130/3b5b7153-0d3d-4723-9e96-a258f998aaee"
  mikrotik_name = message["Name"]
  test_time = message["Time"]
  upload_speed = message["Upload"]
  download_speed = message["Download"]
  headers = {
    "Content-Type":"application/json"
  }
  payload = {
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions",
    "themeColor": "0076D7",
    "summary": f"Speedtest Result for {mikrotik_name}",
    "sections": [{
        "activityTitle": f"Speedtest Result for {mikrotik_name}",
        "activitySubtitle": "Powered by magic",
        "activityImage": "https://img.icons8.com/bubbles/100/000000/fortune-teller.png",
        "facts": [{
            "name": "Time",
            "value": f"{test_time}"
        }, {
            "name": "Upload",
            "value": f"{upload_speed}"
        }, {
            "name": "Download",
            "value": f"{download_speed}"
        }],
        "markdown": True
    }]
}
  requests.post(webhook_url, data=json.dumps(payload), headers=headers)

def upload_to_influxdb(values):
  bucket = "Bandwidth"
  org = "95d7a60f56db87a4"
  token = "l1yV1Rpqw70oMPW5rwPX_5YgsthJXf9624uNE0uVaLImzP0s9h08DcQQ6q2p3jpzRraydEQ2iHQ_8g2AQ66RLg=="
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
  else:
    return float(band_val.split('k')[0])/1000

def check_interface_speed(mkt_ip):
  time.sleep(4)
  api = connect(username='backup', password='N3tb@ckup', host=f'{mkt_ip}')
  for address in list(api.path('ip', 'address')):
    network_address = address['address']
    if ipaddress.ip_address(f'{mkt_ip}') in ipaddress.ip_network(f'{network_address}', False).hosts():
      interface = address['interface']
      ssh_client.connect(hostname=f'{mkt_ip}',username='backup',password='N3tb@ckup', port=2244)
      stdin,stdout,stderr = ssh_client.exec_command(f"interface monitor-traffic {interface} once")
      result_dic={}
      for line in iter(stdout.readline, ""):
        if line == '\r\n':
          continue
        else:
          lst = line.split(':')
          res_dct = {lst[i].strip(): lst[i + 1].strip().replace('\r\n',"") for i in range(0, len(lst), 2)}
          result_dic.update(res_dct)
      mkt_hostname = list(api.path('system', 'identity'))
      speed_res = {
        "Name": mkt_hostname[0]['name'],
        "Upload": convert_bandwidth(result_dic['tx-bits-per-second']),
        "Download": convert_bandwidth(result_dic["rx-bits-per-second"])
      }
      print(speed_res)
      upload_to_influxdb(speed_res)

pop_ips = db_access()
for ip in pop_ips:
  source = pop_ips['SOURCE']
  destination = pop_ips[ip]
  runInParallel([{'name':perform_speedtest, 'args':[f'{source}',f'{destination}']},
                  {'name':check_interface_speed, 'args':[f'{destination}']}])


