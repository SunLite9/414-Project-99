# %% [markdown]
# # 02 · Almost Certain? Models, validation and results
# Question: among Kalshi YES contracts first seen at a 90–99¢ ask, do market features (volume, time to the event,
# recent price movement, category) predict which favorites lose better than the quoted price itself?
#
# Design: fit on **train** (before Oct 15), choose hyperparameters on **validation** (Oct 15–19) by Brier score,
# refit the chosen setting on train + validation, then score the untouched **test** period (Oct 20 onward) once.

# %%
import json, warnings
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt  # styled via style_guide/ucla_style.py
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score, average_precision_score
from xgboost import XGBClassifier
warnings.filterwarnings('ignore')
ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
RES = ROOT/'results/midterm'; FIG = RES/'figures'; FIG.mkdir(parents=True, exist_ok=True)
SEED = 414; rng = np.random.default_rng(SEED)
d = pd.read_parquet(ROOT/'data/processed/midterm_entries.parquet')
print(d.groupby('split').agg(markets=('y_win','size'), events=('event_slug','nunique'), losses=('y_win', lambda s: int((1-s).sum()))))

# %% [markdown]
# ## Features
# Everything is measured at or before the entry candle. Time-to-event uses the *scheduled* event time; the actual close
# time is never a feature. Missing trailing history is filled with 0 plus an explicit indicator.

# %%
h = d.hours_to_event.clip(-72, 336)
d['slog_hours_to_event'] = np.sign(h) * np.log1p(h.abs())
d['log_hours_since_open'] = np.log1p(d.hours_since_open.clip(lower=0))
d['has_prior_quote'] = d.prev_mid.notna().astype(int)
d['mid_change_6h_f'] = d.mid_change_6h.fillna(0)
d['fresh_cross_f'] = d.fresh_cross.fillna(0)
PRICE = ['midpoint']
MARKET = ['midpoint','spread','log_open_interest','slog_hours_to_event','log_hours_since_open','has_prior_quote',
          'mid_change_6h_f','fresh_cross_f','prior_candles_6h','log_event_size']
VOLUME = ['log_volume','volume_missing','log_volume_prev_6h']
CAT = ['category_group']
FEATS = {'price_only': (PRICE, []), 'no_volume': (MARKET, CAT), 'with_volume': (MARKET + VOLUME, CAT)}
tr, va, te = (d[d.split == s] for s in ['train','validation','test'])
trva = pd.concat([tr, va])

def prep(num, cat):
    t = [('num', Pipeline([('imp', SimpleImputer(strategy='median')), ('sc', StandardScaler())]), num)]
    if cat: t.append(('cat', OneHotEncoder(handle_unknown='ignore', min_frequency=10), cat))
    return ColumnTransformer(t)

def metrics(y, p):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return dict(brier=brier_score_loss(y, p), log_loss=log_loss(y, p, labels=[0, 1]),
                auc=roc_auc_score(y, p), loss_ap=average_precision_score(1 - y, 1 - p))

# %% [markdown]
# ## Model families and validation grids
# * **Elastic-net logistic regression**: penalty strength C and L1 share (l1_ratio 0 = ridge, 1 = lasso), Week 3.
# * **Random forest** and **XGBoost** (gradient-boosted trees): small depth / leaf / learning-rate grids, Week 4.
# Each family is tuned on validation Brier only. The test set is not touched until the end.

# %%
def logit(C, l1): return LogisticRegression(penalty='elasticnet', solver='saga', C=C, l1_ratio=l1, max_iter=5000, random_state=SEED)
GRIDS = {
  'elastic_net_logistic': [dict(C=C, l1=l1) for C in [0.01, 0.1, 1, 10] for l1 in [0, 0.5, 1]],
  'random_forest': [dict(max_depth=md, min_samples_leaf=ml) for md in [4, 8] for ml in [20, 50]],
  'xgboost': [dict(max_depth=md, learning_rate=lr, n_estimators=ne) for md in [2, 3] for lr in [0.03, 0.1] for ne in [200]],
}
def make(family, hp):
    if family == 'elastic_net_logistic': return logit(**hp)
    if family == 'random_forest': return RandomForestClassifier(n_estimators=300, n_jobs=4, random_state=SEED, **hp)
    return XGBClassifier(subsample=0.8, colsample_bytree=0.8, min_child_weight=5, reg_lambda=1.0, n_jobs=4,
                         random_state=SEED, eval_metric='logloss', **hp)

