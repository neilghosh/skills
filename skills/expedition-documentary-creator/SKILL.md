---
name: expedition-documentary-creator
description: >-
  Creates broadcast-grade 4K Ultra HD expedition documentaries (NatGeo / BBC / Vox style) for public
  YouTube uploads from raw action-cam, dashcam, and mobile videos/photos using multilingual neural
  and F5-TTS MLX voices. Enforces zero-human-face shot selection, human-voice suppression with real
  ambient preservation, zero-silence melodic score auto-swell, adaptive per-clip luminance grading,
  bonnet/dashboard cropping with post-crop stabilization, embedded transparent place/road/fact HUDs,
  unidirectional satellite route maps, and high-CTR Vox-style 3D relief thumbnails.
---

# Expedition Documentary Creator

Transforms raw action-cam, dashcam, and mobile footage/photos (plus optional Google Maps `Timeline.json`) into broadcast-quality **4K Ultra HD (`3840×2160`, `25 fps`)** multi-language expedition documentaries ready for YouTube Multi-Language Audio (MLA) upload and DaVinci Resolve (`.drp` / `.drt` / `.otio`).

---

## 1. Multi-Language Voices & Bundled Scripts

| Track Language | Engine | Voice ID / Asset | Style |
| :--- | :--- | :--- | :--- |
| **English (UK)** | Edge-TTS | `en-GB-RyanNeural` (`rate="-8%"`) | BBC / NatGeo British documentary narrator |
| **English (US)** | Edge-TTS | `en-US-AndrewMultilingualNeural` | Discovery / American expedition narrator |
| **Custom Cloned / Fine-Tuned** | F5-TTS MLX | `F5TTS.from_pretrained("<ckpt_dir>")` | Personal or studio fine-tuned MLX voice |
| **Hindi (`हिन्दी`)** | Edge-TTS / IndicF5 | `hi-IN-MadhurNeural` / IndicF5-MLX | Native Devanagari broadcast narrator |
| **Bangla (`বাংলা`)** | Edge-TTS | `bn-IN-BashkarNeural` | Native Bengali documentary narrator |
| **Odia (`ଓଡ଼ିଆ`)** | IndicF5-MLX / Edge-TTS | `voices/odia_native_clean.wav` / `or-IN-SubhasiniNeural` | Native Odia script narrator |

### Bundled Scripts (`scripts/`)
- `auto_discover_shots.py` — Automated shot discovery (Sobel sharpness, saturation, YCbCr skin rejection) + single montage preview.
- `vision_face_scanner` / `smart_human_cutter_blur.py` — macOS `Vision` face/body detector + clean sub-window trimmer & localized Gaussian face blur (`crop + gblur + overlay`).
- `voice_suppressor.py` — Strips passenger chatter (`280–3400 Hz` band-stop / spectral gating) while preserving real road, water, wind, and bird ambience.
- `map_telemetry_hud.py` — Renders 4K satellite route maps and transparent Place / Road / Landmark HUD overlays.
- `f5_batch_synth.py` — Warm single-session F5-TTS / IndicF5 MLX batch synthesizer with `48 kHz` studio EQ upscaling.
- `build_vox_style_thumbnail.py` — High-CTR Vox-style 3D satellite relief map + hero frame thumbnail generator.
- `verify_audio_tracks.py` — Pre-mux stream and duration validator.

---

## 2. Timeline Curation & Visual Standards

### Rule 2A — Equal-Treatment Multi-Source Pool (Action-Cam + Mobile Videos & Photos)
1. **Chronological Merge:** Combine all action-cam clips, mobile videos (`16:9` and `3:4`), Live Photos, and still photographs into a single chronological pool sorted by capture timestamp and correlated with GPS / `Timeline.json` waypoints.
2. **Quality & Luminance Filtering:**
   - Reject clips with Sobel sharpness `< 35` or mean saturation `< 18`.
   - **Lower-Half Terrain Luminance (`Y_low55 >= 65`):** Measure mean luma of the lower 55 % terrain/road region after cropping. When a clip passes through dark canopy/cliff shadow, scan at `2.5 s` intervals to select the brightest open-view sub-window (`max(Y_low55)`).
   - **Zero Unblurred Faces:** Trim out frames containing human faces/bodies (`find_longest_clean_window >= 5.0 s`) or apply localized time-gated Gaussian blur (`crop + gblur=sigma=28 + overlay`).
