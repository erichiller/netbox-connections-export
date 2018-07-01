""" Netbox classes """

from typing import Dict, Optional, List, Union, TypeVar, Any, cast
from logging import getLogger

import requests
import json

from .common import Multiton
from .sheet import RowData, CellData
from secrets import NETBOX_SEND_HEADERS


getLogger().setLevel(0)
debug = getLogger().debug


from pprint import pprint

QUERY_SITE: str = "hkg1"

T = TypeVar('T')


from enum import Enum


class NetboxQuery(Enum):
    QUERY_RACKS                 = "/dcim/racks/"
    QUERY_INTERFACE_CONNECTIONS = "/dcim/interface-connections/"
    QUERY_DATACENTERS           = "/dcim/sites/"
    QUERY_DEVICES               = "/dcim/devices/"



class NetboxRequest:
    """ HTTP request to netbox """




    _BASE_URL = "https://netbox.roblox.local/api"

    def __init__(self, query_endpoint: NetboxQuery, query_parameters: Dict[str, any], limit: int=None) -> None:
        """ Create initial params for Request

        site: str = id of datacenter
        """
        # query_parameters = {"q": rack.name, "site": rack.datacenter.name.lower()}
        if limit is not None and type(limit) is int and limit > 0:
            query_parameters["limit"] = limit
        query_parameters["limit"] = 1
        self.response: requests.Response = requests.get(
            self._BASE_URL + str(query_endpoint),
            query_parameters,
            headers=NETBOX_SEND_HEADERS,
            verify=False)
        debug(self.response.status_code)

    def toJSON(self) -> object:
        """ Return json from response """
        j = self.response.json()
        debug(json.dumps(j, indent=4))
        return j



class DataCenter(Multiton):
    """ DataCenter aka Site is the geographical location equipment is located within """

    _instances: dict = {}

    def __init__(self, **kwargs):
        self.id_site: int = None
        self.name: str
        self.Racks: list = []
        self.devices: list = []

        for key, val in kwargs.items():
            setattr(self, key, val)

    @classmethod
    def equivalency(cls, origin, test) -> bool:
        """ Return True if supplied datacenter is equal """
        if test.name == origin.name:
            return True
        if test.id_site and test.id_site == origin.id_site:
            return True
        return False

    @classmethod
    def getIndex(cls, **kwargs) -> str:
        """ Return unique string for object """
        if [ "name" in kwargs ]:
            return kwargs["name"]
        IndexError(f"{kwargs} did not contain a name+datacenter for Rack matching")
        return "IndexError"


class Rack(Multiton):
    """ Container for Rack obj - these contain Devices, contained by DataCenter """

    _instances: dict = {}

    def __init__(self, **kwargs):
        """ Init Rack """
        self.id_netbox: int = None
        self.id_facility: int = None
        self.name: str
        self.datacenter: DataCenter

        self.u_height: int = None

        self.obj_idx = None

        self.devices: list = []
        for key, val in kwargs.items():
            setattr(self, key, val)

    @classmethod
    def getIndex(cls, **kwargs) -> str:
        """ Return unique string for object """
        if all(x in kwargs for x in [ "name", "datacenter" ]):
            return str( kwargs["name"] + "+" + kwargs["datacenter"].name)
        IndexError(f"{kwargs} did not contain a name+datacenter for Rack matching")
        return "IndexError"

    @classmethod
    def equivalency(cls, origin, test) -> bool:
        """ Return True if supplied datacenter is equal """
        if test.name == origin.name and test.datacenter.equivalency(origin.datacenter):
            return True
        if test.id_netbox and test.id_netbox == origin.id_netbox:
            return True
        return False



class Device(Multiton):
    """ Container for physical assets """

    _instances: dict = {}

    @classmethod
    def jsonToObj(T, jd: Dict[str, Any], merge_object: T = None) -> Union[T, dict]:
        """ Create initialized Interface from JSON """
        if "url" not in jd:
            return jd
        if not cast(str, jd["url"]).find("/dcim/devices/"):
            return jd
        print(f"{'*'*30} jd into Device.jsonToObj {'*'*30} ---->")
        pprint(jd)
        print(f"<---- {'*'*30} jd into Device.jsonToObj {'*'*30}")
        # normally this is used for JSONDecode to create a NEW instance, but it could also be used to update an existing object
        if merge_object is None:
            ic = Device()
        ic.id = jd["id"]
        ic.url = jd["url"]
        ic.name = jd["name"]
        ic.display_name = jd["display_name"]
        return ic

    def __init__(self, **kwargs):
        """ Init Device """
        self.id_netbox: int
        self._datacenter: DataCenter
        self.rack: Rack
        self.device: str
        self.asset_tag: str
        self.rack_unit: int
        self.obj_idx = None
        for key, val in kwargs.items():
            setattr(self, key, val)

    @property
    def datacenter(self) -> DataCenter:
        """ Return DataCenter object """
        if type(self._datacenter) is not DataCenter:
            Device.jsonToObj(NetboxRequest(NetboxQuery.QUERY_DEVICES, {"id": self.id_netbox}), self)
        return self._datacenter

    # @property
    # def rack(self) -> Rack:
    #     """ Return DataCenter object """
    #     if type(self._datacenter) is not DataCenter:
    #         Device.jsonToObj(NetboxRequest(NetboxQuery.QUERY_RACK, {"id": self.id_netbox}), self)
    #     return self._datacenter

    @classmethod
    def getIndex(cls, **kwargs) -> str:
        """ Return unique string for object """
        if all(x in kwargs for x in [ "name", "datacenter", "rack" ]):
            plus = ""
            if "rack_unit" in kwargs:
                plus = str("+" + kwargs["rack_unit"])
            return str( kwargs["name"] + "+" + kwargs["datacenter"].name + "+" + kwargs["rack"].name + plus)
        IndexError(f"{kwargs} did not contain a name+datacenter for Rack matching")
        return "IndexError"

    @classmethod
    def equivalency(cls, origin, test) -> bool:
        """ Return True if supplied datacenter is equal """
        if test.name == origin.name and test.datacenter.equivalency(origin.datacenter) and test.Rack.equivalency(origin.Rack):
            return True
        return False





