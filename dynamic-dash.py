import json
import requests
import os
import re
import shutil
import ast
from json import loads
from functools import reduce  # forward compatibility for Python 3
import operator
import time

###### Load the config file
cwd = os.getcwd()
with open(f"{cwd}/config.txt", "r") as file:
  data = file.readlines()

arr_data = []
for i in data:
  arr_data.append(i.strip())

controller_host = arr_data[1].rsplit(' ', 1)[1]
username = arr_data[4].rsplit(' ', 1)[1]
accountname = arr_data[7].rsplit(' ', 1)[1]
password = arr_data[10].rsplit(' ', 1)[1]
selectedNamespace = arr_data[13].rsplit(' ', 1)[1]
dash_template = arr_data[16].rsplit(' ', 1)[1]

##### Get CSRF Token to access Alert API
url_auth = f"http://{controller_host}:8090/controller/auth?action=login"
headers = {'Content-Type': 'application/json'}
r = requests.get(url_auth, auth=(f'{username}@{accountname}', password), headers=headers)
data_cookites = r.cookies.get_dict()
jsessionid = data_cookites['JSESSIONID']
csrf_token = data_cookites['X-CSRF-TOKEN']


###### Collect latest server entity (Server, Pod, Container)
url_sim = f"http://{controller_host}:8090/controller/sim/v2/user/machines"
payload = {}
headers = {
    'Content-Type': 'application/json;charset=UTF-8',
    'X-CSRF-TOKEN': csrf_token,
    'Authorization': 'Basic dGNhZG1pbkBjdXN0b21lcjE6R29vZDJkYXk=',
    'Cookie': f'X-CSRF-TOKEN={csrf_token}; JSESSIONID={jsessionid}'
}
response = requests.request("GET", url_sim, headers=headers, data=payload)
string = response.content.decode('utf-8')
list_d = json.loads(string)
print(f"Status Code: {response.status_code}")
print(f"Number of Entity: {(len(list_d))}")
with open(f"{cwd}/entity-response.json", "w+") as file:
	file.write(string)


##### Search Pods in the selected Namespace
# with open(f"{cwd}/entity-response.json", "r") as file:
# 	d_input = json.loads(file.read())

cwd = os.getcwd()

list_all_data = []

# def getFromDict(dataDict, mapList):
#     return reduce(operator.getitem, mapList, dataDict)

# def setInDict(dataDict, mapList, value):
#     getFromDict(dataDict, mapList[:-1])[mapList[-1]] = value

# for i in range(len(list_d)):
#     b = getFromDict(list_d[i], ["properties", "Container|K8S|Namespace"])
#     print(f"Test: {b}")

try:
    for i in range(len(list_d)):
        check = list_d[i].get('properties', {}).get('Container|K8S|Namespace', None)
        if (list_d[i]['hierarchy'] == []):
            machaine_hostname = (list_d[i]['hostId'])
            list_all_data.append(f"{machaine_hostname}")
        elif (list_d[i]['hierarchy']) and (check != None):
            namespace = (list_d[i]['properties']['Container|K8S|Namespace'])
            podname = (list_d[i]['properties']['Container|K8S|PodName'])
            list_all_data.append(f"{namespace}/{podname}")
            list_all_data.append(list_d[i]['hostId'])
        else:
            containername = (list_d[i]['hostId'])
            list_all_data.append(f"{containername}")
except Exception as e:
    pass

print(f"List of All Enitites: {list_all_data}")


list_latest_data = []
try:
    for i in range(len(list_d)):
        check = list_d[i].get('properties', {}).get('Container|K8S|Namespace', None)
        if (list_d[i]['hierarchy']) and (check != None) and ((list_d[i]['properties']['Container|K8S|Namespace']) == selectedNamespace):
            namespace = (list_d[i]['properties']['Container|K8S|Namespace'])
            podname = (list_d[i]['properties']['Container|K8S|PodName'])
            list_latest_data.append(f"{namespace}/{podname}")
        else:
            None
except Exception as e:
    pass

print(f"List of the latest selected Namespace Enitites: {list_latest_data}")

##### Compare Pods between new pods and existing pods
writepath = f"{cwd}/entity-based.json"
mode = 'r+' if os.path.exists(writepath) else 'w+'
with open(writepath, mode) as f:
	string_based_data = f.read()
	list_based_data = []
	if string_based_data:
		list_based_data = ast.literal_eval(string_based_data)
	else:
		None
print(f"List of the previous selected Namespace Enitites: {list_based_data}")
list_add_data = list(set(list_latest_data) - set(list_based_data))
list_remove_data = list(set(list_based_data) - set(list_latest_data))

# Summary of Pods to be added and Pods to be removed
print(f"List of ADDED entities: {list_add_data}")
print(f"List of REMOVED entities: {list_remove_data}")



##### Write the lastest Pods information to the test-entity-based.json
with open(f"{cwd}/entity-based.json", "w") as new:
  new.seek(0)
  new.write(json.dumps(list_latest_data))


# add_list_data = ["gaming5/xxx1", "gaming5/xxx2", "gaming5/xxx3"]
# # remove_list_data = []
# remove_list_data = ["gaming4/yyyyyyyyyyy"]

