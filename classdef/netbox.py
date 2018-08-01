""" Netbox classes """

from typing import Dict, Optional, List, Union, TypeVar, Any, cast, Tuple, Callable
from logging import getLogger

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import json
import base64
import pickle
import os
from copy import deepcopy
from pprint import pprint

from .common import Multiton
from .sheet import RowData, CellData, ExtendedValue
from classdef import sheet
from .secrets import NETBOX_SEND_HEADERS
from .print_color import Print

from copy import copy


# getLogger().setLevel(0)
getLogger().setLevel(40)
trace = getLogger().debug
debug = getLogger().debug
info  = getLogger().info


SITE: str = "hkg1"

T = TypeVar('T')

from enum import Enum, auto


class NetboxQuery(Enum):
    """ Query Endpoints """

    RACKS                 = "/dcim/racks/"
    INTERFACECONNECTIONS  = "/dcim/interface-connections/"
    INTERFACES            = "/dcim/interfaces/"
    INTERFACE             = ( "/dcim/interfaces/", "id" )
    DATACENTERS           = "/dcim/sites/"
    DEVICES               = "/dcim/devices/"
    DEVICE                = ( "/dcim/devices/", "id" )


class RESULT(Enum):
    """ Inband signifier of result """

    NULL = auto()
    UNINIT = auto()



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
        "device":           { "class": "Device", "obj_attr": "_device" },
        "parent_device":    { "class": "Device", "obj_attr": "_parent_device" },
        "site":             { "class": "DataCenter", "obj_attr": "_datacenter" },
        "datacenter":       { "class": "DataCenter", "obj_attr": "_datacenter" },
        "rack":             { "class": "Rack", "obj_attr": "_rack" },
        "interface":        { "class": "Interface", "obj_attr": "_interface" },
        "interface_a":      { "class": "Interface", "obj_attr": "_interface_a" },
        "interface_b":      { "class": "Interface", "obj_attr": "_interface_b" }
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
        debug(f"{'*'*30} jd into (NetboxData) {cls.__name__}.jsonToObj {'*'*30} ---->")
        trace(jd)
        if type(jd) is not dict:
            raise ValueError(f"jd is not a dict: {jd}")
            # return jd
        if "detail" in jd.keys() and jd["detail"] == "Not found.":
            Print.red_bg("not found with")
        debug(f"<---- {'*'*30} jd into {cls.__name__}.jsonToObj {'*'*30}")
        if "url" in jd:
            if cast(str, jd["url"]).find(NetboxQuery[f"{cls.__name__}S".upper()].value) == -1:
                return jd
        elif not all([True if identifier_field in jd else False for identifier_field in cls._identifier_fields ]):
            info(f"identifier_fields{cls._identifier_fields} check did not pass")
            return jd
        debug(f"{'*'*30} PASS (NetboxData) {cls.__name__}.jsonToObj {'*'*30}")
        # copy jd into obj_args,
        # ``obj_args`` will be passed into class to create new instance
        obj_args = deepcopy(jd)
        for json_field, field in cls.field_to_object_map.items():
            if json_field in obj_args:
                obj_attr = json_field if len(field) == 1 else field["obj_attr"]
                Print.magenta_bg(f"**{cls.__name__}.jsonToObj ; setting {obj_attr} from {json_field}" +
                                 f"\n\ttype(field) = {type(field)}" +
                                 f"\n\ttype(jd) = {type(jd)}" )
                # try:
                #     print("str to class: ", end="")
                #     print(str_to_class(field["class"]))
                #     print("jd: ", end="")
                #     pprint(jd)
                #     print("jsonToObj: ", end="")
                #     print(str_to_class(field["class"]).jsonToObj(jd[json_field]))
                #     print("jd[json_field]: ", end="")
                #     print(jd[json_field])
                #     print(type(jd[json_field]["id"]))
                # except Exception as e: print(e)
                if jd[json_field] is None:
                    obj_args[obj_attr] = RESULT.NULL
                elif type(jd[json_field]) is str_to_class(field["class"]):
                    Print.cyan(f"The field {json_field} is already of {type(jd[json_field])}")
                else:
                    obj_args[obj_attr] = str_to_class(field["class"]).jsonToObj(jd[json_field]) if json_field in jd and type(jd[json_field]["id"]) is int else None
                obj_args.pop(json_field)  # remove json_field
        debug(f"cls={cls}")
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
        debug(f"setattr_helper\nattr_name: {attr_name}\nvalues: {values}")
        if attr_name in cls.field_to_object_map and cls.field_to_object_map[attr_name]["obj_attr"] in values and cls.field_to_object_map[attr_name]["obj_attr"]:
            debug(f"found {attr_name}")
            return_value = values[cls.field_to_object_map[attr_name]["obj_attr"]]
        elif attr_name in values:
            return_value = values[attr_name]
        else:
            return_value = RESULT.UNINIT
        return return_value

    @property
    def datacenter(self) -> "DataCenter":
        """ Return DataCenter object """
        if type(self._datacenter) is not DataCenter:
            NetboxRequest(NetboxQuery.DEVICE, {"id": self.id}, self)
        return self._datacenter

    @property
    def rack(self) -> "Rack":
        """ Return DataCenter object """
        Print.red(f"parent_device={type(self.parent_device)}\_rack={type(self._rack)}")
        if type(self._rack) is not Rack:
            NetboxRequest(NetboxQuery[self.__class__.__name__.upper()], {"id": self.id}, self)
            Print.red(f"parent_device={type(self.parent_device)}")
            if type(self.parent_device) is Device:
                Print.red(f"parent_device.rack={self.parent_device.rack}")
                self._rack = self.parent_device.rack
        if self._rack is not None:
            return self._rack
        import traceback
        print("<-----traceback---->")
        traceback.print_stack()
        traceback.print_exc()
        print("<-----traceback---->")
        raise Exception(f"rack not found on {self} with id={self.id}")

    @property
    def device(self) -> "Device":
        """ Return Device object """
        if type(self._device) is not Device:
            NetboxRequest(NetboxQuery[self.__class__.__name__.upper()], {"id": self.id}, self)
        return self._device
    
    @property
    def parent_device(self) -> "Device":
        """ Return Device object of parent if present"""
        Print.red_bg(f"querying{self.__class__.__name__}.{self.id} ; parent_device={self._parent_device}")
        if type(self._parent_device) is not Device:
            NetboxRequest(NetboxQuery[self.__class__.__name__.upper()], {"id": self.id}, self)
        if self._parent_device is not None:
            return self._parent_device


    @classmethod
    @property
    def query_class_all(cls) -> NetboxQuery:
        """ Return endpoint for this device """
        return NetboxQuery[f"{cls.__name__.__name__.upper()}S"]

    def __setstate__(self, state):
        debug(f"{'*'*40} setstate={state}")

    def __getnewargs_ex__(self) -> Tuple[Tuple, Dict]:
        return ((), self.__dict__)





