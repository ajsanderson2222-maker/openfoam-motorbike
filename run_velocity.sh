#!/bin/bash
# Usage: ./run_velocity.sh <velocity>
# Reuses existing snappyHexMesh; resets BCs and re-runs solver.
set -e

# Source OpenFOAM — disable strict mode around it to avoid bashrc triggering set -e/-u
set +eu
source /opt/openfoam13/etc/bashrc
set -e

V=$1
TAG="${V}ms"

# k scales as U^2, omega scales as U (relative to 20 m/s baseline)
K=$(python3 -c "print(f'{0.24*(int($V)/20)**2:.4f}')")
OMEGA=$(python3 -c "print(f'{1.78*(int($V)/20):.4f}')")

echo "=== Running U=$V m/s  k=$K  omega=$OMEGA ==="

# Update initial conditions (plain key-value, no OF header needed for include file)
python3 - <<PYEOF
content = f"""flowVelocity         ($V 0 0);
pressure             0;
turbulentKE          $K;
turbulentOmega       $OMEGA;
"""
with open("0/include/initialConditions", "w") as f:
    f.write(content)
PYEOF

# Copy U.orig -> U
cp 0/U.orig 0/U

# Clean solution time dirs from all processor dirs (keep constant/ and 0/)
for d in processor*/; do
    find "$d" -maxdepth 1 -name "[1-9]*" -type d -exec rm -rf {} + 2>/dev/null || true
    find "$d" -maxdepth 1 -name "5*"     -type d -exec rm -rf {} + 2>/dev/null || true
done

# Re-copy 0/ BCs to processor dirs
decomposePar -copyZero > log.decomposePar_${TAG} 2>&1
echo "decomposePar done"

# Solve
mpirun -np 8 potentialFoam -parallel > log.potentialFoam_${TAG} 2>&1
echo "potentialFoam done"
mpirun -np 8 foamRun -parallel > log.foamRun_${TAG} 2>&1
echo "foamRun done"

reconstructPar -latestTime > log.reconstructPar_${TAG} 2>&1
echo "reconstructPar done"

echo "=== $V m/s complete ==="
