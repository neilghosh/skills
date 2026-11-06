---
name: expedition-documentary-creator
description: >-
  Creates broadcast-grade 4K Ultra HD expedition documentaries (NatGeo / BBC / Vox style) for public
  YouTube uploads from a folder of raw GoPro or action-cam videos using commercial-safe multilingual
  neural voices (UK English en-GB-RyanNeural, US English en-US-AndrewMultilingualNeural, Hindi
  hi-IN-MadhurNeural, Bangla bn-IN-BashkarNeural, and Odia IndicF5-MLX).
  Enforces zero-human-face shot selection, GoPro human-voice suppression with real surrounding ambient
  (car, water, wind, birds) preservation, subtle -30 dBFS background score, clean 44pt-54pt 4K Geographic
  Cards on chapter leads, and high-CTR Vox-style 3D relief map thumbnails.
---

# Expedition Documentary Creator

Transforms a folder of raw GoPro / travel footage into broadcast-quality **4K Ultra HD (`3840×2160`)** expedition documentaries (`25 fps`, H.264 + `48 kHz` studio-mastered stereo AAC) ready for public YouTube Multi-Language Audio (MLA) upload.

> [!NOTE]
> **Personal & Commentary Voice Overdubbing (`neil`, `nasser`, `atherton`, `shastri`, `tony`, `holding`, `attenborough`):**
> Personal and celebrity commentary voices are intentionally excluded from this public YouTube skill and reside in the separate [`youtube-custom-voice-player`](../youtube-custom-voice-player/SKILL.md) skill, which pairs an already-uploaded YouTube video with a custom HTML5 player that suppresses the YouTube vocal track and streams personal/commentary voices in sync.

---

## 1. Public YouTube Multi-Language Voices & Scripts (`voices/` & `scripts/`)

All production builders in [`scripts/`](./scripts) (`build_4k_clean_hud_master.py`, `build_5languages_scratch_doc.py`, `build_vox_style_thumbnail.py`, `create_cinematic_music_bed.py`, `map_telemetry_hud.py`, `voice_suppressor.py`, `f5_batch_synth.py`, `auto_discover_shots.py`, `smart_human_cutter_blur.py`, `vision_face_scanner.swift`, `verify_audio_tracks.py`) and public multilingual TTS assets in [`voices/`](./voices) (`odia_native_clean.wav` + `indic_f5_mlx/vocab.txt`) are bundled directly inside this skill.

| Track Language | Engine | Voice ID / Bundled Asset | Description |
| :--- | :--- | :--- | :--- |
| **English (UK)** | Edge-TTS v7.3.1 | `en-GB-RyanNeural` | BBC Earth / British expedition narrator |
| **English (US)** | Edge-TTS v7.3.1 | `en-US-AndrewMultilingualNeural` | Discovery / NatGeo warm American narrator |
| **Hindi (`हिन्दी`)** | Edge-TTS v7.3.1 | `hi-IN-MadhurNeural` | Native Devanagari broadcast narrator |
| **Bangla (`বাংলা`)** | Edge-TTS v7.3.1 | `bn-IN-BashkarNeural` | Native Bengali documentary narrator |
| **Odia (`ଓଡ଼ିଆ`)** | IndicF5-MLX | `voices/odia_native_clean.wav` | AI4Bharat open-source Odia studio narrator |

---

## 1b. Indian Language Audio Tracks

The `indic_f5_mlx` model (AI4Bharat IndicF5-MLX, at `/Users/neilghosh/devtools/voice/indic_f5_mlx/`) supports synthesis in **Hindi, Sanskrit, Odia, and Bangla** using Unicode Devanagari / Odia / Bengali scripts. For Edge-TTS fallback, use the voice names below.

### Supported Indian Languages & Edge-TTS Voices

