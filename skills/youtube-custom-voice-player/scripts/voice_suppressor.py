import subprocess
import numpy as np
import os

def extract_stereo_audio(video_path, sr=48000, start=0.0, duration=None):
    cmd = ['ffmpeg', '-v', 'error']
    if start > 0:
        cmd += ['-ss', f'{start:.3f}']
    if duration is not None:
        cmd += ['-t', f'{duration:.3f}']
    cmd += ['-i', video_path, '-vn', '-ac', '2', '-ar', str(sr), '-f', 'f32le', '-']
    try:
        raw = subprocess.check_output(cmd)
    except subprocess.CalledProcessError:
        return None
    if not raw:
        return None
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2)


def stft_channel(x, n_fft=2048, hop=512):
    win = np.hanning(n_fft).astype(np.float32)
    pad = n_fft
    x_pad = np.pad(x, (pad, pad), mode='reflect')
    n_frames = 1 + (len(x_pad) - n_fft) // hop
    frames = np.lib.stride_tricks.sliding_window_view(x_pad, n_fft)[::hop][:n_frames]
    spec = np.fft.rfft(frames * win, axis=1)
    return spec, len(x), pad


def istft_channel(spec, orig_len, pad, n_fft=2048, hop=512):
    win = np.hanning(n_fft).astype(np.float32)
    n_frames = spec.shape[0]
    total_len = (n_frames - 1) * hop + n_fft
    y = np.zeros(total_len, dtype=np.float32)
    wsum = np.zeros(total_len, dtype=np.float32)
    frames = np.fft.irfft(spec, n=n_fft, axis=1).astype(np.float32) * win
    for i in range(n_frames):
        idx = i * hop
        y[idx:idx + n_fft] += frames[i]
        wsum[idx:idx + n_fft] += win ** 2
    y /= np.maximum(wsum, 1e-8)
    return y[pad:pad + orig_len]


