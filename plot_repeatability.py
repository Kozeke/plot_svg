"""
Repeatability plots for aligned nanoindentation curves.

Input format (one CSV per hydrogel, as exported from the processing software):
    metadata rows (tip_radius, tip_geometry, ...)
    curve_id,<n>
    index,Z indent (µm),Force indent (µN)
    0,...,...
    curve_id,<n+1>
    ...

Usage:
    python plot_repeatability.py processed_data_merged_0.2kPa.csv processed_data_merged_XXkPa.csv
Output: one <name>_repeatability.svg per input file + printed variation stats.
"""
import sys, os, re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.colors import to_rgb
from scipy.signal import savgol_filter

N_GRID = 400          # points on the common depth grid
EVAL_FRACTION = 0.8   # depth (fraction of common max depth) where force CV is reported
COLORS = ["#2a78d6", "#eb6834"]   # soft = blue, stiff = orange

plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#555555", "axes.labelcolor": "#222222",
    "xtick.color": "#555555", "ytick.color": "#555555",
    "svg.fonttype": "none",   # text stays editable in Inkscape/Illustrator
})


def load_file(path):
    """Return (metadata dict, {curve_id: (z_um, f_uN)})."""
    meta, curves, cur = {}, {}, None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            p = [s.strip() for s in line.strip().split(",")]
            if not p or p == [""]:
                continue
            if p[0] == "curve_id":
                cur = p[1]
                curves[cur] = []
            elif cur is None:
                if len(p) > 1:
                    meta[p[0]] = p[1]
            elif p[0].isdigit() and len(p) >= 3:
                curves[cur].append((float(p[1]), float(p[2])))
    out = {}
    for k, v in curves.items():
        a = np.array(v)
        a = a[np.argsort(a[:, 0], kind="stable")]  # guard against tiny non-monotonic steps
        out[k] = (a[:, 0], a[:, 1])
    return meta, out


def process(path, color):
    meta, curves = load_file(path)
    name = re.sub(r"^processed_data_merged_", "", os.path.splitext(os.path.basename(path))[0])

    zs = [c[0] for c in curves.values()]
    fs = [c[1] for c in curves.values()]
    d_max = min(z.max() for z in zs)                       # common depth range
    grid = np.linspace(0, d_max, N_GRID)
    F = np.array([np.interp(grid, z, f) for z, f in zip(zs, fs)])

    mean, sd = F.mean(0), F.std(0, ddof=1)
    # light smoothing of mean/SD for display only (stats below use the unsmoothed values)
    mean_s, sd_s = savgol_filter(mean, 31, 2), savgol_filter(sd, 31, 2)
    i_eval = int(EVAL_FRACTION * (N_GRID - 1))
    cv_force = sd[i_eval] / mean[i_eval] * 100

    sl = slice(N_GRID // 5, None)                           # skip first 20% (near-contact, force ~ offset)
    cv_mean = np.mean(sd[sl] / mean[sl]) * 100

    # individual curves fade as their number grows; mean drawn in a darker shade with a white halo
    curve_alpha = float(np.clip(2.5 / len(F), 0.08, 0.35))
    dark = tuple(c * 0.55 for c in to_rgb(color))
    fig, ax = plt.subplots(figsize=(5.2, 4))
    for z, f in zip(zs, fs):                                # raw curves, faint
        ax.plot(z * 1e3, f, color=color, alpha=curve_alpha, lw=0.5, zorder=1)
    ax.fill_between(grid * 1e3, mean_s - sd_s, mean_s + sd_s, color=color, alpha=0.25, lw=0,
                    label="±1 SD", zorder=2)
    ax.plot(grid * 1e3, mean_s, color=dark, lw=3, zorder=4, label=f"Mean (n = {len(F)})",
            path_effects=[pe.Stroke(linewidth=5.5, foreground="white"), pe.Normal()])
    ax.plot([], [], color=color, alpha=0.5, lw=0.8, label="Individual curves")
    ax.axvline(grid[i_eval] * 1e3, color="#999999", lw=0.8, ls=":")
    ax.set_xlabel("Indentation depth (nm)")
    ax.set_ylabel("Force (µN)")
    ax.set_title(f"{name} hydrogel", loc="left", fontsize=12)
    ax.text(0.03, 0.97,
            f"CV of force at {grid[i_eval]*1e3:.0f} nm: {cv_force:.1f}%\n"
            f"Mean CV over curve: {cv_mean:.1f}%",
            transform=ax.transAxes, va="top", fontsize=9.5, color="#222222")
    ax.legend(frameon=False, loc="lower right", fontsize=9.5)
    ax.set_xlim(0, max(z.max() for z in zs) * 1e3)
    ax.set_ylim(bottom=0)
    ax.grid(color="#e6e6e6", lw=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    out = f"{name}_repeatability.svg"
    fig.savefig(out)
    fig.savefig(out.replace(".svg", ".png"), dpi=150)

    print(f"\n{name}  (n = {len(F)} curves)")
    print(f"  CV of force at {grid[i_eval]*1e3:.0f} nm depth : {cv_force:.1f}%")
    print(f"  Mean CV of force over 20-100% of depth range: {cv_mean:.1f}%")
    print(f"  Mean force at {grid[i_eval]*1e3:.0f} nm: {mean[i_eval]:.2f} ± {sd[i_eval]:.2f} µN")
    print(f"  -> {out}")


if __name__ == "__main__":
    for path, c in zip(sys.argv[1:], COLORS):
        process(path, c)