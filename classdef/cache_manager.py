""" CacheManager manages object , class caching """

from typing import Dict, Type, List, Optional
import sys
import os

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
        if inspect.isclass(cls) and cls.__module__ == "classdef.netbox":
            print(f"cls={cls} module={cls.__module__}")
            classdict[name] = cls
    return classdict


def stash(objects: Optional[List[object]] = None) -> None:
    """ Pickle all classdef.netbox objects to minimize lookups"""
    import pickle
    if objects is None:
        for name, cls in get_cachable_classes().items():
            with open(os.path.join(ROOT_PATH, f'cache_{cls.__name__}.pkl'), 'wb') as f:
                # Pickle using the highest protocol available.
                pickle.dump(cls, f, pickle.HIGHEST_PROTOCOL)
    else:
        # pickle specific objects
        raise NotImplementedError("pickling specific objects is not yet supported")


def unstash(objects: Optional[List[object]] = None) -> None:
    """ Unpickle all classdef.netbox objects to minimize lookups"""
    import pickle
    if objects is None:
        unstash(list(get_cachable_classes().values()) )
        for name, cls in get_cachable_classes().items():
            unstash
            pkl_file_name = os.path.join(ROOT_PATH, f'cache_{cls.__name__}.pkl')
            if os.path.isfile(pkl_file_name):
                with open(pkl_file_name, 'rb') as f:
                    # Pickle using the highest protocol available.
                    # cls = pickle.load(f)
                    print(f"loading...{name} from {pkl_file_name}")
                    print(pickle.load(f, encoding="bytes"))
    else:
        # pickle specific objects
        raise NotImplementedError("pickling specific objects is not yet supported")
