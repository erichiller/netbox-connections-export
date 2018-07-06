""" init.py """
import os
import sys

ROOT_PATH = os.path.abspath( os.path.join( __file__, "..", ".." ) )
if ROOT_PATH not in sys.path:
    sys.path.append( ROOT_PATH )

import logging

logging.getLogger().setLevel(0)
logging.debug("DEBUG SET")


import classdef.netbox as nb

# def test_InterfaceConnection_jsonToObj():

#     nb.getInterfaceConnections()





ic = nb.InterfaceConnection.getInterfaceConnections()

print(f"{'*'*25} Results {'*'*25}")
from pprint import pprint
pprint(ic, indent=2)
pprint(ic[0].__dict__, indent=2)

print(f"{'*'*25} InterfaceConnection.interface_a.device.datacenter {'*'*25}")
pprint(ic[0].interface_a.device.datacenter.name)

