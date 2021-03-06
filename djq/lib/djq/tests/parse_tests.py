# (C) British Crown Copyright 2016, Met Office.
# See LICENSE.md in the top directory for license details.
#

# Tests for the parser
#

from StringIO import StringIO
from nose.tools import raises
from djq.parse import BadParse, BadJSON, BadSyntax
from djq.parse import (read_request, validate_toplevel_request,
                       validate_single_request)

# Tests of the top-level reader
#
def read_stringy_request(s):
    # I assume that StringIO streams don't need to be closed (because
    # they don't suport with properly)
    return read_request(StringIO(s))

good_toplevels = (
    "[]",
    "[{}]",
    """
[{"mip": "one",
  "experiment": "two"}]""",
    """
[{"mip": "one",
  "experiment": null}]""",
    """[{"one": 2}]""")

def test_good_toplevels():
    for j in good_toplevels:
        yield (read_stringy_request, j)

bad_toplevels = (
    "1",
    "[1]",
    "[[]]")

def test_bad_toplevels():
    @raises(BadSyntax)
    def read_bad(json):
        return read_stringy_request(json)
    for j in bad_toplevels:
        yield (read_bad, j)

hopeless_toplevels = (
    "",
    "["
    "{1:}",
    "not even trying")

def test_hopless_toplevels():
    @raises(BadJSON)
    def read_hopeless(json):
        return read_stringy_request(json)
    for j in hopeless_toplevels:
        yield (read_hopeless, j)

# Tests of request at toplevel
#

good_toplevel_requests = (
    [],
    (),
    [{}],
    ({}, {}),
    [{'not': "tested"}])

def test_good_toplevel_requests():
    for r in good_toplevel_requests:
        yield (validate_toplevel_request, r)

bad_toplevel_requests = (
    1,
    [1, {}])

def test_bad_toplevel_requests():
    @raises(BadSyntax)
    def validate_bad(r):
        return validate_toplevel_request(r)
    for r in bad_toplevel_requests:
        yield(validate_bad, r)

# tests of single requests
#

good_single_requests = (
    {'mip': "a",
     'experiment': "b"},
    {'mip': "c",
     'experiment': "d",
     'dreq': "e"},
    {'MIP': "a",
     'ExpeRiMENT': "b"},
    {'mip': "a",
     'experiment': None},
    {'mip': "a",
     'experiment': "b",
     'request-optional': "c"})

def test_good_single_requests():
    for s in good_single_requests:
        yield (validate_single_request, s)

bad_single_requests = (
    {'mip': 1,
     'experiment': "ok"},
    {'unknown': "key"},
    1,
    [1, 2],
    {})

def test_bad_single_requests():
    @raises(BadSyntax)
    def validate_bad(s):
        return validate_single_request(s)
    for s in bad_single_requests:
        yield(validate_bad, s)
