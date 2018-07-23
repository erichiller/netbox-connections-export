""" Netbox classes """

from typing import Dict, Optional, List, Union, TypeVar, Any, cast
from logging import getLogger

import requests
import json

from .common import Multiton
from .sheet import RowData, CellData, ExtendedValue
import classdef.sheet as sheet
from .secrets import NETBOX_SEND_HEADERS


getLogger().setLevel(0)
debug = getLogger().debug
info  = getLogger().info


from pprint import pprint

SITE: str = "hkg1"

T = TypeVar('T')


from enum import Enum




class Print(object):
    ANSI_CLEAR               = "\u001b[0m"
    ANSI_CLEOL               = "\u001b[K"                           # CLEAR TO END OF LINE
    ANSI_CLSML               = "\u001b[1K"                          # CLEAR SAME LINE
    ANSI_RSCUR               = "\u001b[G"                           # RESET / MOVE the CURSOR to the line beginning

    ANSI_BLACK               = "\u001b[30m"
    ANSI_RED                 = "\u001b[31m"
    ANSI_GREEN               = "\u001b[32m"
    ANSI_YELLOW              = "\u001b[33m"
    ANSI_BLUE                = "\u001b[34m"
    ANSI_MAGENTA             = "\u001b[35m"
    ANSI_CYAN                = "\u001b[36m"
    ANSI_WHITE               = "\u001b[37m"

    ANSI_BG_BLACK            = "\u001b[40m"
    ANSI_BG_RED              = "\u001b[41m"
    ANSI_BG_GREEN            = "\u001b[42m"
    ANSI_BG_YELLOW           = "\u001b[43m"
    ANSI_BG_BLUE             = "\u001b[44m"
    ANSI_BG_MAGENTA          = "\u001b[45m"
    ANSI_BG_CYAN             = "\u001b[46m"
    ANSI_BG_WHITE            = "\u001b[47m"

    @classmethod
    def title(cls, title: str):
        length = len(title)
        ppsl = 4
        ps = '*' * (length + (ppsl * 2) + 2)
        pps = '*' * ppsl
        if length > 0:
            print(f"{Print.ANSI_BG_WHITE}{Print.ANSI_BLACK}{ps}\n{pps} {title} {pps}\n{ps}{Print.ANSI_CLEAR}{Print.ANSI_CLEOL}")
    
    @classmethod    
    def green(cls, output: str):
        color = Print.ANSI_GREEN
        eol = Print.ANSI_CLEOL
        clear = Print.ANSI_CLEAR
        print(f"{color}{output}{eol}{clear}")


    @classmethod
    def green_bg(cls, output: str):
        color = f"{Print.ANSI_BG_GREEN}{Print.ANSI_BLACK}"
        eol = Print.ANSI_CLEOL
        clear = Print.ANSI_CLEAR
        print(f"{color}{output}{eol}{clear}")

    @classmethod
    def red_bg(cls, output: str):
        color = f"{Print.ANSI_BG_RED}{Print.ANSI_BLACK}"
        eol = Print.ANSI_CLEOL
        clear = Print.ANSI_CLEAR
        print(f"{color}{output}{eol}{clear}")

    @classmethod
    def magenta_bg(cls, output: str):
        color = f"{Print.ANSI_BG_MAGENTA}{Print.ANSI_BLACK}"
        eol = Print.ANSI_CLEOL
        clear = Print.ANSI_CLEAR
        print(f"{color}{output}{eol}{clear}")

    @classmethod
    def label_value(cls, label: str, value):
        """ Output in the form of =>  label               : value """
        # color = f"{Print.ANSI_BG_GREEN}{Print.ANSI_BLACK}"
        # eol = Print.ANSI_CLEOL
        # clear = Print.ANSI_CLEAR
        # print(f"{color}{output}{eol}{clear}")
        print(f"{label:<50} : {value}")

    @classmethod
    def progress(cls, complete, total, char_width=80):
        """ Create dynmaically updating progress bar """
        to_check = ( complete, total, char_width )
        if not all( type(i) is int for i in to_check):
            raise TypeError(f"all inputs must be of type int, {to_check}")
        complete = complete + 1
        to_check = ( complete, total, char_width )
        if total != 0 and char_width != 0:
            interval = total / char_width
        if any( i == 0 for i in to_check):
            raise ValueError(f"Inputs can not be 0, {to_check}")
        else:
            mod = ( interval ) % complete == 0
            percent = complete / total
            intervals = round( complete / interval)
        if mod == 0:
            print(f"{cls.ANSI_CLSML}{cls.ANSI_RSCUR} 0% [{percent:6.01%}] |{intervals * '='}" + ( " " * ( char_width - intervals ) ) + "| 100%", end='')
        if complete == total:
            print("... complete")


