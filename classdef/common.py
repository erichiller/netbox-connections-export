""" Shared base class definitions """

from pprint import pprint

class Multiton(object):
    """ Single Globally Uniquely ID / keyed object, use by subclassing Multiton

    Must define on the subclass the class variable:
        _instances
    this is a list which contains the subclass instances, indexed by the obj_idx strings
    """

    def __new__(cls, *args, **kwargs):
        """ Restrict instances to the first one """
        print(f"Multiton.__new__")
        pprint(kwargs, indent=2)
        print(f"cls={cls}")
        obj_idx: str = cls.getIndex(**kwargs)
        # this code assumes that the first parameter input is the key
        if hasattr(cls, '_instances') and obj_idx in cls._instances:
            print(f"{'Multiton has_attr DUPLICATE':!>130}\n\t{cls}\n\t{obj_idx}")
            for attr in kwargs:
                print(f"Multiton.__new__ -> Setting attr={attr} on {cls.__name__} with id={obj_idx}")
                if hasattr(cls._instances[obj_idx], attr):
                    print(f"setting {cls._instances[obj_idx]} obj_idx={obj_idx} attr={attr} to->\n{kwargs[attr]}")
                    setattr(cls._instances[obj_idx], attr, kwargs[attr])
            return cls._instances[obj_idx]
        # wasn't found, so add an instance
        instance = object.__new__(cls)
        instance.obj_idx = obj_idx
        if not hasattr(cls, '_instances'):
            print(f"{'Multiton create new _instances':!>120}\n\t{cls}\n\t{obj_idx}")
            # create new list and start it with this instance
            # setattr(cls, '_instances', {argval: instance})
            cls._instances = {obj_idx: instance}
        else:
            # print(f"{'Multiton append to _instances':!>120}\n\t{cls}\n\t{obj_idx}")
            # else append to instances list
            cls._instances[obj_idx] = instance
        return instance

