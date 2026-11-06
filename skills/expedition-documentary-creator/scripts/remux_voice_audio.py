#!/usr/bin/env python3
"""
Fast Audio-Only Documentary Remuxer (Zero Video Re-encoding)
------------------------------------------------------------
Re-synthesizes documentary voiceover narration using /Users/neilghosh/devtools/voice
(F5-TTS MLX + 48kHz studio vocal exciter), mixes it with cached voice-suppressed
GoPro ambient audio to match the exact frame durations of existing video segments,
and remuxes with `-c:v copy` in seconds.
"""

import os
import sys
import json
import hashlib
import argparse
import subprocess
import numpy as np

VIDEO_DIR = '/Users/neilghosh/dev/video'
sys.path.insert(0, VIDEO_DIR)

from voice_suppressor import extract_stereo_audio, suppress_voice_keep_ambient
import map_telemetry_hud as mth
import build_sample_doc as bsd

DEVTOOLS_VOICE_PYTHON = '/Users/neilghosh/devtools/voice/.venv/bin/python'
F5_BATCH_SCRIPT = '/Users/neilghosh/dev/skills/skills/expedition-documentary-creator/scripts/f5_batch_synth.py'
WORK_DIR = '/Users/neilghosh/dev/video/work/segments_v4'
SR = 48000


def get_video_duration(mp4_path):
    out = subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', mp4_path
    ]).decode('utf-8').strip()
    return float(out)


