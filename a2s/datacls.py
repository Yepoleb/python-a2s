"""
Cheap dataclasses module backport

Check out the official documentation to see what this is trying to
achieve:
https://docs.python.org/3/library/dataclasses.html
"""

import collections
import copy

class DataclsBase:
    def __init__(self, **kwargs):
        for name, value in self._defaults.items():
            if name in kwargs:
                value = kwargs[name]
            setattr(self, name, copy.copy(value))

    def __iter__(self):
        for name in self.__annotations__:
            yield (name, getattr(self, name))

    def __repr__(self):
        return "{}({})".format(
            self.__class__.__name__,
            ", ".join(name + "=" + repr(value) for name, value in self))

class DataclsMeta(type):
    def __new__(cls, name, bases, prop):
        values = collections.OrderedDict()
        for member_name in prop["__annotations__"].keys():
            # Check if member has a default value set as class variable
            if member_name in prop:
                # Store default value and remove the class variable
                values[member_name] = prop[member_name]
                del prop[member_name]
            else:
                # Set None as the default value
                values[member_name] = None

        prop["__slots__"] = list(values.keys())
        prop["_defaults"] = values
        bases = (DataclsBase, *bases)
        return super().__new__(cls, name, bases, prop)

    def __prepare__(self, *args, **kwargs):
        return collections.OrderedDict()
