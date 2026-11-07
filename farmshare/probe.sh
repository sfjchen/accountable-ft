#!/usr/bin/env bash
# farmshare/probe.sh: prints the cluster facts the sbatch scripts depend on (GPU model, memory, time caps, QOS
# limits, CUDA modules, quotas). Read-only. Usage: bash farmshare/probe.sh | tee ~/probe.txt
set -euo pipefail
# shellcheck source=farmshare/env.sh
source "${SCRATCH:-/scratch/users/$USER}/accountable-ft/farmshare/env.sh" 2>/dev/null || true

# Prints a header, then runs the command and keeps going if it fails.
run() {
  echo
  echo "== $*"
  "$@" 2>&1 || echo "(exit $?)"
}

run sinfo -p gpu -o "%P %a %l %D %c %m %G %T"
run sinfo -p gpu -N -o "%N %c %m %G %f %T"
run sinfo -s
run scontrol show partition gpu
run scontrol show partition normal
run sacctmgr -P show qos gpu,normal,long format=Name,MaxTRESPU,MaxWall,MaxJobsPU,MaxSubmitPU,Priority
run sacctmgr -P show assoc user="$USER" format=Cluster,Account,User,Partition,QOS,DefaultQOS,MaxTRES,MaxWall
run module -t avail cuda
run df -h "$HOME" "${SCRATCH:-/scratch/users/$USER}"
run quota -s
