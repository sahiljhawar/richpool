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
