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
    base = Path(__file__).parent

    # 1. Process Tony Greig video (nNHZFmOzMt0) at full 48kHz
    raw_tg = base / "tony_greig_raw.wav"
    if raw_tg.exists():
        tg_48k, sr = load_mono(raw_tg, target_sr=STUDIO_SR)
        noise_clip = np.concatenate([
            tg_48k[int(2.55 * sr) : int(3.15 * sr)],
            tg_48k[int(10.25 * sr) : int(11.85 * sr)],
        ])

        p1 = clean_broadcast_segment(tg_48k[int(0.65 * sr) : int(2.50 * sr)], noise_clip, prop_decrease=0.80)
        p2 = clean_broadcast_segment(tg_48k[int(3.20 * sr) : int(10.05 * sr)], noise_clip, prop_decrease=0.80)
        pause = np.zeros(int(0.18 * sr), dtype=np.float32)
        tg_main_24k, tg_main_48k = finalize_reference_clip(np.concatenate([p1, pause, p2]))

        sf.write(str(base / "tony_greig_clean.wav"), tg_main_24k, F5_SR, subtype="PCM_16")
        sf.write(str(base / "tony_greig_clean_48k.wav"), tg_main_48k, STUDIO_SR, subtype="PCM_16")
        print(f"Saved tony_greig_clean.wav (24kHz) & tony_greig_clean_48k.wav (48kHz, {len(tg_main_48k)/STUDIO_SR:.2f}s)")

        p3 = clean_broadcast_segment(tg_48k[int(11.90 * sr) : int(15.70 * sr)], noise_clip, prop_decrease=0.80)
        p4 = clean_broadcast_segment(tg_48k[int(75.55 * sr) : int(80.35 * sr)], noise_clip, prop_decrease=0.80)
        tg_alt_24k, tg_alt_48k = finalize_reference_clip(np.concatenate([p3, pause, p4]))

        sf.write(str(base / "tony_greig_clean_alt.wav"), tg_alt_24k, F5_SR, subtype="PCM_16")
        print(f"Saved tony_greig_clean_alt.wav ({len(tg_alt_24k)/F5_SR:.2f}s)")

    # 2. Process 13s-26s clip from z4IX4e1ZUHQ (ref_voice.wav)
    ref_wav = base / "ref_voice.wav"
    if ref_wav.exists():
        ref_48k, sr = load_mono(ref_wav, target_sr=STUDIO_SR)
        ref_noise = ref_48k[int(6.3 * sr) : int(7.3 * sr)]
        s1 = clean_broadcast_segment(ref_48k[int(0.3 * sr) : int(6.3 * sr)], ref_noise, prop_decrease=0.75)
        s2 = clean_broadcast_segment(ref_48k[int(7.3 * sr) : int(12.5 * sr)], ref_noise, prop_decrease=0.75)
        ref_24k, ref_48k_out = finalize_reference_clip(
            np.concatenate([s1, np.zeros(int(0.20 * sr), dtype=np.float32), s2])
        )
        sf.write(str(base / "atherton_clean.wav"), ref_24k, F5_SR, subtype="PCM_16")
        sf.write(str(base / "ref_voice_clean_48k.wav"), ref_48k_out, STUDIO_SR, subtype="PCM_16")
        print(f"Saved atherton_clean.wav (24kHz) & ref_voice_clean_48k.wav (48kHz, {len(ref_48k_out)/STUDIO_SR:.2f}s)")

    # 3. Process Neil.m4a directly from original 48kHz recording with ultra-light room denoising
    neil_m4a = base / "Neil.m4a"
    neil_source = base / "neil_raw.wav"
    if neil_m4a.exists() or neil_source.exists():
        # Decode Neil.m4a at native 48kHz float
        import subprocess
        neil_48k_path = base / "neil_48k_raw.wav"
        if neil_m4a.exists():
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(neil_m4a), "-ac", "1", "-ar", "48000", str(neil_48k_path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            neil_48k, sr = load_mono(neil_48k_path, target_sr=STUDIO_SR)
        else:
            neil_48k, sr = load_mono(neil_source, target_sr=STUDIO_SR)

        neil_noise = np.concatenate([
            neil_48k[int(8.4 * sr) : int(9.3 * sr)],
            neil_48k[int(39.6 * sr) : int(40.3 * sr)],
        ])
        neil_seg = neil_48k[int(40.35 * sr) : int(46.50 * sr)]
        # Ultra-gentle room floor reduction (prop_decrease=0.45) to preserve 100% of Neil's natural timbre
        neil_cleaned = clean_broadcast_segment(neil_seg, neil_noise, prop_decrease=0.45, gate_db=-42.0)
        neil_24k, neil_48k_out = finalize_reference_clip(neil_cleaned)

        sf.write(str(base / "neil_clean.wav"), neil_24k, F5_SR, subtype="PCM_16")
        sf.write(str(base / "neil_clean_48k.wav"), neil_48k_out, STUDIO_SR, subtype="PCM_16")
        if neil_48k_path.exists():
            neil_48k_path.unlink()
        print(f"Saved neil_clean.wav (24kHz) & neil_clean_48k.wav (48kHz, {len(neil_48k_out)/STUDIO_SR:.2f}s)")

    # 4. Process Michael Holding (B7yDz-HQDww)
    holding_wav = base / "holding_raw.wav"
    if holding_wav.exists():
        h_48k, sr = load_mono(holding_wav, target_sr=STUDIO_SR)
        h_noise = h_48k[int(51.40 * sr) : int(52.15 * sr)]
        h_seg = h_48k[int(54.45 * sr) : int(60.60 * sr)]
        h_cleaned = clean_broadcast_segment(h_seg, h_noise, prop_decrease=0.55, gate_db=-40.0)
        h_24k, h_48k_out = finalize_reference_clip(h_cleaned)
        sf.write(str(base / "holding_clean.wav"), h_24k, F5_SR, subtype="PCM_16")
        sf.write(str(base / "holding_clean_48k.wav"), h_48k_out, STUDIO_SR, subtype="PCM_16")
        print(f"Saved holding_clean.wav (24kHz) & holding_clean_48k.wav (48kHz, {len(h_48k_out)/STUDIO_SR:.2f}s)")

    # 5. Process Sir David Attenborough (mBgek078dxQ)
    atten_wav = base / "attenborough_raw.wav"
    if atten_wav.exists():
        a_48k, sr = load_mono(atten_wav, target_sr=STUDIO_SR)
        a_noise = np.concatenate([
            a_48k[int(8.45 * sr) : int(8.90 * sr)],
            a_48k[int(18.25 * sr) : int(18.70 * sr)],
        ])
        a_seg = a_48k[int(0.10 * sr) : int(8.40 * sr)]
        a_cleaned = clean_broadcast_segment(a_seg, a_noise, prop_decrease=0.72, gate_db=-38.0)
        a_24k, a_48k_out = finalize_reference_clip(a_cleaned)
        sf.write(str(base / "attenborough_clean.wav"), a_24k, F5_SR, subtype="PCM_16")
        sf.write(str(base / "attenborough_clean_48k.wav"), a_48k_out, STUDIO_SR, subtype="PCM_16")
        print(f"Saved attenborough_clean.wav (24kHz) & attenborough_clean_48k.wav (48kHz, {len(a_48k_out)/STUDIO_SR:.2f}s)")

    # 6. Process Bear Grylls Hindi (7VvvAEnFbQ8?t=948)
    bear_wav = base / "bear_hindi_raw.wav"
    if bear_wav.exists():
        b_48k, sr = load_mono(bear_wav, target_sr=STUDIO_SR)
        b_noise = b_48k[int(44.0 * sr) : int(46.0 * sr)]
        b_seg = b_48k[int(46.6 * sr) : int(56.6 * sr)]
        b_cleaned = clean_broadcast_segment(b_seg, b_noise, prop_decrease=0.78, gate_db=-38.0)
        b_24k, b_48k_out = finalize_reference_clip(b_cleaned)
        sf.write(str(base / "bear_hindi_clean.wav"), b_24k, F5_SR, subtype="PCM_16")
        sf.write(str(base / "bear_hindi_clean_48k.wav"), b_48k_out, STUDIO_SR, subtype="PCM_16")
        print(f"Saved bear_hindi_clean.wav (24kHz) & bear_hindi_clean_48k.wav (48kHz, {len(b_48k_out)/STUDIO_SR:.2f}s)")


if __name__ == "__main__":
    main()