class NetboxQuery(Enum):
    """ Query Endpoints """

    RACKS                 = "/dcim/racks/"
    INTERFACECONNECTIONS  = "/dcim/interface-connections/"
    INTERFACES            = "/dcim/interfaces/"
    INTERFACE             = ( "/dcim/interfaces/", "id" )
    DATACENTERS           = "/dcim/sites/"
    DEVICES               = "/dcim/devices/"
    DEVICE                = ( "/dcim/devices/", "id" )



def str_to_class(classname: str):
    """ Input a string and returns the class object named it """
    import sys
    return getattr(sys.modules[__name__], classname)


class NetboxData:
    """ Base for all netbox data objects, provide basic helper functions """

    # define mapping of json fields to objects to create
    # must pass the object as a string because of issues with forward references
    # to place the newly created object into the ``local_attr`` attribute of the instance
    field_to_object_map = {
        "device":       { "class": "Device", "obj_attr": "_device" },
        "site":         { "class": "DataCenter", "obj_attr": "_datacenter" },
        "datacenter":   { "class": "DataCenter", "obj_attr": "_datacenter" },
        "rack":         { "class": "Rack", "obj_attr": "_rack" },
        "interface":    { "class": "Interface", "obj_attr": "_interface" },
        "interface_a":  { "class": "Interface", "obj_attr": "_interface_a" },
        "interface_b":  { "class": "Interface", "obj_attr": "_interface_b" }
    }

    def updateFromJson(self: T, jd: Dict[str, Any]) -> T:
        """ Update self with JSON """
        return self.__class__.jsonToObj(jd, self)

    @classmethod
    def jsonToObj(cls: T, jd: Dict[str, Any], merge_object: T = None) -> Union[T, dict]:
        """ Input json object and create/update object

        shared jsonToObj from base ``NetboxData``

        Parameters
        ----------
        jd : Dict[str, any]
            this is the input json dict
        merge_object : T
            Accepts an instance of the object this is a class of
            if None:
                return new object
            else:
                The object provided by ``merge_object`` is updated

        """
        print(f"{'*'*30} jd into (NetboxData) {cls.__name__}.jsonToObj {'*'*30} ---->")
        pprint(jd)
        print(f"<---- {'*'*30} jd into {cls.__name__}.jsonToObj {'*'*30}")
        if "url" in jd:
            if cast(str, jd["url"]).find(NetboxQuery[f"{cls.__name__}S".upper()].value) == -1:
                return jd
        elif not all([True if identifier_field in jd else False for identifier_field in cls._identifier_fields ]):
            info(f"identifier_fields{cls._identifier_fields} check did not pass")
            return jd
        print(f"{'*'*30} PASS (NetboxData) {cls.__name__}.jsonToObj {'*'*30}")
        # copy jd into obj_args,
        # ``obj_args`` will be passed into class to create new instance
        obj_args = jd
        for json_field, field in cls.field_to_object_map.items():
            if json_field in obj_args:
                obj_attr = json_field if len(field) == 1 else field["obj_attr"]
                Print.green_bg(f"**{cls.__name__}.jsonToObj ; setting {obj_attr} from {json_field}")
                obj_args[obj_attr] = str_to_class(field["class"]).jsonToObj(jd[json_field]) if json_field in jd and type(jd[json_field]["id"]) is int else None
                obj_args.pop(json_field)  # remove json_field
        print(f"cls={cls}")
        instance = cls( **obj_args )
        return instance

    @classmethod
    def getIndex(cls, **kwargs) -> str:
        """ Return unique string for object """
        # if id not in kwargs and not all([True if identifier_field in kwargs else False for identifier_field in cls._identifier_fields ]):
            # raise IndexError(f"Indexable fields not present, unable to create index.\nEither all{cls._identifier_fields} or {cls.__name__}.id were not present\n{kwargs}")
        if "id" not in kwargs:
            raise IndexError(f"-->\nIndexable fields not present, unable to create index.\n{cls.__name__}.id was not present\n{kwargs}\n<--")
        return kwargs["id"]

    @classmethod
    def setattr_helper(cls, attr_name: str, values) -> Any:
        """ Return mapped field if necessary (for objects) """
        Print.magenta_bg(f"setattr_helper\nattr_name: {attr_name}\nvalues: {values}")
        if attr_name in cls.field_to_object_map and cls.field_to_object_map[attr_name]["obj_attr"] in values:
            Print.green_bg(f"found {attr_name}")
            return values[cls.field_to_object_map[attr_name]["obj_attr"]]
        if attr_name in values:
            return values[attr_name]
        return None

    @property
    def datacenter(self) -> "DataCenter":
        """ Return DataCenter object """
        if type(self._datacenter) is not DataCenter:
            NetboxRequest(NetboxQuery.DEVICE, {"id": self.id}, self)
        return self._datacenter

    @property
    def rack(self) -> "Rack":
        """ Return DataCenter object """
        if type(self._rack) is not Rack:
            NetboxRequest(NetboxQuery[self.__class__.__name__.upper()], {"id": self.id}, self)
        return self._rack

    @property
    def device(self) -> "Device":
        """ Return Device object """
        if type(self._device) is not Device:
            NetboxRequest(NetboxQuery[self.__class__.__name__.upper()], {"id": self.id}, self)
        return self._device

    @classmethod
    @property
    def query_class_all(cls) -> NetboxQuery:
        """ Return endpoint for this device """
        return NetboxQuery[f"{cls.__name__.__name__.upper()}S"]
    




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
            query_parameters["limit"] = 5
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
        Print.red_bg(f"creating DataCenter object from {kwargs}")
        self.id_site: int = None
        self.name: str
        self.Racks: list = []
        self.devices: list = []

        for key, val in kwargs.items():
            setattr(self, key, val)
        Print.red_bg(f"created -> DataCenter object from {self.__dict__}")

    @classmethod
    def equivalency(cls, origin, test) -> bool:
        """ Return True if supplied datacenter is equal """
        if test.name == origin.name:
            return True
        if test.id_site and test.id_site == origin.id_site:
            return True
        return False