def suppress_voice_keep_ambient(stereo_audio, sr=48000):
    """
    Suppresses all human voices, laughter, and crowd chatter while preserving
    natural car engine, road rumble, tire hum, wind, and nature ambience.
    """
    if stereo_audio is None or len(stereo_audio) < sr // 2:
        return stereo_audio

    n_fft = 2048
    hop = 512
    freqs = np.fft.rfftfreq(n_fft, 1.0 / sr)
    n_bins = len(freqs)

    # Convert to Left/Right STFT
    spec_L, orig_len, pad = stft_channel(stereo_audio[:, 0], n_fft, hop)
    spec_R, _, _ = stft_channel(stereo_audio[:, 1], n_fft, hop)
    n_frames = spec_L.shape[0]

    mag_L = np.abs(spec_L)
    mag_R = np.abs(spec_R)
    mag_mean = 0.5 * (mag_L + mag_R) + 1e-8

    # 1. Detect quietest / least-voiced frames across the clip to model true ambient road/nature bed
    # Speech lives heavily in 180 Hz - 4500 Hz and has high peak-to-average (harmonicity) + modulation
    voice_bins = (freqs >= 180) & (freqs <= 4500)
    low_bins = (freqs >= 25) & (freqs < 160)

    voice_band_mag = mag_mean[:, voice_bins]
    # Spectral flatness in voice band (broadband road/wind has high flatness; voice harmonics have low flatness)
    geo_mean = np.exp(np.mean(np.log(voice_band_mag + 1e-8), axis=1))
    arith_mean = np.mean(voice_band_mag, axis=1) + 1e-8
    flatness = geo_mean / arith_mean

    voice_energy = arith_mean
    low_energy = np.mean(mag_mean[:, low_bins], axis=1) + 1e-8

    # Frame-level voice likelihood score: high voice_energy, low flatness, high voice/low ratio
    v_score = (voice_energy / np.percentile(voice_energy, 20)) * (1.0 / (flatness + 0.1))

    # 2. Estimate slowly varying stationary ambient floor B(t, f)
    # Using a sliding window of ~3 seconds (approx 280 frames) taking the 15th percentile per bin
    win_t = min(n_frames, 240)
    step_t = max(1, win_t // 4)
    anchor_times = list(range(0, n_frames, step_t))
    if anchor_times[-1] != n_frames - 1:
        anchor_times.append(n_frames - 1)

    floor_anchors_L = []
    floor_anchors_R = []
    for t0 in anchor_times:
        s = max(0, t0 - win_t // 2)
        e = min(n_frames, t0 + win_t // 2 + 1)
        # In this window, pick the 25% lowest-v_score frames (purest ambient frames)
        local_scores = v_score[s:e]
        thresh = np.percentile(local_scores, 30)
        clean_idx = np.where(local_scores <= thresh)[0] + s
        if len(clean_idx) < 4:
            clean_idx = np.arange(s, e)
        fl_L = np.percentile(mag_L[clean_idx], 35, axis=0)
        fl_R = np.percentile(mag_R[clean_idx], 35, axis=0)
        floor_anchors_L.append(fl_L)
        floor_anchors_R.append(fl_R)

    floor_anchors_L = np.array(floor_anchors_L)
    floor_anchors_R = np.array(floor_anchors_R)

    # Interpolate ambient floor smoothly across all frames
    t_grid = np.arange(n_frames)
    ambient_L = np.zeros_like(mag_L)
    ambient_R = np.zeros_like(mag_R)
    for b in range(n_bins):
        ambient_L[:, b] = np.interp(t_grid, anchor_times, floor_anchors_L[:, b])
        ambient_R[:, b] = np.interp(t_grid, anchor_times, floor_anchors_R[:, b])

    # Smooth the ambient floor across frequency bins (removes any residual harmonic comb from speech)
    # Kernel size of 17 bins (~400 Hz width) for frequencies above 75 Hz
    kernel = np.hanning(17)
    kernel /= np.sum(kernel)
    start_smooth_bin = int(75 * n_fft / sr)
    for t in range(n_frames):
        ambient_L[t, start_smooth_bin:] = np.convolve(ambient_L[t, start_smooth_bin:], kernel, mode='same')
        ambient_R[t, start_smooth_bin:] = np.convolve(ambient_R[t, start_smooth_bin:], kernel, mode='same')

    # 3. Frequency-dependent suppression mask:
    # - Below 65 Hz: Keep real sub-bass engine/road vibration.
    # - 65 Hz to 140 Hz: Smooth crossover where male fundamental voice harmonics ("hum") are clamped to ambient floor.
    # - 140 Hz+: Strict clamping to the smooth ambient road/wind spectral envelope with
    #   decorrelated stochastic phase whenever energy exceeds the ambient floor, completely erasing
    #   all speech formants, syllables, laughs, and shouts while preserving steady tire/wind/water texture!
    f_weight = np.clip((freqs - 65.0) / (140.0 - 65.0), 0.0, 1.0)
    f_weight = f_weight[None, :]  # shape (1, n_bins)

    # Excess energy ratio above ambient floor in each (t, f) bin
    excess_L = mag_L / (ambient_L + 1e-8)
    excess_R = mag_R / (ambient_R + 1e-8)
    excess = np.maximum(excess_L, excess_R)

    # Soft mask that pulls any excess above 1.05x ambient floor down to the ambient floor in >110 Hz
    clamped_mag_L = (1.0 - f_weight) * mag_L + f_weight * np.minimum(mag_L, ambient_L * 1.05)
    clamped_mag_R = (1.0 - f_weight) * mag_R + f_weight * np.minimum(mag_R, ambient_R * 1.05)

    # Where speech excess was significant (excess > 1.35 in speech band), randomize phase slightly
    # so pitch harmonics cannot reconstruct a robotic whisper in the residual floor
    rng = np.random.default_rng(42)
    rand_phase_L = np.exp(1j * rng.uniform(-np.pi, np.pi, size=spec_L.shape)).astype(np.complex64)
    rand_phase_R = np.exp(1j * rng.uniform(-np.pi, np.pi, size=spec_R.shape)).astype(np.complex64)
    orig_phase_L = spec_L / (mag_L + 1e-8)
    orig_phase_R = spec_R / (mag_R + 1e-8)

    # Blend phase: original phase in low frequencies & unvoiced bins, stochastic phase in suppressed voice bins
    phase_blend = np.clip((excess - 1.2) / 1.5, 0.0, 1.0) * f_weight
    new_phase_L = (1.0 - phase_blend) * orig_phase_L + phase_blend * rand_phase_L
    new_phase_L /= (np.abs(new_phase_L) + 1e-8)
    new_phase_R = (1.0 - phase_blend) * orig_phase_R + phase_blend * rand_phase_R
    new_phase_R /= (np.abs(new_phase_R) + 1e-8)

    out_spec_L = clamped_mag_L * new_phase_L
    out_spec_R = clamped_mag_R * new_phase_R

    out_L = istft_channel(out_spec_L, orig_len, pad, n_fft, hop)
    out_R = istft_channel(out_spec_R, orig_len, pad, n_fft, hop)
    return np.stack([out_L, out_R], axis=1)


if __name__ == '__main__':
    gopro_dir = '/Users/neilghosh/Pictures/Kerala 2026/GoPro'
    out_dir = '/Users/neilghosh/dev/video/work'
    os.makedirs(out_dir, exist_ok=True)
    for name in ['GX011476.MP4', 'GX011503.MP4', 'GX011512.MP4', 'GX011576.MP4', 'GX011587.MP4']:
        path = os.path.join(gopro_dir, name)
        audio = extract_stereo_audio(path, sr=48000, start=0, duration=12)
        clean = suppress_voice_keep_ambient(audio, sr=48000)
        out_mp3 = os.path.join(out_dir, f"{name[:8].lower()}_clean.mp3")
        p = subprocess.Popen(
            ['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', '48000', '-ac', '2', '-i', '-',
             '-acodec', 'libmp3lame', '-q:a', '3', out_mp3],
            stdin=subprocess.PIPE
        )
        p.communicate(input=clean.astype(np.float32).tobytes())
        print('Saved', out_mp3)
