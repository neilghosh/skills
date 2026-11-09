import argparse
import subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from f5_tts_mlx.generate import generate
from isolate_voice import STUDIO_SR, studio_vocal_eq_and_exciter

BASE_DIR = Path(__file__).resolve().parent
_DEVTOOLS_INDIC = Path.home() / "devtools" / "voice" / "indic_f5_mlx"
INDIC_MODEL_DIR = (
    str(BASE_DIR / "indic_f5_mlx")
    if (BASE_DIR / "indic_f5_mlx" / "model_v1.safetensors").exists()
    else (str(_DEVTOOLS_INDIC) if _DEVTOOLS_INDIC.exists() else "6Morpheus6/IndicF5")
)


def has_indic_script(text: str) -> bool:
    """Return True if text contains any Indic Unicode block character (Devanagari, Bengali, Odia, etc.)."""
    return any("\u0900" <= ch <= "\u0DFF" for ch in text)


VOICE_PRESETS: dict[str, dict[str, str]] = {
    "odia": {
        "ref_audio": str(BASE_DIR / "odia_native_clean.wav"),
        "ref_text": "ସେଇ ପ୍ରାକୃତିକ ସମ୍ପଦଭରା, ବଣ ରାଇଜରେ ରାଜୁତି ଚାଲିଥିଲା, ପଶୁରାଜ ସିଂହ ଆଉ ମହାବଳ ବାଘର ।",
        "model_name": INDIC_MODEL_DIR,
    },
    "bangla": {
        "edge_voice": "bn-IN-BashkarNeural",
    },
    "hindi": {
        "edge_voice": "hi-IN-MadhurNeural",
    },
    "uk_english": {
        "edge_voice": "en-GB-RyanNeural",
    },
    "us_english": {
        "edge_voice": "en-US-AndrewMultilingualNeural",
    },
}


