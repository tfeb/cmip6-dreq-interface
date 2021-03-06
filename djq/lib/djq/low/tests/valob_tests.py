# (C) British Crown Copyright 2016, Met Office.
# See LICENSE.md in the top directory for license details.
#

# Tests for valob
#

from djq.low.valob import validate_object, every_element, all_of, one_of
from djq.low import stringlike

should_match = ((1, 1),
                ("a", "a"),
                ([1, 2, 3], [1, 2, 3]),
                (1, int),
                ({'a': "b", 1: True},
                 {1: True, 'a': "b"}),
                ([1, 2, 3], every_element(int, list)),
                ({1: [1, 2],
                  2: lambda x: x,
                  3: {'a': 1}},
                 {1: [1, int],
                  2: callable,
                  3: {'a': 1}}),
                (1, all_of((1, int))),
                (1, one_of((list, 1))))

def test_should_match():
    def checker(ob, pattern):
        assert validate_object(ob, pattern) is True, "failed to match"
    for (ob, pattern) in should_match:
        yield (checker, ob, pattern)


should_not_match = ((1, 2),
                    ("a", "b"),
                    ([[[[[[[1, [2]]]]]]]],
                     [[[[[[[1, [3]]]]]]]]),
                    ((1, 2, 3), every_element(int, list)),
                    ([1, 2, 3, "a"], every_element(int)))

def test_should_not_match():
    def checker(ob, pattern):
        assert validate_object(ob, pattern) is False, "matched unexpectedly"
    for (ob, pattern) in should_not_match:
        yield (checker, ob, pattern)
