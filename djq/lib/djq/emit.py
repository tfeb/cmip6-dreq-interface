"""Emitting replies
"""

# Currently this does no checking at all
#

from json import dump
from djq.low import InternalException

__all__ = ('EmitFailed',
           'emit_reply')

class EmitFailed(InternalException):
    def __init__(self, string, wrapped=None):
        super(EmitFailed, self).__init__(string)
        self.wrapped = wrapped

def emit_reply(reply, fp):
    """Emit a reply as JSON on a stream.

    No useful return value.  Raises EmitFailed if anything goes wrong.
    """
    try:
        dump(reply, fp, indent=2)
    except Exception as e:
        raise EmitFailed("badness when emitting", e)