def upscale_to_studio_48k(wav_path: Path) -> None:
    """Upscale 24kHz F5-TTS output to 48kHz with harmonic air restoration and studio broadcast EQ."""
    audio, sr = sf.read(str(wav_path), dtype="float32")
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)

    if sr != STUDIO_SR:
        audio_48k = resample_poly(audio, STUDIO_SR // sr, 1).astype(np.float32)
    else:
        audio_48k = audio

    enhanced = studio_vocal_eq_and_exciter(audio_48k, sr=STUDIO_SR)
    peak = np.max(np.abs(enhanced))
    if peak > 1e-6:
        enhanced = enhanced * (0.89 / peak)

    sf.write(str(wav_path), enhanced, STUDIO_SR, subtype="PCM_16")


def extract_youtube_segment(
    url: str,
    start: str = "00:00:13",
    end: str = "00:00:26",
    output_wav: Path = BASE_DIR / "ref_voice.wav",
) -> Path:
    """Download and extract an audio segment from YouTube as 24kHz mono 16-bit PCM WAV."""
    stem = str(output_wav.with_suffix(""))
    cmd = [
        "yt-dlp",
        "-f",
        "bestaudio",
        "--download-sections",
        f"*{start}-{end}",
        "--force-keyframes-at-cuts",
        "-x",
        "--audio-format",
        "wav",
        "--postprocessor-args",
        "ffmpeg:-ac 1 -ar 24000 -sample_fmt s16",
        "-o",
        f"{stem}.%(ext)s",
        url,
    ]
    subprocess.run(cmd, check=True)
    return output_wav


def clone_and_speak(
    generation_text: str,
    ref_audio_path: str | None = None,
    ref_audio_text: str | None = None,
    output_path: str = "output.wav",
    speed: float = 1.0,
    steps: int = 8,
    quantization_bits: int | None = None,
    studio_upscale: bool = True,
    model_name: str | None = None,
) -> None:
    """Generate speech from text, cloning the reference voice, and master to 48kHz studio audio."""
    selected_model = model_name or (INDIC_MODEL_DIR if has_indic_script(generation_text) else "lucasnewman/f5-tts-mlx")
    kwargs: dict = {
        "generation_text": generation_text,
        "output_path": output_path,
        "speed": speed,
        "steps": steps,
        "quantization_bits": quantization_bits,
        "estimate_duration": True,
        "model_name": selected_model,
    }
    if ref_audio_path:
        kwargs["ref_audio_path"] = ref_audio_path
    if ref_audio_text:
        kwargs["ref_audio_text"] = ref_audio_text

    generate(**kwargs)
    if studio_upscale:
        upscale_to_studio_48k(Path(output_path))
    print(f"Saved 48kHz studio-mastered audio to: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clone a voice and generate audio from text or a script file using F5-TTS MLX / IndicF5."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-t", "--text", help="Direct text to synthesize")
    group.add_argument("-f", "--script-file", type=Path, help="Path to a text file containing the script")

    parser.add_argument(
        "-v",
        "--voice",
        choices=list(VOICE_PRESETS.keys()),
        default="odia",
        help="Public YouTube-safe preset voice: 'odia', 'bangla', 'hindi', 'uk_english', or 'us_english'",
    )
    parser.add_argument("-r", "--ref-audio", help="Custom path to reference WAV audio (overrides --voice preset)")
    parser.add_argument("--ref-text", help="Transcript of the reference audio (overrides --voice preset)")
    parser.add_argument("--indic", action="store_true", help="Force using AI4Bharat IndicF5 model (Hindi, Bangla, Odia, etc.)")
    parser.add_argument("--youtube-url", help="Optional YouTube URL to extract a new reference audio clip")
    parser.add_argument("--start", default="00:00:13", help="Start timestamp for YouTube clip (default: 00:00:13)")
    parser.add_argument("--end", default="00:00:26", help="End timestamp for YouTube clip (default: 00:00:26)")
    parser.add_argument("-o", "--output", default="output.wav", help="Output WAV file path (default: output.wav)")
    parser.add_argument("--speed", type=float, default=1.0, help="Speech speed multiplier (default: 1.0)")
    parser.add_argument("--steps", type=int, default=8, help="RK4 ODE steps (default: 8 = 32 NFEs)")
    parser.add_argument(
        "-q",
        "--quantization-bits",
        type=int,
        choices=[4, 8],
        help="Optional 4-bit or 8-bit model quantization for faster inference",
    )
    parser.add_argument("--no-upscale", action="store_true", help="Disable 48kHz studio upscaling and harmonic EQ")

    args = parser.parse_args()

    preset = VOICE_PRESETS[args.voice]
    text = args.script_file.read_text(encoding="utf-8").strip() if args.script_file else args.text

    if "edge_voice" in preset and not args.ref_audio and not args.indic:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_mp3 = Path(tmp.name)
        edge_bin = str(BASE_DIR / ".venv" / "bin" / "edge-tts")
        subprocess.run(
            [edge_bin, "--voice", preset["edge_voice"], "--text", text, "--write-media", str(tmp_mp3)],
            check=True,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(tmp_mp3), "-ac", "1", "-ar", str(STUDIO_SR), str(args.output)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        tmp_mp3.unlink(missing_ok=True)
        if not args.no_upscale:
            upscale_to_studio_48k(Path(args.output))
        print(f"Saved 48kHz studio-mastered audio to: {args.output}")
        return

    ref_audio = args.ref_audio or preset.get("ref_audio")
    ref_text = args.ref_text if args.ref_audio and not args.ref_text else (args.ref_text or preset.get("ref_text"))
    model_name = INDIC_MODEL_DIR if args.indic else preset.get("model_name")

    if args.youtube_url:
        extract_youtube_segment(
            url=args.youtube_url,
            start=args.start,
            end=args.end,
            output_wav=Path(ref_audio),
        )

    clone_and_speak(
        generation_text=text,
        ref_audio_path=ref_audio,
        ref_audio_text=ref_text,
        output_path=args.output,
        speed=args.speed,
        steps=args.steps,
        quantization_bits=args.quantization_bits,
        studio_upscale=not args.no_upscale,
        model_name=model_name,
    )


if __name__ == "__main__":
    main()