| Language | Script | Edge-TTS Voice | IndicF5 Model Support | `--voice` preset |
|----------|--------|---------------|----------------------|-----------------|
| **Hindi** | Devanagari (`हिन्दी`) | `hi-IN-MadhurNeural` (male) / `hi-IN-SwaraNeural` (female) | ✅ Yes | `hindi` |
| **Sanskrit** | Devanagari (`संस्कृत`) | `hi-IN-MadhurNeural` (closest; Sanskrit uses Devanagari script) | ✅ Yes | `sanskrit` |
| **Bangla** | Bengali (`বাংলা`) | `bn-IN-BashkarNeural` (male) / `bn-IN-TanishaaNeural` (female) | ✅ Yes | `bangla` |
| **Odia** | Odia (`ଓଡ଼ିଆ`) | `or-IN-SubhasiniNeural` (female) / `or-IN-SukantNeural` (male) | ✅ Yes | `odia` |
| **Indian English** | Latin | `en-IN-NeerjaNeural` (female) / `en-IN-PrabhatNeural` (male) | N/A (use Edge-TTS) | `en-IN-NeerjaNeural` |

### How to Generate Indian Language Audio

**Method 1 – Edge-TTS (simplest, best quality for production):**
```bash
cd /Users/neilghosh/devtools/voice

# Hindi
.venv/bin/edge-tts --voice hi-IN-MadhurNeural --rate=-6% \
  --text "पुराना दीपस्तम्भ तूफान के सामने चुपचाप खड़ा था" \
  --write-media hindi_out.mp3
ffmpeg -i hindi_out.mp3 -ar 48000 -ac 2 hindi_out.wav

# Sanskrit
.venv/bin/edge-tts --voice hi-IN-MadhurNeural --rate=-8% \
  --text "पुरातनः दीपस्तम्भः प्रबलझञ्झावातस्य सम्मुखे निश्चलः अतिष्ठत्" \
  --write-media sanskrit_out.mp3
ffmpeg -i sanskrit_out.mp3 -ar 48000 -ac 2 sanskrit_out.wav

# Bangla
.venv/bin/edge-tts --voice bn-IN-BashkarNeural --rate=-5% \
  --text "পুরানো বাতিঘরটি ঝড়ের সামনে নীরবে দাঁড়িয়ে ছিল" \
  --write-media bangla_out.mp3
ffmpeg -i bangla_out.mp3 -ar 48000 -ac 2 bangla_out.wav

# Odia
.venv/bin/edge-tts --voice or-IN-SubhasiniNeural --rate=-5% \
  --text "ପୁରୁଣା ଦୀପ-ସ୍ତମ୍ଭଟି ଝଡ଼ ସାମ୍ନାରେ ନୀରବରେ ଠିଆ ହୋଇଥିଲା" \
  --write-media odia_out.mp3
ffmpeg -i odia_out.mp3 -ar 48000 -ac 2 odia_out.wav

# Indian English (Bharat / IndicF5 model, en-IN accent)
.venv/bin/edge-tts --voice en-IN-NeerjaNeural --rate=-5% \
  --text "The old lighthouse stood silent against the gathering storm" \
  --write-media indian_english_out.mp3
ffmpeg -i indian_english_out.mp3 -ar 48000 -ac 2 indian_english_out.wav
```

**Method 2 – IndicF5-MLX (AI4Bharat, cloned voice TTS in Indian scripts):**
```bash
cd /Users/neilghosh/devtools/voice

# Verify OOV (out-of-vocabulary characters) before synthesis
.venv/bin/python -c "
from pathlib import Path
vocab = set(Path('indic_f5_mlx/vocab.txt').read_text().split('\n'))
text = 'पुराना दीपस्तम्भ तूफान के सामने चुपचाप खड़ा था'
oov = [c for c in text if c not in vocab and c.strip()]
print('OOV:', oov)
"

# Synthesize Hindi using IndicF5
.venv/bin/python -c "
from indic_f5_mlx import IndicF5
model = IndicF5.from_pretrained()
model.synthesize(
    text='पुराना दीपस्तम्भ तूफान के सामने चुपचाप खड़ा था',
    ref_audio='neil_clean.wav',
    ref_text='reference transcript here',
    output_path='hindi_indicf5_out.wav'
)
"
```