def load_wav_48k_stereo(wav_path, target_max_dur=None, sr=SR):
    cmd = ['ffmpeg', '-y', '-v', 'error', '-i', wav_path, '-ar', str(sr), '-ac', '2', '-f', 'f32le', '-']
    raw = subprocess.check_output(cmd)
    audio = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2)
    mono_abs = np.max(np.abs(audio), axis=1)
    active = np.where(mono_abs > 0.005)[0]
    if len(active) > 0:
        s = max(0, active[0] - int(0.03 * sr))
        e = min(len(audio), active[-1] + int(0.06 * sr))
        audio = audio[s:e]

    # If the cloned voiceover is longer than (target_max_dur - 0.50s), gently speed-fit via atempo
    if target_max_dur is not None:
        max_allowed = max(1.5, target_max_dur - 0.50)
        cur_dur = len(audio) / sr
        if cur_dur > max_allowed:
            tempo = min(1.38, max(1.01, cur_dur / max_allowed))
            p = subprocess.Popen(
                ['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(sr), '-ac', '2', '-i', '-',
                 '-af', f'atempo={tempo:.4f}', '-f', 'f32le', '-ar', str(sr), '-ac', '2', '-'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE
            )
            out_bytes, _ = p.communicate(input=audio.astype(np.float32).tobytes())
            audio = np.frombuffer(out_bytes, dtype=np.float32).reshape(-1, 2)

    peak = np.max(np.abs(audio)) + 1e-8
    return audio * (0.80 / peak)


def ensure_ambient_cache(work_dir):
    amb_cache_dir = os.path.join(work_dir, 'ambient_cache')
    os.makedirs(amb_cache_dir, exist_ok=True)

    breeze_npy = os.path.join(amb_cache_dir, 'breeze_clean.npy')
    if os.path.exists(breeze_npy):
        breeze_clean = np.load(breeze_npy, allow_pickle=True)
    else:
        breeze_raw = extract_stereo_audio(os.path.join(bsd.GOPRO_DIR, bsd.SHOTS[7][0]), sr=SR, start=2.0, duration=12.0)
        breeze_clean = suppress_voice_keep_ambient(breeze_raw, sr=SR)
        np.save(breeze_npy, breeze_clean)

    ambient_cache = []
    for idx, (fname, start, base_dur, _, _) in enumerate(bsd.SHOTS):
        in_path = os.path.join(bsd.GOPRO_DIR, fname)
        amb_npy = os.path.join(amb_cache_dir, f'amb_{fname}_{start:.1f}_{base_dur:.1f}.npy')
        if os.path.exists(amb_npy):
            clean_amb = np.load(amb_npy, allow_pickle=True)
        else:
            raw_audio = extract_stereo_audio(in_path, sr=SR, start=start, duration=base_dur + 4.5)
            clean_amb = suppress_voice_keep_ambient(raw_audio, sr=SR)
            np.save(amb_npy, clean_amb)
        ambient_cache.append(clean_amb)

    return breeze_clean, ambient_cache


def remux_for_voice(voice_preset, ref_audio, out_mp4, steps=8, q_bits=8, base_seg_tag='en-US-AndrewMultilingualNeural', overwrite_tts=False):
    os.makedirs(WORK_DIR, exist_ok=True)
    cache_dir = os.path.join(WORK_DIR, 'tts_cache')
    os.makedirs(cache_dir, exist_ok=True)

    breeze_clean, ambient_cache = ensure_ambient_cache(WORK_DIR)

    shot_texts = [s[4] for s in bsd.SHOTS]
    chap_texts = [c['narration'] for c in mth.CHAPTERS]
    all_texts = shot_texts + chap_texts

    batch_items = []
    wav_paths = []
    for text in all_texts:
        h = hashlib.sha1(f"{voice_preset}:{steps}:{q_bits}:{ref_audio}:{text.strip()}".encode('utf-8')).hexdigest()[:14]
        out_wav = os.path.join(cache_dir, f'f5_{voice_preset}_{h}.wav')
        wav_paths.append(out_wav)
        batch_items.append({'text': text, 'output': out_wav})

    batch_json_path = os.path.join(cache_dir, f'batch_{voice_preset}.json')
    with open(batch_json_path, 'w') as f:
        json.dump(batch_items, f, indent=2)

    cmd = [
        DEVTOOLS_VOICE_PYTHON, F5_BATCH_SCRIPT,
        '--batch-json', batch_json_path,
        '--voice', voice_preset,
        '--steps', str(steps),
        '-q', str(q_bits),
    ]
    if ref_audio:
        cmd.extend(['--ref-audio', ref_audio])
    if overwrite_tts:
        cmd.append('--overwrite')

    subprocess.run(cmd, check=True)

    chap_by_shot = {c['before_shot']: (c_idx, c) for c_idx, c in enumerate(mth.CHAPTERS)}
    seg_files = []

    for idx, (fname, _, _, loc_label, _) in enumerate(bsd.SHOTS):
        if idx in chap_by_shot:
            c_idx, chap_dict = chap_by_shot[idx]
            base_chap_mp4 = os.path.join(WORK_DIR, f'chap_{base_seg_tag}_{c_idx:02d}.mp4')
            vid_dur = get_video_duration(base_chap_mp4)
            chap_narr = load_wav_48k_stereo(wav_paths[len(bsd.SHOTS) + c_idx], target_max_dur=vid_dur, sr=SR)

            target_samples = int(round(vid_dur * SR))
            chap_amb = breeze_clean[:target_samples].copy()
            if len(chap_amb) < target_samples:
                chap_amb = np.pad(chap_amb, ((0, target_samples - len(chap_amb)), (0, 0)), mode='reflect')

            chap_mix = bsd.mix_ambient_and_narration(chap_amb, chap_narr, sr=SR, target_ambient_rms=0.032, fade_sec=0.35)
            chap_wav = os.path.join(WORK_DIR, f'chap_{voice_preset}_{c_idx:02d}.wav')
            chap_mp4 = os.path.join(WORK_DIR, f'chap_{voice_preset}_{c_idx:02d}.mp4')

            p = subprocess.Popen(
                ['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', chap_wav],
                stdin=subprocess.PIPE
            )
            p.communicate(input=chap_mix.astype(np.float32).tobytes())

            subprocess.run([
                'ffmpeg', '-y', '-v', 'error',
                '-i', base_chap_mp4, '-i', chap_wav,
                '-map', '0:v:0', '-map', '1:a:0',
                '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                '-shortest', chap_mp4
            ], check=True)
            print(f'  [Remux Chapter {c_idx+1}] {chap_dict["title"]} ({vid_dur:.2f}s, -c:v copy)')
            seg_files.append(chap_mp4)

        base_seg_mp4 = os.path.join(WORK_DIR, f'seg_{base_seg_tag}_{idx:02d}.mp4')
        vid_dur = get_video_duration(base_seg_mp4)
        narr_audio = load_wav_48k_stereo(wav_paths[idx], target_max_dur=vid_dur, sr=SR)

        target_samples = int(round(vid_dur * SR))
        clean_ambient = ambient_cache[idx]
        if len(clean_ambient) < target_samples:
            clean_ambient = np.pad(clean_ambient, ((0, target_samples - len(clean_ambient)), (0, 0)), mode='reflect')
        else:
            clean_ambient = clean_ambient[:target_samples]

        final_audio = bsd.mix_ambient_and_narration(clean_ambient, narr_audio, sr=SR, target_ambient_rms=0.046, fade_sec=0.35)
        wav_path = os.path.join(WORK_DIR, f'seg_{voice_preset}_{idx:02d}.wav')
        seg_out = os.path.join(WORK_DIR, f'seg_{voice_preset}_{idx:02d}.mp4')

        p = subprocess.Popen(
            ['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', wav_path],
            stdin=subprocess.PIPE
        )
        p.communicate(input=final_audio.astype(np.float32).tobytes())

        subprocess.run([
            'ffmpeg', '-y', '-v', 'error',
            '-i', base_seg_mp4, '-i', wav_path,
            '-map', '0:v:0', '-map', '1:a:0',
            '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
            '-shortest', seg_out
        ], check=True)
        print(f'[{idx+1}/{len(bsd.SHOTS)}] Remuxed {fname} ({vid_dur:.2f}s, -c:v copy) | {loc_label}')
        seg_files.append(seg_out)

    list_file = os.path.join(WORK_DIR, f'concat_{voice_preset}.txt')
    with open(list_file, 'w') as f:
        for s in seg_files:
            f.write(f"file '{s}'\n")

    subprocess.run([
        'ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0',
        '-i', list_file, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
        '-movflags', '+faststart', out_mp4
    ], check=True)
    print(f'Successfully remuxed audio-only documentary: {out_mp4}')


def main():
    parser = argparse.ArgumentParser(description='Remux existing documentary video segments with new cloned voice audio')
    parser.add_argument('--voice', required=True, help='Preset name: neil, tony, atherton, etc.')
    parser.add_argument('--ref-audio', default=None, help='Optional reference WAV path override')
    parser.add_argument('--output', required=True, help='Output MP4 path')
    parser.add_argument('--steps', type=int, default=8, help='RK4 ODE steps (default: 8 = 32 NFEs)')
    parser.add_argument('-q', '--quantization-bits', type=int, default=8, help='Quantization bits (default: 8)')
    parser.add_argument('--overwrite-tts', action='store_true', help='Force re-synthesis of TTS segments')
    args = parser.parse_args()

    remux_for_voice(
        voice_preset=args.voice,
        ref_audio=args.ref_audio,
        out_mp4=args.output,
        steps=args.steps,
        q_bits=args.quantization_bits,
        overwrite_tts=args.overwrite_tts,
    )


if __name__ == '__main__':
    main()