#### Add and Remove
with open(dash_template, 'r') as f:
    dash_data = json.loads(f.read())
    if len(list_add_data) != 0:
        cpu_data = dash_data['widgetTemplates'][0]['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate']['entityMatchCriteria']['entityNames']
        for i in list_add_data:
            add = {"applicationName": "Server & Infrastructure Monitoring", "entityType": "APPLICATION_COMPONENT_NODE","entityName": i, "scopingEntityType": "APPLICATION_COMPONENT", "scopingEntityName": "Root", "subtype": None}
            cpu_data.append(add)
            # print(cpu_data)
        print("Add new entity to CPU Utilization Widget Successfully")
        mem_data = dash_data['widgetTemplates'][1]['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate']['entityMatchCriteria']['entityNames']
        for i in list_add_data:
            add = {"applicationName": "Server & Infrastructure Monitoring", "entityType": "APPLICATION_COMPONENT_NODE","entityName": i, "scopingEntityType": "APPLICATION_COMPONENT", "scopingEntityName": "Root", "subtype": None}
            mem_data.append(add)
            # print(mem_data)
        print("Add new entity to Mem Usage Widget Successfully")

        if len(list_remove_data) != 0:
            try:
                rcpu_data = dash_data['widgetTemplates'][0]['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate']['entityMatchCriteria']['entityNames']
                for i in list_remove_data:
                    rm = {"applicationName": "Server & Infrastructure Monitoring", "entityType": "APPLICATION_COMPONENT_NODE","entityName": i, "scopingEntityType": "APPLICATION_COMPONENT", "scopingEntityName": "Root", "subtype": None}
                    rcpu_data.remove(rm)
                # print(rcpu_data)
                print("Remove old entity to CPU Utilization Widget Successfully")
                
                rmem_data = dash_data['widgetTemplates'][1]['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate']['entityMatchCriteria']['entityNames']
                for i in list_remove_data:
                    rm = {"applicationName": "Server & Infrastructure Monitoring", "entityType": "APPLICATION_COMPONENT_NODE","entityName": i, "scopingEntityType": "APPLICATION_COMPONENT", "scopingEntityName": "Root", "subtype": None}
                    rmem_data.remove(rm)
                # print(rmem_data)
                print("Remove old entity to Mem Usage Widget Successfully")
            except Exception as e:
                print(f"Error: {e}")
        else:
            None
        
    elif (len(list_add_data) == 0) and (len(list_remove_data) != 0):
        try:
            rcpu_data = dash_data['widgetTemplates'][0]['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate']['entityMatchCriteria']['entityNames']
            for i in list_remove_data:
                rm = {"applicationName": "Server & Infrastructure Monitoring", "entityType": "APPLICATION_COMPONENT_NODE", "entityName": i, "scopingEntityType": "APPLICATION_COMPONENT", "scopingEntityName": "Root", "subtype": None}
                rcpu_data.remove(rm)
            # print(rcpu_data)
            print("Remove old entity to CPU Utilization Widget Successfully")
            
            rmem_data = dash_data['widgetTemplates'][1]['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate']['entityMatchCriteria']['entityNames']
            for i in list_remove_data:
                rm = {"applicationName": "Server & Infrastructure Monitoring", "entityType": "APPLICATION_COMPONENT_NODE", "entityName": i, "scopingEntityType": "APPLICATION_COMPONENT", "scopingEntityName": "Root", "subtype": None}
                rmem_data.remove(rm)
            # print(rmem_data)
            print("Remove old entity to Mem Usage Widget Successfully")
        except Exception as e:
            print(f"Error: {e}")
    
    else:
        None
    
    writepath = f"{cwd}/dynamic-dash-out.json"
    mode = 'r+' if os.path.exists(writepath) else 'w+'
    with open(writepath, mode) as file:
        file.seek(0)
        file.write(json.dumps(dash_data))
    
with open(dash_template, 'w+') as f2:
    f2.seek(0)
    f2.write(json.dumps(dash_data))

    
###### Get the list of Dashboard
url_dash = f"http://{controller_host}:8090/controller/restui/dashboards/getAllDashboardsByType/false"
payload = {}
headers = {
    'Content-Type': 'application/json;charset=UTF-8',
    'X-CSRF-TOKEN': csrf_token,
    'Authorization': 'Basic dGNhZG1pbkBjdXN0b21lcjE6R29vZDJkYXk=',
    'Cookie': f'X-CSRF-TOKEN={csrf_token}; JSESSIONID={jsessionid}'
}

response = requests.request("GET", url_dash, headers=headers, data=payload)
print(response.status_code)
string = response.content.decode('utf-8')
list_dash_new = json.loads(string)

for i in range(len(list_dash_new)):
    dashname = list_dash_new[i]['name']
    if dashname == "dynamic-dash-pod":
        dash_id = list_dash_new[i]['id']
        print(dash_id)
    else:
        None

print(dash_id)
url = f"http://{controller_host}:8090/controller/restui/dashboards/deleteDashboards?dashboardId={dash_id}"

payload = f"[{dash_id}]"
headers = {
    'Content-Type': 'application/json;charset=UTF-8',
    'X-CSRF-TOKEN': csrf_token,
    'Authorization': 'Basic dGNhZG1pbkBjdXN0b21lcjE6R29vZDJkYXk=',
    'Cookie': f'X-CSRF-TOKEN={csrf_token}; JSESSIONID={jsessionid}'
}
response = requests.request("POST", url, headers=headers, data=payload)
print(response.status_code)

time.sleep(5)

##### Import Dashboard.json
files = {
    'file': ('dynamic-dash-out.json', open('dynamic-dash-out.json', 'rb'))
}
response = requests.post(f'http://{controller_host}:8090/controller/CustomDashboardImportExportServlet',
                         files=files, auth=(f'{username}@{accountname}', password))
print(response.status_code)