> [!TIP] **When to use which method:**
> - **Edge-TTS** is faster, requires no local GPU, and has excellent accent/intonation for Hindi, Bangla, Odia. Use for all production tracks.
> - **IndicF5-MLX** is for **voice-cloned** Indian language synthesis (same speaker identity in Hindi/Sanskrit). Always check OOV list first — if the text contains characters not in `indic_f5_mlx/vocab.txt`, Edge-TTS is the fallback.
> - **Sanskrit** has no dedicated Edge-TTS voice — use `hi-IN-MadhurNeural` at `--rate=-8%` (slower rate improves classical pronunciation).

### Adding Indian Language Tracks to Multi-Audio Documentary

To add Hindi/Sanskrit/Bangla/Odia as selectable audio tracks in a single MP4 alongside English voices:

```python
# In build_9voice_single_video.py style scripts:
# Use ced.load_or_synthesize_edge_tts_texts() for Indian languages
hindi_map = ced.load_or_synthesize_edge_tts_texts(
    texts=list(hindi_chapter_dict.values()),
    voice='hi-IN-MadhurNeural',
    rate='-6%',
    cache_dir=HINDI_EDGE_DIR,
)
bangla_map = ced.load_or_synthesize_edge_tts_texts(
    texts=list(bangla_chapter_dict.values()),
    voice='bn-IN-BashkarNeural',
    rate='-5%',
    cache_dir=BANGLA_EDGE_DIR,
)
```

> [!IMPORTANT] **Indian language tracks** use `hi-IN-MadhurNeural`, `bn-IN-BashkarNeural`, `or-IN-SubhasiniNeural` via Edge-TTS routed through `ced.load_or_synthesize_edge_tts_texts()`.

---

## 1c. Real Voice-Suppressed Surrounding Audio & Silence Handling (Critical Audio Pipeline Rule)

Every video segment's raw audio MUST first pass through `suppress_voice_keep_ambient()` in `voice_suppressor.py` (which strips human speech/chatter via STFT spectral floor clamping + phase randomization in 140–4500 Hz while preserving authentic car engine, tire hum, rushing water, wind, and bird calls) and be cached as `amb_<clip_file>_*.npy`.

When loading segment ambient audio during multi-language track assembly:
1. **Resolve real per-clip cache across all work directories**: Search `os.path.dirname(seg['mp4'])/ambient_cache/amb_<clip_file>_*.npy` and `glob('/Users/neilghosh/dev/video/work/*/ambient_cache/amb_<clip_file>_*.npy')`. Never hardcode a single empty `ambient_cache` folder or wrong filename pattern, which causes 100% fallback to synthetic `breeze_clean.npy`.
2. **Preserve quiet natural clips (`1e-4 < RMS < 0.038`)**: Do **NOT** overwrite quiet stream, water, or forest recordings with `breeze_clean.npy`! Instead, gently lift quiet natural audio (`gain = min(3.0, 0.028 / rms)`) and gently tame excessive highway wind buffeting (`if rms > 0.065: arr *= 0.060 / rms`).
3. **Silent GoPro TimeWarp / Hyperlapse clips (`RMS <= 1e-4`)**: Inherit the real voice-suppressed ambient audio from the neighboring clip in the same chapter (filmed at the same location) rather than synthetic noise.

```python
def load_real_segment_ambient(seg, target_samples, fallback_arr=None):
    npy_path = find_real_ambient_npy_path(seg)
    arr = None
    if npy_path and os.path.exists(npy_path):
        raw = np.load(npy_path).astype(np.float32)
        if float(np.sqrt(np.mean(raw ** 2))) > 1e-4:
            arr = raw
    if arr is None and fallback_arr is not None:
        arr = fallback_arr.copy()
    # Pad/slice to target_samples and apply gentle natural dynamics normalization
```

---

## 1d. Audio Track Validation Before Muxing

Before the final ffmpeg mux step (combining video + all audio tracks into one `.mp4`), always validate each `.m4a`/`.wav` audio file with:

