#!/Users/neilghosh/devtools/voice/.venv/bin/python
"""
Batch & Single Voice Cloning Bridge for /Users/neilghosh/devtools/voice
-----------------------------------------------------------------------
Uses the F5-TTS MLX environment and pre-cleaned reference voices in /Users/neilghosh/devtools/voice:
  - neil      -> /Users/neilghosh/devtools/voice/neil_clean.wav
  - tony      -> /Users/neilghosh/devtools/voice/tony_greig_clean.wav (aliases: toney greg, tony greig, tonygreig)
  - tony_alt  -> /Users/neilghosh/devtools/voice/tony_greig_clean_alt.wav
  - atherton  -> /Users/neilghosh/devtools/voice/atherton_clean.wav (aliases: arthoron, arthoton, mike atherton, bumble)

Loads F5TTS.from_pretrained ONCE for an entire documentary script batch and masters each output
to 48kHz using upscale_to_studio_48k() from /Users/neilghosh/devtools/voice/main.py.
"""

import argparse
import json
import sys
from pathlib import Path

_BUNDLED_VOICE_DIR = Path(__file__).resolve().parent.parent / "voices"
VOICE_DIR = _BUNDLED_VOICE_DIR if _BUNDLED_VOICE_DIR.exists() else Path("/Users/neilghosh/devtools/voice")
sys.path.insert(0, str(VOICE_DIR))

import math
import mlx.core as mx
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from f5_tts_mlx.cfm import F5TTS
from f5_tts_mlx.generate import FRAMES_PER_SEC, SAMPLE_RATE, TARGET_RMS, estimated_duration, split_sentences
from f5_tts_mlx.utils import convert_char_to_pinyin


from main import VOICE_PRESETS, upscale_to_studio_48k

VOICE_ALIASES: dict[str, str] = {
    "odia": "odia",
    "oriya": "odia",
    "or_in": "odia",
}


def resolve_voice_preset(name: str) -> str | None:
    norm = name.strip().lower().replace("-", "_").replace(" ", "_")
    if norm in VOICE_ALIASES:
        return VOICE_ALIASES[norm]
    if norm in VOICE_PRESETS:
        return norm
    return None