class Interface(Multiton):
    """ Interfaces exist on devices """

    _instances: dict = {}

    @classmethod
    def getIndex(cls, **kwargs) -> str:
        """ Return unique string for object """
        if all(x in kwargs for x in [ "name", "datacenter" ]):
            return str( kwargs["name"] + "+" + kwargs["datacenter"].name)
        IndexError(f"{kwargs} did not contain a name+datacenter for Rack matching")
        return "IndexError"

    def __init__(self, **kwargs):
        """ Create """
        self.id: int
        self.url: str
        self.device: Device
        self.name: str
        self.form_factor: dict      # this should be a new type of InterfaceFormFactor object; value, label attrs
        self.enabled: bool
        self.lag: Optional[int]
        self.mtu: Optional[int]
        self.mac_address: Optional[str]
        self.mgmt_only: bool
        self.description: str
        self.obj_idx = None



    @classmethod
    def jsonToObj(T, jd: Dict) -> Union[T, dict]:
        """ Create initialized Interface from JSON """
        if "device" not in jd or "form_factor" not in jd or "lag" not in jd or "mtu" not in jd:
            return jd
        print(f"{'*'*30} jd into Interface.jsonToObj {'*'*30} ---->")
        pprint(jd)
        print(f"<---- {'*'*30} jd into Interface.jsonToObj {'*'*30}")
        ic = Interface(
            "id" = jd["id"]
        )
        ic.id =
        ic.url = jd["url"]

        ic.device = Device.jsonToObj(jd["device"])

        ic.name = jd["name"]
        ic.form_factor = jd["form_factor"]
        ic.enabled = jd["enabled"]
        ic.lag = jd["lag"]
        ic.mtu = jd["mtu"]
        ic.mac_address = jd["mac_address"]
        ic.mgmt_only = jd["mgmt_only"]
        ic.description = jd["description"]
        pprint(ic)
        return ic


class InterfaceConnection(Multiton):
    """ Connect two Interfaces """

    @classmethod
    def getInterfaceConnections(T, data_center: Union[DataCenter, str] = QUERY_SITE, rack: Union[DataCenter, str, None] = None) -> List[T]:
        """ Get List of InterfaceConnection matching input params """
        query_parameters: Dict[str, str] = {}
        if data_center is not None:
            if type(data_center) is str:
                query_parameters["site"] = data_center.lower()
            elif type(data_center) is DataCenter:
                query_parameters["site"] = data_center.name.lower()
        if rack is not None:
            if type(rack) is str:
                query_parameters["q"] = rack.lower()
            elif type(rack) is Rack:
                query_parameters["q"] = rack.name.lower()
        r = NetboxRequest(NetboxQuery.QUERY_INTERFACE_CONNECTIONS, query_parameters)
        return r.response.json(object_hook=InterfaceConnection.jsonToObj)["results"]

    @classmethod
    def jsonToObj(T, jd: dict) -> Union[T, dict]:
        """ Create InterfaceConnection from JSON """
        if "interface_a" not in jd or "interface_b" not in jd:
            return jd
        print(f"{'*'*30} jd into InterfaceConnections.jsonToObj {'*'*30} ---->")
        pprint(jd)
        print(f"<---- {'*'*30} jd into InterfaceConnections.jsonToObj {'*'*30}")
        ic = InterfaceConnection()
        ic.id = jd["id"]
        ic.interface_a = Interface.jsonToObj(jd["interface_a"])
        ic.interface_b = Interface.jsonToObj(jd["interface_b"])
        ic.connection_status = jd["connection_status"]
        pprint(ic)
        return ic

    def __init__(self):
        """ Create """
        self.id: int
        self.interface_a: Interface
        self.interface_b: Interface
        self.connection_status: dict = {
            "value": bool,
            "label": str
        }

    def getSheetRowData(self) -> RowData:
        """ Create RowData for Sheets from this object """
        return RowData(
            [
                # checkbox
                CellData( self.connection_status ),
                # border 1
                CellData( self.interface_a.name ),
                CellData( self.interface_a.device.name ),
                CellData( self.interface_a.device.rack_unit ),
                CellData( self.interface_a.device.rack.name ),
                # border 2
                CellData( self.interface_b.name ),
                CellData( self.interface_b.device.name ),
                CellData( self.interface_b.device.rack_unit ),
                CellData( self.interface_b.device.rack.name )
            ])




