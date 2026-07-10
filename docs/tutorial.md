# Tutorial: MATSim and This Project

Written for someone who's new to MATSim. If you already know MATSim, skip to
[Part 2](#part-2-this-project).

## Part 1: MATSim concepts

MATSim (Multi-Agent Transport Simulation) simulates a whole city's daily
travel by simulating every person individually, then having them learn
better travel behavior over repeated simulated days.

### The core loop

Each **iteration** is one simulated day, and MATSim runs many iterations in
a row:

```
   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
   │  Replanning │ ──▶ │   Mobsim    │ ──▶ │   Scoring   │ ──┐
   │ (some agents│     │ (simulate   │     │ (rate how   │   │
   │  try a new  │     │  everyone's │     │  good each  │   │
   │  plan)      │     │  day on the │     │  day was)   │   │
   └─────────────┘     │  network)   │     └─────────────┘   │
          ▲            └─────────────┘                       │
          └───────────────────────────────────────────────────┘
                         next iteration
```

1. **Replanning**: each agent has a memory of a few past "plans" (a plan =
   a sequence of activities and trips for the day, e.g. home → work → gym →
   home, each with a mode, route, and timing). Some fraction of agents,
   controlled by the `strategy` module, try a *modified* plan this
   iteration — a different route, a different mode, a different departure
   time — instead of repeating their best plan so far.
2. **Mobsim** (mobility simulation): every agent's plan for the day is
   executed simultaneously on the road/transit network. This is where
   congestion emerges — if too many agents try to use the same link at the
   same time, they queue up and slow down. This project uses `qsim`, a
   queue-based (not physics-based) traffic simulator.
3. **Scoring**: each agent's *executed* day (which may differ from their
   plan if they got stuck in traffic) is converted into a single utility
   score — time spent at activities is worth something, travel time and
   cost are penalties, arriving early/late is penalized, etc. The formula
   and its weights live in the `planCalcScore` config module.
4. Agents remember their scored plans. Over many iterations, agents that
   keep trying variations converge toward plans that score well *given what
   everyone else is doing* — this is why the process is called reaching
   (approximate) equilibrium.

### Key vocabulary

| Term | Meaning |
|---|---|
| **Person / Agent** | One simulated traveler with attributes (subpopulation, etc.) |
| **Plan** | One full day's schedule of activities + trips for a person |
| **Activity** | A stop in a plan: Home, Work, School, etc., with a duration |
| **Leg / Trip** | The travel between two activities, with a mode and route |
| **Network** | The graph of nodes and links (road/rail segments) agents travel on |
| **Link** | One directed road/rail segment, with length, freespeed, capacity |
| **Events** | A time-stamped log of everything that happened during one mobsim run (departures, link entries/exits, vehicle boardings, etc.) — this is MATSim's rawest, most complete output |
| **Scoring function** | The formula that converts an executed day into a utility number |
| **Strategy** | A replanning move an agent might try (reroute, change mode, shift time, or just repeat their best plan) |
| **Subpopulation** | A named group of agents (here: `man`, `nonman`, `default`, `outside`) that can have different scoring/strategy parameters |
| **Iteration** | One pass through replan → simulate → score, across the whole population |

