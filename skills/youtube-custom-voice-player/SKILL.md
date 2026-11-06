---
name: youtube-custom-voice-player
description: >-
  Overdubs an existing video already uploaded to YouTube into personal and sports commentary voices
  (neil, nasser, atherton, shastri, tony, holding, attenborough, bear_hindi) without re-uploading
  celebrity/personal voices to YouTube. Suppresses the YouTube video's original human voice while
  retaining real surrounding ambient sounds (car, water, wind, birds, background score), synthesizes
  synced voice tracks via F5-TTS-MLX / IndicF5-MLX, and generates a hostable Custom HTML5 + YouTube
  IFrame API Web Player (`index.html`) that streams the 4K video from YouTube (`ytPlayer.mute()`)
  while playing the selected personal/commentator voice and ambient audio in sub-30ms sync.
---

# YouTube Custom Voice Overdub & HTML5 Sync Player (`youtube-custom-voice-player`)

Allows any video already generated and uploaded to YouTube to be experienced in **personal (`neil`)** or **iconic commentary voices (`nasser`, `atherton`, `shastri`, `tony`, `holding`, `attenborough`, `bear_hindi`)** via a lightweight, self-hosted Custom HTML5 Player — keeping public YouTube uploads 100% free of personal/celebrity cloned voices.

---

## 1. How It Suppresses YouTube Voice & Streams Custom Voices

1. **4K Video Streamed Directly from YouTube (`YT.Player`):**
   - The generated `index.html` embeds your uploaded YouTube video via the official **YouTube IFrame Player API (`new YT.Player`)** at `hd2160` (4K) and automatically calls `ytPlayer.mute()` on load and on every state change.
   - Because `ytPlayer.mute()` silences the YouTube stream's built-in narrator, the original YouTube voice is **100% suppressed** in the browser with zero video hosting bandwidth required.
2. **Real Surrounding Ambient Audio Preserved (`audio/ambient_clean.m4a`):**
   - `scripts/build_custom_voice_player.py` extracts the audio from the YouTube video (or local source MP4) and passes it through `scripts/voice_suppressor.py` (STFT vocal-formant notch filter attenuating `250 Hz – 3800 Hz` speech harmonics while preserving `<200 Hz` engine/road rumble and `>4 kHz` rushing water, mountain wind, and birds).
3. **Personal & Commentary Voice Tracks (`audio/voice_<preset>.m4a`):**
   - Synthesizes the script/chapter manifest using the bundled 24 kHz reference voices in [`voices/`](./voices) (`F5-TTS-MLX` / `IndicF5-MLX`) and aligns each narration clip to its exact chapter `start_sec`.
4. **Sub-30ms Drift-Locked Web Player (`index.html`):**
   - Locks `<audio id="ambient-audio">` and `<audio id="voice-audio">` to `ytPlayer.getCurrentTime()` (`Play`, `Pause`, `Seek`, `Buffering`, and `PlaybackRate`), with live **Voice Switcher Buttons**, independent **Voice vs. Ambient Volume Sliders**, **Live Subtitles**, and **Clickable Chapter Navigation**.

---

## 2. Bundled Personal & Commentary Reference Voices (`voices/`)

| Preset Key | Aliases | Bundled 24 kHz Reference WAV | Description |
| :--- | :--- | :--- | :--- |
| `neil` | `neil_ghosh` | [`voices/neil_clean.wav`](./voices/neil_clean.wav) | Neil's personal isolated & denoised narration voice |
| `nasser` | `nasser_hussain`, `hussain` | [`voices/nasser_clean.wav`](./voices/nasser_clean.wav) | Nasser Hussain Sky Sports commentary (`QrpzO2NjGHg`) |
| `atherton` | `mike_atherton`, `bumble`, `arthoron` | [`voices/atherton_clean.wav`](./voices/atherton_clean.wav) | Mike Atherton / Bumble commentary (`z4IX4e1ZUHQ`) |
| `shastri` | `ravi_shastri` | [`voices/shastri_clean.wav`](./voices/shastri_clean.wav) | Ravi Shastri energetic broadcast commentary |
| `tony` | `tony_greig`, `toney_greg` | [`voices/tony_greig_clean.wav`](./voices/tony_greig_clean.wav) | Tony Greig classic commentary (`nNHZFmOzMt0`) |
| `holding` | `michael_holding` | [`voices/holding_clean.wav`](./voices/holding_clean.wav) | Michael Holding silky Test commentary (`B7yDz-HQDww`) |
| `attenborough` | `david_attenborough` | [`voices/attenborough_clean.wav`](./voices/attenborough_clean.wav) | Sir David Attenborough natural history narration |
| `bear_hindi` | `bear_grylls_hindi` | [`voices/bear_hindi_clean.wav`](./voices/bear_hindi_clean.wav) | Expedition Hindi narrator (`IndicF5-MLX`) |

---

## 3. End-to-End Usage (`build_custom_voice_player.py`)

### Build a Custom HTML5 Player for an Uploaded YouTube Video
```bash
/Users/neilghosh/devtools/voice/.venv/bin/python \
  ~/.gemini/config/skills/youtube-custom-voice-player/scripts/build_custom_voice_player.py \
  --youtube-url "https://www.youtube.com/watch?v=YOUR_YOUTUBE_ID" \
  --source-video "/Users/neilghosh/dev/video/expedition_all_videos_multiaudio.mp4" \
  --manifest "/Users/neilghosh/dev/video/work/equal_timeline_v2/timeline_manifest.json" \
  --voices "neil,nasser,atherton,shastri,tony,holding,attenborough" \
  --title "South India 2,000 KM Expedition" \
  --out-dir "/Users/neilghosh/dev/video/custom_voice_player"
```

### Serve Locally or Host on Any Static Web Host (GitHub Pages / Cloudflare Pages / Vercel)
```bash
# Preview locally
python3 -m http.server 8080 --directory "/Users/neilghosh/dev/video/custom_voice_player"
# Open http://localhost:8080
```

### Output Bundle Structure (`--out-dir`)
```text
custom_voice_player/
├── index.html                 # Standalone Custom HTML5 + YouTube IFrame API Sync Player
└── audio/
    ├── ambient_clean.m4a      # Voice-suppressed surrounding ambient (car, water, wind, birds, score)
    ├── voice_neil.m4a         # Synced Neil narration track
    ├── voice_nasser.m4a       # Synced Nasser Hussain commentary track
    ├── voice_atherton.m4a     # Synced Mike Atherton commentary track
    ├── voice_shastri.m4a      # Synced Ravi Shastri commentary track
    ├── voice_tony.m4a         # Synced Tony Greig commentary track
    ├── voice_holding.m4a      # Synced Michael Holding commentary track
    └── voice_attenborough.m4a # Synced David Attenborough narration track
```