search, chosen = [], {}
for family, grid in GRIDS.items():
    for fs in ['no_volume', 'with_volume']:
        num, cat = FEATS[fs]
        for hp in grid:
            m = Pipeline([('prep', prep(num, cat)), ('model', make(family, hp))]).fit(tr, tr.y_win)
            search.append(dict(family=family, features=fs, **{k: str(v) for k, v in hp.items()},
                               val_brier=brier_score_loss(va.y_win, m.predict_proba(va)[:, 1])))
search = pd.DataFrame(search)
for (family, fs), g in search.groupby(['family', 'features']):
    best = g.sort_values('val_brier').iloc[0]
    chosen[(family, fs)] = {k: (float(best[k]) if k in ('C', 'l1', 'learning_rate') else int(best[k]))
                            for k in GRIDS[family][0]}
search.to_csv(RES/'validation_search.csv', index=False)
search.sort_values('val_brier').groupby(['family','features']).head(1)

# %% [markdown]
# ## Refit on train + validation, score the test period once

# %%
preds = {'midpoint': te.midpoint.values, 'training_win_rate': np.full(len(te), trva.y_win.mean())}
val_preds = {'midpoint': va.midpoint.values}
m = Pipeline([('prep', prep(PRICE, [])), ('model', LogisticRegression(C=1e6, max_iter=5000))])
val_preds['price_only_logistic'] = m.fit(tr, tr.y_win).predict_proba(va)[:, 1]
preds['price_only_logistic'] = m.fit(trva, trva.y_win).predict_proba(te)[:, 1]
fitted = {}
for (family, fs), hp in chosen.items():
    num, cat = FEATS[fs]; name = f'{family}__{fs}'
    m = Pipeline([('prep', prep(num, cat)), ('model', make(family, hp))])
    val_preds[name] = m.fit(tr, tr.y_win).predict_proba(va)[:, 1]
    m = Pipeline([('prep', prep(num, cat)), ('model', make(family, hp))]).fit(trva, trva.y_win)
    preds[name] = m.predict_proba(te)[:, 1]; fitted[name] = m
rows = [dict(split='validation', model=k, **metrics(va.y_win.values, v)) for k, v in val_preds.items()]
rows += [dict(split='test', model=k, **metrics(te.y_win.values, v)) for k, v in preds.items()]
scores = pd.DataFrame(rows); scores.to_csv(RES/'model_scores.csv', index=False)
scores[scores.split == 'test'].sort_values('brier').round(5)

# %% [markdown]
# ## Uncertainty: event-level bootstrap of Brier differences on test
# Markets in one event share an outcome driver, so whole events are resampled (1,000 replicates).

# %%
ev = te.event_slug.values; uev = np.unique(ev); idx = {e: np.where(ev == e)[0] for e in uev}; y = te.y_win.values
def boot_diff(pa, pb, B=1000):
    out = []
    for _ in range(B):
        ii = np.concatenate([idx[e] for e in rng.choice(uev, len(uev))])
        out.append(np.mean((pa[ii] - y[ii])**2) - np.mean((pb[ii] - y[ii])**2))
    out = np.array(out); return float(np.mean((pa - y)**2) - np.mean((pb - y)**2)), *np.percentile(out, [2.5, 97.5]).tolist()
cmp = []
for k in preds:
    if k != 'midpoint':
        pt, lo, hi = boot_diff(preds[k], preds['midpoint']); cmp.append(dict(model=k, brier_minus_midpoint=pt, ci_low=lo, ci_high=hi))
for fam in GRIDS:
    pt, lo, hi = boot_diff(preds[f'{fam}__with_volume'], preds[f'{fam}__no_volume'])
    cmp.append(dict(model=f'{fam}: with minus without volume', brier_minus_midpoint=pt, ci_low=lo, ci_high=hi))
cmp = pd.DataFrame(cmp); cmp.to_csv(RES/'bootstrap_comparisons.csv', index=False); cmp.round(5)

# %% [markdown]
# ## What the best model learned
# Standardized elastic-net coefficients (positive = more likely to win) and XGBoost permutation importance on test.

# %%
en = fitted['elastic_net_logistic__with_volume']
names = en.named_steps['prep'].get_feature_names_out(); coef = en.named_steps['model'].coef_[0]
coefs = pd.Series(coef, index=[n.split('__', 1)[1] for n in names]).sort_values()
coefs.to_csv(RES/'elastic_net_coefficients.csv'); print(chosen[('elastic_net_logistic','with_volume')]); coefs.round(3)

