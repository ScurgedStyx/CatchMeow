import os, glob
import numpy as np
import pandas as pd
import librosa

def extract_features(path, sr=16000, frame_length=1024, hop_length=256, top_db=35):
    y, _sr = librosa.load(path, sr=sr, mono=True)
    total_dur = len(y) / sr


    intervals = librosa.effects.split(y, top_db=top_db)
    speech_dur = float(sum((e - s) for s, e in intervals)) / sr
    pause_dur  = max(0.0, total_dur - speech_dur)
    pause_ratio = pause_dur / max(1e-6, speech_dur)
    pause_count = max(0, len(intervals) - 1)

    if len(intervals):
        y_speech = np.concatenate([y[s:e] for s, e in intervals])
    else:
        y_speech = np.zeros(0, dtype=np.float32)

    if len(y_speech) >= hop_length * 2:
        rms = librosa.feature.rms(y=y_speech, frame_length=frame_length, hop_length=hop_length).flatten()
        rms_db = 20.0 * np.log10(np.maximum(rms, 1e-8))
        mean_rms_db = float(np.mean(rms_db))
    else:
        mean_rms_db = -120.0

    fmin, fmax = 75, 300
    mean_f0 = 0.0
    if len(y_speech) >= hop_length * 2:
        try:
            f0, vflag, _ = librosa.pyin(
                y_speech, fmin=fmin, fmax=fmax, sr=sr,
                frame_length=frame_length, hop_length=hop_length
            )
            f0_voiced = f0[(vflag == True)] if vflag is not None else f0[~np.isnan(f0)]
        except Exception:
            f0 = librosa.yin(
                y_speech, fmin=fmin, fmax=fmax, sr=sr,
                frame_length=frame_length, hop_length=hop_length
            )
            f0_voiced = f0[~np.isnan(f0)]
        if len(f0_voiced) > 0:
            mean_f0 = float(np.mean(f0_voiced))

    return {
        "duration_s": round(total_dur, 3),
        "pause_ratio": round(pause_ratio, 3),
        "pause_count": int(pause_count),
        "mean_f0": round(mean_f0, 2),
        "mean_rms_db": round(mean_rms_db, 2),
    }

def process_directory(audio_dir, out_csv, pattern="*.wav"):
    files = sorted(glob.glob(os.path.join(audio_dir, pattern)))
    rows = []
    for fp in files:
        try:
            feats = extract_features(fp)
        except Exception as e:
            feats = {
                "duration_s": np.nan, "pause_ratio": np.nan,
                "pause_count": np.nan, "mean_f0": np.nan, "mean_rms_db": np.nan,
                "error": str(e)
            }
        feats["fname"] = os.path.splitext(os.path.basename(fp))[0]
        rows.append(feats)

    df = pd.DataFrame(rows).set_index("fname")
    df.to_csv(out_csv, index=True)
    print(f"Done. Wrote {len(df)} rows to: {out_csv}")
    return df

if __name__ == "__main__":
    AUDIO_DIR = "/Users/yajing/Desktop/Test_Files_Wav"#"audio_folder"
    OUT_CSV = "features_librosa0.csv"
    process_directory(AUDIO_DIR, OUT_CSV)
