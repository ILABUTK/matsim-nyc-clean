# Simulation Model

This is a MATSim activity-based traffic simulation of New York City. Agents
(`Person`s) hold daily plans (chains of activities connected by trips) and,
across iterations, learn/replan toward higher-scoring plans.

## Transport modes

Configured in `planCalcScore` / `planscalcroute` / `subtourModeChoice`:

| Mode | Type | Notes |
|---|---|---|
| `car` | network mode | tolled via road pricing |
| `taxi` | network mode | own scoring constant/utility per subpopulation |
| `FHV` | network mode | for-hire vehicle (e.g. Uber/Lyft-style) |
| `pt` | transit | routed via SwissRailRaptor, uses `separated-schedule.xml` |
| `walk`, `bike`, `ride`, `cb` (carshare/bikeshare?) | teleported modes | travel time from beeline distance × factor / speed, no network assignment |
| `access_walk`, `egress_walk`, `transit_walk` | teleported | walk legs at the start/end of a pt trip |

Mode choice happens via the `SubtourModeChoice` replanning strategy.

## Subpopulations and scoring

The population is split into subpopulations (`man`, `nonman`, `default`,
`outside`), each with its own `scoringParameters` block in the config —
different `marginalUtilityOfMoney`, mode-choice constants, and travel-time
disutilities per mode. These were fit via an SPSA calibration process (see
the note in the top-level README about hardcoded `ExpressFactor`/
`ArterialFactor` values, which came from the same effort).

Replanning strategy weights also differ by subpopulation (`strategy`
module): `man`/`nonman` use `SelectExpBeta` (0.7) + `TimeAllocationMutator`
(0.1) + `ReRoute` (0.1) + `SubtourModeChoice` (0.1); `outside` only uses
`SelectExpBeta` (1.0), i.e. it never re-routes or changes mode/timing.

Scoring itself uses MATSim's standard Charypar-Nagel formulation
(`CharyparNagelActivityScoring`, `CharyparNagelLegScoring`,
`CharyparNagelMoneyScoring`, `CharyparNagelAgentStuckScoring`), assembled in
`TaxiScoringFunctionFactory`
(`src/main/java/.../scoring/example16customscoring/RunCustomScoringExampleTaxi.java`)
plus an additional `NewScoring` term.

## Time-variant network (peak/off-peak capacity and speed)

`RunTimeDependentNetworkExample.main()` attaches `NetworkChangeEvent`s to
every link at 7 times of day (0, 7, 10, 13, 16, 19, 22h). Two sets of
calibrated multipliers are applied:

- **Express links** (freespeed > 33 m/s, i.e. highways): capacity scaled by
  `ExpressFactor[]`, freespeed by `ExpressFactor1[]`.
- **Arterial links** (freespeed ≤ 33 m/s): capacity scaled by
  `ArterialFactor[]`; freespeed scaling picks one of three factor arrays
  (`ArterialFactor1/2/3`) depending on the link's *original* freespeed band
  (>22, 10–22, or <10 m/s).

Both factor sets are hardcoded doubles calibrated via SPSA — the file has
several earlier calibration attempts left in as commented-out arrays for
reference/history.

## Road pricing

`RoadPricingConfigGroup` + `RoadPricingSchemeUsingTollFactor` implement a
cordon/link toll: `TollFactor.getTollFactor()` returns `1` for vehicles whose
type id is `"car"` and `0` otherwise, so only cars pay. The actual toll
amounts and tolled links live in `input/pricing-1.xml` ($9.16 peak) or
`input/pricing-2.xml` ($14 peak) — the config currently points at
`pricing-1.xml`.

## Custom events (`ScoreEngine`)

`RunTimeDependentNetworkExample.ScoreEngine` is an event handler
(`LinkLeaveEventHandler`, `PersonLeavesVehicleEventHandler`) that derives
higher-level, mode-specific events from raw MATSim events and re-emits them
through the `EventsManager`:

- On `PersonLeavesVehicleEvent`: if the person *is* the vehicle (i.e. a
  private car, since `personId.equals(vehicleId)`), emits
  `PersonParkingEvent`. If the vehicle id contains `"taxi"` or `"FHV"`, emits
  `PersonLeavesTaxiEvent` / `PersonLeavesFHVEvent` instead.
- On `LinkLeaveEvent`: if the link is in the `toll1` or `toll2` static link-id
  arrays (hardcoded in the class), emits `TollPersonEvent1` /
  `TollPersonEvent2`.

These synthetic events exist so that the custom scoring functions in
`scoring/example16customscoring/` (e.g. `ParkScoring`, `RainScoring`,
`FHVScoring`, `ExtremeTimePenaltyScoring`) can react to them. Note the
top-level README's "known open items": rain-conditioning logic is referenced
in a comment (`// It starts raining on link 1 at 7:30.`) but never actually
implemented — no rain-triggering handler exists despite `RainScoring` /
`RainOnPersonEvent` classes being present.

## Iteration loop

Set in the `controler` module: `firstIteration`/`lastIteration` bound the
loop, `mobsim=qsim` selects the queue-based mesoscopic traffic simulator,
`routingAlgorithmType=FastAStarLandmarks` selects the router. Within each
iteration MATSim scores the previous iteration's executed plans, has agents
replan according to the `strategy` weights above, then re-simulates with
`qsim`.
