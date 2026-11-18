"""ML models from the proposal (chapter 5), trained on SYNTHETIC data.

Metrics reported here describe fit on synthetic data only; they are not real model performance.
  - Demand forecast: LightGBM quantile (champion), TFT challenger in SIMULATION MODE (seasonal-naive proxy)
  - Ship arrival time: Random Forest regression, spread across trees as range (Eq. 7)
  - Silo stock-out time: ARIMA on silo drawdown, adjusted with forecast and planned deliveries (Eq. 9-10)
  - Predictive maintenance: Weibull survival analysis (Eq. 11-13)
  - Vessel activity: geofence rule (proposal) + DBSCAN on GPS pings (course requirement)
"""
import math
import warnings

import numpy as np
import pandas as pd

HORIZON = 14
QUANTILES = {"p10": 0.1, "p50": 0.5, "p90": 0.9}


# ------------------------------------------------------------------ demand forecast
def _features(series: np.ndarray, origin: int, h: int, target_date: pd.Timestamp, sid: int, opc: int):
    lag = series[origin + h - 7] if h <= 7 else series[origin + h - 14]
    return [sid, opc, h, target_date.dayofweek, target_date.month,
            series[origin - 6:origin + 1].mean(), series[origin - 27:origin + 1].mean(), lag]


FEATURES = ["series", "is_opc", "h", "dow", "month", "mean7", "mean28", "lag_same_dow"]


class DemandForecaster:
    def __init__(self):
        self.models, self.metrics, self.keys = {}, {}, []

    def _rows(self, wide, origins):
        X, y = [], []
        dates = wide.index
        for sid, key in enumerate(self.keys):
            s = wide[key].to_numpy()
            for o in origins:
                for h in range(1, HORIZON + 1):
                    X.append(_features(s, o, h, dates[o + h], sid, int(key[1] == "OPC")))
                    y.append(s[o + h])
        return np.array(X), np.array(y)

    def fit(self, sales: pd.DataFrame):
        import lightgbm as lgb
        wide = sales.pivot_table(index="date", columns=["plant_id", "cement_type"], values="sales_ton").sort_index()
        wide.index = pd.to_datetime(wide.index)
        self.keys = list(wide.columns)
        n = len(wide)
        cut = n - 56
        train_o, test_o = range(30, cut - HORIZON, 2), range(cut, n - HORIZON, 7)
        Xtr, ytr = self._rows(wide, train_o)
        Xte, yte = self._rows(wide, test_o)
        preds = {}
        for name, q in QUANTILES.items():
            m = lgb.LGBMRegressor(objective="quantile", alpha=q, n_estimators=250, learning_rate=0.05,
                                  num_leaves=31, min_child_samples=20, verbose=-1)
            m.fit(pd.DataFrame(Xtr, columns=FEATURES), ytr, categorical_feature=["series"])
            self.models[name] = m
            preds[name] = m.predict(pd.DataFrame(Xte, columns=FEATURES))
        naive = Xte[:, 7]  # same weekday last week/fortnight: TFT challenger proxy (simulation mode)
        ens = (preds["p50"] + naive) / 2
        wape = lambda p: float(np.abs(yte - p).sum() / np.abs(yte).sum())
        champion, challenger, ensemble = wape(preds["p50"]), wape(naive), wape(ens)
        self.metrics = {
            "champion": "LightGBM (quantile, pinball loss)", "challenger": "TFT (simulation mode: seasonal-naive proxy, not a trained TFT)",
            "wape_champion": round(champion, 4), "wape_challenger": round(challenger, 4), "wape_ensemble": round(ensemble, 4),
            "coverage_p10_p90": round(float(((yte >= preds["p10"]) & (yte <= preds["p90"])).mean()), 3),
            "ensemble_selected": ensemble < champion, "backtest_origins": len(test_o), "horizon_days": HORIZON,
            "train_rows": len(ytr), "data": "synthetic",
        }
        self._wide = wide
        return self

    def forecast(self, sales: pd.DataFrame, multipliers=None):
        wide = sales.pivot_table(index="date", columns=["plant_id", "cement_type"], values="sales_ton").sort_index()
        wide.index = pd.to_datetime(wide.index)
        o = len(wide) - 1
        start = wide.index[-1]
        rows = []
        for key in wide.columns:
            sid = self.keys.index(key)
            s = np.append(wide[key].to_numpy(), np.zeros(HORIZON))
            X = [_features(s, o, h, start + pd.Timedelta(days=h), sid, int(key[1] == "OPC")) for h in range(1, HORIZON + 1)]
            X = pd.DataFrame(X, columns=FEATURES)
            out = {k: np.maximum(0, m.predict(X)) for k, m in self.models.items()}
            mult = (multipliers or {}).get(key[0], 1.0)
            for h in range(HORIZON):
                lo, mid, hi = sorted([out["p10"][h], out["p50"][h], out["p90"][h]])
                rows.append({"plant_id": key[0], "cement_type": key[1],
                             "date": (start + pd.Timedelta(days=h + 1)).date().isoformat(),
                             "p10": round(lo * mult, 1), "p50": round(mid * mult, 1), "p90": round(hi * mult, 1)})
        return rows


