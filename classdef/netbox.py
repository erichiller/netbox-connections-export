""" Netbox classes """

from typing import Dict, Optional, List, Union, TypeVar, Any, cast
from logging import getLogger

import requests
import json

from .common import Multiton
from .sheet import RowData, CellData
from .secrets import NETBOX_SEND_HEADERS


getLogger().setLevel(0)
debug = getLogger().debug
info  = getLogger().info


from pprint import pprint

QUERY_SITE: str = "hkg1"

T = TypeVar('T')


from enum import Enum


class NetboxQuery(Enum):
    QUERY_RACKS                 = "/dcim/racks/"
    QUERY_INTERFACE_CONNECTIONS = "/dcim/interface-connections/"
    QUERY_DATACENTERS           = "/dcim/sites/"
    QUERY_DEVICES               = "/dcim/devices/"
    QUERY_DEVICE                = ( "/dcim/devices/", "id" )




class NetboxData:
    """ Base for all netbox data objects, provide basic helper functions """

    def updateFromJson(self: T, jd: Dict[str, Any]) -> T:
        """ Update self with JSON """
        return self.__class__.jsonToObj(jd, self)

    @classmethod
    def jsonToObj(cls: T, jd: Dict[str, Any]) -> Union[T, dict]:
        print(f"{'*'*30} jd into {cls.__name__}.jsonToObj {'*'*30} ---->")
        pprint(jd)
        print(f"<---- {'*'*30} jd into {cls.__name__}.jsonToObj {'*'*30}")
        if "url" in jd:
            if cast(str, jd["url"]).find(NetboxQuery[f"QUERY_{cls.__name__}S".upper()].value) == -1:
                return jd
        elif not all([True if identifier_field in jd else False for identifier_field in cls._identifier_fields ]):
            info("identifier_fields check did not pass")
            return jd
        print(f"{'*'*30} PASS (NetboxData) {cls.__name__}.jsonToObj {'*'*30}")
        instance = cls( **jd )
        return instance




class NetboxRequest:
    """ HTTP request to netbox """

    _BASE_URL = "https://netbox.roblox.local/api"

    def __init__(self, query_endpoint: NetboxQuery, query_parameters: Dict[str, any], update_obj = None, limit: int=None) -> None:
        """ Create initial params for Request

        query_endpoint : NetboxQuery
            baseURL to call
        query_parameters : Dict[str, any]
            Dict of str: Any for GET parameters
        update_obj : Object
            update_obj should point back to the object to be updated, if not creating a new Object
        limit : int
            limit the number of returned results
        """
        # query_parameters = {"q": rack.name, "site": rack.datacenter.name.lower()}
        if limit is not None and type(limit) is int and limit > 0:
            query_parameters["limit"] = limit

        if type(query_endpoint.value) is tuple and query_endpoint.value[1] == "id":
            query_endpoint_str = (
                str(query_endpoint.value[0]) +
                str(query_parameters.pop(query_endpoint.value[1])) +
                str("/")
            )
        else:
            #NOTE: kill
            query_parameters["limit"] = 1
            query_endpoint_str = str(query_endpoint.value)
        self.response: requests.Response = requests.get(
            self._BASE_URL + query_endpoint_str,
            query_parameters,
            headers=NETBOX_SEND_HEADERS,
            verify=False)
        debug(self.response.status_code)
        if update_obj is not None and hasattr(update_obj, "updateFromJson"):
            self.response.json(object_hook=update_obj.updateFromJson)


    def toJSON(self) -> object:
        """ Return json from response """
        j = self.response.json()
        debug(json.dumps(j, indent=4))
        return j


class DataCenter(Multiton, NetboxData):
    """ DataCenter aka Site is the geographical location equipment is located within """

    _instances: dict = {}
    _identifier_fields = { "name": True, "physical_address": True }

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
        print(kwargs)
        if [ "name" in kwargs ]:
            return kwargs["name"]
        IndexError(f"{kwargs} did not contain a name+datacenter for Rack matching")
        return "IndexError"


class Rack(Multiton, NetboxData):
    """ Container for Rack obj - these contain Devices, contained by DataCenter """

    _instances: dict = {}
    _identifier_fields = { "u_height": True, "facility_id": True }

    def __init__(self, **kwargs):
        """ Init Rack """
        self.id: int = None
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
        if test.id and test.id == origin.id:
            return True
        return False



