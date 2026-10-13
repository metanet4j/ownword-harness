#!/usr/bin/env bash
set -euo pipefail
task_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
export JAVA_HOME=/home/haodev/.sdkman/candidates/java/25.0.4.1-tem
export PATH="$JAVA_HOME/bin:$PATH"
cd -- "$task_root/metanet4j-junglebus"
exec /home/haodev/.sdkman/candidates/maven/3.9.16/bin/mvn -s "$task_root/settings.xml" -Dmaven.repo.local="$task_root/.cache/maven" -B "$@"
