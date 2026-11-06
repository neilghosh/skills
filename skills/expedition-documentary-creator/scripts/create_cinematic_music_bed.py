#!/usr/bin/env python3
"""Generates a continuous 26-minute broadcast-grade cinematic music bed (1566.85s @ 48kHz stereo)
Crossfades Kevin MacLeod's 'Tranquility Base' (Highway expanses) into 'Ambiment' (Forests/Ghats).
"""

import os
import sys
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

SR = 48000
TARGET_DURATION = 1566.850  # Must match video length down to the millisecond
TOTAL_SAMPLES = int(round(TARGET_DURATION * SR))  # 75,208,800 samples

MUSIC_DIR = '/Users/neilghosh/dev/video/work/music'
TR_PATH = os.path.join(MUSIC_DIR, 'Tranquility_Base.mp3')
AMB_PATH = os.path.join(MUSIC_DIR, 'Ambiment.mp3')
OUT_NPY = os.path.join(MUSIC_DIR, 'expedition_music_bed_48k.npy')
OUT_WAV = os.path.join(MUSIC_DIR, 'expedition_music_bed_48k.wav')

print("=" * 70)
print(f"BUILDING CONTINUOUS CINEMATIC MUSIC BED: {TARGET_DURATION:.3f}s ({TOTAL_SAMPLES} samples @ {SR}Hz)")
print("=" * 70)

def load_resample_stereo_48k(file_path):
    print(f"Loading {os.path.basename(file_path)}...")
    data, sr = sf.read(file_path, dtype='float32')
    if data.ndim == 1:
        data = np.column_stack([data, data])
    elif data.shape[1] > 2:
        data = data[:, :2]
    if sr != SR:
        print(f"  Resampling {sr}Hz -> {SR}Hz...")
        data = resample_poly(data, SR // 1000, sr // 1000, axis=0).astype(np.float32)
    return data

# 1. Load both tracks
data_tr = load_resample_stereo_48k(TR_PATH)
data_amb = load_resample_stereo_48k(AMB_PATH)

print(f"  Tranquility Base: {len(data_tr)/SR:.2f}s | Ambiment: {len(data_amb)/SR:.2f}s")

# 2. Transition Point: At 810s (~13.5 min, entering Bandipur & Nilgiri foothills)
# Crossfade duration: 20 seconds (800s to 820s)
CROSSFADE_START = 800.0
CROSSFADE_DUR = 20.0
cf_start_samp = int(CROSSFADE_START * SR)
cf_len_samp = int(CROSSFADE_DUR * SR)
cf_end_samp = cf_start_samp + cf_len_samp

music_master = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

# First part: Tranquility Base
music_master[:cf_start_samp] = data_tr[:cf_start_samp]

# Crossfade section
t = np.linspace(0.0, 1.0, cf_len_samp)[:, None]
fade_out = np.cos(t * (np.pi / 2.0)).astype(np.float32) # equal power
fade_in  = np.sin(t * (np.pi / 2.0)).astype(np.float32)

music_master[cf_start_samp:cf_end_samp] = (
    data_tr[cf_start_samp:cf_end_samp] * fade_out +
    data_amb[:cf_len_samp] * fade_in
)

# Second part: Ambiment onwards until TOTAL_SAMPLES
rem_samples = TOTAL_SAMPLES - cf_end_samp
amb_offset = cf_len_samp
music_master[cf_end_samp:TOTAL_SAMPLES] = data_amb[amb_offset:amb_offset + rem_samples]

# 3. Fade in (first 3s) and fade out (last 6.85s)
fi_samples = int(3.0 * SR)
fo_samples = int(6.85 * SR)
music_master[:fi_samples] *= np.linspace(0.0, 1.0, fi_samples)[:, None].astype(np.float32)
music_master[-fo_samples:] *= np.linspace(1.0, 0.0, fo_samples)[:, None].astype(np.float32)

# 4. Calibrate overall music bed volume to -24 dBFS
# This ensures it provides warm, rich emotional backing without overpowering speech
current_rms = float(np.sqrt(np.mean(music_master ** 2)) + 1e-9)
target_rms = 0.055  # ~ -25 dBFS
scale = target_rms / current_rms
music_master *= scale

print(f"Target RMS calibrated: {current_rms:.4f} -> {np.sqrt(np.mean(music_master ** 2)):.4f} (Peak: {np.max(np.abs(music_master)):.3f})")

# 5. Save NPY and WAV
print(f"Saving {OUT_NPY}...")
np.save(OUT_NPY, music_master)

print(f"Exporting preview WAV {OUT_WAV}...")
sf.write(OUT_WAV, music_master, SR, subtype='PCM_16')

print(f"[SUCCESS] Continuous 26-minute cinematic music bed generated! File size: {os.path.getsize(OUT_WAV)/(1024*1024):.1f} MB")
