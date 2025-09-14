import numpy as np

def _safe(v, default=0.0):
    return default if v is None or (isinstance(v, float) and np.isnan(v)) else v

def _mad_std(vals):
    vals = np.asarray(vals, dtype=float)
    vals = vals[~np.isnan(vals)]
    if len(vals) == 0:
        return 1.0
    med = np.median(vals)
    mad = np.median(np.abs(vals - med))
    return max(1e-6, 1.4826 * mad)

def _z(val, mean, std):
    std = std if std and std > 1e-6 else 1.0
    return (val - mean) / std

def _normalize_delta(val, lo, hi):
    return float(max(0.0, min(1.0, (val - lo) / (hi - lo))))

def calculate_bluff_score_with_baselines(
    target_feats: dict,
    intro_feats: dict,
    hobby_feats: dict,
    story_feats: dict,
    norm_feats: dict,
):

    def _avg_feats(a, b, keys):
        out = {}
        for k in keys:
            va, vb = _safe(a.get(k), np.nan), _safe(b.get(k), np.nan)
            out[k] = np.nanmean([va, vb]) if not (np.isnan(va) and np.isnan(vb)) else np.nan
        return out

    conv_keys = ["pause_ratio", "pause_count", "mean_rms_db", "max_rms_db"]
    read_keys = ["mean_f0", "mean_rms_db"] 
    conv_base = _avg_feats(intro_feats, hobby_feats, conv_keys + ["mean_f0"])
    read_base = _avg_feats(story_feats, norm_feats, read_keys)

    def _dist_to(base, feats):
        d = 0.0; cnt = 0
        for k in ["pause_ratio", "mean_rms_db"]:
            if k in base and base[k] is not None and not np.isnan(base[k]) and k in feats:
                d += abs(_safe(feats.get(k)) - _safe(base.get(k)))
                cnt += 1
        return d / cnt if cnt else 1.0

    target = {k: _safe(target_feats.get(k), np.nan) for k in set(conv_keys + read_keys + ["pause_ratio"])}
    d_conv = _dist_to(conv_base, target)
    d_read = _dist_to(read_base, target)
    if np.isfinite(d_conv) and np.isfinite(d_read) and (d_conv + d_read) > 0:
        conv_w = float(d_read / (d_conv + d_read)) 
        conv_w = 1.0 - conv_w
    else:
        conv_w = 0.6 
    read_w = 1.0 - conv_w

    contributions = {}

    conv_pool = {
        "pause_ratio": [intro_feats.get("pause_ratio"), hobby_feats.get("pause_ratio")],
        "pause_count": [intro_feats.get("pause_count"), hobby_feats.get("pause_count")],
        "mean_rms_db": [intro_feats.get("mean_rms_db"), hobby_feats.get("mean_rms_db")],
        "max_rms_db":  [intro_feats.get("max_rms_db"),  hobby_feats.get("max_rms_db")],
    }
    conv_std = {k: _mad_std(np.array(v, dtype=float)) for k, v in conv_pool.items()}

    read_pool = {
        "mean_f0":     [story_feats.get("mean_f0"),     norm_feats.get("mean_f0")],
        "mean_rms_db": [story_feats.get("mean_rms_db"), norm_feats.get("mean_rms_db")],
    }
    read_std = {k: _mad_std(np.array(v, dtype=float)) for k, v in read_pool.items()}

    if np.isfinite(target.get("pause_ratio")) and np.isfinite(conv_base.get("pause_ratio")):
        z_pause = abs(_z(target["pause_ratio"], conv_base["pause_ratio"], conv_std["pause_ratio"]))
        contributions["pause_ratio"] = conv_w * _normalize_delta(z_pause, 0.0, 3.0)

    if np.isfinite(target.get("pause_count")) and np.isfinite(conv_base.get("pause_count")):
        z_pcnt = abs(_z(target["pause_count"], conv_base["pause_count"], max(1.0, conv_std["pause_count"])))
        contributions["pause_count"] = conv_w * _normalize_delta(z_pcnt, 0.0, 3.0)

    if np.isfinite(target.get("mean_rms_db")):
        val = target["mean_rms_db"]
        comp = []
        if np.isfinite(conv_base.get("mean_rms_db")):
            comp.append( abs(_z(val, conv_base["mean_rms_db"], read_std.get("mean_rms_db", 2.0))) * conv_w )
        if np.isfinite(read_base.get("mean_rms_db")):
            comp.append( abs(_z(val, read_base["mean_rms_db"], read_std.get("mean_rms_db", 2.0))) * read_w )
        if comp:
            contributions["mean_rms_db"] = _normalize_delta(np.mean(comp), 0.0, 3.0)

    if np.isfinite(target.get("max_rms_db")) and np.isfinite(conv_base.get("max_rms_db")):
        z_max = abs(_z(target["max_rms_db"], conv_base["max_rms_db"], max(1.5, conv_std["max_rms_db"])))
        contributions["max_rms_db"] = conv_w * _normalize_delta(z_max, 0.0, 3.0)

    if np.isfinite(target.get("mean_f0")) and np.isfinite(read_base.get("mean_f0")):
        z_f0 = abs(_z(target["mean_f0"], read_base["mean_f0"], max(5.0, read_std["mean_f0"])))
        contributions["mean_f0"] = read_w * _normalize_delta(z_f0, 0.0, 3.0)

    weights = {
        "pause_ratio": 0.26,
        "pause_count": 0.18,
        "mean_rms_db": 0.20,
        "max_rms_db":  0.16,
        "mean_f0":     0.20,
    }

    active = {k: v for k, v in contributions.items() if np.isfinite(v)}
    if not active:
        return {"score": 0.0, "confidence": 0.3, "reasons": ["insufficient data"], "detail": {}}
    wsum = sum(weights[k] for k in active.keys())
    score01 = sum(contributions[k] * (weights[k] / wsum) for k in active.keys())
    score = round(100.0 * max(0.0, min(1.0, score01)), 1)

    dur = _safe(target_feats.get("duration_s"), 10.0)
    speech = _safe(target_feats.get("speech_dur_s"), max(0.6*dur, 6.0))
    speech_ratio = speech / max(1e-6, dur)
    missing_penalty = 0.1 * (5 - len(active))  # 缺一项-0.1
    conf = max(0.3, min(0.95, 0.6 * min(1.0, speech_ratio) + 0.35 * (1.0 - missing_penalty)))

    top = sorted(active.items(), key=lambda kv: -kv[1])[:2]
    reason_map = {
        "pause_ratio": "More/longer pauses vs conversational baseline",
        "pause_count": "More pause events vs conversational baseline",
        "mean_rms_db": "Loudness shift vs baseline",
        "max_rms_db":  "Peaks louder than baseline",
        "mean_f0":     "Pitch higher/lower vs reading baseline",
    }
    reasons = [reason_map[k] for k, _ in top]

    return {
        "score": score,
        "confidence": round(conf, 2),
        "reasons": reasons,
        "detail": {
            "conv_weight": round(conv_w, 2),
            "read_weight": round(read_w, 2),
            "contributions": {k: round(float(v), 3) for k, v in contributions.items()}
        }
    }


