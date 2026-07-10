# Input Data

All files live in `input/` and are tracked with Git LFS (see `.gitattributes`).
A fresh clone only has small LFS pointer stubs until `git lfs pull` is run —
see [local-toolchain.md](local-toolchain.md) if `git-lfs` isn't installed.

| File | Approx. size (real) | Purpose |
|---|---|---|
| `config-with-mode-vehicles.xml` | 40K | Main MATSim config; wires together all the files below and holds scoring/strategy/qsim parameters. |
| `separated-network.xml` | ~100M | Road network graph used by the simulation (confirmed correct by Dr. He, per top-level README). |
| `separated-schedule.xml` | ~18M | Transit (pt) schedule paired with `separated-network.xml`. |
| `separated-vehicle.xml` | ~2.3M | Transit vehicle definitions for the schedule above. |
| `BQX-separated-network.xml` | ~100M | Brooklyn-Queens Connector variant of the network. **Not currently used** by the config. |
| `BQX-separated-schedule.xml` | ~18M | BQX variant schedule. **Not currently used**. |
| `final_population.xml` | ~187M | Full population: 389,301 people. Swap in for `subset_population_100.xml` in the config to run at full scale. |
| `subset_population_100.xml` | 60K | 100-person subset of the population, for fast/lightweight test runs. This is what the shipped config uses. |
| `final_subpopulation.xml` | ~42M | Person attributes file (`inputPersonAttributesFile`) — assigns each person to a subpopulation (`man`, `nonman`, `default`, `outside`) used for per-group scoring/strategy parameters. |
| `count.xml` | 40K | Observed traffic counts, used by the `counts` module to compare simulated vs. observed link volumes. |
| `vehicle_type.xml` | 4K | Vehicle type definitions (referenced by the `vehicles` module). |
| `pricing-1.xml` | 4K | Road pricing scheme: $9.16 peak toll. **Currently active** (config points here). |
| `pricing-2.xml` | 4K | Road pricing scheme: $14 peak toll. Alternative scenario, not currently wired in. |

## Switching to the full population

Edit `config-with-mode-vehicles.xml`:

```xml
<module name="plans">
    <param name="inputPlansFile" value="final_population.xml" />
    ...
</module>
```

This is the change referenced by the top-level README's hardware note — full
population runs are memory-intensive independent of the ~262k-link ×
6-time-bin network change events described in
[simulation-model.md](simulation-model.md), so budget accordingly (16GB+ RAM
recommended, more for the full 389k-person population).