If you want the deeper reference, the [MATSim book](https://www.matsim.org/the-book)
is the canonical source; this tutorial only covers what you need to work
with this repo.

## Part 2: This project

### What scenario is this?

A New York City simulation: real road network, real transit schedule
(subway/bus), a calibrated travel-demand population, congestion pricing
(tolls), and car/taxi/FHV/pt/walk/bike mode choice. See
[data-inputs.md](data-inputs.md) for what each input file is, and
[simulation-model.md](simulation-model.md) for how modes, scoring, tolling,
and the time-of-day network calibration work.

### The one thing that makes this scenario special

Most MATSim tutorials use a static network. This one uses a
**time-variant network**: link capacity and freespeed change at 7 fixed
times of day (rush hour vs. off-peak), using calibrated multipliers. That
logic lives entirely in one file:
[`RunTimeDependentNetworkExample.java`](../src/main/java/org/matsim/codeexamples/network/timeDependentNetwork/RunTimeDependentNetworkExample.java) —
see [architecture.md](architecture.md#entry-point) for a walkthrough.

### Running it yourself

Full instructions: top-level [README.md](../README.md#how-to-run). Short
version:

```bash
mvn clean install -DskipTests
mvn dependency:build-classpath -Dmdep.outputFile=cp.txt
java -Xmx6g -cp "target/classes:$(cat cp.txt)" \
  org.matsim.codeexamples.network.timeDependentNetwork.RunTimeDependentNetworkExample \
  input/config-with-mode-vehicles.xml
```

The shipped config runs only 3 iterations (`lastIteration=2`) on a
**100-person subset** of the population (`subset_population_100.xml`) — this
is meant for fast iteration on code/config changes, not for real results.
Swap in `final_population.xml` (389,301 people) and raise `lastIteration`
(MATSim scenarios typically need 50-200+ iterations to converge) once you
want a real run — see [data-inputs.md](data-inputs.md#switching-to-the-full-population).
That's much more compute — budget accordingly and see the note about
`numberOfThreads` below.

Each run writes everything to `output/<outputDirectory>/` (set in the
config's `controler` module — currently `bqx-8mph-newparams`). The `output/`
folder is gitignored; nothing there is version-controlled.

### Making sense of the output

A finished run directory has ~20 files. The ones worth knowing:

| File | What it is |
|---|---|
| `*.output_events.xml.gz` | Every event during the *last* iteration's mobsim: departures, link entries/exits, boardings, etc. This is the ground truth for any custom analysis. |
| `*.output_network.xml.gz` | The network as actually simulated (after time-variant changes attached) |
| `*.output_plans.xml.gz` | Each agent's final plan |
| `*.modestats.txt` / `.png` | Mode share per iteration |
| `*.scorestats.txt` / `.png` | Average agent score (executed/worst/average/best) per iteration — the standard "did it converge" chart |
| `*.stopwatch.txt` / `.png` | Wall-clock time spent in each phase per iteration |
| `*.output_toll.xml.gz` | Which links are tolled and how much |
| `*.logfileWarningsErrors.log` | Just the warnings/errors from the full log, for quick sanity-checking a run |

The raw `.txt`/`.xml.gz` files are functional but not presentation-ready —
that's what the `analysis/` scripts below are for.

### Turning output into figures and maps

The `analysis/` directory (Python, not part of the Maven build) is its own
[uv](https://docs.astral.sh/uv/)-managed project with two scripts:

Run from the repo root so the default input/output paths line up:

```bash
uv run --project analysis analysis/convergence_charts.py output/bqx-8mph-newparams
uv run --project analysis analysis/link_volumes.py       output/bqx-8mph-newparams
```

`uv run` creates an isolated virtualenv and installs the pinned
dependencies from `uv.lock` on first use — no manual `pip install` step,
and no risk of polluting your system Python. If you don't have `uv`,
install it per [the uv docs](https://docs.astral.sh/uv/getting-started/installation/)
(no root required — it's a single binary you can drop in `~/.local/bin`).

`convergence_charts.py` reads `modestats.txt` / `scorestats.txt` and writes
clean mode-share and score-convergence line charts.

`link_volumes.py` reads the network + events files and produces:
- `link_volumes.geojson` — every link with a `volume` column (vehicles that
  entered it during the simulated day), in WGS84, for use in QGIS or any
  other GIS tool
- `link_volume_map.png` — a static map (full network in light gray, used
  links colored by volume) — good for a paper figure
- `link_volume_map.html` — the same thing, interactive (pan/zoom/hover), via
  `geopandas.explore()` + folium/Leaflet
- `hourly_loading.png` — total link-entry events by hour of day, i.e. when
  the network is busiest

All outputs land in `analysis/output/` (gitignore that directory too if you
don't want generated figures in version control — it isn't currently
ignored, so check before committing).

**Viewing the interactive map over SSH**: since this runs on a headless
server, `link_volume_map.html` is just a static HTML file — open it through
VS Code's file explorer (Remote-SSH will render it), or serve the folder
(`python3 -m http.server --directory analysis/output 8000`) and let VS Code
auto-forward port 8000 to your local browser.

### Compute notes for this machine

This server has 128 cores (you can use up to 64). Two config knobs actually
use them:

- `qsim.numberOfThreads` / `global.numberOfThreads` (currently `16` in
  `config-with-mode-vehicles.xml`) — parallelizes the mobsim and routing.
  Worth raising once you run the full 389k-person population; not worth it
  for the 100-person subset (thread overhead exceeds the benefit).
- The network-change-event setup loop in `RunTimeDependentNetworkExample`
  (building ~262k×7 change events) is single-threaded application code —
  more cores won't speed that part up regardless of config.

See [local-toolchain.md](local-toolchain.md) if you ever need to rebuild the
Java 8 / Maven / Git LFS toolchain from scratch without root access.

### Suggested next steps

- Run the full population (`final_population.xml`) with more iterations to
  get a converged, publication-worthy result — the 100-person/3-iteration
  run in this repo right now is a smoke test, not a result.
- Compare `pricing-1.xml` vs `pricing-2.xml` (different peak toll amounts)
  by pointing `roadpricing.tollLinksFile` at each and diffing the resulting
  mode share / link volumes.
- Extend `analysis/link_volumes.py` to bucket volumes by hour (the events
  parser already extracts `time`) if you want AM-peak vs. PM-peak maps
  instead of whole-day totals.
