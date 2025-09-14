## mean F0; mean energy; loudness; hesitation; speech errors; pauses; phonation type; 
import os
import glob
import numpy as np
import pandas as pd
import librosa

def extract_features(path, sr=16000, frame_length=1024, hop_length=256):
    y, _sr = librosa.load(path, sr=sr, mono=True)


    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length).flatten()
    rms_db = 20.0 * np.log10(np.maximum(rms, 1e-8))
    mean_rms_db = float(np.mean(rms_db))

    fmin, fmax = 75, 300
    mean_f0 = 0.0
    try:
        f0, vflag, _ = librosa.pyin(
            y, fmin=fmin, fmax=fmax, sr=sr,
            frame_length=frame_length, hop_length=hop_length
        )
        if vflag is not None:
            f0_voiced = f0[vflag == True]
        else:
            f0_voiced = f0[~np.isnan(f0)]
    except Exception:
        f0 = librosa.yin(
            y, fmin=fmin, fmax=fmax, sr=sr,
            frame_length=frame_length, hop_length=hop_length
        )
        f0_voiced = f0[~np.isnan(f0)]

    if len(f0_voiced) > 0:
        mean_f0 = float(np.mean(f0_voiced))

    return {
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
            feats = {"mean_f0": np.nan, "mean_rms_db": np.nan, "error": str(e)}
        feats["fname"] = os.path.splitext(os.path.basename(fp))[0]
        #feats["path"] = fp
        rows.append(feats)

    df = pd.DataFrame(rows).set_index("fname")
    df.to_csv(out_csv, index=True)
    print(f"Done. Wrote {len(df)} rows to: {out_csv}")
    return df

if __name__ == "__main__":
    AUDIO_DIR = "audio_folder"
    OUT_CSV = "features_librosa.csv"
    process_directory(AUDIO_DIR, OUT_CSV)
