import pytest
import more_itertools
from more_itertools import replace

assert more_itertools.__file__.startswith("/workspace/more_itertools/")


@pytest.mark.parametrize("window_size", [2, 3, 4])
@pytest.mark.parametrize("match", [False, True])
def test_empty_input_never_yields_padding(window_size, match):
    assert list(replace([], lambda *args: match, [9], window_size=window_size)) == []


def test_actual_none_is_preserved():
    assert list(replace([None], lambda *args: False, [9], window_size=2)) == [None]


def test_normal_replacement_is_preserved():
    assert list(replace([1, 2, 3], lambda *args: args == (1, 2), [9], window_size=2)) == [9, 3]


def test_default_empty_input():
    assert list(replace([], lambda *args: True, [9])) == []