# %%
from sklearn.inspection import permutation_importance
xg = fitted['xgboost__with_volume']; cols = MARKET + VOLUME + CAT
pi = permutation_importance(xg, te[cols], te.y_win, scoring='neg_brier_score', n_repeats=10, random_state=SEED)
imp = pd.Series(pi.importances_mean, index=cols).sort_values(ascending=False); imp.to_csv(RES/'xgboost_permutation_importance.csv'); imp.round(5)

# %% [markdown]
# ## Descriptive findings: calibration, time to event, category, economics

# %%
def wilson(k, n, z=1.96):
    p = k / n; den = 1 + z*z/n; c = (p + z*z/(2*n)) / den; hw = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n)) / den; return c - hw, c + hw
bins = [0.895, 0.92, 0.94, 0.96, 0.97, 0.98, 0.99, 1.0]
cal = d.assign(b=pd.cut(d.midpoint, bins)).groupby(['split', 'b'], observed=True).agg(n=('y_win','size'), wins=('y_win','sum'), mid=('midpoint','mean')).reset_index()
cal['win_rate'] = cal.wins / cal.n; cal[['lo','hi']] = [wilson(k, n) for k, n in zip(cal.wins, cal.n)]
cal.to_csv(RES/'calibration.csv', index=False)
hb = pd.cut(d.hours_to_event, [-1e9, 0, 1, 6, 24, 72, 1e9], labels=['event passed','0–1 h','1–6 h','6–24 h','1–3 days','> 3 days'])
tte = d.assign(hb=hb).groupby('hb', observed=True).agg(n=('y_win','size'), losses=('y_win', lambda s: int((1-s).sum())), mean_mid=('midpoint','mean')).reset_index()
tte['loss_rate'] = tte.losses / tte.n; tte['implied_loss'] = 1 - tte.mean_mid; tte.to_csv(RES/'loss_by_time_to_event.csv', index=False)
catt = d.groupby('category_group').agg(n=('y_win','size'), losses=('y_win', lambda s: int((1-s).sum())), mean_mid=('midpoint','mean'))
catt['loss_rate'] = catt.losses / catt.n; catt['implied_loss'] = 1 - catt.mean_mid; catt = catt.sort_values('n', ascending=False)
# event-level bootstrap CI for (observed − implied) loss rate per category: markets in one event (e.g. a ladder of strikes) move together
def cat_ci(g, B=1000):
    gev = g.groupby('event_slug').agg(l=('y_win', lambda s: (1-s).sum()), im=('midpoint', lambda s: (1-s).sum()), n=('y_win','size'))
    v = gev.values; out = []
    for _ in range(B):
        r = v[rng.integers(0, len(v), len(v))]; out.append((r[:,0].sum() - r[:,1].sum()) / r[:,2].sum())
    return pd.Series(dict(events=len(gev), gap_lo=np.percentile(out, 2.5), gap_hi=np.percentile(out, 97.5)))
catt = catt.join(d.groupby('category_group').apply(cat_ci)); catt['gap'] = catt.loss_rate - catt.implied_loss
catt.to_csv(RES/'loss_by_category.csv')
d['gross'] = d.y_win - d.ask
econ = d.groupby(['split','price_band']).agg(n=('gross','size'), wins=('y_win','sum'), gross_per_contract=('gross','mean'), total=('gross','sum')).reset_index()
econ.to_csv(RES/'economics_by_split_band.csv', index=False)
display(tte.round(4)); display(catt.round(4)); display(econ.round(4))

# %% [markdown]
# ## Does a model-based filter change the economics? (illustration only)
# Buy only when the chosen model's win probability exceeds the ask by a margin picked on validation. One contract per
# entry, bought at the displayed ask, held to settlement, before fees. Not an executable backtest.

# %%
best = scores[(scores.split == 'validation') & scores.model.str.contains('__')].sort_values('brier').iloc[0].model   # best fitted feature model
vb = val_preds[best]; trials = []
for mg in [0, 0.005, 0.01, 0.02, 0.03]:
    s = vb - va.ask.values > mg
    trials.append(dict(margin=mg, val_entries=int(s.sum()), val_gross_per=float((va.y_win.values - va.ask.values)[s].mean()) if s.sum() else np.nan))
