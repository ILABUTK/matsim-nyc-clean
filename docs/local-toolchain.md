# Running Without Root/Apt Access

The top-level README assumes `brew`/system package installs (macOS) or
manual installers (Windows). On a Linux machine where you can't `sudo
apt-get install` (e.g. a sandboxed CI or dev container), all three missing
tools — Java 8 JDK, Maven, Git LFS — can be fetched as self-contained
tarballs/binaries with no root privileges:

```bash
mkdir -p ~/local-tools && cd ~/local-tools

# Maven (official Apache binary distribution)
curl -sL https://archive.apache.org/dist/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.tar.gz -o maven.tar.gz
tar xzf maven.tar.gz

# Java 8 JDK (Eclipse Temurin)
curl -sL "https://api.adoptium.net/v3/binary/latest/8/ga/linux/x64/jdk/hotspot/normal/eclipse" -o jdk8.tar.gz
tar xzf jdk8.tar.gz

# Git LFS (GitHub release binary)
curl -sL https://github.com/git-lfs/git-lfs/releases/download/v3.5.1/git-lfs-linux-amd64-v3.5.1.tar.gz -o gitlfs.tar.gz
tar xzf gitlfs.tar.gz
```

Then point `JAVA_HOME`/`PATH` at the extracted directories (names will
include the actual downloaded versions):

```bash
export JAVA_HOME=~/local-tools/jdk8u492-b09
export PATH=$JAVA_HOME/bin:~/local-tools/apache-maven-3.9.9/bin:~/local-tools/git-lfs-3.5.1:$PATH
```

Why not `apt-get download` + `dpkg-deb -x`? It looked promising (no root
needed to *download* or *extract* a `.deb`), but both the `maven` and
`openjdk-8-jdk` Ubuntu packages are thin wrappers that symlink into
`/usr/share/java` and expect ~40 transitive dependency packages
(`libmaven3-core-java`, `libplexus-*`, etc.) and shared libraries
(`libjli.so`) to already be installed system-wide. Resolving that whole tree
without `apt-get install` isn't practical — the upstream tarballs are fully
self-contained and avoid the problem entirely.

Once the tools are on `PATH`, pull the real LFS data and build/run as normal
(see [architecture.md](architecture.md#build--run)):

```bash
cd /path/to/matsim-nyc-clean
git-lfs install --local
git-lfs pull
mvn clean install -DskipTests
mvn dependency:build-classpath -Dmdep.outputFile=cp.txt
java -Xmx6g -cp "target/classes:$(cat cp.txt)" \
  org.matsim.codeexamples.network.timeDependentNetwork.RunTimeDependentNetworkExample \
  input/config-with-mode-vehicles.xml
```
