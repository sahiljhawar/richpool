# Examples

Every example below is executed as part of building the docs (via
[sphinx-exec-code](https://github.com/spacemanspiff2007/sphinx-exec-code)).

## SerialPool

```{eval-rst}
.. exec_code::
   :filename: ../examples/serial_pool_example.py
   :linenos:
```

## MultiPool

```{eval-rst}
.. exec_code::
   :filename: ../examples/multi_pool_example.py
   :linenos:
```

## MultiPool with emcee

Adapted from `schwimmbad`'s "Using MultiPool with emcee" example:
https://schwimmbad.readthedocs.io/en/latest/examples/index.html#using-multipool-with-emcee

`emcee`'s `EnsembleSampler` accepts any pool object exposing a `.map()` method, so
`richpool`'s `MultiPool` can be passed directly to parallelize likelihood
evaluations across worker processes. `log_probability` sleeps briefly to stand
in for a realistic, non-trivial likelihood (e.g. one involving a simulation
or numerical integration); without that, each evaluation is a handful of
floating-point ops that finishes in microseconds.

`emcee` calls `pool.map()` several times per MCMC step internally, so letting
MultiPool render its usual per-call progress bar produces a handful of tiny,
near-instant, low-information bars, not real progress bars. Passing `disable=True` to
`MultiPool`'s constructor turns off those per-call bars (the default for every
`map()` call unless a call overrides it), and a single rich progress bar below
tracks real progress across the `n_steps` MCMC steps instead, while the
likelihood evaluations for each step still run in parallel underneath it.

Needs the extra `emcee`, `numpy`, and `matplotlib` dependencies:
```bash
uv pip install emcee numpy matplotlib
```

```{eval-rst}
.. exec_code::
   :filename: ../examples/emcee_multipool_example.py
   :linenos:
```

```{eval-rst}
.. plot:: ../examples/emcee_multipool_example.py
```

## JoblibPool

```{eval-rst}
.. exec_code::
   :filename: ../examples/joblib_pool_example.py
   :linenos:
```

## MPIPool

`MPIPool` needs to be launched with `mpiexec`, so it can't run inline like the
examples above. Run it with:

```
mpiexec -n 4 python examples/mpi_pool_example.py
```

```{eval-rst}
.. literalinclude:: ../examples/mpi_pool_example.py
   :language: python
   :linenos:
```

## p_map

```{eval-rst}
.. exec_code::
   :filename: ../examples/functional_pmap_example.py
   :linenos:
```

## p_imap

```{eval-rst}
.. exec_code::
   :filename: ../examples/functional_pimap_example.py
   :linenos:
```

## p_umap

```{eval-rst}
.. exec_code::
   :filename: ../examples/functional_pumap_example.py
   :linenos:
```

## p_uimap

```{eval-rst}
.. exec_code::
   :filename: ../examples/functional_puimap_example.py
   :linenos:
```

## t_map

```{eval-rst}
.. exec_code::
   :filename: ../examples/functional_tmap_example.py
   :linenos:
```

## t_imap

```{eval-rst}
.. exec_code::
   :filename: ../examples/functional_timap_example.py
   :linenos:
```
