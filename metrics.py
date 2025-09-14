def normalize(value, vmin, vmax):
    return max(0.0, min(1.0, (value - vmin) / (vmax - vmin)))

def calculate_bluff_score(arr):

    pause_ratio, pause_count, mean_f0, max_rms_db, mean_rms_db = arr

    norm_pause_ratio = normalize(pause_ratio, 0, 3)
    norm_pause_count = normalize(pause_count, 0, 10)
    norm_f0          = normalize(mean_f0, 75, 300)
    norm_max_rms     = normalize(max_rms_db, -40, 0)
    norm_mean_rms    = normalize(mean_rms_db, -40, 0)

    weights = {
        "pause_ratio": 0.25,
        "pause_count": 0.20,
        "mean_f0": 0.15,
        "max_rms_db": 0.20,
        "mean_rms_db": 0.20,
    }

    score = (
        norm_pause_ratio * weights["pause_ratio"] +
        norm_pause_count * weights["pause_count"] +
        norm_f0          * weights["mean_f0"] +
        norm_max_rms     * weights["max_rms_db"] +
        norm_mean_rms    * weights["mean_rms_db"]
    )

    return round(score * 100, 1)

