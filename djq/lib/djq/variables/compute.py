"""Finding variables, top level
"""

# This is the top level part of finding variables.  It deals with
# sanity checking everything, finding the experiment IDs (exids)
# corresponding to an experiment, and then dispatching to a back end.
# The back end can be selected, using cv_implementation.  A back end
# is either itself function, or a module with a function named
# compute_cmvids_for_exids (in which case the actual back end
# implementation is set to that function).
#
# The back end function is called with:
#  - the dreq
#  - the MIP name
#  - a set of experiment ids belonging to that MIP
# and should return an iterable of cmvids
#
# There is no abstraction from the dreq interface at all here
#
# There is a check tree, called checks: checkers in it are called with
#  - the dreq
#  - the mip
#  - an exid
#
__all__ = ('cv_implementation', 'compute_variables',

           'NoMIP', 'WrongExperiment', 'NoExperiment',
           'BadCVImplementation')

from threading import local
from djq.low import ExternalException, InternalException, Disaster
from djq.low import mutter, mumble, make_checktree
from djq.low import stringlike, arraylike, setlike

class NoMIP(ExternalException):
    def __init__(self, mip):
        self.mip = mip

class NoExperiment(ExternalException):
    def __init__(self, experiment):
        self.experiment = experiment

class WrongExperiment(ExternalException):
    def __init__(self, experiment, mip):
        self.experiment = experiment
        self.mip = mip

class BadCVImplementation(ExternalException):
    pass

# Implementations import this to add checkers.
checks = make_checktree()

# Thread-local state
#
state = local()
state.implementation = None

def cv_implementation(impl=None):
    """Get or set a back end for computing variables.
    """
    if impl is None:
        # read
        impl = state.implementation
        if callable(impl):
            return impl
        elif impl is None:
            return None
        else:
            raise Disaster("mutant cv implementation")
    else:
        # set
        if callable(impl):
            state.implementation = impl
        elif (hasattr(impl, "compute_cmvids_for_exids")
              and callable(impl.compute_cmvids_for_exids)):
            state.implementation = impl.compute_cmvids_for_exids
        else:
            raise BadCVImplementation("{} is no good".format(impl))

def compute_variables(dq, mip, experiment):
    """Compute the variables for a MIP and generalised experiment name.

    This is the only public function in this module.

    returns a set of cmvids suitable for JSONification.

    See cv_implementation for selecting a back end.
    """
    mutter("  mip {} experiment {}", mip, experiment)
    validate_mip_experiment(dq, mip, experiment)

    if (stringlike(experiment) or experiment is None
        or isinstance(experiment, bool)):
        exids = exids_of_mip(dq, mip, experiment)
        for label in sorted(dq.inx.uid[exid].label for exid in exids):
            mumble("      {}", label)
        cmvids = cv_implementation()(dq, mip, exids)
        mutter("  -> {} variables", len(cmvids))
        return cmvids
    else:
        raise Disaster("this can't happen")

def validate_mip_experiment(dq, mip, experiment):
    """Validate a MIP and an experiment if it is stringy.

    Raise suitable exceptions on failure, return value undefined.
    """
    if mip not in dq.inx.uid or dq.inx.uid[mip]._h.label != 'mip':
        raise NoMIP(mip)
    if stringlike(experiment):
        # a literal experiment
        if experiment not in dq.inx.experiment.label:
            # No experiment at all with that name
            raise NoExperiment(experiment)
    exids = exids_of_mip(dq, mip, experiment)
    if len(exids) == 0:
        # Nothing matched
        raise WrongExperiment(experiment, mip)
    for exid in exids:
        if checks(args=(dq, mip, exid)) is False:
            raise Disaster("failed sanity checks")

def exids_of_mip(dq, mip, match):
    """Find all the names of the experiments of mip matched by match.

    match may be a string, a list of strings, a set or frozenset of
    strings, or something truthy or falsy.

    This is more general than the system needs (you never get lists or
    sets of experiments, currently).

    """
    def expt_matches(expt):
        # there must be a more idiomatic way of doing type dispatch
        if stringlike(match):
            return expt.label == match
        elif arraylike(match) or setlike(match):
            return True if expt.label in match else False
        else:
            return True if match else False

    return set(expt.uid for expt in dq.coll['experiment'].items
               if expt.mip == mip and expt_matches(expt))