trials = pd.DataFrame(trials); ok = trials[trials.val_entries >= 30]
mg = float(ok.sort_values('val_gross_per', ascending=False).iloc[0].margin) if len(ok) else 0.0
s = preds[best] - te.ask.values > mg; g = te.y_win.values - te.ask.values
strategy = pd.DataFrame([dict(rule='buy every eligible test entry', entries=len(te), losses=int((1-te.y_win).sum()), total_gross=g.sum(), per_contract=g.mean()),
                         dict(rule=f'{best}: p − ask > {mg}', entries=int(s.sum()), losses=int((1-te.y_win.values)[s].sum()), total_gross=g[s].sum(), per_contract=g[s].mean() if s.sum() else np.nan)])
strategy.to_csv(RES/'strategy_illustration.csv', index=False); trials.to_csv(RES/'strategy_validation_trials.csv', index=False); strategy.round(4)

# %% [markdown]
# ## Figures for the slides
# Styled with `style_guide/ucla_style.py` (UCLA colors, Arial). Slide figures carry no title: the slide title states the
# finding. Blue = the data, gray = the benchmark, gold = worse than the benchmark.

# %%
import sys; sys.path.insert(0, str(ROOT/'style_guide'))
import ucla_style as us
us.apply()

# 1 · calibration on test
fig, ax = us.figure((5.4, 4.3))
ct = cal[cal.split == 'test']
ax.plot([0.9, 1], [0.9, 1], color=us.REFERENCE, lw=1.4, ls='--', zorder=1)
ax.errorbar(ct.mid, ct.win_rate, yerr=[ct.win_rate - ct.lo, ct.hi - ct.win_rate], fmt='none', ecolor=us.DARK, lw=1.3, zorder=2)
ax.scatter(ct.mid, ct.win_rate, color=us.PRIMARY, s=60, zorder=3)
for k, (_, r) in enumerate(ct.iterrows()): us.label(ax, r.mid, 0.8625 + 0.0075 * (k % 2), f'n={r.n:,}', va='bottom', fontsize=9, color=us.GRAY_60)
ax.set(xlabel='Quoted midpoint (market probability)  ·  dashed: win rate = price', ylabel='Share of favorites that won', xlim=(0.9, 1.0), ylim=(0.86, 1.005))
ax.grid(axis='x', color=us.GRAY_10)
us.save(fig, FIG/'calibration_test.png')

# 2 · loss rate by time to the scheduled event
fig, ax = us.figure((5.8, 4.0)); x = np.arange(len(tte))
ax.bar(x - 0.19, tte.loss_rate * 100, 0.36, color=us.PRIMARY, label='Observed loss rate')
ax.bar(x + 0.19, tte.implied_loss * 100, 0.36, color=us.REFERENCE, label='Implied by price')
for i, r in tte.iterrows(): us.label(ax, i - 0.19, r.loss_rate * 100 + 0.12, f'{r.loss_rate*100:.1f}%', fontsize=9.5)
ax.set_xticks(x, [str(h).replace('event passed', 'started') for h in tte.hb]); ax.set_ylim(0, 7.2)
ax.set_ylabel('Favorites that lost (%)'); ax.set_xlabel('Time from entry to the scheduled event')
ax.legend(loc='upper left', ncol=2)
us.save(fig, FIG/'loss_by_time_to_event.png')

# 3 · every model vs the price (test Brier difference, event bootstrap 95% CI)
lab = {'price_only_logistic': 'Price-only logistic', 'training_win_rate': 'Training win rate',
       'elastic_net_logistic__no_volume': 'Elastic net', 'elastic_net_logistic__with_volume': 'Elastic net + volume',
       'random_forest__no_volume': 'Random forest', 'random_forest__with_volume': 'Random forest + volume',
       'xgboost__no_volume': 'XGBoost', 'xgboost__with_volume': 'XGBoost + volume'}
cm = cmp[cmp.model.isin(lab)].assign(label=lambda t: t.model.map(lab)).sort_values('brier_minus_midpoint', ascending=False)
fig, ax = us.figure((6.0, 4.1)); yy = np.arange(len(cm))
col = [us.PRIMARY if h < 0 else (us.ATTENTION if l > 0 else us.REFERENCE) for l, h in zip(cm.ci_low, cm.ci_high)]
ax.errorbar(cm.brier_minus_midpoint * 1e3, yy, xerr=[(cm.brier_minus_midpoint - cm.ci_low) * 1e3, (cm.ci_high - cm.brier_minus_midpoint) * 1e3],
            fmt='none', ecolor=us.DARK, lw=1.2)
