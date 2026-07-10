#!/usr/bin/env bash
# Runs the 3893-person (~1/100 of the full population), 100-iteration scenario.
# Population sample: input/subset_population_3893.xml (regenerate with
# analysis/sample_population.py). Config: input/config-3893-100iter.xml.
# Output: output/run-3893-100iter/ (gitignored).
#
# Env vars: XMX (default 24g), THREADS (default 32, must match the config's
# qsim/global numberOfThreads if you override it there too).
set -euo pipefail
cd "$(dirname "$0")/.."

XMX="${XMX:-24g}"
CONFIG="input/config-3893-100iter.xml"

mvn -q compile
mvn dependency:build-classpath -Dmdep.outputFile=cp.txt -q

java -Xmx"$XMX" -cp "target/classes:$(cat cp.txt)" \
  org.matsim.codeexamples.network.timeDependentNetwork.RunTimeDependentNetworkExample \
  "$CONFIG"
