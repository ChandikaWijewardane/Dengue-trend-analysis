# ============ DENGUE 5-YEAR TREND + BASELINE ANALYSIS (11 districts) ============ 
import pandas as pd, numpy as np, matplotlib.pyplot as plt, io
import matplotlib
try:
    from google.colab import files
    IN_COLAB = True
except ImportError:
    IN_COLAB = False

# ---------- SETTINGS YOU CAN CHANGE ----------
FILES = {2021: '2021.xls', 2022: '2022.xls', 2023: '2023 from DenSys.xls',
         2024: '2024.xlsx', 2025: '2025.xlsx'}
PEAK_HALF_WIDTH = 4     # peak period = national peak week +/- 4 weeks (9 weeks)
BASELINE_WEEKS  = 8     # baseline = the 8 weeks BEFORE the peak period starts
THRESH_SD       = 2     # alert threshold = baseline mean + 2 x standard deviation
ELEVEN = ['Colombo','Gampaha','Kalutara','Kandy','Matara','Kegalle',
          'Galle','Batticaloa','Ratnapura','Trincomalee','Jaffna']
FIX = {'Kaluthara':'Kalutara','Rathnapura':'Ratnapura'}

def clean(n):
    n = str(n).replace('RDHS','').strip()
    return FIX.get(n, n)

# ---------- READERS ----------
def read_long(path, year):            # 2021, 2022, 2023 layout: District | Week | Total
    d = pd.read_excel(path, header=None, skiprows=6, usecols=[0,1,2])
    d.columns = ['district','week','cases']
    d['week']  = pd.to_numeric(d['week'],  errors='coerce')
    d['cases'] = pd.to_numeric(d['cases'], errors='coerce')
    d = d.dropna(subset=['week','cases'])
    d['district'] = d['district'].map(clean); d['year'] = year
    return d

def read_wide(path, year):            # 2024, 2025 layout: one column per week
    d = pd.read_excel(path, sheet_name=0, header=1)
    d = d[d['Province'].notna() & (d['Province'] != 'Grand Total')].copy()
    d['district'] = d['District'].map(clean)
    wk = [c for c in d.columns if isinstance(c, (int, float))]
    m = d.melt(id_vars='district', value_vars=wk, var_name='week', value_name='cases')
    m['year'] = year
    return m.dropna(subset=['cases'])

# ---------- LOAD ----------
if IN_COLAB:
    print('Select all 5 files in the window below...')
    files.upload()
frames = []
for y, f in FILES.items():
    frames.append(read_long(f, y) if y <= 2023 else read_wide(f, y))
df = pd.concat(frames)
df = df[df.district.isin(ELEVEN) & (df.week >= 1)]      # week 0 = partial week, excluded
df['week'] = df['week'].astype(int)

# fill weeks that are missing in the source (no cases reported) with 0
rows = []
for (y, dist), g in df.groupby(['year','district']):
    full = pd.Series(0.0, index=range(1, int(df[df.year==y].week.max())+1))
    full.loc[g.week.values] = g.cases.values
    rows.append(pd.DataFrame({'year':y,'district':dist,'week':full.index,'cases':full.values}))
df = pd.concat(rows, ignore_index=True)
df['t'] = df['year'] + (df['week']-1)/53                # continuous time axis

print('Rows loaded:', len(df), '| districts:', df.district.nunique())
print(df.groupby('year').cases.sum().astype(int).rename('Total cases (11 districts)'))

