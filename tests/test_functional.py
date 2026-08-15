from functools import partial

import pytest

from richpool import p_imap, p_map, p_uimap, p_umap, t_imap, t_map


def add_1(a):
    return a + 1


def add_2(a, b):
    return a + b


def add_3(a, b, c=0):
    return a + 2 * b + 3 * c


# (func, is_generator, is_ordered)
_VARIANTS = [
    pytest.param(p_map, False, True, id="p_map"),
    pytest.param(p_imap, True, True, id="p_imap"),
    pytest.param(p_umap, False, False, id="p_umap"),
    pytest.param(p_uimap, True, False, id="p_uimap"),
    pytest.param(t_map, False, True, id="t_map"),
    pytest.param(t_imap, True, True, id="t_imap"),
]

# Only the p_* functions accept `kind` (t_map/t_imap are always sequential).
_PARALLEL_VARIANTS = [
    pytest.param(p_map, False, True, id="p_map"),
    pytest.param(p_imap, True, True, id="p_imap"),
    pytest.param(p_umap, False, False, id="p_umap"),
    pytest.param(p_uimap, True, False, id="p_uimap"),
]


def _materialize(result, is_generator):
    return list(result) if is_generator else result


def _check(result, expected, is_ordered):
    if is_ordered:
        assert result == expected
    else:
        assert sorted(result) == sorted(expected)


@pytest.mark.parametrize("func, is_generator, is_ordered", _VARIANTS)
def test_one_list(func, is_generator, is_ordered):
    result = _materialize(func(add_1, [1, 2, 3]), is_generator)
    _check(result, [2, 3, 4], is_ordered)


@pytest.mark.parametrize("func, is_generator, is_ordered", _VARIANTS)
def test_two_lists(func, is_generator, is_ordered):
    result = _materialize(func(add_2, [1, 2, 3], [10, 11, 12]), is_generator)
    _check(result, [11, 13, 15], is_ordered)


@pytest.mark.parametrize("func, is_generator, is_ordered", _VARIANTS)
def test_two_lists_and_one_single(func, is_generator, is_ordered):
    result = _materialize(func(partial(add_3, 5), [1, 2, 3], [10, 11, 12]), is_generator)
    _check(result, [37, 42, 47], is_ordered)


@pytest.mark.parametrize("func, is_generator, is_ordered", _VARIANTS)
def test_one_list_and_two_singles(func, is_generator, is_ordered):
    result = _materialize(func(partial(add_3, 5, c=-2), [1, 2, 3]), is_generator)
    _check(result, [1, 3, 5], is_ordered)


@pytest.mark.parametrize("func, is_generator, is_ordered", _VARIANTS)
def test_lambda(func, is_generator, is_ordered):
    result = _materialize(func(lambda x: x * x, [1, 2, 3]), is_generator)
    _check(result, [1, 4, 9], is_ordered)


@pytest.mark.parametrize("func, is_generator, is_ordered", _VARIANTS)
def test_num_cpus_float(func, is_generator, is_ordered):
    result = _materialize(func(add_1, [1, 2, 3], num_cpus=0.5), is_generator)
    assert sorted(result) == [2, 3, 4]


@pytest.mark.parametrize("func, is_generator, is_ordered", _VARIANTS)
def test_num_cpus_int(func, is_generator, is_ordered):
    result = _materialize(func(add_1, [1, 2, 3], num_cpus=2), is_generator)
    assert sorted(result) == [2, 3, 4]


@pytest.mark.parametrize("func, is_generator, is_ordered", _VARIANTS)
def test_total_override(func, is_generator, is_ordered):
    result = _materialize(func(add_1, [1, 2, 3], total=3), is_generator)
    assert sorted(result) == [2, 3, 4]


@pytest.mark.parametrize("func, is_generator, is_ordered", _VARIANTS)
def test_disable(func, is_generator, is_ordered):
    result = _materialize(func(add_1, [1, 2, 3], disable=True), is_generator)
    assert sorted(result) == [2, 3, 4]


@pytest.mark.parametrize("func, is_generator, is_ordered", _VARIANTS)
def test_progress_bar_shown_by_default(func, is_generator, is_ordered, capsys):
    _materialize(func(add_1, [1, 2, 3], desc="probing"), is_generator)
    out = capsys.readouterr().out
    assert "probing" in out
    assert "100%" in out


@pytest.mark.parametrize("func, is_generator, is_ordered", _VARIANTS)
def test_progress_bar_hidden_by_disable(func, is_generator, is_ordered, capsys):
    _materialize(func(add_1, [1, 2, 3], desc="probing", disable=True), is_generator)
    out = capsys.readouterr().out
    assert out == ""


@pytest.mark.parametrize("func, is_generator, is_ordered", _PARALLEL_VARIANTS)
def test_kind_defaults_to_process(func, is_generator, is_ordered):
    result = _materialize(func(add_1, [1, 2, 3]), is_generator)
    _check(result, [2, 3, 4], is_ordered)


@pytest.mark.parametrize("func, is_generator, is_ordered", _PARALLEL_VARIANTS)
def test_kind_process(func, is_generator, is_ordered):
    result = _materialize(func(add_1, [1, 2, 3], kind="process"), is_generator)
    _check(result, [2, 3, 4], is_ordered)


@pytest.mark.parametrize("func, is_generator, is_ordered", _PARALLEL_VARIANTS)
def test_kind_thread(func, is_generator, is_ordered):
    result = _materialize(func(add_1, [1, 2, 3], kind="thread"), is_generator)
    _check(result, [2, 3, 4], is_ordered)


@pytest.mark.parametrize("func, is_generator, is_ordered", _PARALLEL_VARIANTS)
def test_kind_thread_multiple_iterables(func, is_generator, is_ordered):
    result = _materialize(func(add_2, [1, 2, 3], [10, 11, 12], kind="thread"), is_generator)
    _check(result, [11, 13, 15], is_ordered)


@pytest.mark.parametrize("func, is_generator, is_ordered", _PARALLEL_VARIANTS)
def test_kind_invalid_raises(func, is_generator, is_ordered):
    with pytest.raises(ValueError, match="Invalid pool kind"):
        _materialize(func(add_1, [1, 2, 3], kind="bogus"), is_generator)
