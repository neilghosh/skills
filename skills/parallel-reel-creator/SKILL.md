---
name: parallel-reel-creator
description: >-
  Creates Instagram-ready 9:16 vertical Reels (1080x1920) combining a YouTube reference video
  and a local video recording (e.g. GoPro, phone camera). Supports sequential comparison mode
  (reference plays while recreation is still, then recreation plays while reference is still),
  simultaneous side-by-side or stacked playback, custom timestamp slicing, and flexible audio routing.
  Use whenever the user wants to make a split-screen or comparison reel from YouTube and a local video file.
---

# Parallel Reel Creator

Creates polished, Instagram-ready 9:16 vertical Reels (1080×1920) pairing a YouTube reference video with a local recording (such as a GoPro clip or smartphone footage).

## Key Features

1. **Sequential Freeze-Frame Mode (`--mode sequential` - Default):**
   - **Phase 1:** The YouTube reference clip plays for $T_1$ seconds while the local video remains frozen on its first frame.
   - **Phase 2:** The local video plays for $T_2$ seconds while the YouTube video stays frozen on its last frame.
   - Ideal for recreation, parody, dance-cover, or side-by-side comparison Reels.

2. **Simultaneous Mode (`--mode simultaneous`):**
   - Both the YouTube clip and the local video play side-by-side or top/bottom at the exact same time.

3. **Instagram Reel Standards:**
   - Exact **1080×1920** canvas (9:16 aspect ratio).
   - Strict **SAR 1:1** (square pixels) to eliminate distortion across mobile devices.
   - 30 fps progressive H.264 (libx264) + AAC audio with high compatibility for Instagram, TikTok, and YouTube Shorts.
   - Centered letterboxing/pillarboxing so wide or square angles are not stretched or cropped.

4. **Automated YouTube Clip Extraction:**
   - Direct segment download via `yt-dlp` using exact start and end timestamps (saves bandwidth and storage).

---

## Tooling Requirements

The skill utilizes:
- `yt-dlp` (for YouTube snippet extraction)
- `ffmpeg` & `ffprobe` (for video analysis, trimming, filter-graph compositing, and encoding)
- Python 3 (standard library only)

All tools are pre-configured and detected automatically from `/opt/homebrew/bin/` or standard paths.

---

## Script Location

The automated helper script is located at:
`scripts/create_reel.py` (relative to the skill directory, or `~/.gemini/config/skills/parallel-reel-creator/scripts/create_reel.py` when installed globally).

---

## CLI Options & Usage

```bash
python3 <skill_dir>/scripts/create_reel.py \
  --yt "<YOUTUBE_URL_OR_LOCAL_FILE>" \
  --local "<PATH_TO_LOCAL_VIDEO>" \
  --output "<OUTPUT_MP4_PATH>" \
  [OPTIONS]
```

### Options

| Flag | Description | Default |
| :--- | :--- | :--- |
| `--yt` | YouTube URL (e.g. `https://youtube.com/watch?v=...`) or path to a local reference video. | *Required* |
| `--local` | Absolute path to local recording (e.g. `/Users/.../GX011654.mov`). | *Required* |
| `--output` | Destination path for the `.mp4` file. | `instagram_reel.mp4` |
| `--yt-start` | YouTube clip start timestamp (seconds or `MM:SS` / `HH:MM:SS`). | `00:00:00` |
| `--yt-end` | YouTube clip end timestamp (e.g. `13` or `00:00:13`). | `None` (full clip) |
| `--local-start`| Local video start timestamp. | `00:00:00` |
| `--local-end` | Local video end timestamp. | `None` (full video) |
| `--mode` | `sequential` (A plays, then B plays) or `simultaneous` (both play together). | `sequential` |
| `--audio` | Audio configuration: `sequential`, `yt_full`, `yt_loop`, `local_full`, `mix`, `local`, `mute`. | `sequential` |
| `--layout` | `stack` (Top/Bottom, 1080x960 each) or `side_by_side` (Left/Right, 540x1920 each). | `stack` |
| `--fps` | Output framerate. | `30` |

---

## Audio Routing Modes

- `sequential` (Default): Plays YouTube audio during Phase 1, then switches to the local video's audio during Phase 2.
- `yt_full`: Plays the YouTube soundtrack continuously across both phases (ideal when the recreation was choreographed to the original song).
- `yt_loop`: Loops the short snippet of YouTube audio across both phases.
- `local_full`: Uses the local video audio for the entire reel.
- `mix`: Mixes both audio streams together (for simultaneous mode).
- `mute`: Generates a silent video (useful when adding trending audio directly inside the Instagram app).

---

## Step-by-Step Procedure for the Agent

When a user requests creating a reel from a YouTube video and a local file:

1. **Parse User Inputs:**
   - Extract the YouTube URL and local video path.
   - Identify timestamps or durations (e.g., "first 13 seconds" or "from 1:05 to 1:20").
   - Determine playback preference (sequential vs. simultaneous) and audio behavior.

2. **Execute the Reel Creator:**
   Run the CLI script:
   ```bash
   python3 <skill_dir>/scripts/create_reel.py \
     --yt "<URL>" \
     --local "<PATH_TO_LOCAL_FILE>" \
     --yt-start <START> \
     --yt-end <END> \
     --local-start <LOCAL_START> \
     --local-end <LOCAL_END> \
     --mode sequential \
     --audio sequential \
     --output "<OUTPUT_PATH>"
   ```

3. **Verify Output:**
   - Confirm file exists and inspect duration using `ffprobe`.
   - View generated preview thumbnails (`<name>_part1_preview.jpg` and `<name>_part2_preview.jpg`) using `view_file` to confirm visual framing and alignment.

4. **Deliver to User:**
   - Provide clickable github markdown file links (`file://...`) to the output MP4 and preview images.
   - Mention the layout, duration, and audio setup.