years = sorted(df.year.unique())
colors = dict(zip(years, ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd']))

# ---------- GRAPH 1: 5-year trend, all 11 districts combined ----------
tot = df.groupby(['year','week','t']).cases.sum().reset_index()
fig, ax = plt.subplots(figsize=(14,5))
for y in years:
    s = tot[tot.year==y]; ax.plot(s.t, s.cases, color=colors[y], lw=1.8, label=str(y))
ax.set_title('Weekly dengue cases, 11 districts combined, 2021-2025'); ax.set_xlabel('Year'); ax.set_ylabel('Cases per week')
ax.legend(ncol=5); ax.grid(alpha=.3); plt.tight_layout(); plt.savefig('1_combined_trend.png', dpi=150); plt.show()

# ---------- GRAPH 2: each district, 5-year timeline (11 small charts) ----------
fig, axes = plt.subplots(4, 3, figsize=(16,14), sharex=True)
for ax, dist in zip(axes.flat, ELEVEN):
    s = df[df.district==dist].sort_values('t'); ax.plot(s.t, s.cases, color='#333', lw=1.2)
    ax.set_title(dist); ax.grid(alpha=.3)
axes.flat[-1].axis('off')
fig.suptitle('Weekly dengue cases by district, 2021-2025', fontsize=15); plt.tight_layout()
plt.savefig('2_district_trends.png', dpi=150); plt.show()

# ---------- GRAPH 3: year-on-year overlay per district (week 1-52) ----------
fig, axes = plt.subplots(4, 3, figsize=(16,14), sharex=True)
for ax, dist in zip(axes.flat, ELEVEN):
    for y in years:
        s = df[(df.district==dist)&(df.year==y)]; ax.plot(s.week, s.cases, color=colors[y], lw=1.2, label=str(y))
    ax.set_title(dist); ax.grid(alpha=.3)
axes.flat[0].legend(fontsize=8); axes.flat[-1].axis('off')
fig.suptitle('Same district, each year overlaid (by week number)', fontsize=15); plt.tight_layout()
plt.savefig('3_year_overlay.png', dpi=150); plt.show()

# ---------- BASELINE ANALYSIS AT PEAK PERIOD ----------
# Works on one continuous weekly timeline (2021 wk1 -> 2025 last week), so when a year
# peaks in its first weeks (e.g. 2024) the baseline is taken from the end of the previous year.
df = df.sort_values(['district','t']).reset_index(drop=True)
df['pos'] = df.groupby('district').cumcount()                 # 0,1,2,... position on the timeline
pos_of = df[df.district=='Colombo'].set_index(['year','week']).pos
lab    = df[df.district=='Colombo'].set_index('pos')[['year','week']]
def L(p): return f"{lab.loc[p,'year']} wk{lab.loc[p,'week']}"

out = []
for y in years:
    nat = tot[tot.year==y].set_index('week').cases
    nat_peak = int(nat.idxmax())
    pk0, pk1 = pos_of[(y, nat_peak)] - PEAK_HALF_WIDTH, pos_of[(y, nat_peak)] + PEAK_HALF_WIDTH
    pk1 = min(pk1, pos_of[(y, int(nat.index.max()))])
    pk0 = max(pk0, 0)
    b0, b1 = max(0, pk0-BASELINE_WEEKS), pk0-1
    for dist in ELEVEN:
        s = df[df.district==dist].set_index('pos').cases
        base = s.loc[b0:b1] if b1 >= b0 else s.iloc[:0]
        b_mean = base.mean() if len(base) else np.nan
        b_med  = base.median() if len(base) else np.nan
        b_sd   = base.std() if len(base) > 1 else np.nan
        thr    = b_mean + THRESH_SD*b_sd if len(base) > 1 else np.nan
        win = s.loc[pk0:pk1]; d_pk_pos = int(win.idxmax()); d_pk = win.max()
        seg = s.loc[b0:d_pk_pos] if b1 >= b0 else s.iloc[:0]
        seg = seg[(seg > thr) & (seg.index >= pk0 - 4)] if pd.notna(thr) else seg.iloc[:0]
        fc = int(seg.index[0]) if len(seg) else np.nan
        out.append({'Year':y, 'District':dist, 'National_peak_week':nat_peak,
            'Peak_period':f'{L(pk0)} to {L(pk1)}', 'Baseline_period':f'{L(b0)} to {L(b1)}' if b1>=b0 else 'n/a',
            'Baseline_mean':round(b_mean,1), 'Baseline_median':b_med,
            'Baseline_SD':round(b_sd,1) if pd.notna(b_sd) else np.nan,
            'Alert_threshold':round(thr,1) if pd.notna(thr) else np.nan,
            'District_peak_week':int(lab.loc[d_pk_pos,'week']), 'District_peak_cases':int(d_pk),
            'Peak_to_baseline_ratio':round(d_pk/b_mean,1) if b_mean and b_mean>0 else np.nan,
            'First_week_above_threshold':int(lab.loc[fc,'week']) if pd.notna(fc) else np.nan,
            'Lead_time_weeks':(d_pk_pos-fc) if pd.notna(fc) else np.nan})
res = pd.DataFrame(out)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30)
print(res.to_string(index=False))

# ---------- GRAPH 4: baseline bars vs peak, per year ----------
fig, axes = plt.subplots(5, 1, figsize=(13,22))
for ax, y in zip(axes, years):
    r = res[res.Year==y].set_index('District').loc[ELEVEN]; x = np.arange(len(ELEVEN))
    ax.bar(x-0.2, r.Baseline_mean, 0.4, label='Baseline (mean weekly cases)', color='#4c9be8')
    ax.bar(x+0.2, r.District_peak_cases, 0.4, label='Peak-period maximum', color='#e8574c')
    ax.set_xticks(x); ax.set_xticklabels(ELEVEN, rotation=30); ax.set_title(f'{y}: baseline vs peak ({r.Peak_period.iloc[0]}, baseline {r.Baseline_period.iloc[0]})')
    ax.legend(); ax.grid(alpha=.3, axis='y')
plt.tight_layout(); plt.savefig('4_baseline_vs_peak.png', dpi=150); plt.show()

# ---------- SAVE EXCEL ----------
with pd.ExcelWriter('dengue_baseline_results.xlsx') as w:
    res.to_excel(w, sheet_name='Baseline_by_district_year', index=False)
    df.pivot_table(index=['year','week'], columns='district', values='cases').to_excel(w, sheet_name='Clean_weekly_data')
if IN_COLAB:
    for f in ['1_combined_trend.png','2_district_trends.png','3_year_overlay.png','4_baseline_vs_peak.png','dengue_baseline_results.xlsx']:
        files.download(f)