class Rack(Multiton, NetboxData):
    """ Container for Rack obj - these contain Devices, contained by DataCenter """

    _instances: dict = {}
    _identifier_fields = { "u_height": True, "facility_id": True }

    def __init__(self, **kwargs):
        """ Init Rack """
        self.id: int = None
        self.id_facility: int = None
        self.name: str
        self._datacenter: DataCenter = self.__class__.setattr_helper("datacenter", kwargs)

        self.u_height: int = None

        self.obj_idx = None

        self.devices: list = []
        for key, val in kwargs.items():
            setattr(self, key, val)

    # @classmethod
    # def getIndex(cls, **kwargs) -> str:
    #     """ Return unique string for object """
    #     if all(x in kwargs for x in [ "name", "datacenter" ]):
    #         return str( kwargs["name"] + "+" + kwargs["datacenter"].name)
    #     raise IndexError(f"{kwargs} did not contain a name+datacenter for Rack matching")

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
    _identifier_fields = { "device_type": True }

    def __init__(self, **kwargs):
        """ Init Device """
        self.id: int                    = kwargs["id"] if "id" in kwargs else None
        self._datacenter: DataCenter    = self.__class__.setattr_helper("datacenter", kwargs)
        self._rack: Rack                = self.__class__.setattr_helper("rack", kwargs)
        self.url: str                   = kwargs["url"] if "url" in kwargs else None
        self.name: str                  = kwargs["name"] if "name" in kwargs else None
        self.display_name: str          = kwargs["display_name"] if "display_name" in kwargs else None
        self.asset_tag: str             = kwargs["asset_tag"] if "asset_tag" in kwargs else None
        self.rack_unit: int             = kwargs["rack_unit"] if "rack_unit" in kwargs else None
        self.obj_idx                    = None
        # for key, val in kwargs.items():
        #     setattr(self, key, val)


    # @property
    # def rack(self) -> Rack:
    #     """ Return DataCenter object """
    #     if type(self._datacenter) is not DataCenter:
    #         Device.jsonToObj(NetboxRequest(NetboxQuery.RACK, {"id": self.id}), self)
    #     return self._datacenter

    # @classmethod
    # def getIndex(cls, **kwargs) -> str:
    #     """ Return unique string for object """
    #     if all(x in kwargs for x in [ "name", "datacenter", "rack" ]):
    #         plus = ""
    #         if "rack_unit" in kwargs:
    #             plus = str("+" + kwargs["rack_unit"])
    #         return str( kwargs["name"] + "+" + kwargs["datacenter"].name + "+" + kwargs["rack"].name + plus)
    #     raise IndexError(f"{kwargs} did not contain a name+datacenter for Rack matching")

    @classmethod
    def equivalency(cls, origin, test) -> bool:
        """ Return True if supplied datacenter is equal """
        if test.name == origin.name and test.datacenter.equivalency(origin.datacenter) and test.Rack.equivalency(origin.Rack):
            return True
        return False





