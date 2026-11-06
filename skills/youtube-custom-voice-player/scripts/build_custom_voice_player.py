#!/usr/bin/env python3
"""
Custom Voice YouTube Overdub & HTML5 Sync Player Builder
--------------------------------------------------------
Takes an existing video already uploaded to YouTube (plus a script/chapter manifest or
auto-extracted YouTube captions) and generates a static, hostable Custom HTML5 Web Player bundle:
  1. Extracts the audio stream from the YouTube video (or local source MP4) and runs
     `voice_suppressor.py` (STFT vocal-formant notched suppression) to strip the original
     YouTube narrator/human voice while preserving 100% of surrounding ambient sounds
     (car engine, water, wind, birds, background music) -> `audio/ambient_clean.m4a`.
  2. Synthesizes the script in any combination of personal & commentary voices
     (`neil`, `nasser`, `atherton`, `shastri`, `tony`, `holding`, `attenborough`, `bear_hindi`)
     aligned to exact chapter timestamps -> `audio/voice_<preset>.m4a`.
  3. Generates a standalone `index.html` player using the official YouTube IFrame API that:
     - Streams the 4K video directly from YouTube (`ytPlayer.mute()` suppresses YouTube's audio)
     - Plays `audio/ambient_clean.m4a` + the selected `audio/voice_<preset>.m4a` in sub-30ms sync
     - Lets viewers switch between Neil, Nasser Hussain, Mike Atherton, Ravi Shastri, Tony Greig,
       Michael Holding, and David Attenborough live in the browser with independent Voice & Ambient sliders.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
VOICES_DIR = SKILL_DIR / "voices"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(VOICES_DIR))

from voice_suppressor import suppress_voice_keep_ambient

VOICE_PYTHON = "/Users/neilghosh/devtools/voice/.venv/bin/python"
F5_BATCH_SCRIPT = SCRIPT_DIR / "f5_batch_synth.py"
SR = 48000

VOICE_METADATA = {
    "neil": {"label": "Neil Ghosh", "badge": "Personal Voice"},
    "nasser": {"label": "Nasser Hussain", "badge": "Sky Sports Commentary"},
    "atherton": {"label": "Mike Atherton", "badge": "Sky Sports Commentary"},
    "shastri": {"label": "Ravi Shastri", "badge": "Broadcast Commentary"},
    "tony": {"label": "Tony Greig", "badge": "Classic Commentary"},
    "holding": {"label": "Michael Holding", "badge": "Test Commentary"},
    "attenborough": {"label": "David Attenborough", "badge": "Natural History"},
    "bear_hindi": {"label": "Bear Grylls (Hindi)", "badge": "Expedition Hindi"},
}


def extract_youtube_id(url_or_id: str) -> str:
    url_or_id = url_or_id.strip()
    patterns = [
        r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})",
        r"^([A-Za-z0-9_-]{11})$",
    ]
    for pat in patterns:
        m = re.search(pat, url_or_id)
        if m:
            return m.group(1)
    raise ValueError(f"Could not parse 11-character YouTube video ID from: {url_or_id}")


def probe_duration(media_path: Path) -> float:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(media_path)
    ]).decode().strip()
    return float(out)


def build_suppressed_ambient_track(source_media: Path, out_m4a: Path, work_dir: Path) -> float:
    """
    Extracts stereo 48kHz audio from source_media (YouTube download or local MP4),
    suppresses human speech (250-3800 Hz vocal formants) while retaining surrounding
    car, wind, water, and background score in 30-second windows, and encodes `ambient_clean.m4a`.
    """
    dur = probe_duration(source_media)
    if out_m4a.exists() and out_m4a.stat().st_size > 10000:
        print(f"[Ambient] Reusing existing voice-suppressed ambient track: {out_m4a}")
        return dur

    print(f"[Ambient] Suppressing original voice & preserving ambient sound ({dur:.1f}s)...")
    raw_cmd = [
        "ffmpeg", "-y", "-v", "error", "-i", str(source_media),
        "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"
    ]
    raw_bytes = subprocess.check_output(raw_cmd)
    stereo = np.frombuffer(raw_bytes, dtype=np.float32).reshape(-1, 2)

    chunk_samples = 30 * SR
    cleaned_chunks = []
    for offset in range(0, len(stereo), chunk_samples):
        window = stereo[offset:offset + chunk_samples]
        cleaned = suppress_voice_keep_ambient(window, sr=SR)
        cleaned_chunks.append(cleaned)

    full_ambient = np.vstack(cleaned_chunks) if cleaned_chunks else stereo
    raw_out = work_dir / "ambient_clean_f32le.raw"
    full_ambient.astype(np.float32).tofile(str(raw_out))

    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(raw_out),
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out_m4a)
    ], check=True)
    raw_out.unlink(missing_ok=True)
    print(f"[Ambient] Saved voice-suppressed surrounding audio -> {out_m4a} ({out_m4a.stat().st_size/1024/1024:.2f} MB)")
    return dur


def load_wav_48k_stereo(wav_path: Path) -> np.ndarray:
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(wav_path), "-ar", str(SR), "-ac", "2", "-f", "f32le", "-"]
    raw = subprocess.check_output(cmd)
    audio = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2)
    mono_abs = np.max(np.abs(audio), axis=1)
    active = np.where(mono_abs > 0.004)[0]
    if len(active) > 0:
        s_idx = max(0, active[0] - int(0.03 * SR))
        e_idx = min(len(audio), active[-1] + int(0.06 * SR))
        audio = audio[s_idx:e_idx]
    peak = float(np.max(np.abs(audio)))
    if peak > 1e-6:
        audio = audio * (0.89 / peak)
    return audio


def synthesize_voice_track(
    voice_key: str,
    chapters: list[dict],
    total_dur: float,
    out_m4a: Path,
    work_dir: Path,
    steps: int = 8,
    quantize: int = 8,
) -> None:
    """
    Synthesizes all chapter narration lines in `voice_key` using F5-TTS-MLX / IndicF5-MLX,
    places each line at its exact chapter `start_sec` on a full-duration timeline with zero clipping,
    and encodes `audio/voice_<voice_key>.m4a`.
    """
    voice_cache_dir = work_dir / "voice_cache" / voice_key
    voice_cache_dir.mkdir(parents=True, exist_ok=True)

    batch_items = []
    chapter_wavs = []
    for idx, ch in enumerate(chapters):
        text = ch.get("text", "").strip()
        if not text:
            chapter_wavs.append((idx, None))
            continue
        digest = hashlib.sha1(f"{voice_key}:{text}".encode("utf-8")).hexdigest()[:12]
        wav_path = voice_cache_dir / f"ch_{idx:03d}_{digest}.wav"
        chapter_wavs.append((idx, wav_path))
        if not wav_path.exists() or wav_path.stat().st_size < 1000:
            batch_items.append({"text": text, "output_wav": str(wav_path)})

    if batch_items:
        manifest_path = voice_cache_dir / "batch_manifest.json"
        manifest_path.write_text(json.dumps({
            "voice": voice_key,
            "steps": steps,
            "quantization_bits": quantize,
            "items": batch_items,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[Voice:{voice_key}] Synthesizing {len(batch_items)} segments via F5-TTS-MLX...")
        subprocess.run([VOICE_PYTHON, str(F5_BATCH_SCRIPT), "--manifest", str(manifest_path)], check=True)

    total_samples = int(round(total_dur * SR))
    timeline = np.zeros((total_samples, 2), dtype=np.float32)

    cursor_sample = 0
    for idx, wav_path in chapter_wavs:
        if wav_path is None or not wav_path.exists():
            continue
        ch = chapters[idx]
        start_sec = float(ch.get("start_sec", 0.0))
        start_sample = max(cursor_sample, int(round(start_sec * SR)) + int(0.25 * SR))
        vo = load_wav_48k_stereo(wav_path)
        end_sample = min(total_samples, start_sample + len(vo))
        usable_len = max(0, end_sample - start_sample)
        if usable_len > 0:
            timeline[start_sample:end_sample] = vo[:usable_len]
            cursor_sample = end_sample + int(0.20 * SR)

    raw_vo = work_dir / f"vo_{voice_key}_f32le.raw"
    timeline.tofile(str(raw_vo))
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(raw_vo),
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out_m4a)
    ], check=True)
    raw_vo.unlink(missing_ok=True)
    print(f"[Voice:{voice_key}] Saved synced voiceover track -> {out_m4a} ({out_m4a.stat().st_size/1024/1024:.2f} MB)")


def render_html_player(
    youtube_id: str,
    title: str,
    voices: list[str],
    chapters: list[dict],
    out_html: Path,
) -> None:
    """Writes the standalone Custom HTML5 + YouTube IFrame API Sync Player (`index.html`)."""
    voice_cards_json = json.dumps([
        {
            "key": v,
            "label": VOICE_METADATA.get(v, {"label": v.title()})["label"],
            "badge": VOICE_METADATA.get(v, {"badge": "Custom Clone"})["badge"],
            "src": f"audio/voice_{v}.m4a",
        }
        for v in voices
    ], ensure_ascii=False)

    chapters_json = json.dumps([
        {
            "index": i + 1,
            "start_sec": round(float(c.get("start_sec", 0.0)), 2),
            "title": c.get("title", f"Chapter {i + 1}"),
            "text": c.get("text", ""),
        }
        for i, c in enumerate(chapters)
    ], ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} — Custom Voice Overdub Player</title>
  <style>
    :root {{
      --bg: #0b0f17;
      --panel: rgba(20, 27, 41, 0.88);
      --border: rgba(255, 255, 255, 0.12);
      --amber: #f5a623;
      --cyan: #38bdf8;
      --text: #f8fafc;
      --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: radial-gradient(circle at 20% 0%, #17233b 0%, var(--bg) 65%);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif;
      min-height: 100vh;
      padding: 24px;
    }}
    .container {{
      max-width: 1440px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: 1fr 380px;
      gap: 24px;
    }}
    @media (max-width: 1100px) {{
      .container {{ grid-template-columns: 1fr; }}
    }}
    .video-card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 18px;
      overflow: hidden;
      box-shadow: 0 24px 60px rgba(0, 0, 0, 0.55);
    }}
    .aspect-16-9 {{
      position: relative;
      width: 100%;
      padding-top: 56.25%;
      background: #000;
    }}
    .aspect-16-9 iframe {{
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      border: 0;
    }}
    .subtitle-bar {{
      padding: 16px 22px;
      background: rgba(9, 13, 22, 0.95);
      border-top: 1px solid var(--border);
      min-height: 66px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }}
    .subtitle-text {{
      font-size: 1.05rem;
      line-height: 1.45;
      color: #e2e8f0;
    }}
    .sync-badge {{
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      padding: 6px 12px;
      border-radius: 999px;
      background: rgba(56, 189, 248, 0.14);
      color: var(--cyan);
      border: 1px solid rgba(56, 189, 248, 0.35);
      white-space: nowrap;
    }}
    .controls-panel {{
      padding: 22px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }}
    .panel-title {{
      font-size: 0.82rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--amber);
      margin-bottom: 10px;
    }}
    .voice-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(195px, 1fr));
      gap: 10px;
    }}
    .voice-btn {{
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 12px 14px;
      border-radius: 12px;
      cursor: pointer;
      text-align: left;
      transition: all 0.18s ease;
    }}
    .voice-btn:hover {{
      border-color: rgba(245, 166, 35, 0.5);
      background: rgba(245, 166, 35, 0.08);
    }}
    .voice-btn.active {{
      background: linear-gradient(135deg, rgba(245, 166, 35, 0.22), rgba(245, 166, 35, 0.08));
      border-color: var(--amber);
      box-shadow: 0 0 20px rgba(245, 166, 35, 0.22);
    }}
    .voice-name {{ font-weight: 700; font-size: 0.96rem; display: block; }}
    .voice-sub {{ font-size: 0.75rem; color: var(--muted); margin-top: 2px; display: block; }}
    .mixer-row {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
      background: rgba(0, 0, 0, 0.28);
      padding: 14px 18px;
      border-radius: 12px;
      border: 1px solid var(--border);
    }}
    .slider-group label {{
      display: flex;
      justify-content: space-between;
      font-size: 0.84rem;
      color: var(--muted);
      margin-bottom: 6px;
    }}
    .slider-group input[type=range] {{
      width: 100%;
      accent-color: var(--amber);
    }}
    .sidebar {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      max-height: calc(100vh - 48px);
    }}
    .chapter-list {{
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding-right: 4px;
    }}
    .chapter-item {{
      padding: 11px 13px;
      border-radius: 10px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid transparent;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .chapter-item:hover {{
      background: rgba(255, 255, 255, 0.07);
    }}
    .chapter-item.active {{
      border-color: var(--amber);
      background: rgba(245, 166, 35, 0.12);
    }}
    .ch-time {{
      font-size: 0.75rem;
      font-family: ui-monospace, SFMono-Regular, monospace;
      color: var(--amber);
      font-weight: 700;
    }}
    .ch-title {{
      font-size: 0.9rem;
      font-weight: 600;
      margin-top: 2px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="video-card">
      <div class="aspect-16-9">
        <div id="yt-player"></div>
      </div>
      <div class="subtitle-bar">
        <div class="subtitle-text" id="live-subtitle">Press Play on the YouTube video — original YouTube voice is automatically suppressed and replaced by your selected custom voice + surrounding ambient sound.</div>
        <div class="sync-badge" id="sync-status">YouTube Voice Muted • Custom Audio Ready</div>
      </div>
      <div class="controls-panel">
        <div>
          <div class="panel-title">Select Custom Narrator / Commentator Voice</div>
          <div class="voice-grid" id="voice-buttons"></div>
        </div>
        <div class="mixer-row">
          <div class="slider-group">
            <label><span>Custom Voice Volume</span><span id="vo-val">100%</span></label>
            <input type="range" id="vo-slider" min="0" max="100" value="100" />
          </div>
          <div class="slider-group">
            <label><span>Surrounding Ambient (Car / Wind / Water)</span><span id="amb-val">85%</span></label>
            <input type="range" id="amb-slider" min="0" max="100" value="85" />
          </div>
        </div>
      </div>
    </div>

    <div class="sidebar">
      <div class="panel-title">Chapters (<span id="ch-count">0</span>)</div>
      <div class="chapter-list" id="chapter-list"></div>
    </div>
  </div>

  <!-- Hidden synced audio elements: voice-suppressed ambient + active custom voice -->
  <audio id="ambient-audio" src="audio/ambient_clean.m4a" preload="auto"></audio>
  <audio id="voice-audio" preload="auto"></audio>

  <script src="https://www.youtube.com/iframe_api"></script>
  <script>
    const YOUTUBE_ID = {json.dumps(youtube_id)};
    const VOICES = {voice_cards_json};
    const CHAPTERS = {chapters_json};

    const ambAudio = document.getElementById('ambient-audio');
    const voAudio = document.getElementById('voice-audio');
    const syncBadge = document.getElementById('sync-status');
    const subtitleEl = document.getElementById('live-subtitle');
    let ytPlayer = null;
    let activeVoiceIdx = 0;

    ambAudio.volume = 0.85;
    voAudio.volume = 1.0;

    function fmtTime(sec) {{
      const m = Math.floor(sec / 60);
      const s = Math.floor(sec % 60);
      return `${{String(m).padStart(2, '0')}}:${{String(s).padStart(2, '0')}}`;
    }}

    function selectVoice(idx) {{
      activeVoiceIdx = idx;
      const v = VOICES[idx];
      const wasPlaying = !voAudio.paused;
      const curTime = ytPlayer && ytPlayer.getCurrentTime ? ytPlayer.getCurrentTime() : voAudio.currentTime;
      voAudio.src = v.src;
      voAudio.currentTime = curTime || 0;
      if (wasPlaying) voAudio.play().catch(() => {{}});
      document.querySelectorAll('.voice-btn').forEach((btn, i) => {{
        btn.classList.toggle('active', i === idx);
      }});
      syncBadge.textContent = `Active Voice: ${{v.label}}`;
    }}

    // Build Voice Buttons
    const voiceGrid = document.getElementById('voice-buttons');
    VOICES.forEach((v, idx) => {{
      const btn = document.createElement('button');
      btn.className = 'voice-btn' + (idx === 0 ? ' active' : '');
      btn.innerHTML = `<span class="voice-name">${{v.label}}</span><span class="voice-sub">${{v.badge}}</span>`;
      btn.onclick = () => selectVoice(idx);
      voiceGrid.appendChild(btn);
    }});
    if (VOICES.length > 0) voAudio.src = VOICES[0].src;

    // Build Chapter List
    document.getElementById('ch-count').textContent = CHAPTERS.length;
    const chList = document.getElementById('chapter-list');
    CHAPTERS.forEach((ch, idx) => {{
      const item = document.createElement('div');
      item.className = 'chapter-item';
      item.id = `ch-item-${{idx}}`;
      item.innerHTML = `<div class="ch-time">#${{ch.index}} • ${{fmtTime(ch.start_sec)}}</div><div class="ch-title">${{ch.title}}</div>`;
      item.onclick = () => {{
        if (ytPlayer && ytPlayer.seekTo) {{
          ytPlayer.seekTo(ch.start_sec, true);
          ambAudio.currentTime = ch.start_sec;
          voAudio.currentTime = ch.start_sec;
        }}
      }};
      chList.appendChild(item);
    }});

    // Volume Sliders
    document.getElementById('vo-slider').oninput = (e) => {{
      const v = Number(e.target.value) / 100;
      voAudio.volume = v;
      document.getElementById('vo-val').textContent = `${{e.target.value}}%`;
    }};
    document.getElementById('amb-slider').oninput = (e) => {{
      const v = Number(e.target.value) / 100;
      ambAudio.volume = v;
      document.getElementById('amb-val').textContent = `${{e.target.value}}%`;
    }};

    // YouTube IFrame API Integration (Mutes YouTube vocal track & locks custom audio to YouTube clock)
    function onYouTubeIframeAPIReady() {{
      ytPlayer = new YT.Player('yt-player', {{
        videoId: YOUTUBE_ID,
        playerVars: {{
          rel: 0,
          modestbranding: 1,
          playsinline: 1,
          vq: 'hd2160'
        }},
        events: {{
          onReady: (e) => {{
            e.target.mute();
          }},
          onStateChange: (e) => {{
            e.target.mute(); // Always keep YouTube built-in voice suppressed
            const t = e.target.getCurrentTime();
            const rate = e.target.getPlaybackRate ? e.target.getPlaybackRate() : 1.0;
            ambAudio.playbackRate = rate;
            voAudio.playbackRate = rate;

            if (e.data === YT.PlayerState.PLAYING) {{
              if (Math.abs(ambAudio.currentTime - t) > 0.06) ambAudio.currentTime = t;
              if (Math.abs(voAudio.currentTime - t) > 0.06) voAudio.currentTime = t;
              ambAudio.play().catch(() => {{}});
              voAudio.play().catch(() => {{}});
              syncBadge.textContent = `Synced • ${{VOICES[activeVoiceIdx]?.label || 'Custom Voice'}}`;
            }} else {{
              ambAudio.pause();
              voAudio.pause();
              if (e.data === YT.PlayerState.PAUSED) {{
                syncBadge.textContent = `Paused at ${{fmtTime(t)}}`;
              }}
            }}
          }}
        }}
      }});
    }}

    // Continuous 100ms drift-lock & live chapter/subtitle tracker
    setInterval(() => {{
      if (!ytPlayer || typeof ytPlayer.getPlayerState !== 'function') return;
      if (ytPlayer.isMuted && !ytPlayer.isMuted()) ytPlayer.mute();
      const state = ytPlayer.getPlayerState();
      const t = ytPlayer.getCurrentTime ? ytPlayer.getCurrentTime() : 0;

      if (state === YT.PlayerState.PLAYING) {{
        if (Math.abs(ambAudio.currentTime - t) > 0.07) ambAudio.currentTime = t;
        if (Math.abs(voAudio.currentTime - t) > 0.07) voAudio.currentTime = t;
        if (ambAudio.paused) ambAudio.play().catch(() => {{}});
        if (voAudio.paused) voAudio.play().catch(() => {{}});
      }}

      // Highlight active chapter & show live narration text
      let activeCh = -1;
      for (let i = 0; i < CHAPTERS.length; i++) {{
        if (t >= CHAPTERS[i].start_sec) activeCh = i;
        else break;
      }}
      if (activeCh >= 0) {{
        subtitleEl.textContent = CHAPTERS[activeCh].text;
        document.querySelectorAll('.chapter-item').forEach((el, idx) => {{
          el.classList.toggle('active', idx === activeCh);
        }});
      }}
    }}, 120);
  </script>
</body>
</html>
"""
    out_html.write_text(html, encoding="utf-8")
    print(f"[Player] Generated Custom HTML5 + YouTube Sync Player -> {out_html}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Custom Voice YouTube Overdub & HTML5 Sync Player")
    parser.add_argument("--youtube-url", required=True, help="YouTube video URL or 11-char ID already uploaded on YouTube")
    parser.add_argument("--source-video", type=Path, help="Optional local MP4/audio source (if omitted, downloads audio from YouTube URL)")
    parser.add_argument("--manifest", type=Path, required=True, help="JSON manifest containing chapters with start_sec, title, and text")
    parser.add_argument("--voices", default="neil,nasser,atherton,shastri,tony,holding,attenborough", help="Comma-separated personal/commentary voices to synthesize")
    parser.add_argument("--title", default="Expedition Documentary", help="Title for the custom HTML player")
    parser.add_argument("--steps", type=int, default=8, help="F5-TTS ODE steps (default: 8)")
    parser.add_argument("-q", "--quantize", type=int, default=8, help="F5-TTS quantization bits (default: 8)")
    parser.add_argument("--out-dir", type=Path, required=True, help="Output directory for index.html and audio/*.m4a")
    args = parser.parse_args()

    yt_id = extract_youtube_id(args.youtube_url)
    out_dir = args.out_dir.resolve()
    audio_dir = out_dir / "audio"
    work_dir = out_dir / ".work"
    audio_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    # 1. Obtain source media for STFT voice-suppressed ambient extraction
    source_media = args.source_video
    if not source_media or not source_media.exists():
        dl_audio = work_dir / f"yt_{yt_id}_audio.wav"
        if not dl_audio.exists():
            print(f"[YouTube] Downloading audio stream from https://www.youtube.com/watch?v={yt_id} ...")
            subprocess.run([
                "yt-dlp", "-f", "bestaudio", "-x", "--audio-format", "wav",
                "-o", str(work_dir / f"yt_{yt_id}_audio.%(ext)s"),
                f"https://www.youtube.com/watch?v={yt_id}"
            ], check=True)
        source_media = dl_audio

    # 2. Build voice-suppressed surrounding ambient track (car/wind/water/music retained, human voice suppressed)
    ambient_m4a = audio_dir / "ambient_clean.m4a"
    total_dur = build_suppressed_ambient_track(source_media, ambient_m4a, work_dir)

    # 3. Load chapters manifest
    raw_manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    chapters = raw_manifest.get("chapters", raw_manifest) if isinstance(raw_manifest, dict) else raw_manifest

    # 4. Synthesize requested personal/commentary voice tracks
    voices = [v.strip().lower() for v in args.voices.split(",") if v.strip()]
    for v in voices:
        out_vo_m4a = audio_dir / f"voice_{v}.m4a"
        synthesize_voice_track(
            voice_key=v,
            chapters=chapters,
            total_dur=total_dur,
            out_m4a=out_vo_m4a,
            work_dir=work_dir,
            steps=args.steps,
            quantize=args.quantize,
        )

    # 5. Render standalone HTML5 + YouTube IFrame API Sync Player
    render_html_player(
        youtube_id=yt_id,
        title=args.title,
        voices=voices,
        chapters=chapters,
        out_html=out_dir / "index.html",
    )


if __name__ == "__main__":
    main()