class Device(Multiton, NetboxData):
    """ Container for physical assets """

    _instances: dict = {}

    @classmethod
    def jsonToObj(T, jd: Dict[str, Any], merge_object: T = None) -> Union[T, dict]:
        """ Create initialized Interface from JSON """
        if "url" in jd:
            if cast(str, jd["url"]).find("/dcim/devices/") == -1:
                return jd
        elif "device_type" not in jd or "device_role" not in jd or "asset_tag" not in jd:
            return jd
        print(f"{'*'*30} jd into Device.jsonToObj {'*'*30} ---->")
        pprint(jd)
        print(f"<---- {'*'*30} jd into Device.jsonToObj {'*'*30}")
        # normally this is used for JSONDecode to create a NEW instance, but it could also be used to update an existing object
        if merge_object is None:
            ic = Device()
        else:
            ic = merge_object
        ic.id               = jd["id"]
        ic.url              = jd["url"] if "url" in jd else None
        ic.name             = jd["name"]
        ic.display_name     = jd["display_name"]
        ic._datacenter      = DataCenter.jsonToObj(jd["site"]) if "site" in jd and type(jd["site"]["id"]) is int else None
        ic._rack            = Rack.jsonToObj(jd["rack"]) if "rack" in jd and type(jd["rack"]["id"]) is int else None
        return ic

    def __init__(self, **kwargs):
        """ Init Device """
        self.id: int                    = kwargs["id"] if "id" in kwargs else None
        self._datacenter: DataCenter    = kwargs["datacenter"] if "datacenter" in kwargs else None
        self._rack: Rack                = kwargs["rack"] if "rack" in kwargs else None
        self.url: str                   = kwargs["url"] if "url" in kwargs else None
        self.name: str                  = kwargs["name"] if "name" in kwargs else None
        self.display_name: str          = kwargs["display_name"] if "display_name" in kwargs else None
        self.asset_tag: str             = kwargs["asset_tag"] if "asset_tag" in kwargs else None
        self.rack_unit: int             = kwargs["rack_unit"] if "rack_unit" in kwargs else None
        self.obj_idx                    = None
        for key, val in kwargs.items():
            setattr(self, key, val)

    @property
    def datacenter(self) -> DataCenter:
        """ Return DataCenter object """
        if type(self._datacenter) is not DataCenter:
            NetboxRequest(NetboxQuery.QUERY_DEVICE, {"id": self.id}, self)
        return self._datacenter

    @property
    def rack(self) -> Rack:
        """ Return DataCenter object """
        if type(self._rack) is not Rack:
            Device.jsonToObj(NetboxRequest(NetboxQuery.QUERY_DEVICE, {"id": self.id}), self)
        return self._rack

    # @property
    # def rack(self) -> Rack:
    #     """ Return DataCenter object """
    #     if type(self._datacenter) is not DataCenter:
    #         Device.jsonToObj(NetboxRequest(NetboxQuery.QUERY_RACK, {"id": self.id}), self)
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
        if all(x in kwargs for x in [ "name", "url" ]):
            return str( kwargs["name"] + "+" + kwargs["url"])
        IndexError(f"{kwargs} did not contain a name+url for Interface matching")
        return "IndexError"

    def __init__(self, **kwargs) -> None:
        """ Create """
        self.id: int                    = kwargs["id"] if "id" in kwargs else None
        self.url: str                   = kwargs["url"] if "url" in kwargs else None
        self.device: Device             = kwargs["device"] if "device" in kwargs else None
        self.name: str                  = kwargs["name"] if "name" in kwargs else None
        # this should be a new type of InterfaceFormFactor object; value, label attrs
        self.form_factor: dict          = kwargs["form_factor"] if "form_factor" in kwargs else None
        self.enabled: bool              = kwargs["enabled"] if "enabled" in kwargs else None
        self.lag: Optional[int]         = kwargs["lag"] if "lag" in kwargs else None
        self.mtu: Optional[int]         = kwargs["mtu"] if "mtu" in kwargs else None
        self.mac_address: Optional[str] = kwargs["mac_address"] if "mac_address" in kwargs else None
        self.mgmt_only: bool            = kwargs["mgmt_only"] if "mgmt_only" in kwargs else None
        self.description: str           = kwargs["description"] if "description" in kwargs else None
        self.obj_idx = None



    @classmethod
    def jsonToObj(T, jd: Dict, merge_object: T = None) -> Union[T, dict]:
        """ Create initialized Interface from JSON """
        if "device" not in jd or "form_factor" not in jd or "lag" not in jd or "mtu" not in jd:
            return jd
        # normally this is used for JSONDecode to create a NEW instance, but it could also be used to update an existing object

        print(f"{'*'*30} jd into Interface.jsonToObj {'*'*30} ---->")
        pprint(jd)
        print(f"<---- {'*'*30} jd into Interface.jsonToObj {'*'*30}")
        if merge_object is None:
            ic = Interface(
                id            = jd["id"],
                url           = jd["url"],
                device        = Device.jsonToObj(jd["device"]),
                name          = jd["name"],
                form_factor   = jd["form_factor"],
                enabled       = jd["enabled"],
                lag           = jd["lag"],
                mtu           = jd["mtu"],
                mac_address   = jd["mac_address"],
                mgmt_only     = jd["mgmt_only"],
                description   = jd["description"],
            )
        else:
            ic = merge_object
            ic.id            = jd["id"],
            ic.url           = jd["url"],
            ic.device        = Device.jsonToObj(jd["device"]),
            ic.name          = jd["name"],
            ic.form_factor   = jd["form_factor"],
            ic.enabled       = jd["enabled"],
            ic.lag           = jd["lag"],
            ic.mtu           = jd["mtu"],
            ic.mac_address   = jd["mac_address"],
            ic.mgmt_only     = jd["mgmt_only"],
            ic.description   = jd["description"],
        pprint(ic)
        return ic


class InterfaceConnection(Multiton, NetboxData):
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
        pprint(r.__dict__)
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
        print(f"{'*'*30} jd //PASS// InterfaceConnections.jsonToObj {'*'*30}")
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




