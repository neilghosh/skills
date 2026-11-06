#!/usr/bin/env python3
"""
Zero-Token Automated Shot Discovery & Human-Face Filter
-------------------------------------------------------
Scans a folder of raw GoPro / action-cam / travel videos, evaluates candidate windows
locally using YCbCr skin-cluster rejection + Sobel sharpness + color richness, and
outputs:
  1. A declarative JSON manifest (--out-manifest) of the best landscape/driving shots
  2. A single composite contact sheet (--out-preview) so verification takes at most 1 image read.
"""

import os
import re
import json
import argparse
import subprocess
import numpy as np
from PIL import Image, ImageDraw


def probe_clip(path):
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration:format_tags=creation_time,location,com.apple.quicktime.location.iso6709',
        '-of', 'json', path
    ]
    try:
        info = json.loads(subprocess.check_output(cmd))
        fmt = info.get('format', {})
        dur = float(fmt.get('duration', 0.0))
        tags = fmt.get('tags', {}) or {}
        loc_raw = tags.get('location') or tags.get('com.apple.quicktime.location.iso6709') or ''
        lat, lon = None, None
        m = re.match(r'([+-]\d+\.\d+)([+-]\d+\.\d+)', loc_raw)
        if m:
            lat, lon = float(m.group(1)), float(m.group(2))
        return {'duration': dur, 'creation_time': tags.get('creation_time', ''), 'lat': lat, 'lon': lon}
    except Exception:
        return {'duration': 0.0, 'creation_time': '', 'lat': None, 'lon': None}


