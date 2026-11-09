from pathlib import Path
from math import gcd
import numpy as np
import soundfile as sf
import noisereduce as nr
from scipy.signal import butter, sosfiltfilt, resample_poly

F5_SR = 24000
STUDIO_SR = 48000


def load_mono(path: Path, target_sr: int = STUDIO_SR) -> tuple[np.ndarray, int]:
    data, sr = sf.read(str(path), dtype="float32")
    if data.ndim > 1:
        data = np.mean(data, axis=1)
    if sr != target_sr:
        g = gcd(sr, target_sr)
        data = resample_poly(data, target_sr // g, sr // g).astype(np.float32)
    return data, target_sr


def highpass_rumble(audio: np.ndarray, sr: int, cutoff_hz: float = 80.0) -> np.ndarray:
    """Remove only sub-vocal stadium/room rumble (<80 Hz), preserving 100% of upper vocal harmonics."""
    sos = butter(3, cutoff_hz, btype="highpass", fs=sr, output="sos")
    return sosfiltfilt(sos, audio).astype(np.float32)


def studio_vocal_eq_and_exciter(audio: np.ndarray, sr: int) -> np.ndarray:
    """Restore vocal body (150-300 Hz), presence (3-5 kHz), and high-frequency air (8-16 kHz)."""
    # 1. Warmth body band (140 - 320 Hz)
    sos_warm = butter(2, [140.0, 320.0], btype="bandpass", fs=sr, output="sos")
    warmth = sosfiltfilt(sos_warm, audio)

    # 2. Vocal clarity/presence band (2800 - 5500 Hz)
    sos_pres = butter(2, [2800.0, 5500.0], btype="bandpass", fs=sr, output="sos")
    presence = sosfiltfilt(sos_pres, audio)

    # 3. High-frequency air & subtle harmonic exciter
    nyq = sr / 2.0
    if nyq > 10000.0:
        sos_air = butter(2, 7500.0, btype="highpass", fs=sr, output="sos")
        # Soft-saturate presence band to generate natural upper harmonics, then highpass >7.5 kHz
        excited = np.tanh(presence * 2.5) * 0.15
        air = sosfiltfilt(sos_air, audio + excited)
    else:
        sos_air = butter(2, 6500.0, btype="highpass", fs=sr, output="sos")
        air = sosfiltfilt(sos_air, audio)

    enhanced = audio + 0.18 * warmth + 0.25 * presence + 0.30 * air
    return enhanced.astype(np.float32)


def soft_expander_gate(audio: np.ndarray, sr: int, threshold_db: float = -38.0, ratio: float = 2.5) -> np.ndarray:
    """Smooth downward expander (not a hard gate) so inter-word pauses are quiet without choppy tails."""
    win = int(0.030 * sr)
    rms = np.sqrt(np.convolve(audio**2, np.ones(win) / win, mode="same") + 1e-12)
    peak_rms = np.max(rms) + 1e-9
    thresh = peak_rms * (10.0 ** (threshold_db / 20.0))

    ratio_env = np.minimum(rms / (thresh + 1e-9), 1.0)
    gain = np.power(np.clip(ratio_env, 0.12, 1.0), ratio - 1.0)

    smooth_win = int(0.035 * sr)
    gain = np.convolve(gain, np.ones(smooth_win) / smooth_win, mode="same")
    return (audio * gain).astype(np.float32)


def finalize_reference_clip(audio_48k: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Fade edges gently and downsample cleanly to 24kHz for F5-TTS native mel frontend."""
    fade_len = int(0.020 * STUDIO_SR)
    if len(audio_48k) > 2 * fade_len:
        audio_48k[:fade_len] *= np.linspace(0.0, 1.0, fade_len, dtype=np.float32)
        audio_48k[-fade_len:] *= np.linspace(1.0, 0.0, fade_len, dtype=np.float32)

    peak = np.max(np.abs(audio_48k))
    if peak > 1e-6:
        audio_48k = audio_48k * (0.89 / peak)

    # Downsample cleanly to 24kHz for F5-TTS native mel frontend
    audio_24k = resample_poly(audio_48k, 1, 2).astype(np.float32)
    return audio_24k, audio_48k.astype(np.float32)


def clean_broadcast_segment(
    audio_48k: np.ndarray,
    noise_clip_48k: np.ndarray,
    prop_decrease: float = 0.78,
    gate_db: float = -36.0,
) -> np.ndarray:
    """High-fidelity 48kHz vocal isolation with smooth spectral masking to prevent watery artifacts."""
    sig = highpass_rumble(audio_48k, sr=STUDIO_SR)
    noise = highpass_rumble(noise_clip_48k, sr=STUDIO_SR)

    # Single-pass smoothed spectral gating at 48kHz (preserves vocal formants & sibilance)
    denoised = nr.reduce_noise(
        y=sig,
        sr=STUDIO_SR,
        y_noise=noise,
        stationary=True,
        prop_decrease=prop_decrease,
        freq_mask_smooth_hz=500,
        time_mask_smooth_ms=60,
        n_fft=2048,
        win_length=2048,
        hop_length=512,
    )

    expanded = soft_expander_gate(denoised, sr=STUDIO_SR, threshold_db=gate_db)
    mastered = studio_vocal_eq_and_exciter(expanded, sr=STUDIO_SR)
    return mastered


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Clean and master a voice reference clip to 24kHz and 48kHz WAV.")
    parser.add_argument("--input", required=True, type=Path, help="Input raw audio file")
    parser.add_argument("--output-24k", required=True, type=Path, help="Output 24kHz reference WAV")
    parser.add_argument("--output-48k", type=Path, default=None, help="Optional output 48kHz studio WAV")
    parser.add_argument("--noise-start", type=float, default=0.0, help="Noise profile start (sec)")
    parser.add_argument("--noise-end", type=float, default=0.8, help="Noise profile end (sec)")
    parser.add_argument("--seg-start", type=float, default=1.0, help="Speech segment start (sec)")
    parser.add_argument("--seg-end", type=float, default=10.0, help="Speech segment end (sec)")
    args = parser.parse_args()

    audio_48k, sr = load_mono(args.input, target_sr=STUDIO_SR)
    noise_clip = audio_48k[int(args.noise_start * sr) : int(args.noise_end * sr)]
    seg_clip = audio_48k[int(args.seg_start * sr) : int(args.seg_end * sr)]
    cleaned = clean_broadcast_segment(seg_clip, noise_clip)
    out_24k, out_48k = finalize_reference_clip(cleaned)
    sf.write(str(args.output_24k), out_24k, F5_SR, subtype="PCM_16")
    if args.output_48k:
        sf.write(str(args.output_48k), out_48k, STUDIO_SR, subtype="PCM_16")


if __name__ == "__main__":
    main()
