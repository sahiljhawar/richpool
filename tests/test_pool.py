import pytest

from richpool import JoblibPool, MultiPool, SerialPool, choose_pool


def square(x):
    return x * x


def test_choose_pool_processes_one_returns_serial():
    pool = choose_pool(processes=1)
    assert isinstance(pool, SerialPool)


def test_choose_pool_processes_many_returns_multi():
    pool = choose_pool(processes=2)
    assert isinstance(pool, MultiPool)
    pool.close()


def _make_pool(kind, disable=False):
    if kind == "serial":
        return SerialPool(disable=disable)
    if kind == "multi":
        return MultiPool(processes=2, disable=disable)
    if kind == "joblib":
        return JoblibPool(n_jobs=2, disable=disable)
    raise ValueError(kind)


_POOL_KINDS = ["serial", "multi", "joblib"]


@pytest.fixture(params=_POOL_KINDS)
def pool(request):
    with _make_pool(request.param) as p:
        yield p


def test_map_basic(pool):
    result = pool.map(square, range(6))
    assert result == [0, 1, 4, 9, 16, 25]


def test_map_with_callback(pool):
    seen = []
    result = pool.map(square, range(6), callback=seen.append)
    assert sorted(seen) == sorted(result)


def test_map_with_lambda(pool):
    result = pool.map(lambda x: x + 1, range(5))
    assert result == [1, 2, 3, 4, 5]


def test_map_disable(pool):
    result = pool.map(square, range(4), disable=True)
    assert result == [0, 1, 4, 9]


def test_map_explicit_total(pool):
    result = pool.map(square, iter(range(4)), total=4)
    assert result == [0, 1, 4, 9]


def test_is_master(pool):
    assert pool.is_master()
    assert not pool.is_worker()


@pytest.mark.parametrize("kind", _POOL_KINDS)
def test_progress_bar_shown_by_default(kind, capsys):
    with _make_pool(kind) as p:
        p.map(square, range(4), desc="probing")
    out = capsys.readouterr().out
    assert "probing" in out
    assert "100%" in out


@pytest.mark.parametrize("kind", _POOL_KINDS)
def test_progress_bar_hidden_by_call_disable(kind, capsys):
    with _make_pool(kind) as p:
        p.map(square, range(4), desc="probing", disable=True)
    out = capsys.readouterr().out
    assert out == ""


@pytest.mark.parametrize("kind", _POOL_KINDS)
def test_progress_bar_hidden_by_constructor_disable(kind, capsys):
    with _make_pool(kind, disable=True) as p:
        p.map(square, range(4), desc="probing")
    out = capsys.readouterr().out
    assert out == ""


@pytest.mark.parametrize("kind", _POOL_KINDS)
def test_call_disable_overrides_constructor_disable(kind, capsys):
    with _make_pool(kind, disable=True) as p:
        p.map(square, range(4), desc="probing", disable=False)
    out = capsys.readouterr().out
    assert "probing" in out
    assert "100%" in out