class NetboxRequest:
    """ HTTP request to netbox """

    _BASE_URL = "https://netbox.roblox.local/api"
    cache_dir = os.path.abspath( os.path.join( __file__, "..", "..", "data_cache" ) )

    def __init__(self, query_endpoint: NetboxQuery, query_parameters: Dict[str, any], update_obj = None, limit: int=None, json_callback: Callable = None) -> None:
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
        self.query_parameters = copy(query_parameters)
        self.query_endpoint   = query_endpoint
        self.json_callback    = json_callback
        self.update_obj       = update_obj
        debug(f"NetboxRequest !!! self.query_parameters -> {self.query_parameters}")
        # for k, v in query_parameters.items():
        #     try:
        #         raise Exception(f"this->{k}={v}")
        #     except Exception as e:
        #         print(e)
        if limit is not None and type(limit) is int and limit > 0:
            query_parameters["limit"] = limit
        if type(self.query_endpoint.value) is tuple and self.query_endpoint.value[1] == "id":
            self.query_endpoint_str = (
                str(self.query_endpoint.value[0]) +
                str(query_parameters.pop(self.query_endpoint.value[1])) +
                str("/")
            )
        else:
            #NOTE: kill
            query_parameters["limit"] = 5
            self.query_endpoint_str = str(self.query_endpoint.value)
        if not self.load_from_cache():
            Print.red_bg(f"cache **MISS** -> NetboxRequest !!! endpoint={self.query_endpoint} ; query_parameters -> {self.query_parameters}/{query_parameters} ; query_endpoint_str -> {self.query_endpoint_str}")
            self.response: requests.Response = requests.get(
                self._BASE_URL + self.query_endpoint_str,
                query_parameters,
                headers=NETBOX_SEND_HEADERS,
                verify=False)
            debug(self.response.status_code)
            if self.response:
                self.set_to_cache()
        if self.update_obj is not None and hasattr(update_obj, "updateFromJson"):
            self.response.json(object_hook=self.update_obj.updateFromJson)



    @property
    def get_pickle_file_name(self) -> str:
        """ Create standard pickle file name from query and endpoint return String """
        # input(self.query_endpoint.__repr__())
        # input(sorted(self.query_parameters.items()).__repr__())
        encoded_query = base64.b32encode(self.query_endpoint.__repr__().encode() + sorted(self.query_parameters.items()).__repr__().encode()).decode()
        pkl_file_name = os.path.join(self.cache_dir, f'cache_{encoded_query}.pkl')
        input(f"Confirm:\n\tpkl_file_name: {pkl_file_name}\n\tcache_dir: {self.cache_dir}\n\tself.query_endpoint.__repr__().encode(): {self.query_endpoint.__repr__().encode()}\n\tsorted(self.query_parameters.items()).__repr__().encode(){sorted(self.query_parameters.items()).__repr__().encode()}\n???")
        return pkl_file_name


    def load_from_cache(self) -> bool:
        """ Check cache, if query is present, set self._json and return True, else return False """
        pkl_file_name = self.get_pickle_file_name
        if os.path.isfile(pkl_file_name):
            with open(pkl_file_name, 'rb') as f:
                try:
                    Print.green_bg(f"loading...NetboxQuery from {pkl_file_name}")
                    # input("pickle continue?")
                    self.response = pickle.load(f)
                    return True
                except EOFError as e:
                    Print.red_bg(f"pickle file invalid -> {pkl_file_name}")
                    raise e
                    return False
        return False


    def set_to_cache(self) -> None:
        """ Take query param encode as filename and save json of this query """
        pkl_file_name = self.get_pickle_file_name
        with open(pkl_file_name, 'wb') as f:
            # Pickle using the highest protocol available.
            Print.magenta_bg(f"pickling {self.response} into {pkl_file_name}")
            pickle.dump(self.response, f, pickle.HIGHEST_PROTOCOL)
            debug(f"pickle of {self.response} is complete")


    @property
    def read_response(self):
        """ read self.response and output """
        if self.json_callback is not None:
            Print.cyan("json_callback is present for NetboxQuery")
            self._json = self.response.json(object_hook=self.json_callback)
            self._results  = self._json["results"]
        else:
            Print.cyan("json_callback is NOT present for NetboxQuery, returning original json.")
            self._json = self.response.json()
            if 'results' in self._json:
                self._results  = self._json["results"]
            else:
                Print.red(f"**query returned no results**\nquery: {self.query_parameters}\nendpoint: {self.query_endpoint}\n_json: {self.response.json()}")
                input("continue?")

    @property
    def json(self) -> object:
        """ Return json from response """
        self.read_response
        j = self._json
        debug(json.dumps(j, indent=4))
        return j
    
    @property
    def results(self) -> object:
        """ JSON TO results via callback """
        self.read_response
        return self._results