def vec_to_feats(vec):
    return {
        "pause_ratio": float(vec[0]),
        "pause_count": int(vec[1]),
        "mean_f0": float(vec[2]),
        "max_rms_db": float(vec[3]),
        "mean_rms_db": float(vec[4]),
    }


#target = vec_to_feats([0.264,2,115.27,-11.74,-25.87])#{"pause_ratio":0.9,"pause_count":4,"mean_f0":128.0,"mean_rms_db":-24.5,"max_rms_db":-10.8,"duration_s":10.2,"speech_dur_s":7.1}
#intro  = vec_to_feats([0.083,2,100.51,-12.95,-29.69])#{"pause_ratio":0.4,"pause_count":2,"mean_f0":118.0,"mean_rms_db":-28.5,"max_rms_db":-14.0}
#hobby  = vec_to_feats([0.123,0,88.15,-14.13,-32.93])#{"pause_ratio":0.5,"pause_count":2,"mean_f0":120.5,"mean_rms_db":-27.9,"max_rms_db":-13.1}
#story  = vec_to_feats([0.049,4,112.47,-11.38,-26.91])#{"mean_f0":110.0,"mean_rms_db":-29.0}
#norm   = vec_to_feats([0.037,2,109.5,-12.65,-29.2])#{"mean_f0":112.0,"mean_rms_db":-28.7}

out = calculate_bluff_score_with_baselines(target, intro, hobby, story, norm)
print(out)
# {'score': 73.4, 'confidence': 0.86, 'reasons': ['Loudness shift vs baseline', 'More/longer pauses vs conversational baseline'], ...}