def score_candidate_frame(rgb_frame):
    """
    Scores a 320x180 RGB frame:
      - Penalizes central skin-tone clusters (YCbCr skin mask) to avoid human faces/bodies
      - Rewards natural landscape sharpness, foliage/sky color richness, and balanced exposure
    """
    arr = rgb_frame.astype(np.float32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    # YCbCr conversion for skin-tone cluster detection
    y = 0.299 * r + 0.587 * g + 0.114 * b
    cb = 128.0 - 0.168736 * r - 0.331264 * g + 0.5 * b
    cr = 128.0 + 0.5 * r - 0.418688 * g - 0.081312 * b

    # Focus on central/lower foreground where faces or bodies appear
    fg_cb = cb[25:165, 40:280]
    fg_cr = cr[25:165, 40:280]
    fg_y = y[25:165, 40:280]
    skin_mask = (fg_cb >= 80) & (fg_cb <= 125) & (fg_cr >= 136) & (fg_cr <= 173) & (fg_y > 45) & (fg_y < 230)
    skin_ratio = float(np.mean(skin_mask))

    if skin_ratio > 0.055:
        return -1000.0, skin_ratio

    # Sharpness (Sobel gradient magnitude)
    gx = np.abs(np.diff(y, axis=1, prepend=y[:, :1]))
    gy = np.abs(np.diff(y, axis=0, prepend=y[:1, :]))
    sharpness = float(np.mean(gx + gy))

    # Saturation & exposure balance
    cmax = np.maximum(np.maximum(r, g), b)
    cmin = np.minimum(np.minimum(r, g), b)
    sat = float(np.mean((cmax - cmin) / (cmax + 1.0)))
    mean_luma = float(np.mean(y))
    exposure_penalty = abs(mean_luma - 122.0) * 0.15

    score = sharpness * 1.4 + sat * 45.0 - exposure_penalty - (skin_ratio * 400.0)
    return score, skin_ratio


def find_best_window_in_clip(path, dur, target_dur=11.0):
    if dur < target_dur + 1.5:
        return None
    usable_end = max(1.0, dur - target_dur - 0.5)
    sample_starts = np.linspace(1.0, usable_end, num=min(3, max(1, int(usable_end // 8.0) + 1)))

    best_score = -1e9
    best_t = 0.0
    best_thumb = None

    for t0 in sample_starts:
        # Check 3 points across the window [t0, t0 + target_dur] to guarantee no people enter the shot
        check_times = [t0 + 0.5, t0 + target_dur * 0.45, t0 + target_dur * 0.85]
        win_scores = []
        mid_thumb = None
        valid_window = True
        for idx_c, tc in enumerate(check_times):
            cmd = [
                'ffmpeg', '-v', 'error', '-ss', f'{tc:.2f}', '-i', path,
                '-frames:v', '1', '-vf', 'scale=320:180', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'
            ]
            try:
                raw = subprocess.check_output(cmd)
                if len(raw) != 320 * 180 * 3:
                    valid_window = False
                    break
                frame = np.frombuffer(raw, dtype=np.uint8).reshape((180, 320, 3))
                sc, skin_r = score_candidate_frame(frame)
                if sc < 0 or skin_r > 0.032:
                    valid_window = False
                    break
                win_scores.append(sc)
                if idx_c == 1:
                    mid_thumb = frame
            except Exception:
                valid_window = False
                break

        if valid_window and win_scores and mid_thumb is not None:
            avg_sc = float(np.mean(win_scores))
            if avg_sc > best_score:
                best_score = avg_sc
                best_t = float(round(t0, 1))
                best_thumb = mid_thumb

    if best_score < 0 or best_thumb is None:
        return None
    return {'start_sec': best_t, 'score': round(best_score, 2), 'thumb': best_thumb}


def main():
    parser = argparse.ArgumentParser(description='Zero-Token Shot Discovery & Face Filter')
    parser.add_argument('--video-dir', required=True, help='Folder containing raw MP4/MOV clips')
    parser.add_argument('--max-shots', type=int, default=24, help='Number of shots to select')
    parser.add_argument('--min-clip-dur', type=float, default=13.5, help='Minimum clip duration in seconds')
    parser.add_argument('--exclude', default='', help='Comma-separated filenames to exclude')
    parser.add_argument('--out-manifest', default='manifest_auto.json', help='Output JSON manifest path')
    parser.add_argument('--out-preview', default='manifest_preview.jpg', help='Single montage preview image path')
    args = parser.parse_args()

    excl = {x.strip() for x in args.exclude.split(',') if x.strip()}
    all_files = sorted([
        f for f in os.listdir(args.video_dir)
        if f.lower().endswith(('.mp4', '.mov')) and not f.startswith('.') and f not in excl
    ])

    # Pre-filter by duration >= min_clip_dur and stratify across the journey
    long_clips = []
    for fname in all_files:
        fpath = os.path.join(args.video_dir, fname)
        meta = probe_clip(fpath)
        if meta['duration'] >= args.min_clip_dur:
            long_clips.append((fname, fpath, meta))

    # Sample up to max_shots * 2 evenly across chronological order for fast scanning
    max_scan = min(len(long_clips), max(args.max_shots * 2, 42))
    scan_indices = np.linspace(0, len(long_clips) - 1, num=max_scan, dtype=int)
    scan_list = [long_clips[i] for i in sorted(set(scan_indices))]

    candidates = []
    print(f'[Auto-Discover] Scanning {len(scan_list)} stratified clips (out of {len(long_clips)} long clips)...', flush=True)
    for fname, fpath, meta in scan_list:
        win = find_best_window_in_clip(fpath, meta['duration'], target_dur=11.0)
        if win:
            candidates.append({
                'file': fname,
                'start_sec': win['start_sec'],
                'base_dur': 11.0,
                'score': win['score'],
                'duration_total': round(meta['duration'], 2),
                'creation_time': meta['creation_time'],
                'lat': meta['lat'],
                'lon': meta['lon'],
                'thumb': win['thumb'],
            })

    # Select top max_shots while keeping chronological spread
    if len(candidates) > args.max_shots:
        # Divide into 4 chronological quartiles and take top from each quartile
        q_size = max(1, len(candidates) // 4)
        per_q = args.max_shots // 4
        selected = []
        for q in range(4):
            sl = candidates[q * q_size : (q + 1) * q_size if q < 3 else len(candidates)]
            sl_top = sorted(sl, key=lambda x: x['score'], reverse=True)[:per_q + 2]
            selected.extend(sl_top)
        top = sorted(selected, key=lambda x: x['score'], reverse=True)[:args.max_shots]
    else:
        top = candidates[:args.max_shots]
    top_chrono = sorted(top, key=lambda x: x['file'])

    # Save 1 single composite contact sheet for 1-call visual verification
    cols = 4
    rows = max(1, (len(top_chrono) + cols - 1) // cols)
    grid = Image.new('RGB', (cols * 320, rows * 180), (12, 16, 20))
    draw = ImageDraw.Draw(grid)
    for idx, item in enumerate(top_chrono):
        r_i, c_i = divmod(idx, cols)
        im = Image.fromarray(item['thumb'])
        grid.paste(im, (c_i * 320, r_i * 180))
        draw.rectangle([c_i * 320, r_i * 180, c_i * 320 + 235, r_i * 180 + 22], fill=(0, 0, 0))
        draw.text((c_i * 320 + 6, r_i * 180 + 4), f"#{idx+1:02d} {item['file']} @{item['start_sec']}s", fill=(255, 220, 80))
        del item['thumb']

    grid.save(args.out_preview, quality=88)

    manifest = {
        'video_dir': args.video_dir,
        'shots': top_chrono,
    }
    with open(args.out_manifest, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f'[Auto-Discover] Selected {len(top_chrono)} clean shots -> {args.out_manifest}')
    print(f'[Auto-Discover] Saved single-read contact sheet -> {args.out_preview}')


if __name__ == '__main__':
    main()
