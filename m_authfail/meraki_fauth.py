import login
import requests, json
import datetime, sys, os, smtplib
import pandas as pd
from pandas import ExcelWriter
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.base import MIMEBase 
from email import encoders

# Wireless Health, List of all failed client connections in the last 24 hours.


def Failed_Connections(file_name):

    sites = pd.read_excel(w, sheet_name=None, dtype={'latencyMs':int})
    site_keys = sites.keys()

    results = []
    for office in site_keys:
        try:
            for failure in sites[office]['failureStep'].where(sites[office]['failureStep'] == 'auth').dropna():
                results.append(office)
        except KeyError:
            continue
        final_results = list(dict.fromkeys(results))
    print(final_results)
    print(len(final_results))

def get_network_name(network_id, networks):
    return [element for element in networks if network_id == element['id']][0]['name']

if __name__ == '__main__':
    try:
        import login
        (API_KEY, ORG_ID) = (login.api_key, login.org_id)
    except ImportError:
        API_KEY = input('Enter your Dashboard API key: ')
        ORG_ID = input('Enter your organization ID: ')
    session = requests.session()
    headers = {'X-Cisco-Meraki-API-Key': API_KEY, 'Content-Type': 'application/json'} 
    try:
        name = json.loads(session.get('https://api.meraki.com/api/v0/organizations/' + login.org_id, headers=headers).text)['name'] # gets name of organization
    except:   
        sys.exit('Incorrect API key or org ID, as no valid data returned') # breaks if ID can't be found

    
#----- log in statement breaks, and now we create variables for applicances.
    networks = json.loads(session.get('https://api.meraki.com/api/v0/organizations/' + login.org_id + '/networks', headers=headers).text) # layer 1 grabs networks
    inventory = json.loads(session.get('https://api.meraki.com/api/v0/organizations/' + login.org_id + '/inventory', headers=headers).text) # layer 2 pulls full inventory
    access_points = [device for device in inventory if device['model'][:2] in ('MR') and device['networkId'] is not None] # layer 3 grabs only mx equipment
    devices = [device for device in inventory if device not in access_points and device['networkId'] is not None] # layer 4 sources everything else
    
    today = datetime.date.today()
    w = pd.ExcelWriter('fauths'+str(today)+'.xlsx') # creates file name
    for access_point in access_points:
        device_name = json.loads(session.get('https://api.meraki.com/api/v0/networks/' + access_point['networkId'] + '/devices/' + access_point['serial'], headers=headers).text)['name']
        f_auth = json.loads(session.get('https://api.meraki.com/api/v1/networks/' + access_point['networkId'] + '/wireless/failedConnections?timespan=86400&ssid=0', headers=headers).text)
        try:
            print('Found appliance ' + device_name)
        except:
            print('Found appliance ' + access_point['serial'])
        df = pd.DataFrame(f_auth)
        df.to_excel(w, sheet_name=str(device_name), index=False)
        w.save()

    Failed_Connections(w)