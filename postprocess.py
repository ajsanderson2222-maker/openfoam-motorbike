#!/usr/bin/env python3
"""
Motorbike RANS post-processing.
Usage:
  python3 postprocess.py <velocity>          # single run: 20, 30, or 40
  python3 postprocess.py combined            # Cd/Cl vs V combined plot
"""
import re, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pyvista as pv

pv.OFF_SCREEN = True
OUT = "results"
os.makedirs(OUT, exist_ok=True)

# ── Combined Cd/Cl vs velocity plot ──────────────────────────────────────────
if len(sys.argv) > 1 and sys.argv[1] == "combined":
    velocities, cds, cls = [], [], []
    for v in [20, 30, 40]:
        log = f"log.foamRun_{v}ms"
        if not os.path.exists(log):
            print(f"  Missing {log}, skipping")
            continue
        cd_v, cl_v = [], []
        with open(log) as f:
            for line in f:
                m = re.search(r'^\s+Cd\s*=\s*([+-]?\d+\.\d+)', line)
                if m: cd_v.append(float(m.group(1)))
                m = re.search(r'^\s+Cl\s*=\s*([+-]?\d+\.\d+)', line)
                if m: cl_v.append(float(m.group(1)))
        if cd_v:
            velocities.append(v)
            cds.append(cd_v[-1])
            cls.append(cl_v[-1])
            print(f"  {v} m/s: Cd={cd_v[-1]:.4f}  Cl={cl_v[-1]:.4f}")

    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    fig.suptitle("Motorbike RANS — Aerodynamic Coefficients vs Freestream Velocity\n"
                 "(k-ω SST, steady SIMPLE)", fontsize=12)

    axes[0].plot(velocities, cds, "ro-", ms=8, lw=2)
    for v, cd in zip(velocities, cds):
        axes[0].annotate(f"{cd:.3f}", (v, cd), textcoords="offset points",
                         xytext=(0, 10), ha="center", fontsize=10)
    axes[0].set_xlabel("U∞ [m/s]"); axes[0].set_ylabel("Cd")
    axes[0].set_title("Drag Coefficient"); axes[0].grid(True, alpha=0.3)
    axes[0].set_xlim(15, 45)

    axes[1].plot(velocities, cls, "bs-", ms=8, lw=2)
    for v, cl in zip(velocities, cls):
        axes[1].annotate(f"{cl:.3f}", (v, cl), textcoords="offset points",
                         xytext=(0, 10), ha="center", fontsize=10)
    axes[1].set_xlabel("U∞ [m/s]"); axes[1].set_ylabel("Cl")
    axes[1].set_title("Lift Coefficient"); axes[1].grid(True, alpha=0.3)
    axes[1].set_xlim(15, 45)

    plt.tight_layout()
    plt.savefig(f"{OUT}/coefficients_vs_velocity.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved {OUT}/coefficients_vs_velocity.png")
    sys.exit(0)

# ── Single velocity run ───────────────────────────────────────────────────────
U_inf = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0
tag   = f"{int(U_inf)}ms"
log   = f"log.foamRun_{tag}"

cd_vals, cl_vals = [], []
with open(log) as f:
    for line in f:
        m = re.search(r'^\s+Cd\s*=\s*([+-]?\d+\.\d+)', line)
        if m: cd_vals.append(float(m.group(1)))
        m = re.search(r'^\s+Cl\s*=\s*([+-]?\d+\.\d+)', line)
        if m: cl_vals.append(float(m.group(1)))

iters = np.arange(1, len(cd_vals) + 1)
fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
fig.suptitle(f"Motorbike RANS — Force Coefficient Convergence (k-ω SST, {int(U_inf)} m/s)",
             fontsize=12)
axes[0].plot(iters, cd_vals, "r-", lw=1.5)
axes[0].axhline(cd_vals[-1], color="k", lw=0.8, ls="--",
                label=f"Final Cd = {cd_vals[-1]:.4f}")
axes[0].set_ylabel("Cd"); axes[0].legend(); axes[0].grid(True, alpha=0.3)
axes[1].plot(iters, cl_vals, "b-", lw=1.5)
axes[1].axhline(cl_vals[-1], color="k", lw=0.8, ls="--",
                label=f"Final Cl = {cl_vals[-1]:.4f}")
axes[1].set_ylabel("Cl"); axes[1].set_xlabel("Iteration")
axes[1].legend(); axes[1].grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUT}/force_coefficients_{tag}.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved {OUT}/force_coefficients_{tag}.png  (Cd={cd_vals[-1]:.4f}, Cl={cl_vals[-1]:.4f})")

# ── Surface pressure renders ──────────────────────────────────────────────────
foam_file = "case.foam"
if not os.path.exists(foam_file):
    open(foam_file, "w").close()

reader = pv.OpenFOAMReader(foam_file)
reader.set_active_time_value(reader.time_values[-1])
mesh   = reader.read()
boundary = mesh["boundary"]

bike_parts = [boundary[k] for k in boundary.keys()
              if k.startswith("motorBike_") and boundary[k] is not None
              and boundary[k].n_points > 0]
bike_surface = pv.merge(bike_parts)

p_arr = np.array(bike_surface["p"]).ravel()
Cp    = p_arr / (0.5 * U_inf**2)
bike_surface["Cp"] = Cp
Cp_min = np.percentile(Cp, 2)
Cp_max = np.percentile(Cp, 98)

def render(surface, scalar, clim, cmap, label, camera_pos, fname):
    pl = pv.Plotter(off_screen=True, window_size=(1600, 900))
    pl.set_background("white")
    pl.add_mesh(surface, scalars=scalar, cmap=cmap, clim=clim, show_scalar_bar=False)
    pl.add_scalar_bar("", n_labels=7, fmt="%.2f",
                      vertical=False,
                      position_x=0.1, position_y=0.06,
                      width=0.80, height=0.07,
                      label_font_size=22, title_font_size=1,
                      bold=True)
    pl.add_text(label, position=(0.44, 0.145), font_size=14,
                color="black", viewport=True)
    pl.camera_position = camera_pos
    pl.screenshot(fname, return_img=False)
    pl.close()
    print(f"Saved {fname}")

side_cam  = [(1.0, -5.0, 1.2),  (1.0, 0.0, 0.6),  (0, 0, 1)]
front_cam = [(-3.5, 0.0, 0.5),  (1.0, 0.0, 0.4),  (0, 0, 1)]
rear_cam  = [(5.5,  0.0, 1.2),  (1.0, 0.0, 0.6),  (0, 0, 1)]
iso_cam   = [(5.0, -3.5, 2.5),  (1.0, 0.0, 0.6),  (0, 0, 1)]

for name, cam in [("side", side_cam), ("front", front_cam),
                  ("rear", rear_cam),  ("iso",   iso_cam)]:
    render(bike_surface, "Cp", [Cp_min, Cp_max], "coolwarm",
           f"Cp = p / (½ρU²)   U∞ = {int(U_inf)} m/s",
           cam, f"{OUT}/pressure_{name}_{tag}.png")

print("\nDone.")
