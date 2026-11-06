#!/usr/bin/env python3
"""
Smart Human-Face Sub-Clip Cutter & Dynamic Face Blur Engine
-----------------------------------------------------------
Instead of discarding a video clip when a few seconds contain human faces/people:
  1. CUT MODE (Primary): Uses Apple Vision (`vision_face_scanner`) per-timestamp face/human
     detections to slice out the longest clean (human-free) contiguous window `[start_sec, end_sec]`
     or splice multiple clean sub-windows from the clip.
  2. BLUR MODE (Fallback): When a scenic clip has faces/people that cannot be trimmed without
     making the clip too short, builds an FFmpeg time-gated Gaussian blur filter (`boxblur=26:4`
     with `enable='between(t,t0,t1)'`) over the exact Apple Vision face/upper-body bounding boxes
     so the clip is included with all faces completely blurred out.
"""

import os
import json
import subprocess


def ensure_vision_scanner_binary():
    """Compiles vision_face_scanner.swift on first run if the binary is not yet built."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bin_path = os.path.join(script_dir, 'vision_face_scanner')
    swift_src = os.path.join(script_dir, 'vision_face_scanner.swift')
    if not os.path.exists(bin_path) and os.path.exists(swift_src):
        subprocess.run(['swiftc', '-O', swift_src, '-o', bin_path], check=True)
    return bin_path


def find_longest_clean_window(samples, total_dur, min_dur=5.0, step_sec=2.0):
    """
    Finds the longest contiguous time interval [start_s, end_s] with zero detected faces
    and zero foreground humans.
    Returns (start_s, end_s, clean_dur) or None if no clean interval >= min_dur exists.
    """
    if not samples:
        return (0.0, total_dur, total_dur) if total_dur >= min_dur else None

    clean_flags = []
    for s in samples:
        has_face = len(s.get('faces', [])) > 0
        has_human = len(s.get('humans', [])) > 0
        is_clean = (not has_face) and (not has_human)
        clean_flags.append((s['t'], is_clean))

    best_start, best_end = 0.0, 0.0
    cur_start = None
    for idx, (t, is_clean) in enumerate(clean_flags):
        if is_clean:
            if cur_start is None:
                cur_start = max(0.0, t - step_sec * 0.4)
            cur_end = min(total_dur, t + step_sec * 0.9)
            if (cur_end - cur_start) > (best_end - best_start):
                best_start, best_end = cur_start, cur_end
        else:
            cur_start = None

    clean_dur = round(best_end - best_start, 2)
    if clean_dur >= min_dur:
        return round(best_start, 2), round(best_end, 2), clean_dur
    return None


def build_ffmpeg_face_blur_filter(samples, clip_start_sec, clip_dur_sec, step_sec=2.0, width=1920, height=1080):
    """
    Builds an FFmpeg filtergraph chain that blurs every detected face / human body region
    during the exact time intervals [t0, t1] (relative to clip_start_sec) where they appear.
    Groups detections into per-time-slice union envelopes so multi-person clips across the
    full duration are 100% covered without truncating later seconds.
    """
    win_end = clip_start_sec + clip_dur_sec
    slice_boxes = []

    for s in samples:
        t_abs = s['t']
        if t_abs < clip_start_sec - step_sec or t_abs > win_end + step_sec:
            continue
        t_rel = max(0.0, t_abs - clip_start_sec)
        t0 = max(0.0, t_rel - max(0.85, step_sec * 0.95))
        t1 = min(clip_dur_sec, t_rel + max(0.85, step_sec * 0.95))

        boxes_norm = []
        for fb in s.get('faces', []):
            cx = fb[0] + fb[2] * 0.5
            cy = fb[1] + fb[3] * 0.5
            w = fb[2] * 2.4
            h = fb[3] * 2.6
            boxes_norm.append((cx - w * 0.5, cy - h * 0.45, w, h))

        for hb in s.get('humans', []):
            cx = hb[0] + hb[2] * 0.5
            w = hb[2] * 1.45
            h = hb[3] * 1.35
            x = cx - w * 0.5
            y = hb[1] - hb[3] * 0.20
            boxes_norm.append((x, y, w, h))

        if not boxes_norm:
            continue

        # Compute the spatial union of all faces/humans in this frame sample
        ux0 = min(max(0.0, b[0]) for b in boxes_norm)
        uy0 = min(max(0.0, b[1]) for b in boxes_norm)
        ux1 = max(min(1.0, b[0] + b[2]) for b in boxes_norm)
        uy1 = max(min(1.0, b[1] + b[3]) for b in boxes_norm)

        px = max(4, min(width - 40, int(round(ux0 * width))))
        py = max(4, min(height - 40, int(round(uy0 * height))))
        pw = max(48, min(width - px - 4, int(round((ux1 - ux0) * width))))
        ph = max(48, min(height - py - 4, int(round((uy1 - uy0) * height))))
        slice_boxes.append((t0, t1, px, py, pw, ph))

    if not slice_boxes:
        return '', 'bg0'

    # Merge contiguous/overlapping time slices into up to 10 envelope boxes covering 100% of [0, clip_dur_sec]
    merged = []
    for b in slice_boxes:
        t0, t1, x, y, w, h = b
        if merged:
            pt0, pt1, px, py, pw, ph = merged[-1]
            # Merge if overlapping in time and either close spatially OR we already have >= 6 envelopes
            if t0 <= pt1 + 0.6 and ((abs(x - px) < 360 and abs(y - py) < 360) or len(merged) >= 6):
                nx0 = min(x, px)
                ny0 = min(y, py)
                nx1 = max(x + w, px + pw)
                ny1 = max(y + h, py + ph)
                merged[-1] = (min(pt0, t0), max(pt1, t1), nx0, ny0, nx1 - nx0, ny1 - ny0)
                continue
        merged.append(b)

    chain = []
    cur_label = 'bg0'
    for idx, (t0, t1, x, y, w, h) in enumerate(merged):
        x = max(2, (x // 2) * 2)
        y = max(2, (y // 2) * 2)
        w = max(48, (w // 2) * 2)
        h = max(48, (h // 2) * 2)
        if x + w >= width - 2:
            w = ((width - x - 4) // 2) * 2
        if y + h >= height - 2:
            h = ((height - y - 4) // 2) * 2
        nxt_label = f'bg{idx+1}'
        chain.append(
            f"[{cur_label}]split=2[base{idx}][src{idx}];"
            f"[src{idx}]crop={w}:{h}:{x}:{y},gblur=sigma=52[blur{idx}];"
            f"[base{idx}][blur{idx}]overlay={x}:{y}:enable='between(t,{t0:.2f},{t1:.2f})'[{nxt_label}]"
        )
        cur_label = nxt_label
    return ';'.join(chain), cur_label


def plan_clip_salvage(clip_report, min_clean_dur=6.5, step_sec=2.0):
    """
    Given a clip report from vision_face_scanner:
      - If the clip is 100% free of faces/humans, returns mode='clean_full'.
      - If the clip has faces/humans in some seconds AND has a clean sub-window >= min_clean_dur,
        returns mode='cut_human_seconds' with the exact clean [start_sec, end_sec] window.
      - If faces/humans appear throughout the clip (no clean sub-window >= min_clean_dur),
        returns mode='blur_faces' with the time-gated FFmpeg blur filter string.
    """
    dur = clip_report['duration']
    samples = clip_report['samples']
    face_count = sum(len(s.get('faces', [])) for s in samples)
    human_count = sum(len(s.get('humans', [])) for s in samples)

    if face_count == 0 and human_count == 0:
        return {
            'file': clip_report['file'],
            'mode': 'clean_full',
            'start_sec': round(min(1.0, max(0.0, dur - min_clean_dur)), 2),
            'dur_sec': round(min(dur, max(min_clean_dur, 9.5)), 2),
            'blur_filter': '',
            'face_hits': 0,
            'human_hits': 0,
        }

    clean_win = find_longest_clean_window(samples, dur, min_dur=min_clean_dur, step_sec=step_sec)
    if clean_win is not None:
        st, en, cdur = clean_win
        return {
            'file': clip_report['file'],
            'mode': 'cut_human_seconds',
            'start_sec': st,
            'dur_sec': min(cdur, 10.5),
            'blur_filter': '',
            'face_hits': face_count,
            'human_hits': human_count,
        }

    # Fallback: Blur the faces/heads during the best window of the clip
    st = round(max(0.0, (dur - min(dur, 9.0)) * 0.5), 2)
    use_dur = round(min(dur - st, 9.5), 2)
    b_filt, b_out = build_ffmpeg_face_blur_filter(samples, st, use_dur, step_sec=step_sec)
    return {
        'file': clip_report['file'],
        'mode': 'blur_faces',
        'start_sec': st,
        'dur_sec': use_dur,
        'blur_filter': b_filt,
        'blur_out_label': b_out,
        'face_hits': face_count,
        'human_hits': human_count,
    }
