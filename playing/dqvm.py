# Map from MIP<->vars
#

from collections import defaultdict
from dqwalker import walk_dq, mips_of_cmv
from dreqPy.dreq import loadDreq

__all__ = ['DQ']

class lazy(object):
    "a decorator class to produce a lazy, read-only slot"
    def __init__(self, getf):
        self.getf = getf
        self.__doc__ = getf.__doc__
        self.__name__ = getf.__name__

    def __get__(self, obj, objtype=None):
        if obj is None:         # class slot reference
            return self
        # This essentially wedges the computed value into the
        # dictionary of obj, which means (since this is not a data
        # descriptor: no __set__ method) that next time the result
        # will come directly from there.
        name = self.__name__
        if name.startswith('__') and not name.endswith('__'):
            name = "_{}{}".format(objtype.__name__, name)
        r = self.getf(obj)
        obj.__dict__[name] = r
        return r
        

class DQ(object):
    # I am not at all clear this is the right approach (all this laziness)
    #
    rules = {'CMORvar': (('mips', (lambda cmv, rules, dq:
                                       mips_of_cmv(cmv, dq))),)}
    @lazy
    def dq(self):
        return loadDreq()
        
    @lazy
    def walked(self):
        return walk_dq(self.dq, self.rules)
    
    @lazy
    def maps(self):
        v2m = defaultdict(set)
        m2v = defaultdict(set)
        for vt in self.walked.values():
            for (vn, vat) in vt.iteritems():
                v2m[vn].update(vat['mips'])
                for vmip in vat['mips']:
                    m2v[vmip].add(vn)
        return (v2m, m2v)

    @lazy
    def vmm(self):
        return self.maps[0]
    
    @lazy
    def mvm(self):
        return self.maps[1]
    