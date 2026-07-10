# Architecture

## Tech stack

- **Java 8** (language level pinned in `pom.xml`; newer JDKs can build MATSim's
  dependency tree but the project targets 8 specifically)
- **Maven** for dependency management and build (`pom.xml`)
- **MATSim 11.0** (`org.matsim:matsim`) as the simulation core, pulled from
  `repo.matsim.org`
- **MATSim contribs**: `minibus`, `otfvis`, `roadpricing`, `taxi`, `av`, `freight`
- **matsim-sbb-extensions 11.5** (SBB SwissRailRaptor) for transit routing
- Data is versioned with **Git LFS** — the XML files under `input/` are large
  (the network and population files are tens to hundreds of MB) and are
  stored as LFS pointers in the repo.

## Module layout

```
src/main/java/org/matsim/codeexamples/
├── network/timeDependentNetwork/
│   └── RunTimeDependentNetworkExample.java   # main entry point
└── scoring/example16customscoring/           # custom scoring functions and events
```

`analysis/` is a separate, [uv](https://docs.astral.sh/uv/)-managed Python
project (its own `pyproject.toml`/`uv.lock`) for post-processing MATSim
output into GIS maps and charts — see
[tutorial.md](tutorial.md#turning-output-into-figures-and-maps). It's
independent of the Maven build; nothing under `analysis/` is needed to
build or run the Java simulation.

There is a single Maven module (no multi-module build). `mvn clean install`
produces two jars in `target/`:
- `matsim-code-examples-0.0.1-SNAPSHOT.jar` — just this project's classes
- `matsim-code-examples-0.0.1-SNAPSHOT-jar-with-dependencies.jar` — a fat jar
  with `org.matsim.gui.MATSimGUI` as `Main-Class` (produced by
  `maven-assembly-plugin`)

## Entry point

`org.matsim.codeexamples.network.timeDependentNetwork.RunTimeDependentNetworkExample`
is the only class with a runnable `main`. It takes one argument: the path to
a MATSim config XML file (e.g. `input/config-with-mode-vehicles.xml`).

At a high level, `main()`:

1. Loads the config and forces `network().setTimeVariantNetwork(true)` —
   this must be set before the scenario loads.
2. Loads the `Scenario` (network, population, transit schedule, vehicles).
3. Builds a `RoadPricingSchemeUsingTollFactor` — cars pay tolls, other vehicle
   types don't (see `TollFactor` in the same file).
4. Iterates every link in the network and attaches `NetworkChangeEvent`s that
   scale flow capacity and freespeed at 7 fixed times of day (0, 7, 10, 13,
   16, 19, 22h), using separate calibrated factors for "express" links
   (freespeed > 33 m/s) vs. "arterial" links. This is what the
   `RunTimeDependentNetworkExample` name refers to, and it's also the
   memory-heavy part described in the top-level README's hardware note
   (~262k links × 6 time bins of change events).
5. Constructs a `Controler`, wires in:
   - `SwissRailRaptorModule` (transit routing)
   - `RoadPricingModule` with the toll scheme from step 3
   - `ScoreEngine` (event handler, see below)
   - A custom `ScoringFunctionFactory` (`TaxiScoringFunctionFactory`, from the
     `scoring` package, reused here even though the class name says "Taxi")
6. Runs the controller (`controler.run()`), which executes the MATSim
   iteration loop (score → replan → simulate) for the number of iterations
   set in the config's `controler` module.

See [simulation-model.md](simulation-model.md) for what `ScoreEngine` and the
scoring functions actually model.

## Build & run

Documented in the top-level [README.md](../README.md#how-to-run). Summary:

```bash
mvn clean install -DskipTests
mvn dependency:build-classpath -Dmdep.outputFile=cp.txt
java -Xmx6g -cp "target/classes:$(cat cp.txt)" \
  org.matsim.codeexamples.network.timeDependentNetwork.RunTimeDependentNetworkExample \
  input/config-with-mode-vehicles.xml
```

If you're on a machine without root/apt access, see
[local-toolchain.md](local-toolchain.md) for how to get Java 8, Maven, and
Git LFS working without installing system packages.
