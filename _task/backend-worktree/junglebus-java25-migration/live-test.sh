#!/usr/bin/env bash
set -euo pipefail
task_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
export JAVA_HOME=/home/haodev/.sdkman/candidates/java/25.0.4.1-tem
if [[ $# -lt 2 || $# -gt 3 ]]; then
  printf '用法：./live-test.sh <subscriptionId> <新输出目录> [JSON|PROTOBUF]\n' >&2
  exit 2
fi
java_classpath="$task_root/metanet4j-junglebus/target/classes"
for jar_path in \
  tools/jackson/core/jackson-databind/3.1.5/jackson-databind-3.1.5.jar \
  tools/jackson/core/jackson-core/3.1.5/jackson-core-3.1.5.jar \
  com/fasterxml/jackson/core/jackson-annotations/2.21/jackson-annotations-2.21.jar \
  com/google/protobuf/protobuf-java/4.35.1/protobuf-java-4.35.1.jar; do
  java_classpath="$java_classpath:$task_root/.cache/maven/$jar_path"
done
exec "$JAVA_HOME/bin/java" --class-path "$java_classpath" "$task_root/metanet4j-junglebus/examples/LiveSubscription.java" "$@"