class Interface(Multiton, NetboxData):
    """ Interfaces exist on devices """

    _instances: dict = {}
    _identifier_fields = {"mac_address": True, "lag": True}

    # @classmethod
    # def getIndex(cls, **kwargs) -> str:
    #     """ Return unique string for object """
    #     if all(x in kwargs for x in [ "name", "url" ]):
    #         return str( kwargs["name"] + "+" + kwargs["url"])
    #     raise IndexError(f"{kwargs} did not contain a name+url for Interface matching")

    def __init__(self, **kwargs) -> None:
        """ Create """
        self.id: int                    = kwargs["id"] if "id" in kwargs else None
        self.url: str                   = kwargs["url"] if "url" in kwargs else None
        self._device: Device            = self.__class__.setattr_helper("device", kwargs)
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
    


class InterfaceConnection(Multiton, NetboxData):
    """ Connect two Interfaces """

    _instances: dict = {}
    _identifier_fields = {"interface_a": True, "interface_b": True}

    @classmethod
    def getInterfaceConnections(cls, data_center: Union[DataCenter, str] = SITE, rack: Union[DataCenter, str, None] = None) -> List["InterfaceConnection"]:
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
        r = NetboxRequest(NetboxQuery.INTERFACECONNECTIONS, query_parameters)
        pprint(r.__dict__)
        return r.response.json(object_hook=InterfaceConnection.jsonToObj)["results"]

    def __init__(self, **kwargs):
        """ Create """
        self.id: int
        self._interface_a: Interface = self.__class__.setattr_helper("interface_a", kwargs)
        self._interface_b: Interface = self.__class__.setattr_helper("interface_b", kwargs)
        self.connection_status: dict = {
            "value": bool,
            "label": str
        }
        for k in kwargs:
            setattr(self, k, kwargs[k])

    def getSheetRowData(self) -> RowData:
        """ Create RowData for Sheets from this object """
        return RowData(
            [
                # checkbox
                CellData( 
                    userEnteredValue = ExtendedValue( True if self.connection_status["value"] is True else False ),
                    dataValidation = sheet.DataValidationRule( sheet.BooleanCondition( sheet.ConditionType.BOOLEAN ) )
                ),
                # border 1
                CellData( ExtendedValue( self.interface_a.name ) ),
                CellData( ExtendedValue( self.interface_a.device.name ) ),
                CellData( ExtendedValue( self.interface_a.device.rack_unit ) ),
                CellData( ExtendedValue( self.interface_a.device.rack.name ) ),
                # border 2
                CellData( ExtendedValue( self.interface_b.name ) ),
                CellData( ExtendedValue( self.interface_b.device.name ) ),
                CellData( ExtendedValue( self.interface_b.device.rack_unit ) ),
                CellData( ExtendedValue( self.interface_b.device.rack.name ) )
            ])

    @property
    def interface_a(self) -> Interface:
        """ Return DataCenter object """
        if type(self._interface_a) is not Rack:
            NetboxRequest(NetboxQuery.INTERFACE, {"id": self.id}, self)
        return self._interface_a

    @property
    def interface_b(self) -> Interface:
        """ Return DataCenter object """
        if type(self._interface_b) is not Rack:
            NetboxRequest(NetboxQuery.INTERFACE, {"id": self.id}, self)
        return self._interface_b
