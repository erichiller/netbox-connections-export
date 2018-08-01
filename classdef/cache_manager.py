""" CacheManager manages object , class caching """

from typing import Dict, Type, List, Optional, Union, cast
import sys
import os
from .print_color import Print
from .netbox import *


ROOT_PATH = os.path.abspath( os.path.join( __file__, "..", ".." ) )
if ROOT_PATH not in sys.path:
    sys.path.append( ROOT_PATH )


def get_cachable_classes() -> Dict[str, Type]:
    """ Return class objects which are cachable by CacheManager """
    import inspect
    # print(sys.modules)
    # print(sys.modules["classdef.netbox"])
    classdict: Dict[str, Type] = {}
    for name, cls in inspect.getmembers(sys.modules["classdef.netbox"]):
        print( f"{inspect.isclass(cls)} and {cls.__module__ if hasattr(cls, 'module') else None} == 'classdef.netbox' and {hasattr(cls, '_instances')}" )
        if inspect.isclass(cls) and cls.__module__ == "classdef.netbox" and hasattr(cls, "_instances"):
            print(f"cls={cls} module={cls.__module__}")
            classdict[name] = cls
    Print.green_bg(classdict)
    return classdict


def stash(objects: Union[List[Type], None, Type] = None) -> None:
    """ Pickle all classdef.netbox objects to minimize lookups"""
    import pickle
    if objects is None:
        objects = list(get_cachable_classes().values())
    if not isinstance(objects, list):
        objects = [objects]
    Print.magenta_bg(f"pickling found {len(objects)}")

    for cls in objects:
        pkl_file_name = os.path.join(ROOT_PATH, f'cache_{cls.__name__}.pkl')
        with open(os.path.join(ROOT_PATH, f'cache_{cls.__name__}.pkl'), 'wb') as f:
            # Pickle using the highest protocol available.
            Print.magenta_bg(f"pickling {cls.__name__} into {pkl_file_name}")
            pickle.dump(cls._instances, f, pickle.HIGHEST_PROTOCOL)
            print(f"pickle of {cls.__name__} is complete")
            # Print.red_bg(f"pickle file invalid {cls.__name__} from {pkl_file_name}")






def unstash(objects: Union[List[Type], None, Type] = None) -> None:
    """ Unpickle all classdef.netbox objects to minimize lookups"""
    import pickle
    if objects is None:
        objects = list(get_cachable_classes().values())
    if not isinstance(objects, list):
        objects = [objects]

    for cls in objects:
        pkl_file_name = os.path.join(ROOT_PATH, f'cache_{cls.__name__}.pkl')
        if os.path.isfile(pkl_file_name):
            with open(pkl_file_name, 'rb') as f:
                # Pickle using the highest protocol available.
                try:
                    # cls = pickle.load(f)
                    
                    # load into cls._instances
                    print(f"loading...{cls.__name__} from {pkl_file_name}")
                    pickle.load(f)
                except EOFError:
                    Print.red_bg(f"pickle file invalid {cls.__name__} from {pkl_file_name}")
    print("------Datacenter------")
    print(DataCenter._instances)
    print("------Rack------")
    print(Rack._instances)
    print("------Device------")
    print(Device._instances)
    print("------InterfaceConnection------")
    print(InterfaceConnection._instances)
    input("press [Enter] to continue")

# def unstash(name, value) -> None:
#     """ Unpickle all classdef.netbox objects to minimize lookups"""
#     import pickle
#     for cls in objects:
#         pkl_file_name = os.path.join(ROOT_PATH, f'cache_{cls.__name__}.pkl')
#         if os.path.isfile(pkl_file_name):
#             with open(pkl_file_name, 'rb') as f:
#                 # Pickle using the highest protocol available.
#                 # cls = pickle.load(f)
#                 print(f"loading...{cls.__name__} from {pkl_file_name}")
#                 print(pickle.load(f, encoding="bytes"))
