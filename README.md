# MATSim NYC — Cleaned Project

## Setup

### macOS

1. Install Homebrew (if not already installed):

    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

2. Install Java 8:

    brew install --cask temurin8

   Verify with `java -version` — should show `1.8.0_...`

3. Install Maven:

    brew install maven

   Verify with `mvn -version`

4. Install Git LFS:

    brew install git-lfs
    git lfs install

   Verify with `git lfs version`

5. Install IntelliJ IDEA (recommended IDE):

    brew install --cask intellij-idea-ce

### Windows

1. Install Java 8 from https://adoptium.net/temurin/releases/?version=8
2. Install Maven from https://maven.apache.org/download.cgi (unzip and add bin to PATH)
3. Install Git LFS from https://git-lfs.com, then run: git lfs install
4. Install IntelliJ IDEA from https://www.jetbrains.com/idea/download

## Hardware requirement

At least 16GB RAM recommended. This simulation creates a large number of network-wide time-variant change events (approximately 262,000 links times 6 time bins), which is memory-intensive independent of population size. 

## Opening the project

1. Open the project folder in IntelliJ (File then Open, select the folder containing pom.xml). Let IntelliJ import it as a Maven project when prompted.
2. Set the Project SDK to Java 8: File then Project Structure then Project then SDK.
3. Build once to confirm everything resolves:

    mvn clean install -DskipTests

   Should end with BUILD SUCCESS.

## How to run

Entry point class:
org.matsim.codeexamples.network.timeDependentNetwork.RunTimeDependentNetworkExample

This class takes the config file path as a command-line argument (args[0]).

### Running in IntelliJ

Edit Run Configuration for RunTimeDependentNetworkExample:
- Program arguments: input/config-with-mode-vehicles.xml
- VM options: -Xmx6g (or higher, depending on available RAM)

### Running from command line

    mvn dependency:build-classpath -Dmdep.outputFile=cp.txt
    java -Xmx6g -cp "target/classes:\$(cat cp.txt)" org.matsim.codeexamples.network.timeDependentNetwork.RunTimeDependentNetworkExample input/config-with-mode-vehicles.xml

## Input files

- config-with-mode-vehicles.xml — main config
- final_population.xml — full population (389,301 people)
- subset_population_100.xml — 100-person subset for lightweight testing
- separated-network.xml and separated-schedule.xml — network and transit schedule (confirmed correct by Dr. He)
- BQX-separated-network.xml and BQX-separated-schedule.xml — Brooklyn-Queens Connector variants (not currently used)
- pricing-1.xml ($9.16 peak toll) and pricing-2.xml ($14 peak toll) — road pricing scenarios; config currently points to pricing-1.xml
- count.xml, vehicle_type.xml, separated-vehicle.xml, final_subpopulation.xml — supporting data

## Known open items

- Rain-conditioning logic referenced during project demo is not yet implemented in this code — only a leftover comment exists ("It starts raining on link 1 at 7:30").
- The ExpressFactor and ArterialFactor speed-capacity values in the code are already calibrated (hardcoded), sourced from the original SPSA calibration process.
