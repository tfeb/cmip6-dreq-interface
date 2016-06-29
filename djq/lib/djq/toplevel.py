"""top-level functionality
"""

__all__ = ('process_stream', 'process_request')

from collections import defaultdict
from low import DJQException, InternalException, ExternalException, Scram
from low import mutter, debug, verbosity_level, debug_level
from emit import emit_reply, emit_catastrophe
from parse import (read_request, validate_toplevel_request,
                   validate_single_request)
from load import (default_dqroot, default_dqtag, valid_dqroot, valid_dqtag,
                  dqload)
from variables import (compute_variables, jsonify_variables,
                       NoMIP, NoExperiment, WrongExperiment)

def process_stream(input, output, backtrace=False,
                   dqroot=None, dqtag=None, dbg=None, verbosity=None):
    """Process a request stream, emitting results on a reply stream.

    This reads a request from input, and from this generates a reply
    on output.  Basic sanity checking is done in this function, but
    detailed checking of ceach single-request takes place further down
    the stack.

    This function is the custodian of exceptions: it has handlers for
    anything which should happen and emits suitable replies in that
    case.  If backtrace is true it also reraises the exception so a
    stack trace can be created.

    dqroot, dqtag, dbg and verbosity, if given, will set the dqroot,
    default tag, debug and verbose printing settings for this call,
    only: the ambient values are restored on exit.

    There's no useful return value.

    Anything below this should normally handle its own exceptions and
    generate a suitable per-single-request error response: anything
    which reaches this function is treated as a catastrophe (ie the
    whole process has failed).
    """

    # Implementing special variables by hand.
    saved_dbg = debug_level()
    saved_verbosity = verbosity_level()
    saved_dqroot = default_dqroot()
    saved_dqtag = default_dqtag()
    try:
        if dbg is not None:
            debug_level(dbg)
        if verbosity is not None:
            verbosity_level(verbosity)
        if dqroot is not None:
            default_dqroot(dqroot)
        if dqtag is not None:
            default_dqtag(dqtag)
        emit_reply(tuple(process_single_request(s)
                         for s in read_request(input)),
                   output)
    except Scram as e:
        raise
    except ExternalException as e:
        emit_catastrophe("{}".format(e), output,
                         note="external error")
        if backtrace:
            raise
    except InternalException as e:
        emit_catastrophe("{}".format(e), output,
                         note="internal error")
        if backtrace:
            raise
    except DJQException as e:
        emit_catastrophe("{}".format(e), output,
                         note="unexpected error")
        if backtrace:
            raise
    except Exception as e:
        emit_catastrophe("{}".format(e), output,
                         note="completely unexpected error")
        if backtrace:
            raise
    finally:
        default_dqtag(saved_dqtag)
        default_dqroot(saved_dqroot)
        verbosity_level(saved_verbosity)
        debug_level(saved_dbg)

def process_request(request, dqroot=None, dqtag=None,
                    dbg=None, verbosity=None):
    """Process a request, as a Python object, and return the results.

    Arguments:

    - request is a toplevel request, so a list or tuple of
      single-request objects.  Each single-request is a dict with
      appropriate keys.

    - dqroot, dqtag, dbg and verbosity, if given, will set the dqroot,
      default tag, debug and verbose printing settings for this call,
      only: the ambient values are restored on exit.

    This returns a tuple of the results for each single-request in the
    request argument.

    If anything goes seriously wrong this (or in fact things it calls)
    raises a suitable exception.  Note that it *doesn't* return a
    catastrophe response, since that's not likely to be useful in this
    context.
    """

    # Implementing special variables by hand.
    saved_dbg = debug_level()
    saved_verbosity = verbosity_level()
    saved_dqroot = default_dqroot()
    saved_dqtag = default_dqtag()
    try:
        if dbg is not None:
            debug_level(dbg)
        if verbosity is not None:
            verbosity_level(verbosity)
        if dqroot is not None:
            default_dqroot(dqroot)
        if dqtag is not None:
            default_dqtag(dqtag)
        return tuple(process_single_request(s)
                     for s in validate_toplevel_request(request))
    finally:
        default_dqtag(saved_dqtag)
        default_dqroot(saved_dqroot)
        verbosity_level(saved_verbosity)
        debug_level(saved_dbg)