3. **Dynamic Still Photo & Vertical Video Framing:**
   - **Still Photos / Live Photos (`photo_kb`):** Extract a clean `16:9` crop around the subject horizon and animate with a smooth `25 fps` 4K Ken Burns push-in (`zoompan=z='1.0+0.12*(on/N)':s=3840x2160:fps=25`).
   - **Vertical `3:4` Videos (`vpan_34` / `vista_34`):** Use a `3840×2160` (`16:9`) window with smooth vertical camera tilt across the `3:4` frame (`y='ih*y0+(ih*(y1-y0))*(t/dur)'`) or crop out top mirrors and bottom dashboards (`crop=iw*0.76:iw*0.76*9/16:iw*0.14:ih*0.30`).

### Rule 2B — Strictly Unidirectional Route Maps & Embedded Place/Road/Fact Overlays
1. **Unidirectional Stage Maps:** Map interstitials (`4.0 s`) must trace **only** the forward progression covered by the upcoming chapters—never plot an entire day's back-and-forth timeline loop.
2. **Transparent Embedded HUD Overlays:** Every clip displays a sleek semi-transparent lower-left card (`rgba(14, 20, 30, 178)`) with **Place Name**, **Road / Highway Name**, and **Historical / Geological / Monument Fact**.

---

## 3. Adaptive Exposure Grading, Cropping & Stabilization

### Rule 3A — Adaptive Per-Clip Luminance Grading
Always measure post-crop `Y_all` (full-frame luma) and `Y_low55` (lower 55 % terrain luma) after `format=yuv420p` before selecting the grade:
1. **Backlit / Overcast / Dark Terrain (`Y_low55 < 108` or `Y_all < 112`) — `bright_lift`:**
   - Never apply static windshield `dehaze` (`rimin > 0`, `gamma < 1.0`) to backlit/shaded clips, as it crushes shadows. Lift shadows and midtones:
   ```text
   format=yuv420p,curves=m='0/0 0.18/0.35 0.45/0.62 0.78/0.84 1/0.96',eq=contrast=1.10:brightness=0.035:saturation=1.30:gamma=1.20,unsharp=5:5:0.65:5:5:0.0
   ```
2. **Sun-Bleached / Glare Clips (`Y_all > 165` or `Y_low55 > 160`) — `highlight_tame`:**
   ```text
   format=yuv420p,colorlevels=rimin=0.03:gimin=0.03:bimin=0.03,curves=m='0/0 0.45/0.41 0.80/0.70 1/0.90',eq=contrast=1.08:saturation=1.20:gamma=0.90,unsharp=5:5:0.65:5:5:0.0
   ```
3. **Balanced Daylight Clips (`108 <= Y_low55 <= 160`) — `dehaze` / `vivid`:**
   ```text
   format=yuv420p,colorlevels=rimin=0.025:gimin=0.025:bimin=0.025:rimax=0.985:gimax=0.985:bimax=0.985,eq=contrast=1.10:saturation=1.18:gamma=1.02,unsharp=5:5:0.65:5:5:0.0
   ```

### Rule 3B — Terrain-Centered Bonnet Cropping & Mandatory `deshake` Stabilization
1. **Terrain-Centered Bonnet Crop (`y = ih*0.10`):**
   - Crop out the car hood/bonnet and A-pillars using `crop=iw*0.76:ih*0.74:iw*0.12:ih*0.10` (starting at `ih*0.10` instead of `ih*0.03` cuts redundant overcast sky while stopping above the bonnet at `ih*0.84`).
2. **Post-Crop Stabilization (`deshake`):**
   - Because a `1.32×` crop magnifies road vibration and suspension bounce, chain `deshake` (`rx` must be a multiple of `16`, e.g., `rx=32:ry=32`) with `edge=clamp` and a `2.5 %` border trim before upscaling to 4K:
   ```text
   scale=1920:1080:flags=lanczos,fps=25,format=yuv420p,deshake=x=-1:y=-1:w=-1:h=-1:rx=32:ry=32:edge=clamp,crop=iw*0.95:ih*0.95:iw*0.025:ih*0.025,scale=3840:2160:flags=lanczos
   ```

