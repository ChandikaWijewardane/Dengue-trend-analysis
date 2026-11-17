# Dengue Weekly Trend and Baseline Analysis (11 Districts, 2021–2025)

Analysis of weekly notified dengue cases across 11 districts in Sri Lanka
(Colombo, Gampaha, Kalutara, Kandy, Matara, Kegalle, Galle, Batticaloa,
Ratnapura, Trincomalee, Jaffna). It builds trend graphs and calculates
district-level baseline case numbers around each year's peak period to
identify pre-outbreak patterns and possible triggers for early intervention.

## What the code does
1. Reads five yearly weekly-case files (2021–2023 long format, 2024–2025 wide format)
2. Cleans district names and fills missing weeks with zero
3. Draws four sets of graphs (combined trend, district trends, year overlay, baseline vs peak)
4. For each year and district, calculates:
   - Peak period: national peak week ± 4 weeks
   - Baseline: mean weekly cases in the 8 weeks before the peak period
   - Alert threshold: baseline mean + 2 standard deviations
   - Lead time: weeks between first crossing the threshold and the district's peak
5. Saves results to `dengue_baseline_results.xlsx`

## How to run

### In Google Colab (easiest)
1. Open colab.research.google.com and create a new notebook
2. Paste the contents of `dengue_analysis.py` into a cell
3. Run the cell and upload the five data files when asked

### On your own computer
1. Install Python 3.10 or newer
2. `pip install -r requirements.txt`
3. Put the five data files in a `data/` folder
4. Set the file paths in `FILES` at the top of the script, for example `'data/2021.xls'`
5. `python dengue_analysis.py`

## Settings you can change (top of the script)
| Setting | Default | Meaning |
|---|---|---|
| PEAK_HALF_WIDTH | 4 | Weeks either side of the national peak |
| BASELINE_WEEKS | 8 | Weeks before the peak period used as baseline |
| THRESH_SD | 2 | Standard deviations above baseline for the alert threshold |

## Data
Raw data files are **not included** in this repository (surveillance data).
Expected files: `2021.xls`, `2022.xls`, `2023 from DenSys.xls`, `2024.xlsx`, `2025.xlsx`.

## Outputs
See the `outputs/` folder for the charts, the results table and the written report.

## Known limitations
- Notified cases, not laboratory-confirmed
- Week 0 (a partial week in 2021–2023 files) is excluded
- 2024's peak is the tail of the late-2023 wave, so its baseline comes from late 2023
- Baseline settings are working choices and should be checked with a sensitivity analysis

## Author
Chandika Wijewardene, Sri Lanka Red cross Society, 11/2026

