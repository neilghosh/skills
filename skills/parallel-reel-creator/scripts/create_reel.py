#!/usr/bin/env python3
"""
Parallel Reel Creator
Creates Instagram-ready 9:16 (1080x1920) vertical videos combining a YouTube reference
and a local video file (e.g. GoPro, phone camera). Supports sequential freeze-frame
comparisons ("original plays while recreation is still, then recreation plays while original is still")
as well as simultaneous side-by-side/stacked playback.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def find_tool(name):
    path = shutil.which(name)
    if path:
        return path
    brew_path = f"/opt/homebrew/bin/{name}"
    if os.path.isfile(brew_path) and os.access(brew_path, os.X_OK):
        return brew_path
    usr_local = f"/usr/local/bin/{name}"
    if os.path.isfile(usr_local) and os.access(usr_local, os.X_OK):
        return usr_local
    return None


FFMPEG = find_tool("ffmpeg")
FFPROBE = find_tool("ffprobe")
YT_DLP = find_tool("yt-dlp")


def parse_timestamp(ts):
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        return float(ts)
    ts = str(ts).strip()
    if not ts:
        return None
    parts = ts.split(":")
    if len(parts) == 1:
        return float(parts[0])
    if len(parts) == 2:
        return float(parts[0]) * 60 + float(parts[1])
    if len(parts) == 3:
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    raise ValueError(f"Invalid timestamp format: {ts}")


def format_seconds(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def get_video_info(file_path):
    cmd = [
        FFPROBE,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(res.stdout)
    video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    duration = float(data.get("format", {}).get("duration", 0.0))
    if duration == 0.0 and video_stream:
        duration = float(video_stream.get("duration", 0.0))
    return {
        "duration": duration,
        "has_audio": audio_stream is not None,
        "width": int(video_stream.get("width", 0)) if video_stream else 0,
        "height": int(video_stream.get("height", 0)) if video_stream else 0,
    }


def download_youtube_clip(url, start_sec, end_sec, work_dir):
    out_template = str(work_dir / "yt_clip.%(ext)s")
    sec_arg = f"*{start_sec:.2f}-{end_sec:.2f}"
    cmd = [
        YT_DLP,
        "--download-sections", sec_arg,
        "--ffmpeg-location", FFMPEG,
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "-o", out_template,
        url
    ]
    print(f"[*] Downloading YouTube snippet ({start_sec}s -> {end_sec}s)...")
    subprocess.run(cmd, check=True)
    for p in work_dir.glob("yt_clip.*"):
        if p.is_file() and not p.name.endswith(".part"):
            return str(p)
    raise FileNotFoundError("Could not find downloaded YouTube clip.")


def build_reel(
    yt_input,
    local_input,
    output_path,
    yt_start=0.0,
    yt_end=None,
    local_start=0.0,
    local_end=None,
    mode="sequential",
    audio_mode="sequential",
    layout="stack",
    fps=30,
    work_dir=None,
    generate_previews=True
):
    if not FFMPEG:
        raise RuntimeError("ffmpeg not found in PATH or standard directories.")
    if not FFPROBE:
        raise RuntimeError("ffprobe not found in PATH or standard directories.")

    work_dir = Path(work_dir) if work_dir else Path(os.getcwd())
    work_dir.mkdir(parents=True, exist_ok=True)
    temp_download = False

    if yt_input.startswith("http://") or yt_input.startswith("https://"):
        if not YT_DLP:
            raise RuntimeError("yt-dlp is required to download YouTube videos.")
        yt_end_time = yt_end if yt_end is not None else 13.0
        yt_file = download_youtube_clip(yt_input, yt_start, yt_end_time, work_dir)
        temp_download = True
        actual_yt_start = 0.0
        actual_yt_duration = yt_end_time - yt_start
    else:
        yt_file = yt_input
        actual_yt_start = yt_start
        yt_info = get_video_info(yt_file)
        if yt_end is not None:
            actual_yt_duration = yt_end - yt_start
        else:
            actual_yt_duration = yt_info["duration"] - yt_start

    local_info = get_video_info(local_input)
    if local_end is not None:
        actual_local_duration = local_end - local_start
    else:
        actual_local_duration = local_info["duration"] - local_start

    print(f"[*] YouTube clip segment duration: {actual_yt_duration:.2f}s")
    print(f"[*] Local video segment duration: {actual_local_duration:.2f}s")

    out_p = Path(output_path).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)

    filter_complex = []
    
    # Dimensions for Instagram Reel: 1080x1920 (9:16)
    if layout == "stack":
        box_w, box_h = 1080, 960
    else:  # side_by_side
        box_w, box_h = 540, 1920

    scale_pad_filter = (
        f"scale={box_w}:{box_h}:force_original_aspect_ratio=decrease,"
        f"pad={box_w}:{box_h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1"
    )

    if mode == "sequential":
        t1 = actual_yt_duration
        t2 = actual_local_duration

        # Stream 0 (YouTube): plays for t1, freezes last frame for t2
        top_filter = (
            f"[0:v]fps={fps},trim=start={actual_yt_start}:duration={t1},setpts=PTS-STARTPTS,"
            f"{scale_pad_filter},tpad=stop_mode=clone:stop_duration={t2}[v0]"
        )
        # Stream 1 (Local): freezes first frame for t1, plays for t2
        bottom_filter = (
            f"[1:v]fps={fps},trim=start={local_start}:duration={t2},setpts=PTS-STARTPTS,"
            f"{scale_pad_filter},tpad=start_mode=clone:start_duration={t1}[v1]"
        )
        filter_complex.extend([top_filter, bottom_filter])

        if layout == "stack":
            filter_complex.append("[v0][v1]vstack[v]")
        else:
            filter_complex.append("[v0][v1]hstack[v]")

        # Audio routing
        if audio_mode == "sequential":
            # YT audio for t1, Local audio for t2
            filter_complex.extend([
                f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=start={actual_yt_start}:duration={t1},asetpts=PTS-STARTPTS[a0]",
                f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=start={local_start}:duration={t2},asetpts=PTS-STARTPTS[a1]",
                "[a0][a1]concat=n=2:v=0:a=1[a]"
            ])
        elif audio_mode == "yt_full":
            # Continuous YouTube audio for t1+t2
            filter_complex.append(
                f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=start={actual_yt_start}:duration={t1+t2},asetpts=PTS-STARTPTS[a]"
            )
        elif audio_mode == "yt_loop":
            # YT audio from segment 1 looped
            filter_complex.extend([
                f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=start={actual_yt_start}:duration={t1},asetpts=PTS-STARTPTS[a0]",
                "[a0]aloop=loop=-1:size=2e+09,atrim=duration={t1+t2}[a]"
            ])
        elif audio_mode == "local_full":
            # Local audio played throughout
            filter_complex.append(
                f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=start={local_start}:duration={t1+t2},asetpts=PTS-STARTPTS[a]"
            )
        elif audio_mode == "mute":
            filter_complex.append(f"anullsrc=channel_layout=stereo:sample_rate=48000:duration={t1+t2}[a]")
        else:
            filter_complex.extend([
                f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=start={actual_yt_start}:duration={t1},asetpts=PTS-STARTPTS[a0]",
                f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=start={local_start}:duration={t2},asetpts=PTS-STARTPTS[a1]",
                "[a0][a1]concat=n=2:v=0:a=1[a]"
            ])

    else:  # simultaneous
        sim_duration = min(actual_yt_duration, actual_local_duration)
        top_filter = (
            f"[0:v]fps={fps},trim=start={actual_yt_start}:duration={sim_duration},setpts=PTS-STARTPTS,"
            f"{scale_pad_filter}[v0]"
        )
        bottom_filter = (
            f"[1:v]fps={fps},trim=start={local_start}:duration={sim_duration},setpts=PTS-STARTPTS,"
            f"{scale_pad_filter}[v1]"
        )
        filter_complex.extend([top_filter, bottom_filter])

        if layout == "stack":
            filter_complex.append("[v0][v1]vstack[v]")
        else:
            filter_complex.append("[v0][v1]hstack[v]")

        if audio_mode == "local":
            filter_complex.append(
                f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=start={local_start}:duration={sim_duration},asetpts=PTS-STARTPTS[a]"
            )
        elif audio_mode == "mix":
            filter_complex.extend([
                f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=start={actual_yt_start}:duration={sim_duration},asetpts=PTS-STARTPTS[a0]",
                f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=start={local_start}:duration={sim_duration},asetpts=PTS-STARTPTS[a1]",
                "[a0][a1]amix=inputs=2:duration=first[a]"
            ])
        else:  # default yt
            filter_complex.append(
                f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=start={actual_yt_start}:duration={sim_duration},asetpts=PTS-STARTPTS[a]"
            )

    cmd = [
        FFMPEG, "-y",
        "-i", yt_file,
        "-i", local_input,
        "-filter_complex", "; ".join(filter_complex),
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        str(out_p)
    ]

    print(f"[*] Rendering Instagram Reel ({mode} mode, {layout} layout)...")
    subprocess.run(cmd, check=True)
    print(f"[✓] Created Reel: {out_p}")

    if generate_previews and mode == "sequential":
        p1 = out_p.parent / f"{out_p.stem}_part1_preview.jpg"
        p2 = out_p.parent / f"{out_p.stem}_part2_preview.jpg"
        t_preview1 = max(1.0, t1 / 2.0)
        t_preview2 = t1 + max(1.0, t2 / 2.0)
        subprocess.run([
            FFMPEG, "-y", "-ss", str(t_preview1), "-i", str(out_p),
            "-vframes", "1", str(p1)
        ], capture_output=True)
        subprocess.run([
            FFMPEG, "-y", "-ss", str(t_preview2), "-i", str(out_p),
            "-vframes", "1", str(p2)
        ], capture_output=True)
        print(f"[✓] Generated previews:\n    - {p1}\n    - {p2}")

    return str(out_p)


def main():
    parser = argparse.ArgumentParser(
        description="Parallel Reel Creator: Convert YouTube & Local Video into 9:16 Instagram Reel"
    )
    parser.add_argument("--yt", required=True, help="YouTube video URL or local file path")
    parser.add_argument("--local", required=True, help="Path to local video file (e.g. GoPro .mov or phone clip)")
    parser.add_argument("--output", default="instagram_reel.mp4", help="Path for output mp4 (default: instagram_reel.mp4)")
    parser.add_argument("--yt-start", default="00:00:00", help="YouTube start timestamp (e.g. 0, 0:05, 00:01:20)")
    parser.add_argument("--yt-end", default=None, help="YouTube end timestamp (e.g. 13, 0:13, 00:00:13)")
    parser.add_argument("--local-start", default="00:00:00", help="Local video start timestamp")
    parser.add_argument("--local-end", default=None, help="Local video end timestamp")
    parser.add_argument(
        "--mode",
        choices=["sequential", "simultaneous"],
        default="sequential",
        help="Playback mode: 'sequential' (A plays with B still, then B plays with A still) or 'simultaneous'"
    )
    parser.add_argument(
        "--audio",
        choices=["sequential", "yt_full", "yt_loop", "local_full", "mix", "local", "mute"],
        default="sequential",
        help="Audio mode: 'sequential', 'yt_full', 'yt_loop', 'local_full', 'mix', 'mute'"
    )
    parser.add_argument(
        "--layout",
        choices=["stack", "side_by_side"],
        default="stack",
        help="Visual arrangement: 'stack' (top/bottom) or 'side_by_side' (left/right)"
    )
    parser.add_argument("--fps", type=int, default=30, help="Output framerate (default 30)")
    parser.add_argument("--work-dir", default=None, help="Working directory for temporary downloads")

    args = parser.parse_args()

    yt_start_sec = parse_timestamp(args.yt_start)
    yt_end_sec = parse_timestamp(args.yt_end)
    local_start_sec = parse_timestamp(args.local_start)
    local_end_sec = parse_timestamp(args.local_end)

    build_reel(
        yt_input=args.yt,
        local_input=args.local,
        output_path=args.output,
        yt_start=yt_start_sec,
        yt_end=yt_end_sec,
        local_start=local_start_sec,
        local_end=local_end_sec,
        mode=args.mode,
        audio_mode=args.audio,
        layout=args.layout,
        fps=args.fps,
        work_dir=args.work_dir
    )


if __name__ == "__main__":
    main()
