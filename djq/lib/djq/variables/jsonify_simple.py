# (C) British Crown Copyright 2016, 2018 Met Office.
# See LICENSE.md in the top directory for license details.
#

"""A simple JSONify implementation
"""

__all__ = ('jsonify_cmvids',)

from sys import modules
from djq.low import checker
from djq.low import validate_object, every_element, one_of, all_of, stringlike
from djq.low import memoizable
from jsonify import checks
from varmip import mips_of_cmv, priority_of_cmv_in_mip

impl = modules[__name__]
checktree = checks[impl]

@checker(checktree, "variables.jsonify/validate-results")
def validate_results(dq, cmvids, results):
    # This checker looks at results and checks they smell basically
    # good: it could actually just be in jsonify itself, since any
    # implementation should pass this.
    number = one_of((int, float)) # a JSON number
    return validate_object(
        results,
        every_element({'uid': all_of((stringlike,
                                      lambda u: u in cmvids)),
                       'label': stringlike,
                       'miptable': stringlike,
                       'priority': number,
                       'mips': every_element(
                           {'mip': stringlike,
                            'priority': number})}))


def jsonify_cmvids(dq, cmvids):
    """Convert a bunch of CMORvar IDs to JSON."""
    return tuple(jsonify_cmvid(dq, cmvid) for cmvid in cmvids)

@memoizable(spread=True)
def jsonify_cmvid(dq, cmvid):
    cmv = dq.inx.uid[cmvid]
    return {'uid': cmvid,
            'label': cmv.label,
            'miptable': cmv.mipTable,
            'priority': cmv.defaultPriority,
            'mips': mipinfo_of_cmv(dq, cmv)}

def mipinfo_of_cmv(dq, cmv):
    # compute the mipinfo for a variable.  This could easily be cached
    # as it gets called many many times for the same MIPs
    return tuple({'mip': mip,
                  'priority': priority_of_cmv_in_mip(dq, cmv, mip)}
                 for mip in mips_of_cmv(dq, cmv))