### Rule 3C — 10-Bit HDR (`yuv420p10le`) & Single-Frame PNG Overlay Rules
1. **Place `format=yuv420p` Before `colorlevels`:** 10-bit HLG/HDR mobile clips (`yuv420p10le`) store `0..1023` in 16-bit containers (`0..65535`). Running `colorlevels=rimin=0.02` before `format=yuv420p` clamps the entire frame to black (`1023/65535 = 0.0156 < 0.02`).
2. **Static Alpha on Unlooped 1-Frame PNG Inputs:** Passing `-i hud.png` without `-loop 1` yields a 1-frame stream at `pts=0.0`; applying `fade=t=in:st=0.25:alpha=1` evaluates `alpha=0` forever. Keep `[1:v]format=rgba[hud]` static and fade the composite `[vout]`.

---

## 4. Zero-Silence Audio Architecture & Narration Pacing

### Rule 4A — Fact-Rich, Unhurried Narration (`110–120 WPM`)
1. **Historical & Geological Facts Over Visual Obvious:** Narration must emphasize historical dynasties, architecture, geological formations, elevation, and route geography rather than describing obvious on-screen objects.
2. **Calm Documentary Cadence (`24–28 Words` per `~17 s` Chapter):**
   - Keep each chapter script to `24–28` words (`160–185` chars, `~12–13.5 s` of speech) so it never rushes.
   - Synthesize at a relaxed pace (`speed=0.92` with `0.078 s/char` duration budget for F5-TTS MLX; `rate="-8%"` for `en-GB-RyanNeural`).
   - Preserve 100 % of natural intra-sentence breathing pauses (never strip internal pauses or apply `atempo > 1.08`).

### Rule 4B — Continuous Melodic Midrange Score & Dynamic Reverse-Ducking (Zero Silence)
1. **Midrange Melodic Score (`196 Hz – 1175 Hz`):**
   - Never rely solely on sub-200 Hz sine drones (`65–196 Hz`), which are inaudible on normal speakers. Generate a warm midrange chord progression (`Gmaj7 → Em9 → Cmaj9 → D6/9` with harmonics + gentle plucked arpeggio notes every `0.85 s` at `-21 dBFS` base RMS) paired with voice-suppressed scene ambient audio (`>= -30 dBFS` floor on maps and still photos).
2. **Dynamic Auto-Swell in Unvoiced Windows:**
   - Compute a `50 ms` voice-activity RMS envelope (`v_rms > 0.008`), dilate by `350 ms`, and smooth with a `450 ms` Hann window (`speak_env`).
   - Apply reverse-ducking gains so music and ambience sit subtly under speech and swell smoothly during the `3–5 s` scenic breathers between chapters and map transitions:
     ```python
     music_gain = 1.15 - 0.77 * speak_env  # 0.38x under speech -> 1.15x in gaps
     amb_gain   = 0.85 - 0.49 * speak_env  # 0.36x under speech -> 0.85x in gaps
     ```
   - Verify that every `100 ms` window across the master mix maintains `RMS >= -30 dBFS` (`0` silent windows) and that all audio tracks match the video duration (`-t "${vid_dur}" -shortest`).

### Rule 4C — Fine-Tuned F5-TTS MLX Checkpoints & Gradient Hygiene
1. **Loading Custom Fine-Tuned Checkpoints:** Pass the checkpoint directory (`model_v1.safetensors`, `duration_v2.safetensors`, `vocab.txt`) to `F5TTS.from_pretrained(ckpt_dir)`, quantize linear layers divisible by 64 (`nn.quantize(..., bits=8, group_size=64, class_predicate=lambda _, m: isinstance(m, nn.Linear) and m.weight.shape[1] % 64 == 0)`), and master outputs to `48 kHz` via `upscale_to_studio_48k()`.
2. **Preventing `NaN` Weights During MLX Fine-Tuning:** In `f5_tts_mlx`, `TextEmbedding` uses `ConvNeXtV2Block` with Global Response Normalization (`GRN`), whose `mx.linalg.norm(0)` on padded text tokens yields `0/0 = NaN` gradients that corrupt all model tensors during `clip_grad_norm()`. Always call `model.transformer.text_embed.freeze()` before fine-tuning DiT blocks, sanitize gradients (`mx.where(mx.isnan(g) | mx.isinf(g), mx.zeros_like(g), g)`) before `clip_grad_norm`, and export `dict(tree_flatten(model.parameters()))`.