class DREQLoadFailure(DJQException):
    """Failure to load the DREQ: it is indeterminate whose fault this is."""
    def __init__(self, message=None, root=None, tag=None, wrapped=None):
        # I assume you don't need to call the superclass method here
        self.message = message
        self.root = root if root is not None else default_dqroot()
        self.tag = tag if tag is not None else default_dqtag()
        self.wrapped = wrapped

# Caching loaded DREQs.  The cache has teo levels, indexed on root and
# then tag: since roots are thread-local this means there won't be
# false positives: identical tags for different roots will not be
# treated as the same.  This depends on dicts being low-level
# thread-safe: x[y] = z should never yield junk in x.  The FAQ
# (https://docs.python.org/2/faq/library.html#what-kinds-of-global-value-mutation-are-thread-safe)
# says that this is true.  Given that, this might end up overwriting
# the same cache entry due to an obvious race, but assuming the DREQ
# files don't change this is just extra work, and won't result in
# anything bad.
#
# There's a potential problem if a huge number of requests come in for
# different tags: I don't think this is likely in practice.
#

dqrs = defaultdict(dict)

def ensure_dq(tag, root=None):
    """Ensure the dreq corresponding to a tag is loaded, returning it.

    Multiple requests for the same tag will return the same instance
    of the dreq.
    """
    if root is None:
        root = default_dqroot()
    dqs = dqrs[root]
    if tag not in dqs:
        debug("missed {} for {}, loading dreq", tag, root)
        if tag is not None:
            if valid_dqtag(tag):
                try:
                    dqs[tag] =  dqload(tag=tag)
                except Exception as e:
                    raise DREQLoadFailure(tag=tag, wrapped=e)
            else:
                raise DREQLoadFailure(message="invalid tag", tag=tag)
        else:
            try:
                dqs[None] = dqload()
            except Exception as e:
                raise DREQLoadFailure(wrapped=e)
    return dqs[tag]

def process_single_request(r):
    """Process a single request, returning a suitable result for JSONisation.

    This returns either the computed result, or a bad-request response
    if the request was bogus, or an error response if the dreq could
    not be loaded.
    """
    # Outer try/except block catches obviously bad requests and dreq
    # load failures
    #
    try:
        rc = validate_single_request(r)
        if 'dreq' in rc:
            mutter("* single-request tag {}", rc['dreq'])
            dq = ensure_dq(rc['dreq'])
        else:
            mutter("* single-request")
            dq = ensure_dq(None)
        reply = dict(rc)
        # inner block handles semantic errors with the request and has
        # a fallback for other errors
        try:
            variables = jsonify_variables(dq,
                                          compute_variables(dq, rc['mip'],
                                                            rc['experiment']))
            reply.update({'reply-status': "ok",
                          'reply-variables': variables})
        except NoMIP as e:
            reply.update({'reply-variables': None,
                          'reply-status': "not-found",
                          'reply-status-detail': "no MIP {}".format(e.mip)})
        except NoExperiment as e:
            reply.update({'reply-variables': None,
                          'reply-status': "not-found",
                          'reply-status-detail':
                          "no experiment {}".format(e.experiment)})
        except WrongExperiment as e:
            reply.update({'reply-variables': None,
                          'reply-status': "not-found",
                          'reply-status-detail':
                          "experiment {} not in MIP {}" .format(e.experiment,
                                                                e.mip)})
        except (ExternalException, InternalException) as e:
            reply.update({'reply-variables': None,
                          'reply-status': "error",
                          'reply-status-detail': "{}".format(e)})
        return reply
    except DREQLoadFailure as e:
        # rc is valid here
        reply = dict(rc)
        reply.update({'reply-variables': None,
                      'reply-status': "error",
                      'reply-status=detail':
                      ("failed to load dreq, root={} tag={}".format(e.root,
                                                                    e.tag)
                       + (": {}".format(e.message)
                          if e.message is not None
                          else ""))})
        return reply
    except ExternalException as e:
        # if this happens then rc is not valid
        return {'mip': r['mip'] if 'mip' in r else "?",
                'experiment': r['experiment'] if 'experiment' in r else "?",
                'reply-variables': None,
                'reply-status': 'bad-request',
                'reply-status-detail': "{}".format(e)}