class DataCenter(Multiton, NetboxData):
    """ DataCenter aka Site is the geographical location equipment is located within """

    _instances: dict = {}
    _identifier_fields = { "name": True, "physical_address": True }

    def __init__(self, **kwargs):
        debug(f"creating DataCenter object from {kwargs}")
        self.id_site: int = None
        self.name: str
        self.Racks: list = []
        self.devices: list = []

        for key, val in kwargs.items():
            setattr(self, key, val)
        debug(f"created -> DataCenter object from {self.__dict__}")

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
        self._parent_device: Device     = self.__class__.setattr_helper("parent_device", kwargs)
        self.url: str                   = kwargs["url"] if "url" in kwargs else None
        self.name: str                  = kwargs["name"] if "name" in kwargs else None
        self.display_name: str          = kwargs["display_name"] if "display_name" in kwargs else None
        self.asset_tag: str             = kwargs["asset_tag"] if "asset_tag" in kwargs else None
        self.rack_unit: int             = kwargs["rack_unit"] if "rack_unit" in kwargs else None
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
        r = NetboxRequest(NetboxQuery.INTERFACECONNECTIONS, query_parameters, json_callback = InterfaceConnection.jsonToObj)
        trace(r.__dict__)
        return r.results

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
        Print.red_bg(f"A={self.interface_a.device.id} ... B={self.interface_b.device.id}")
        # input("continue?")
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
        if type(self._interface_a) is not Interface:
            NetboxRequest(NetboxQuery.INTERFACE, {"id": self.id}, self)
        return self._interface_a

    @property
    def interface_b(self) -> Interface:
        """ Return DataCenter object """
        if type(self._interface_b) is not Interface:
            NetboxRequest(NetboxQuery.INTERFACE, {"id": self.id}, self)
        return self._interface_b
