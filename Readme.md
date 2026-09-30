# plot_svg — Nanoindentation repeatability plots

Creates publication-ready SVG plots from aligned indentation curves: individual curves are drawn faint, with a ±1 SD band and the mean in bold. The script also quantifies the variation as the **coefficient of variation (CV = SD / mean × 100%)**.

It makes **one plot per input CSV**, e.g. one for the soft hydrogel and one for the stiff hydrogel.

---

## 1. Requirements

- **Python 3.9 or newer**
- **Git**

### Check what you have

**macOS** (Terminal):
```bash
python3 --version
git --version
```

**Windows** (PowerShell or Command Prompt):
```powershell
py --version
git --version
```

### Install if missing

**macOS**
- Python: download it from https://www.python.org/downloads/, or with Homebrew run `brew install python`
- Git: running `git --version` offers to install the Xcode Command Line Tools. Accept that, or run `brew install git`.

**Windows**
- Python: download it from https://www.python.org/downloads/. **In the installer, tick "Add python.exe to PATH".**
- Git: download it from https://git-scm.com/download/win and keep the default options.

Close and reopen the terminal after installing.

---

## 2. Get the code

**macOS**
```bash
cd ~/Documents
git clone https://github.com/Kozeke/plot_svg.git
cd plot_svg
```

**Windows**
```powershell
cd $HOME\Documents
git clone https://github.com/Kozeke/plot_svg.git
cd plot_svg
```

---

## 3. Create a virtual environment and install packages

This is done once. It keeps the script's packages separate from the rest of your system.

**macOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows**
```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

When the environment is active, `(.venv)` appears at the start of the prompt.

> **Windows PowerShell error "running scripts is disabled on this system":** run this once, then activate again:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```
> Or use Command Prompt (`cmd`) instead, where the activation command is `.venv\Scripts\activate.bat`.

---

## 4. Run the script

Copy your CSV files into the `plot_svg` folder, or give their full path.

**Each time you open a new terminal**, activate the environment first:

| | macOS | Windows |
|---|---|---|
| go to folder | `cd ~/Documents/plot_svg` | `cd $HOME\Documents\plot_svg` |
| activate | `source .venv/bin/activate` | `.venv\Scripts\activate` |

Then run the script.

**One hydrogel:**
```bash
python plot_repeatability.py processed_data_merged_0.2kPa.csv
```

**Soft and stiff together.** The first file is plotted in blue, the second in orange:
```bash
python plot_repeatability.py processed_data_merged_0.2kPa.csv processed_data_merged_20kPa.csv
```

> Replace the file names with your actual ones. If a path contains spaces, put it in quotes:
> `python plot_repeatability.py "C:\Users\me\My Data\soft.csv"`

---

## 5. Output

For each input CSV the script writes these files into the current folder:

- `<name>_repeatability.svg` — vector plot for the paper or report
- `<name>_repeatability.png` — quick preview

`<name>` is taken from the file name, e.g. `0.2kPa`.

The terminal prints the numbers to report:

```
0.2kPa  (n = 8 curves)
  CV of force at 58 nm depth : 5.6%
  Mean CV of force over 20-100% of depth range: 5.3%
  Mean force at 58 nm: 4.70 ± 0.26 µN
  -> 0.2kPa_repeatability.svg
```

What the numbers mean:
- **CV of force at X nm:** spread between curves at 80% of the common depth range. The plot marks this depth with a dotted line.
- **Mean CV over curve:** the average CV from 20% to 100% of the depth range. The first 20%, near contact, is skipped because the force there is small and noisy.
- **Mean force ± SD:** the absolute spread at that same depth.

Example wording: *"Force–depth curves were highly repeatable (n = 8), with a coefficient of variation of 5.6% at 58 nm depth."*

---

## 6. Input format

The CSV is the export from the processing software. Metadata rows come first, then blocks of curves:

```
file_id,merged-0.2Kpa.hdf5
tip_radius,1e-05
...
curve_id,2
index,Z indent (µm),Force indent (µN)
0,0,0.655
1,0.0006,0.687
...
curve_id,3
index,Z indent (µm),Force indent (µN)
...
```

- The curves must already be aligned to the contact point, so Z starts at 0.
- Depth is in µm in the file and plotted in nm. Force is in µN.

---

## 7. Settings (optional)

These are at the top of `plot_repeatability.py`:

| Setting | Default | Meaning |
|---|---|---|
| `EVAL_FRACTION` | `0.8` | Depth, as a fraction of the common range, where CV is reported |
| `N_GRID` | `400` | Number of points used to average the curves |
| `COLORS` | blue, orange | Colour for the 1st and 2nd file |

The SVG text stays editable in Inkscape or Illustrator.

---

## 8. Updating and troubleshooting

**Get the latest version of the script:**
```bash
git pull
```

**Problems:**

| Problem | Fix |
|---|---|
| `python: command not found` (macOS) | Use `python3`, or activate `.venv` first |
| `'python' is not recognized` (Windows) | Use `py`, or reinstall Python with "Add to PATH" ticked |
| `ModuleNotFoundError: No module named 'numpy'` | The environment is not active. Activate it (step 4), then `pip install -r requirements.txt` |
| `FileNotFoundError` | Check the CSV name and path. `ls` (macOS) or `dir` (Windows) lists the files in the folder |
| Nothing plotted / error on a file | Open the CSV and check that it contains `curve_id` lines and the `index,Z indent (µm),Force indent (µN)` header |

**To leave the environment:** `deactivate`