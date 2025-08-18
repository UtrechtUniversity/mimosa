MIMOSA has some built-in effort sharing regimes. In this example, they are used in combination with a carbon budget (but it could be used in CBA mode). The welfare module is set to cost minimising, as this is typically used with effort sharing regimes. Effort sharing would be impossible without emission trading. Finally, this would often be infeasible for some regions, if we didn't allow for some extra financial transfers beyond just emission trading, which is why we set the relative mitigation cost minimum level to a small negative number.

```python
--8<-- "tests/runs/run_effortsharing.py"
```

1. Some effort sharing regimes can lead to large financial transfers between regions. If baseline carbon intensities are used instead of just baseline emissions, the baseline emissions can vary significantly, leading to numerical instability. Especially for ECPC regime, this setting is important.
2. Some effort sharing regimes require such large financial transfers that they are infeasible without allowing for some extra financial transfers beyond just emission trading. This is why we set the relative mitigation cost minimum level to a negative number.
