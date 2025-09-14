"""
Advanced Bluff Score Calculator
Uses baseline comparison method for more accurate deception detection
"""

import numpy as np
from typing import Dict, List, Optional, Any

def _safe(v, default=0.0):
    """Safely handle None or NaN values"""
    return default if v is None or (isinstance(v, float) and np.isnan(v)) else v

def _mad_std(vals):
    """Calculate robust standard deviation using Median Absolute Deviation"""
    vals = np.asarray(vals, dtype=float)
    vals = vals[~np.isnan(vals)]
    if len(vals) == 0:
        return 1.0
    med = np.median(vals)
    mad = np.median(np.abs(vals - med))
    return max(1e-6, 1.4826 * mad)

def _z(val, mean, std):
    """Calculate z-score with robust standard deviation"""
    std = std if std and std > 1e-6 else 1.0
    return (val - mean) / std

def _normalize_delta(val, lo, hi):
    """Normalize value to 0-1 range"""
    return float(max(0.0, min(1.0, (val - lo) / (hi - lo))))

def calculate_bluff_score_with_baselines(
    target_feats: dict,
    intro_feats: dict,
    hobby_feats: dict,
    story_feats: dict,
    norm_feats: dict,
) -> Dict[str, Any]:
    """
    Calculate bluff score using baseline comparison method
    
    Args:
        target_feats: Features from the target recording (question 5 - truth/lie)
        intro_feats: Features from introduction (question 1)
        hobby_feats: Features from hobby question (question 2) 
        story_feats: Features from story reading (question 3)
        norm_feats: Features from technical reading (question 4)
        
    Returns:
        Dictionary with score, confidence, reasons, and details
    """

    def _avg_feats(a, b, keys):
        """Average features from two recordings"""
        out = {}
        for k in keys:
            va, vb = _safe(a.get(k), np.nan), _safe(b.get(k), np.nan)
            out[k] = np.nanmean([va, vb]) if not (np.isnan(va) and np.isnan(vb)) else np.nan
        return out

    # Define feature keys for different types of speech
    conv_keys = ["pause_ratio", "pause_count", "mean_rms_db", "max_rms_db"]
    read_keys = ["mean_f0", "mean_rms_db"] 
    
    # Create baselines by averaging similar speech types
    conv_base = _avg_feats(intro_feats, hobby_feats, conv_keys + ["mean_f0"])
    read_base = _avg_feats(story_feats, norm_feats, read_keys)

    def _dist_to(base, feats):
        """Calculate distance between target and baseline features"""
        d = 0.0; cnt = 0
        for k in ["pause_ratio", "mean_rms_db"]:
            if k in base and base[k] is not None and not np.isnan(base[k]) and k in feats:
                d += abs(_safe(feats.get(k)) - _safe(base.get(k)))
                cnt += 1
        return d / cnt if cnt else 1.0

    # Determine which baseline is more relevant
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

    # Create feature pools for robust statistics
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

    # Calculate contributions for each feature
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

    # Feature weights
    weights = {
        "pause_ratio": 0.26,
        "pause_count": 0.18,
        "mean_rms_db": 0.20,
        "max_rms_db":  0.16,
        "mean_f0":     0.20,
    }

    # Calculate final score
    active = {k: v for k, v in contributions.items() if np.isfinite(v)}
    if not active:
        return {"score": 0.0, "confidence": 0.3, "reasons": ["insufficient data"], "detail": {}}
    
    wsum = sum(weights[k] for k in active.keys())
    score01 = sum(contributions[k] * (weights[k] / wsum) for k in active.keys())
    score = round(100.0 * max(0.0, min(1.0, score01)), 1)

    # Calculate confidence based on data quality
    dur = _safe(target_feats.get("duration_s"), 10.0)
    speech = _safe(target_feats.get("speech_dur_s"), max(0.6*dur, 6.0))
    speech_ratio = speech / max(1e-6, dur)
    missing_penalty = 0.1 * (5 - len(active))
    conf = max(0.3, min(0.95, 0.6 * min(1.0, speech_ratio) + 0.35 * (1.0 - missing_penalty)))

    # Generate reasons based on top contributing features
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

def simple_bluff_score(features: dict) -> Dict[str, Any]:
    """
    Simple bluff score calculation for single recording (fallback method)
    """
    pause_ratio = _safe(features.get("pause_ratio", 0))
    pause_count = _safe(features.get("pause_count", 0))
    mean_f0 = _safe(features.get("mean_f0", 150))
    mean_rms_db = _safe(features.get("mean_rms_db", -30))
    
    # Simple scoring based on thresholds
    score = 0.0
    
    # Pause indicators
    if pause_ratio > 0.2:
        score += 25
    elif pause_ratio > 0.1:
        score += 10
        
    if pause_count > 10:
        score += 20
    elif pause_count > 5:
        score += 10
    
    # F0 indicators (extreme values suggest stress)
    if mean_f0 < 100 or mean_f0 > 250:
        score += 15
    elif mean_f0 < 120 or mean_f0 > 200:
        score += 8
    
    # Energy indicators
    if mean_rms_db > -10:
        score += 20  # Very loud
    elif mean_rms_db < -50:
        score += 15  # Very quiet
    
    score = min(100, max(0, score))
    
    reasons = []
    if pause_ratio > 0.15:
        reasons.append("High pause ratio detected")
    if pause_count > 8:
        reasons.append("Frequent pausing detected") 
    if mean_f0 < 120 or mean_f0 > 200:
        reasons.append("Unusual pitch patterns")
    
    if not reasons:
        reasons = ["Speech patterns appear normal"]
    
    return {
        "score": round(score, 1),
        "confidence": 0.7,
        "reasons": reasons,
        "detail": {"method": "simple_threshold"}
    }