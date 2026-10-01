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
SMOOTH_WINDOW_UM = 15.0   # default Savitzky-Golay window (µm)
SMOOTH_POLYORDER = 4      # default Savitzky-Golay polynomial order
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


def savgol_smooth(x, y, window_size_um, polyorder=2):
    """Savitzky-Golay smoothing with the window given in µm (same logic as the SavgolSmooth filter)."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if len(x) < 3:
        return y
    xstep = (x.max() - x.min()) / (len(x) - 1)              # average µm per sample
    win = max(1, int(window_size_um / xstep))               # µm -> samples
    if win % 2 == 0:
        win += 1                                            # window must be odd
    max_odd = len(x) if len(x) % 2 == 1 else len(x) - 1
    win = max(1, min(win, max_odd))                         # never longer than the curve
    polyorder = min(polyorder, win - 1)                     # polyorder < window
    if win <= polyorder or win < 3:
        return y
    return savgol_filter(y, win, polyorder)


def ask(prompt, default=""):
    """Ask the user in the terminal; Enter keeps the default."""
    hint = f" [{default}]" if default else ""
    try:
        ans = input(f"{prompt}{hint}: ").strip()
    except EOFError:
        ans = ""
    return ans or default


def ask_yes_no(prompt, default=True):
    ans = ask(prompt + " (y/n)", "y" if default else "n").lower()
    return ans.startswith("y")


def process(path, color):
    meta, curves = load_file(path)
    name = re.sub(r"^processed_data_(merged_)?", "", os.path.splitext(os.path.basename(path))[0])

    zs = [c[0] for c in curves.values()]
    fs_raw = [c[1] for c in curves.values()]

    # ---- optional smoothing of each curve ----
    print(f"\n=== {os.path.basename(path)}  (n = {len(zs)} curves) ===")
    span = float(np.median([z.max() - z.min() for z in zs]))
    step = float(np.median([(z.max() - z.min()) / (len(z) - 1) for z in zs]))
    print(f"  Depth range ~{span:.3g} µm, sample spacing ~{step:.2g} µm")
    smooth = ask_yes_no("Smooth the curves (Savitzky-Golay)?", True)
    if smooth:
        win_um = float(ask("  Window size (µm)", f"{SMOOTH_WINDOW_UM:g}"))
        order = int(ask("  Polynomial order", str(SMOOTH_POLYORDER)))
        if win_um > 0.5 * span:
            print(f"  ! Warning: window ({win_um:g} µm) is more than half the depth range "
                  f"({span:.3g} µm); the curve shape may be distorted.")
        fs = [savgol_smooth(z, f, win_um, order) for z, f in zip(zs, fs_raw)]
        print(f"  Smoothing: window {win_um:g} µm (~{max(1, int(win_um / step)) | 1} points), order {order}")
    else:
        fs = fs_raw

    d_max = min(z.max() for z in zs)                       # common depth range
    grid = np.linspace(0, d_max, N_GRID)
    F = np.array([np.interp(grid, z, f) for z, f in zip(zs, fs)])

    mean, sd = F.mean(0), F.std(0, ddof=1)
    mean_s, sd_s = mean, sd
    i_eval = int(EVAL_FRACTION * (N_GRID - 1))
    z_eval = grid[i_eval]
    cv_force = sd[i_eval] / mean[i_eval] * 100
    sl = slice(N_GRID // 5, None)                           # skip first 20% (near-contact)
    cv_mean = np.mean(sd[sl] / mean[sl]) * 100

    # ---- print stats, then ask the user how the plot should look ----
    if smooth:
        F_raw = np.array([np.interp(grid, z, f) for z, f in zip(zs, fs_raw)])
        m_r, s_r = F_raw.mean(0), F_raw.std(0, ddof=1)
        print(f"  (raw, unsmoothed: CV at {z_eval:.3g} µm = {s_r[i_eval]/m_r[i_eval]*100:.1f}%, "
              f"mean CV = {np.mean(s_r[sl]/m_r[sl])*100:.1f}%)")
    label = "smoothed" if smooth else "raw"
    print(f"  Results ({label} curves):")
    print(f"  CV of force at {z_eval:.3g} µm depth: {cv_force:.1f}%")
    print(f"  Mean CV over 20-100% of depth range: {cv_mean:.1f}%")
    print(f"  Mean force at {z_eval:.3g} µm: {mean[i_eval]:.2f} ± {sd[i_eval]:.2f} µN")
    title = ask("Plot title", f"{name} hydrogel")
    show_cv = ask_yes_no(f"Show 'CV at {z_eval:.3g} µm' on the plot?", True)
    show_cv_mean = ask_yes_no("Show 'Mean CV' on the plot?", True)

    # ---- plot ----
    curve_alpha = float(np.clip(4 / len(F), 0.18, 0.55))    # fainter when there are many curves
    dark = tuple(c * 0.7 for c in to_rgb(color))
    fig, ax = plt.subplots(figsize=(5.2, 4))
    for z, f in zip(zs, fs):
        ax.plot(z, f, color=color, alpha=curve_alpha, lw=0.8, zorder=1)
    ax.fill_between(grid, mean_s - sd_s, mean_s + sd_s, color=color, alpha=0.2, lw=0,
                    label="±1 SD", zorder=2)
    ax.plot(grid, mean_s, color=dark, lw=1.8, zorder=4, label=f"Mean (n = {len(F)})",
            path_effects=[pe.Stroke(linewidth=3, foreground="white"), pe.Normal()])
    ax.plot([], [], color=color, alpha=0.6, lw=0.8, label="Individual curves")

    lines = []
    if show_cv:
        lines.append(f"CV at {z_eval:.3g} µm: {cv_force:.1f}%")
        ax.axvline(z_eval, color="#999999", lw=0.8, ls=":")
    if show_cv_mean:
        lines.append(f"Mean CV: {cv_mean:.1f}%")
    if lines:
        ax.text(0.03, 0.97, "\n".join(lines), transform=ax.transAxes, va="top",
                fontsize=9.5, color="#222222")

    ax.set_xlabel("Indentation depth (µm)")
    ax.set_ylabel("Force (µN)")
    if title:
        ax.set_title(title, loc="left", fontsize=12)
    ax.legend(frameon=False, loc="lower right", fontsize=9.5)

    # axis limits fitted to the data, so there is no empty space under the curves
    f_lo = min(f.min() for f in fs)
    f_hi = max(f.max() for f in fs)
    span = f_hi - f_lo
    ax.set_xlim(0, max(z.max() for z in zs))
    ax.set_ylim(f_lo - 0.05 * span, f_hi + 0.03 * span)
    ax.grid(color="#e6e6e6", lw=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()

    out = f"{name}_repeatability.svg"
    fig.savefig(out)
    fig.savefig(out.replace(".svg", ".png"), dpi=150)
    print(f"  -> saved {out}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for i, path in enumerate(sys.argv[1:]):
        process(path, COLORS[i % len(COLORS)])