# ------------------------------------------------------------------ silo stock-out (ARIMA)
def arima_stockout_days(drawdown: list, usable: float, p50: list, deliveries=None):
    """Eq. 9-10. ARIMA(1,0,0) on daily drawdown, averaged with the P50 forecast, then the first
    day the projected usable stock reaches zero (linear interpolation inside the day)."""
    from statsmodels.tsa.arima.model import ARIMA
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            fc = ARIMA(np.asarray(drawdown, float), order=(1, 0, 0)).fit().forecast(len(p50))
        except Exception:  # fallback rule, proposal 5.3
            fc = np.full(len(p50), float(np.mean(drawdown[-14:])))
    use = (np.asarray(fc) + np.asarray(p50)) / 2
    stock = usable
    arrivals = {}
    for day, qty in deliveries or []:
        arrivals[int(day)] = arrivals.get(int(day), 0) + qty
    for d, u in enumerate(use):
        stock += arrivals.get(d, 0)
        if stock - u <= 0:
            return round(d + stock / u, 2) if u > 0 else float(d), [round(x, 1) for x in use]
        stock -= u
    # beyond horizon: extend with the mean rate
    rate = float(use.mean())
    return round(len(use) + stock / rate, 2) if rate > 0 else 99.0, [round(x, 1) for x in use]


# ------------------------------------------------------------------ ship arrival time (RF)
class EtaModel:
    COLS = ["distance_nm", "avg_speed_kn", "wave_m", "cargo_ton", "plant_idx", "month"]

    def fit(self, voyages: list):
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import train_test_split
        df = pd.DataFrame([{"distance_nm": v["distanceNm"], "avg_speed_kn": v["avgSpeedKn"], "wave_m": v["avgWaveM"],
                            "cargo_ton": v["cargoTon"], "plant_idx": ord(v["toPlant"][-1]) - 65,
                            "month": int(v["departedAt"][5:7]), "y": v["durationHours"]} for v in voyages])
        Xtr, Xte, ytr, yte = train_test_split(df[self.COLS], df["y"], test_size=0.2, random_state=7)
        self.rf = RandomForestRegressor(n_estimators=200, min_samples_leaf=2, random_state=7).fit(Xtr, ytr)
        err = np.abs(self.rf.predict(Xte) - yte)
        self.metrics = {"model": "Random Forest regression", "trees": 200, "train_voyages": len(Xtr),
                        "test_voyages": len(Xte), "mae_hours": round(float(err.mean()), 2),
                        "feature_importance": dict(zip(self.COLS, np.round(self.rf.feature_importances_, 3).tolist())),
                        "data": "synthetic (282 voyages)"}
        return self

    def predict(self, rows):
        """rows: list of (distance_nm, speed_kn, wave_m, cargo_ton, plant_id, month).
        Returns (mean, std) per row; std across the B trees is the +/- range (Eq. 7)."""
        X = np.array([[d, s, w, c, ord(p[-1]) - 65, m] for d, s, w, c, p, m in rows], float)
        per_tree = np.stack([t.predict(X) for t in self.rf.estimators_])
        return list(zip(per_tree.mean(axis=0).tolist(), per_tree.std(axis=0).tolist()))


def eta_fallback(distance_nm, speed_kn, wait_p80_h, wave_m):
    """Eq. 8 route rule: d/v + W + delta(wave)."""
    delta = 0.06 * max(0.0, wave_m - 1.0)
    return distance_nm / max(speed_kn, 1) * (1 + delta) + wait_p80_h


# ------------------------------------------------------------------ vessel activity
def geofence_status(lat, lon, speed_kn, ports, radius_nm=6, anchorage_ids=("PK",)):
    """Proposal 4.1: inside a port polygon (approximated as a radius) and slow -> berthed / anchored."""
    from shared.geo import haversine_nm
    if speed_kn > 1.5:
        return "sailing"
    for p in ports:
        if haversine_nm((lat, lon), (p["lat"], p["lon"])) <= radius_nm:
            return "anchored" if p["id"] in anchorage_ids else "berthed"
    return "anchored"


def dbscan_status(track, ports):
    """DBSCAN over recent GPS pings: a dense stationary cluster means the vessel is not sailing;
    the cluster centre near a berth means berthed, elsewhere anchored."""
    from sklearn.cluster import DBSCAN
    from shared.geo import haversine_nm
    pts = np.radians([[p["lat"], p["lon"]] for p in track[-12:]])
    labels = DBSCAN(eps=1.0 / 3440.065, min_samples=6, metric="haversine").fit_predict(pts)  # 1 nm radius
    last = labels[-1]
    if last == -1:
        return "sailing", int((labels == -1).sum())
    centre = np.degrees(pts[labels == last].mean(axis=0))
    for p in ports:
        if haversine_nm(tuple(centre), (p["lat"], p["lon"])) <= 6:
            return ("anchored" if p["id"] == "PK" else "berthed"), int((labels == last).sum())
    return "anchored", int((labels == last).sum())


# ------------------------------------------------------------------ predictive maintenance (Weibull)
class WeibullMaintenance:
    BETA = {"temp": 0.04, "vib": 0.25}  # AFT coefficients (assumption, documented)

    def fit(self, n_failures=199, seed=11):
        from scipy.stats import weibull_min
        rng = np.random.default_rng(seed)
        # Running hours at the 199 recorded equipment delays (synthetic failure history).
        t = weibull_min.rvs(1.8, scale=5200, size=n_failures, random_state=rng)
        self.kappa, _, self.eta = weibull_min.fit(t, floc=0)
        self.metrics = {"model": "Weibull survival (AFT)", "kappa": round(float(self.kappa), 3),
                        "eta_hours": round(float(self.eta), 1), "failures": n_failures,
                        "note": "censored vessels not used in this prototype fit; data synthetic"}
        return self

    def risk(self, running_hours, temp_c, vib_mm_s, horizon_h=14 * 24):
        eta_k = self.eta * math.exp(-(self.BETA["temp"] * (temp_c - 82) + self.BETA["vib"] * (vib_mm_s - 3.2)))
        S = lambda u: math.exp(-((u / eta_k) ** self.kappa))
        return 1 - S(running_hours + horizon_h) / max(S(running_hours), 1e-12)