```bash
python3 /Users/neilghosh/dev/video/verify_audio_tracks.py
```

Or inline via ffprobe:
```bash
ffprobe -v error -show_entries stream=codec_type \
  -of default=noprint_wrappers=1:nokey=1 \
  /Users/neilghosh/dev/video/audio_tracks/track_shastri.m4a
```

If any track returns no output or errors with `moov atom not found`, regenerate that track before muxing — an invalid track causes ffmpeg to abort the entire mux with exit code 183.

---

## 1e. Zero-Clipping Group-Level Chapter Audio Mixing (Abrupt Truncation Prevention)

> [!CAUTION] **Never slice narration audio strictly at the lead clip boundary (`mixed[:lead_dur * SR]`).**
> When speech takes 7.5s on a 5.5s lead shot, rigid lead-boundary slicing abruptly chops off the ending words/clauses right before the B-roll cut.

### The Group-Level Assembly Rule
In multi-shot documentary editing, every narrated lead shot is accompanied by 1 to 4 B-rolls, creating a continuous chapter window of **20 to 50 seconds**. 
1. **Chapter-Wide Ambient Concatenation:** Concatenate the ambient audio of all segments in the chapter into a single contiguous array (`group_samples = sum(seg_dur * SR)`).
2. **Unclipped Speech Overlay:** Begin narration with a gentle 0.25s inset (`int(0.25 * SR)`). Allow the speech to play completely to its final syllable. If the narration duration exceeds the lead shot, it naturally and gracefully continues over the cut into the start of the first B-roll.
3. **Dynamic Speech Ducking:** Duck ambient audio to **`48%`** only during active speech, followed by a smooth **`0.4s`** linear un-duck ramp back to `100%` ambient volume. The remaining 10–30s of B-roll in the chapter will play authentic, un-ducked road/engine/forest breeze ambience as a natural scenic breather.

---

## 1f. YouTube Multi-Language Audio (MLA) Strict Duration Matching & Verification

> [!WARNING] **YouTube rejects multi-audio video uploads if any audio track duration deviates from the video stream duration** with the fatal ingestion error:  
> `"Processing failed. Audio tracks must match video length."`

To guarantee 100% acceptance on YouTube, Apple TV, and VLC:
1. **Extract Video Stream Duration at Microsecond Precision:** Before muxing, query the master video stream:
   ```bash
   vid_dur=$(ffprobe -v error -select_streams v:0 -show_entries stream=duration -of default=noprint_wrappers=1:nokey=1 master_video.mp4)
   ```
2. **Lock Muxing Bounds:** Always pass `-t ${vid_dur}` and `-shortest` when multiplexing all audio streams into the final MP4 container:
   ```bash
   ffmpeg -y -i master_video.mp4 \
     -i track_uk.m4a -i track_us.m4a -i track_hindi.m4a -i track_bangla.m4a -i track_odia.m4a \
     -map 0:v:0 -map 1:a:0 -map 2:a:0 -map 3:a:0 -map 4:a:0 -map 5:a:0 \
     -t "${vid_dur}" -shortest -c:v copy -c:a copy \
     output_multiaudio.mp4
   ```
3. **Automated Post-Mux Duration Audit:** Verify that `|duration(stream_i) - duration(video)| < 0.05s` across every audio track before publishing:
   ```bash
   ffprobe -v error -show_entries stream=index,codec_type,duration -of json output_multiaudio.mp4
   ```

---

### Single-Line CLI vs. Documentary Batch Mode
- **For a single audio clip or quick test:** Use the global `voice-clone` CLI (`/Users/neilghosh/.local/bin/voice-clone`, backed by `/Users/neilghosh/devtools/voice/main.py`):
  ```bash
  voice-clone --voice neil --text "Your narration text" --steps 16 -q 8 --output out.wav
  ```
