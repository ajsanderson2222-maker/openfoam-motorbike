# OpenFOAM Motorbike RANS — Velocity Sweep

Steady-state RANS simulation of the OpenFOAM motorbike tutorial geometry across three freestream velocities (20, 30, 40 m/s). Uses the k-ω SST turbulence model with the SIMPLE algorithm.

## Setup

- **Solver:** `incompressibleFluid` (foamRun), steady SIMPLE
- **Turbulence:** k-ω SST (RAS)
- **Mesh:** snappyHexMesh on the motorBike STL geometry (~200k cells)
- **Decomposition:** scotch, 8 cores
- **Iterations:** 500 per velocity

### Turbulence inlet conditions

Scaled from a 20 m/s baseline (k=0.24 m²/s², ω=1.78 rad/s):

| U∞ (m/s) | k (m²/s²) | ω (rad/s) |
|----------|-----------|-----------|
| 20       | 0.24      | 1.78      |
| 30       | 0.54      | 2.67      |
| 40       | 0.96      | 3.56      |

k scales as U², ω scales linearly with U.

## Results

### Aerodynamic Coefficients

| U∞ (m/s) | Cd     | Cl     |
|----------|--------|--------|
| 20       | 0.403  | 0.073  |
| 30       | 0.900  | 0.164  |
| 40       | 1.606  | 0.288  |

Cd and Cl scale roughly as U² (dynamic pressure), consistent with incompressible aerodynamics at these Reynolds numbers.

![Cd and Cl vs velocity](results/coefficients_vs_velocity.png)

### Force Coefficient Convergence

| 20 m/s | 30 m/s | 40 m/s |
|--------|--------|--------|
| ![](results/force_coefficients_20ms.png) | ![](results/force_coefficients_30ms.png) | ![](results/force_coefficients_40ms.png) |

### Surface Pressure (Cp = p / ½ρU²)

#### 20 m/s
| Side | Front | Rear | Iso |
|------|-------|------|-----|
| ![](results/pressure_side_20ms.png) | ![](results/pressure_front_20ms.png) | ![](results/pressure_rear_20ms.png) | ![](results/pressure_iso_20ms.png) |

#### 30 m/s
| Side | Front | Rear | Iso |
|------|-------|------|-----|
| ![](results/pressure_side_30ms.png) | ![](results/pressure_front_30ms.png) | ![](results/pressure_rear_30ms.png) | ![](results/pressure_iso_30ms.png) |

#### 40 m/s
| Side | Front | Rear | Iso |
|------|-------|------|-----|
| ![](results/pressure_side_40ms.png) | ![](results/pressure_front_40ms.png) | ![](results/pressure_rear_40ms.png) | ![](results/pressure_iso_40ms.png) |

## Running

### Full mesh + first solve (20 m/s)

```bash
source /opt/openfoam13/etc/bashrc
./Allrun
```

### Additional velocity runs (reuses mesh)

```bash
bash run_velocity.sh 30
bash run_velocity.sh 40
```

### Post-processing

```bash
# Single velocity (force convergence + surface Cp renders)
python3 postprocess.py 20
python3 postprocess.py 30
python3 postprocess.py 40

# Combined Cd/Cl vs velocity plot
python3 postprocess.py combined
```

All outputs are written to `results/` with velocity suffix (e.g. `pressure_side_30ms.png`).

## Software

- OpenFOAM 13
- Python 3.10 (matplotlib, numpy, pyvista)