def _load_ref_audio_24k(ref_audio_path: str) -> mx.array:
    p48 = Path(ref_audio_path).with_name(Path(ref_audio_path).stem + "_48k.wav")
    actual_path = str(p48) if p48.exists() else ref_audio_path
    audio_np, sr = sf.read(actual_path, dtype="float32")
    if audio_np.ndim > 1:
        audio_np = np.mean(audio_np, axis=1)
    if sr != SAMPLE_RATE:
        g = math.gcd(SAMPLE_RATE, sr)
        audio_np = resample_poly(audio_np, SAMPLE_RATE // g, sr // g).astype(np.float32)
    audio = mx.array(audio_np)
    rms = mx.sqrt(mx.mean(mx.square(audio)))
    if rms < TARGET_RMS:
        audio = audio * TARGET_RMS / rms
    return audio


def synthesize_batch(
    items: list[dict[str, str]],
    voice_name: str = "neil",
    ref_audio_override: str | None = None,
    ref_text_override: str | None = None,
    steps: int = 16,
    speed: float = 1.0,
    quantization_bits: int | None = 8,
    overwrite: bool = False,
) -> None:
    default_preset_key = resolve_voice_preset(voice_name)
    if default_preset_key is None and not ref_audio_override:
        raise ValueError(f"Unknown voice '{voice_name}'. Valid presets: {list(VOICE_ALIASES.keys())}")

    pending = [it for it in items if overwrite or not Path(it["output"]).exists()]
    if not pending:
        print(f"[F5-TTS Cache] All {len(items)} segments already cached.")
        return

    print(
        f"[F5-TTS Batch] Loading F5-TTS MLX models (steps={steps}, q={quantization_bits}) "
        f"for {len(pending)}/{len(items)} segments...",
        flush=True,
    )
    model_cache: dict[str, F5TTS] = {}
    ref_cache: dict[str, tuple[mx.array, str]] = {}

    for idx, item in enumerate(pending):
        item_voice = item.get("voice") or default_preset_key or "neil"
        preset_key = resolve_voice_preset(item_voice) or "neil"
        preset = VOICE_PRESETS.get(preset_key, VOICE_PRESETS["neil"])
        model_name = preset.get("model_name", "lucasnewman/f5-tts-mlx")
        if model_name not in model_cache:
            model_cache.clear()
            q_for_model = quantization_bits if model_name == "lucasnewman/f5-tts-mlx" else None
            model_cache[model_name] = F5TTS.from_pretrained(model_name, quantization_bits=q_for_model)
        f5tts = model_cache[model_name]
        r_audio = item.get("ref_audio") or ref_audio_override or preset["ref_audio"]
        r_text = item.get("ref_text") or ref_text_override or preset["ref_text"]
        cache_key = f"{r_audio}::{r_text}"
        if cache_key not in ref_cache:
            ref_cache[cache_key] = (_load_ref_audio_24k(r_audio), r_text)
        audio, ref_audio_text = ref_cache[cache_key]

        gen_text = item["text"].strip()
        out_path = Path(item["output"])
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Synthesize <= 280 chars (~10s documentary line) in a single continuous pass for 2x speed & natural flow
        sentences = [gen_text] if len(gen_text) <= 280 else (split_sentences(gen_text) or [gen_text])
        waves = []
        for sent in sentences:
            step_duration = int(estimated_duration(audio, ref_audio_text, sent, speed) * FRAMES_PER_SEC)
            pinyin_text = convert_char_to_pinyin([ref_audio_text.strip() + " " + sent])
            wave, _ = f5tts.sample(
                mx.expand_dims(audio, axis=0),
                text=pinyin_text,
                duration=step_duration,
                steps=steps,
                method="midpoint",
                speed=speed,
                cfg_strength=2.0,
                sway_sampling_coef=-1.0,
            )
            trim_idx = min(audio.shape[0] + int(0.15 * SAMPLE_RATE), wave.shape[0])
            wave = wave[trim_idx:]
            mx.eval(wave)
            waves.append(np.array(wave))

        full_wave = np.concatenate(waves, axis=0) if len(waves) > 1 else waves[0]
        sf.write(str(out_path), full_wave, SAMPLE_RATE)
        upscale_to_studio_48k(out_path)
        print(f"  [{idx+1}/{len(pending)}] Mastered 48kHz -> {out_path.name} ({len(full_wave)/SAMPLE_RATE:.2f}s)", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch F5-TTS MLX Synthesizer using /Users/neilghosh/devtools/voice")
    parser.add_argument("--batch-json", required=True, type=Path, help="JSON file with [{'text': '...', 'output': '...'}]")
    parser.add_argument("--voice", default="neil", help="Preset name (neil, atherton/arthoron, tony/toney greg, tony_alt, bumble)")
    parser.add_argument("--ref-audio", default=None, help="Optional custom 24kHz mono WAV reference")
    parser.add_argument("--ref-text", default=None, help="Optional transcript for custom reference")
    parser.add_argument("--steps", type=int, default=16, help="ODE steps (16=fast batch mode, 32=max quality)")
    parser.add_argument("--speed", type=float, default=1.0, help="Speech speed multiplier")
    parser.add_argument("-q", "--quantization-bits", type=int, default=8, choices=[0, 4, 8], help="Quantization bits (0 for fp16)")
    parser.add_argument("--overwrite", action="store_true", help="Ignore cached WAV files")
    args = parser.parse_args()

    q_bits = None if args.quantization_bits == 0 else args.quantization_bits
    items = json.loads(args.batch_json.read_text(encoding="utf-8"))
    synthesize_batch(
        items=items,
        voice_name=args.voice,
        ref_audio_override=args.ref_audio,
        ref_text_override=args.ref_text,
        steps=args.steps,
        speed=args.speed,
        quantization_bits=q_bits,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()