ax.scatter(cm.brier_minus_midpoint * 1e3, yy, c=col, s=70, zorder=3, edgecolors=us.DARK, linewidths=0.6)
ax.axvline(0, color=us.GRAY_80, lw=1.2)
ax.set_yticks(yy, cm.label); ax.grid(axis='y', visible=False); ax.grid(axis='x', color=us.GRAY_10)
ax.set_xlabel('Test Brier score minus the quoted price (×1,000)')
ax.text(-0.04, len(cm) - 0.35, '← better than price', ha='right', fontsize=9.5, color=us.GRAY_60)
ax.text(0.04, len(cm) - 0.35, 'worse than price →', ha='left', fontsize=9.5, color=us.GRAY_60)
ax.set_ylim(-0.6, len(cm) - 0.1)
us.save(fig, FIG/'model_vs_price.png')

# 4 · loss rate by category (bars) vs price-implied rate (ticks)
cc = catt[catt.n >= 50].sort_values('loss_rate')
fig, ax = us.figure((6.2, 4.0)); yy = np.arange(len(cc))
bar_col = [us.ATTENTION if g > 0 and lo > 0 else us.PRIMARY for g, lo in zip(cc.gap, cc.gap_lo)]
ax.barh(yy, cc.loss_rate * 100, color=bar_col, height=0.6)
ax.scatter(cc.implied_loss * 100, yy, color=us.DARK, marker='|', s=320, lw=2.4, zorder=3)
xr = max(cc.loss_rate.max(), cc.implied_loss.max()) * 100 + 0.35
for i, (_, r) in enumerate(cc.iterrows()):
    ax.text(xr, i, f'{r.loss_rate*100:.1f}% vs {r.implied_loss*100:.1f}%  (n={int(r.n):,})', va='center', fontsize=9.5, color=us.GRAY_80)
ax.set_xlim(0, xr + 3.6); ax.set_yticks(yy, cc.index); ax.grid(axis='y', visible=False); ax.grid(axis='x', color=us.GRAY_10)
ax.set_xlabel('Favorites that lost (%)   ·   tick = rate implied by price')
us.save(fig, FIG/'loss_by_category.png')

# 5 · gross result per contract by period
es = d.groupby('split').gross.mean().reindex(['train', 'validation', 'test']) * 100
fig, ax = us.figure((5.4, 3.9))
ax.bar(['Train', 'Validation', 'Test'], es.values, color=[us.PRIMARY if v >= 0 else us.ATTENTION for v in es.values], width=0.55)
for i, v in enumerate(es.values): us.label(ax, i, v + (0.06 if v >= 0 else -0.06), f'{v:+.2f}¢'.replace('-', '−'), va='bottom' if v >= 0 else 'top', fontsize=11)
ax.axhline(0, color=us.GRAY_80, lw=1.2); ax.set_ylim(es.min() - 0.5, max(es.max(), 0) + 0.45)
ax.set_ylabel('Average gross result per contract (¢)')
us.save(fig, FIG/'economics_by_split.png')

# 6 · data coverage: hours with candles per day
cov = pd.read_csv(RES/'coverage_by_day.csv')
fig, ax = us.figure((5.8, 3.6))
ax.bar(cov.day.str[3:].astype(int).astype(str), cov.hours, color=us.PRIMARY, width=0.7)
for i, h in enumerate(cov.hours):
    if h == 0: us.label(ax, i, 0.3, 'none', fontsize=8.5, color=us.GRAY_60, rotation=90)
ax.set_ylim(0, 24.5); ax.set_yticks([0, 6, 12, 18, 24]); ax.set_ylabel('Hours with candles'); ax.set_xlabel('Day in October 2026 (UTC)')
us.save(fig, FIG/'coverage_by_day.png')
print(sorted(p.name for p in FIG.glob('*.png')))

# %%
summary = dict(chosen={f'{a}__{b}': v for (a, b), v in chosen.items()}, best_on_validation=best, strategy_margin=mg,
               n=d.groupby('split').y_win.agg(['size', lambda s: int((1-s).sum())]).set_axis(['markets','losses'], axis=1).to_dict('index'),
               collection_lag_median_h=float(d.collection_lag_h.median()), observed_after_close=float(d.observed_after_close.mean()))
(RES/'summary.json').write_text(json.dumps(summary, indent=2, default=str)); summary
