# Low level

__all__ = ['Badness', 'lazy']

class Badness(Exception):
    pass

class lazy(object):
    "a decorator class to produce a lazy, read-only slot"
    def __init__(self, getf):
        self.getf = getf
        self.__doc__ = getf.__doc__
        self.__name__ = getf.__name__

    def __get__(self, obj, objtype=None):
        if obj is None:         # class slot reference
            return self
        # This is depressingly dependent on the details of the
        # implementation: it essentially wedges the computed value
        # into the dictionary of obj, which means (since this is not a
        # data descriptor: no __set__ method) that next time the
        # result will come directly from there.
        name = self.__name__
        if name.startswith('__') and not name.endswith('__'):
            name = "_{}{}".format(objtype.__name__, name)
        r = self.getf(obj)
        obj.__dict__[name] = r
        return r

