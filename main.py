""" application loader for netbox-export-connections , for netbox -> sheets """
import os
import sys
from typing import Optional, List

ROOT_PATH = os.path.abspath( os.path.join( __file__, ".." ) )
if ROOT_PATH not in sys.path:
    sys.path.append( ROOT_PATH )


from pprint import pprint

from googleapiclient.discovery import build
from httplib2 import Http

import json
from oauth2client import file, client, tools

from classdef import *

d = NetboxRequest(NetboxQuery.DEVICE, {"id": 1531}, json_callback = Device.jsonToObj)

# print("-----instances----->")
# print(Device._instances)
# print("<-----instances-----")

# stash(Device)

# print("\n" * 10)

# unstash()

# print("-----instances----->")
# print(Device._instances)
# print("<-----instances-----")

# exit()

r = GridRange(1, 10, 1, 10)
brp = BandingProperties( headerColor = Color(50, 50, 50, 100),
                         firstBandColor = Color(100, 100, 100, 200),
                         secondBandColor = Color(200, 200, 200, 0) )

br = BandedRange(range = r, rowProperties=brp)


# rData = RowData([CellData(ExtendedValue(x)) for x in range(5) for y in range(10)])
# rData = RowData([CellData(ExtendedValue(x)) for x in range(10)])
interface_connections = InterfaceConnection.getInterfaceConnections(data_center='hkg1')
rowData = []
for ic in interface_connections:
    rowData.append(ic.getSheetRowData())
gData = GridData(r.startRowIndex, r.startColumnIndex, rowData)
# gData = GridData(0, 0, rData)

# s = Sheet( [gData], [br] )

# gdata = Sheet(7, 5)
# br = Sheet("three", "four")
# pprint(br)
# pprint(list(br))

ss = Spreadsheet(
    sheets=[Sheet([gData], [br])],
    properties=SpreadsheetProperties(title="look at me")
)
# ss = Spreadsheet([Sheet()])

pprint(ss, indent=2, compact=False )




# # stash()

# from pprint import pprint
# pprint(Devices._instances)
# inputs("Continue?")

spreadsheet_body = json.dumps(ss)
print(spreadsheet_body)
# pprint(json.loads(spreadsheet_body), indent=4)

# print(spreadsheet_body)




# Setup the Sheets API
SCOPES = 'https://www.googleapis.com/auth/drive'
store = file.Storage('credentials.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('sheets', 'v4', http=creds.authorize(Http()))

request = service.spreadsheets().create(body=ss)
# request = service.spreadsheets().create(body=spreadsheet_body)
response = request.execute()

# TODO: Change code below to process the `response` dict:
pprint(response)
