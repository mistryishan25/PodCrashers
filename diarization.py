"""
Experimental Speaker Diarization with K-means Clustering
"""

import librosa
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def diarise_speakers(
    audio_path: str,
    n_speakers: int = 2,
    n_mfcc: int = 20,
    hop_length: int = 512,
    time_fmt: str = "seconds",   # "seconds" or "hms"
):
    """
    Clusters MFCC frames with K-means and returns a list of
    (speaker_id, segment_start, segment_end).

    segment_* are floats in seconds unless time_fmt == "hms",
    in which case they’re "HH:MM:SS.s" strings.
    """
    # 1️⃣  Load & extract MFCCs
    audio, sr = librosa.load(audio_path)
    mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=n_mfcc, hop_length=hop_length)

    # 2️⃣  Standardise & cluster
    mfccs_scaled = StandardScaler().fit_transform(mfccs.T)
    labels = KMeans(n_clusters=n_speakers, random_state=0).fit_predict(mfccs_scaled)

    # 3️⃣  Convert every frame index→time (in seconds)
    frame_times = librosa.frames_to_time(
        np.arange(len(labels)), sr=sr, hop_length=hop_length
    )

    # 4️⃣  Collapse consecutive frames with same speaker label
    segments = []
    start = frame_times[0]
    curr_lbl = labels[0]

    for i in range(1, len(labels)):
        if labels[i] != curr_lbl:  # speaker changed!
            end = frame_times[i]          # boundary is *start of new frame*
            segments.append((curr_lbl, start, end))
            start = end
            curr_lbl = labels[i]

    # close last segment
    segments.append((curr_lbl, start, frame_times[-1]))

    # 5️⃣  Optional pretty formatting
    if time_fmt == "hms":
        def _fmt(t):
            m, s = divmod(t, 60)
            h, m = divmod(m, 60)
            return f"{int(h):02}:{int(m):02}:{s:05.2f}"
        segments = [(spk, _fmt(s0), _fmt(s1)) for spk, s0, s1 in segments]

    return segments


# ----- EXAMPLE ----------------------------------------------------------
if __name__ == "__main__":
    for speaker, t0, t1 in diarise_speakers("debate.mp3", n_speakers=2, time_fmt="hms"):
        print(f"Speaker {speaker}: {t0}  →  {t1}")