- **For a multi-scene documentary (9–50+ segments):** Never call `voice-clone` in a shell loop (which reloads the 1.2 GB `F5TTS` model on every line). Instead, `create_expedition_doc.py` automatically calls [`scripts/f5_batch_synth.py`](file:///Users/neilghosh/dev/skills/skills/expedition-documentary-creator/scripts/f5_batch_synth.py) using `/Users/neilghosh/devtools/voice/.venv/bin/python`, which:
  1. Loads `F5TTS.from_pretrained("lucasnewman/f5-tts-mlx", quantization_bits=8)` **once** in memory.
  2. Synthesizes all uncached narration lines in a single warm MLX session.
  3. Masters each output to `48 kHz` studio quality using `upscale_to_studio_48k()` (`studio_vocal_eq_and_exciter`) from [`/Users/neilghosh/devtools/voice/main.py`](file:///Users/neilghosh/devtools/voice/main.py#L51-L68).
  4. Caches every synthesized line by `sha1(voice + steps + text)` in `work/segments_v4/tts_cache/` so re-renders cost **0 seconds**.

### Adding a New Voice Sample to `/Users/neilghosh/devtools/voice`
If the user provides a new YouTube URL or local `.m4a`/`.wav` recording:
1. Extract 24 kHz mono WAV via `yt-dlp` or `ffmpeg`.
2. Run two-stage spectral denoising + soft noise gating (`clean_segment()` in [`/Users/neilghosh/devtools/voice/isolate_voice.py`](file:///Users/neilghosh/devtools/voice/isolate_voice.py#L39-L76)) using a pure background-noise slice between spoken phrases.
3. Register the cleaned `<name>_clean.wav` and its exact 8–12s transcript in `VOICE_PRESETS` inside [`/Users/neilghosh/devtools/voice/main.py`](file:///Users/neilghosh/devtools/voice/main.py#L12-L48).

---

## 2. Low-Token Architecture for High-Volume Video Generation

To generate a large number of documentary videos with **minimal LLM token consumption**, follow this 4-step zero-bloat workflow:

### Rule 1 — Zero-Token Automated Shot Discovery (`scripts/auto_discover_shots.py`)
- **Do NOT** extract dozens of contact sheets and read them one-by-one into the LLM context window.
- Run [`scripts/auto_discover_shots.py`](file:///Users/neilghosh/dev/skills/skills/expedition-documentary-creator/scripts/auto_discover_shots.py) on the raw video folder:
  ```bash
  /opt/homebrew/bin/python3.14 ~/.gemini/config/skills/expedition-documentary-creator/scripts/auto_discover_shots.py \
    --video-dir "/path/to/videos" \
    --max-shots 9 \
    --out-manifest "/path/to/manifest_auto.json" \
    --out-preview "/path/to/manifest_preview.jpg"
  ```
- This script locally evaluates every clip using **YCbCr foreground skin-cluster rejection** (automatically discarding shots with human faces/bodies), **Sobel sharpness**, and **color saturation**, and writes:
  1. `manifest_auto.json` (chronologically ordered best shots + timestamps + embedded GPS).
  2. A **single** `manifest_preview.jpg` montage grid so visual verification requires **at most 1 image read**.

### Rule 2 — Persistent Disk Caching Across Runs
`create_expedition_doc.py` automatically caches all expensive intermediate artifacts on disk:
- **Esri 3-Layer Hybrid Satellite Tiles:** Cached in `/Users/neilghosh/dev/video/work/sat_tiles/hybrid_{z}_{x}_{y}.png`.
- **Voice-Suppressed GoPro Ambient Audio:** Cached as `.npy` arrays in `work/segments_v4/ambient_cache/amb_<file>_<start>_<dur>.npy`.
- **Rendered `540×268` HUD Cards:** Cached as `work/segments_v4/hud_card_<idx>.png`.
- **SHA-1 Hashed TTS Voiceovers:** Cached in `work/segments_v4/tts_cache/f5_<voice>_<sha1>.wav`.

### Rule 3 — Delegate Bulk Execution to Local Workhorse (`gemma4:26b`)
- Per global hybrid architecture rules, use cloud thinking tokens strictly for planning/verification and delegate bulk batch execution or multi-folder manifest processing to the local workhorse:
  ```bash
  /Users/neilghosh/devtools/agylocal/.venv/bin/python /Users/neilghosh/devtools/agylocal/workhorse.py \
    -w /Users/neilghosh/dev/video \
    "Run create_expedition_doc.py for voices neil, atherton, and tony and verify output MP4 durations via ffprobe"
  ```

---

## 3. Core Documentary Quality Standards

1. **Zero Visible Human Faces (`scripts/vision_face_scanner` + `scripts/smart_human_cutter_blur.py`):**
   - Never include unblurred human faces in the final cut, **and never blindly discard an entire scenic clip just because a person or face appears for a few seconds**:
     - Run [`scripts/vision_face_scanner`](file:///Users/neilghosh/dev/skills/skills/expedition-documentary-creator/scripts/vision_face_scanner) (native macOS Apple `Vision` `VNDetectFaceRectanglesRequest` + `VNDetectHumanRectanglesRequest`) across the raw clips to obtain exact per-timestamp face and upper-body bounding boxes (`x, y, w, h` in `1920×1080`).
     - Use [`scripts/smart_human_cutter_blur.py`](file:///Users/neilghosh/dev/skills/skills/expedition-documentary-creator/scripts/smart_human_cutter_blur.py) to salvage clips with transient humans:
       1. **`cut_human_seconds` (`find_longest_clean_window`)**: When a human or camera-turn only appears at the start/end of a clip, trim out those timestamps and extract the longest contiguous 100% human-free scenic sub-window (`>= 5.0s`).
       2. **`blur_faces` (`build_ffmpeg_face_blur_filter`)**: When pedestrians or bystanders walk through a key landmark shot, apply a localized time-gated Gaussian crop-overlay blur (`split -> crop=w:h:x:y,gblur=sigma=28 -> overlay=x:y:enable='between(t,t0,t1)'`) over the detected face/head coordinates during `[t0, t1]`. (Always use `crop + gblur + overlay` rather than `delogo`, which causes vertical edge-interpolation streaks when a head touches the top of the frame).
2. **Voice-Suppressed Ambient GoPro Audio (`scripts/voice_suppressor.py`):** Strips passenger chatter (`300–3400 Hz` dynamic spectral gating + center-channel reduction) while keeping authentic road, engine, and mountain wind sounds. Ambient audio is mixed at `target_ambient_rms=0.046` and ducked to `48%` during voiceover narration.
3. **Expedition / *Man vs. Wild* Scriptwriting:** Never describe the visual obvious. Every narration line must state **exact route access** (highway numbers, ghat passes, 4x4 trails), **historical context** (kingdoms, colonial planters, indigenous resistance, ancient trade trails), and **ecological significance** (biosphere reserves, watersheds, monsoon escarpments).
4. **Clean, Large-Font 4K Geographic Cards (`scripts/map_telemetry_hud.py`) — Chapter Leads Only:**
   - **Zero Micro-Print Rule:** Never render 9pt–13pt micro-fonts, overlapping town pills, 3 directional edge boxes, GPS decimals, or tiny sparklines inside a corner card.
   - **4K Card Spec (`render_hud_overlay_png(..., is_4k=True)`, `1160×408` on `3840×2160`):**
     - **Left Mini-Map:** Pure `Esri World_Imagery` satellite terrain (`fetch_clean_sat_road_tile`) + bold glowing route trace + pulsing GPS beacon (zero tiny raster road/town text or overlapping boxes).
     - **Right Panel:** Large, high-contrast **44pt–54pt bold typography** showing only **Location Title**, **State/Corridor Pill** (strip `' DIST.'` / `' DISTRICT'` instead of mid-word truncation), and two large metric tiles (**Elevation `m`** and **Route Distance `km`**).
   - **Chapter Leads Only:** Overlay the Geographic Card **only on Chapter Lead clips** (`fade=in` at `0.35s`, `fade=out` at `5.2s`), leaving all **B-roll cuts 100% unobstructed**.
5. **Native 4K Ultra HD (`3840×2160`) Video Pipeline (`build_4k_clean_hud_master.py`):**
   - When the source pool contains 4K GoPro clips (`3840×2160` / `5312×2988`), **never downscale the master timeline to `1920×1080`**.
   - Normalize all segments to **`3840×2160` at `25 fps`** (`fps=25,scale=3840:2160:force_original_aspect_ratio=decrease,pad=3840:2160:(ow-iw)/2:(oh-ih)/2,settb=1/25`) using Apple Silicon hardware encoding (`h264_videotoolbox -b:v 22M -maxrate 30M -bufsize 40M -video_track_timescale 25000`) to preserve 100% native 4K clarity and unlock YouTube's 4K (2160p) VP9/AV1 bitrate tier.
6. **High-CTR Vox-Style YouTube Thumbnail & Multilingual Metadata (`build_vox_style_thumbnail.py`):**
   - **Single Hero Focal Point + Tactile Map Fusion:** Stitch real Zoom 8 satellite tiles along the GPS route and blend seamlessly into a single 4K hero destination frame using a wide 850px non-linear cosine dissolve (`0.5 * (1 - cos(pi * t))`), volumetric horizon sunlight, and edge vignette (never use discrete rectangular photo cards or 4-photo grids).
   - **3-Word Rule & 150px Mobile Squint Test:** Use 110pt–124pt `Arial Black` / `Impact` typography for a 3-word hook (e.g., `2,000 KM` in white with heavy drop shadow + `DRIVE` inside a glowing amber Vox highlighter bar), and verify legibility at `150×84` mobile preview size.
   - **Indic YouTube Titles (Hindi, Bangla, Odia):** Never present Indic titles inside monospaced markdown code blocks (where missing GSUB OpenType tables split conjuncts into disconnected letters with visible halants `्`/`্`/`୍`), and prefer natural conjunct-free vocabulary where possible.

---

## 4. Quick CLI Commands

### Build 5-Language Multi-Audio Tracks & Mux Master Documentary
```bash
/opt/homebrew/bin/python3.14 ~/.gemini/config/skills/expedition-documentary-creator/scripts/build_5languages_scratch_doc.py
```

### Render Native 4K Ultra HD (`3840×2160`) Clean HUD Master
```bash
/opt/homebrew/bin/python3.14 ~/.gemini/config/skills/expedition-documentary-creator/scripts/build_4k_clean_hud_master.py
```

### Generate High-CTR Vox-Style 3D Relief Map Thumbnail
```bash
/opt/homebrew/bin/python3.14 ~/.gemini/config/skills/expedition-documentary-creator/scripts/build_vox_style_thumbnail.py
```

---

## 5. Equal-Treatment Multi-Source Timeline (GoPro + Google Photos / Mobile)

> [!IMPORTANT] **All source clips — GoPro AND Google Photos/mobile — must be treated as equal candidates for the timeline. No source should be systematically demoted to silent B-roll.**

### The Problem with Source-Biased Timelines
Previous builds assigned GoPro clips as "narrated leads" and Google Photos clips as "ambient B-roll only". This caused:
- Mobile clips to appear with no narration (raw ambient/noise audio) or be silently skipped.
- GoPro footage to dominate the story even when GP clips captured better scenery.
- Uneven screen time: days with 40 GoPro leads and 5 GP clips meant most GP clips got 0 B-roll slots.

### Correct Approach — Quality-First Equal Pool
1. **Merge all clips into a single chronological pool** (GoPro + Google Photos), sorted by IST timestamp.
2. **Quality filter first** — before assigning any clip to the timeline:
   - Run `scripts/auto_discover_shots.py` (YCbCr skin-cluster rejection + Sobel sharpness + saturation) on **every** clip regardless of source.
   - Discard clips below sharpness/saturation thresholds (shaky footage, severely blurred, or overexposed clips from either source).
   - Discard clips flagged by `vision_face_scanner` as human-only with no recoverable scenic sub-window ≥ 5 s.
3. **Assign narrated leads from the merged pool** — every clip that passes quality filtering is a candidate for a narrated lead slot, not just GoPro clips.
4. **Story re-write required** — when adding new clips from the equal pool, the chapter script must be rewritten to reference those specific clips (location, time, GPS elevation) rather than defaulting to GoPro-only story lines.
5. **Chapter Maps re-embedded** — after reordering the timeline with the merged pool, re-run `map_telemetry_hud.py` to regenerate the 6 full-screen animated chapter transition maps and all Smart-Corner PiP HUDs so they reflect the new clip order and GPS waypoints.

### Quality Discard Criteria
A clip should be discarded (from both sources) if **any** of the following are true:
- Sobel sharpness score < 35 (motion blur / extreme shake)
- Mean saturation < 18 (washed-out / indoor / overcast flat grey)
- > 85 % of frames flagged as containing human faces/bodies with no clean sub-window ≥ 5 s
- Duration < 3 s after trimming human-contaminated frames
- Audio RMS < 0.005 AND video is also a duplicate (same GPS coords ± 10 m as another clip within ± 30 s)

### Implementation Blueprint (for future build)
```python
# 1. Load all clips from both sources into one list
all_clips = load_gopro_clips() + load_gphotos_clips()

# 2. Quality filter — equal treatment
quality_clips = [c for c in all_clips if passes_quality_filter(c)]

# 3. Sort chronologically by IST timestamp
quality_clips.sort(key=lambda c: c['ts_ist'])

# 4. Assign narrated leads — every Nth clip is a lead (based on total narration chapters)
# No source-based distinction; leads are chosen by quality score rank within each day
day_groups = group_by_ist_day(quality_clips)
for day, clips in day_groups.items():
    clips.sort(key=lambda c: c['quality_score'], reverse=True)
    n_leads = min(len(clips), TARGET_CHAPTERS_PER_DAY)
    leads = clips[:n_leads]
    brolls = clips[n_leads:]
    # Every lead gets at least 1–2 brolls; overflow brolls cycle back to next lead

# 5. Rewrite story chapters to reference actual clip metadata (GPS, time, source, location)

# 6. Re-embed maps at major geographical transitions in the merged timeline
regenerate_chapter_maps(timeline)
```

> [!TIP] For the story rewrite, use each clip's GPS coordinates, IST timestamp, elevation, and source (GoPro/mobile) to generate contextually accurate narration — e.g. "At 3:42 p.m., a mobile clip captures the Banasura Dam spillway from the eastern embankment path, a vantage point the GoPro never reached."

> [!WARNING] **Do not start this reprocessing until explicitly instructed.** The current build (`expedition_all_videos_multiaudio.mp4`) remains the active output. This section is planning documentation only.
To bundle **1 video stream (`-c:v copy`) + all 5 narrator voices** (`neil`, `tony`, `atherton`, `en-US-AndrewMultilingualNeural`, `en-GB-RyanNeural`) as selectable audio tracks inside a single `.mp4` (switchable in QuickTime, VLC, IINA, Apple TV, Plex):
```bash
/opt/homebrew/bin/python3.14 ~/.gemini/config/skills/expedition-documentary-creator/scripts/create_expedition_doc.py \
  --video-dir "/Users/neilghosh/Pictures/Kerala 2026/GoPro" \
  --voice "neil,tony,atherton,en-US-AndrewMultilingualNeural,en-GB-RyanNeural" \
  --steps 8 -q 8 \
  --audio-only \
  --output "/Users/neilghosh/dev/video/sample_documentary_neil.mp4,/Users/neilghosh/dev/video/sample_documentary_tonygreig.mp4,/Users/neilghosh/dev/video/sample_documentary_atherton.mp4,/Users/neilghosh/dev/video/sample_documentary.mp4,/Users/neilghosh/dev/video/sample_documentary_british_synced.mp4" \
  --multi-audio-output "/Users/neilghosh/dev/video/sample_documentary_multiaudio.mp4"
```
