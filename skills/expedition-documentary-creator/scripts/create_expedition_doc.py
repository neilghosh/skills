#!/usr/bin/env python3
"""
Expedition Documentary Creator CLI (Low-Token Batch & Multi-Voice Engine)
-------------------------------------------------------------------------
Integrates directly with voices (`voice-clone` / F5-TTS MLX)
when instructed with preset names:
  - primary                     -> voices/primary_clean.wav
  - narrator_uk / narrator_uk_alt      -> voices/narrator_uk_clean.wav (Mike NarratorUK / Bumble)
  - tony / narrator classic        -> voices/narrator_classic_clean.wav (Classic Narrator)
  - tony_alt                 -> voices/narrator_classic_clean_alt.wav
Also supports Edge-TTS neural voices (en-US-AndrewMultilingualNeural, en-GB-RyanNeural).

Caches all cleaned GoPro ambient audio, Esri 3-layer Hybrid Satellite tiles, HUD cards,
and SHA-1 hashed voiceover WAVs on disk for near-zero-cost batch video generation.
"""

import os
import sys
import json
import hashlib
import argparse
import subprocess
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from voice_suppressor import extract_stereo_audio, suppress_voice_keep_ambient
import map_telemetry_hud as mth
import build_sample_doc as bsd

DEVTOOLS_VOICE_PYTHON = 'python3'
F5_BATCH_SCRIPT = os.path.join(SCRIPT_DIR, 'f5_batch_synth.py')

F5_VOICE_ALIASES = {
    'odia': 'odia',
    'oriya': 'odia',
}


def resolve_f5_preset(voice_str):
    norm = voice_str.strip().lower().replace('-', '_').replace(' ', '_')
    return F5_VOICE_ALIASES.get(norm)


def load_wav_48k_stereo(wav_path, sr=48000):
    cmd = ['ffmpeg', '-y', '-v', 'error', '-i', wav_path, '-ar', str(sr), '-ac', '2', '-f', 'f32le', '-']
    raw = subprocess.check_output(cmd)
    audio = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2)
    mono_abs = np.max(np.abs(audio), axis=1)
    active = np.where(mono_abs > 0.005)[0]
    if len(active) > 0:
        s = max(0, active[0] - int(0.04 * sr))
        e = min(len(audio), active[-1] + int(0.08 * sr))
        audio = audio[s:e]
    peak = np.max(np.abs(audio)) + 1e-8
    return audio * (0.78 / peak)


def synthesize_f5_devtools_texts(texts, work_dir, voice_preset, steps=16, q_bits=8, ref_audio=None, ref_text=None, sr=48000):
    """
    Uses python3 + f5_batch_synth.py to load F5-TTS MLX
    once and synthesize all uncached lines, with content-hash caching on disk.
    """
    cache_dir = os.path.join(work_dir, 'tts_cache')
    os.makedirs(cache_dir, exist_ok=True)

    batch_items = []
    wav_paths = []
    for text in texts:
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
    if ref_text:
        cmd.extend(['--ref-text', ref_text])

    subprocess.run(cmd, check=True)
    return [load_wav_48k_stereo(p, sr=sr) for p in wav_paths]


def fit_narration_to_window(narr_audio, max_narr_sec, sr=48000):
    """If synthesized narration exceeds available video window, time-compress gently via ffmpeg atempo (pitch-preserving)."""
    cur_sec = len(narr_audio) / sr
    if cur_sec <= max_narr_sec or max_narr_sec <= 0.5:
        return narr_audio
    tempo = min(1.38, max(1.01, (cur_sec / max_narr_sec) * 1.01))
    cmd = [
        'ffmpeg', '-y', '-v', 'error',
        '-f', 'f32le', '-ar', str(sr), '-ac', '2', '-i', '-',
        '-af', f'atempo={tempo:.4f}',
        '-f', 'f32le', '-ar', str(sr), '-ac', '2', '-'
    ]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out_bytes, _ = p.communicate(input=narr_audio.astype(np.float32).tobytes())
    fitted = np.frombuffer(out_bytes, dtype=np.float32).reshape(-1, 2)
    target_len = int(max_narr_sec * sr)
    return fitted[:target_len]


def get_video_duration(mp4_path):
    probe = subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', mp4_path
    ])
    return float(json.loads(probe)['format']['duration'])


def remux_existing_video_with_narration(tag, narr_audios, chap_audios, out_mp4, work_dir, breeze_clean, ambient_cache, base_tag='en-US-AndrewMultilingualNeural'):
    """
    Re-does ONLY the audio track for all 12 segments and remuxes against existing video segments
    using `-c:v copy` (zero video frame re-encoding).
    """
    chap_by_shot = {c['before_shot']: (c_idx, c) for c_idx, c in enumerate(mth.CHAPTERS)}
    seg_files = []
    total_shots = len(bsd.SHOTS)

    for idx, (fname, start, base_dur, loc_label, _) in enumerate(bsd.SHOTS):
        if idx in chap_by_shot:
            c_idx, chap_dict = chap_by_shot[idx]
            existing_chap_mp4 = os.path.join(work_dir, f'chap_{base_tag}_{c_idx:02d}.mp4')
            if not os.path.exists(existing_chap_mp4):
                raise FileNotFoundError(f'Missing existing chapter video: {existing_chap_mp4}')

            chap_dur = get_video_duration(existing_chap_mp4)
            chap_narr = fit_narration_to_window(chap_audios[c_idx], max_narr_sec=chap_dur - 0.45, sr=bsd.SR)
            chap_wav = os.path.join(work_dir, f'chap_{tag}_{c_idx:02d}.wav')
            chap_mp4 = os.path.join(work_dir, f'chap_{tag}_{c_idx:02d}.mp4')

            target_chap_samples = int(round(chap_dur * bsd.SR))
            chap_amb = breeze_clean[:target_chap_samples].copy()
            if len(chap_amb) < target_chap_samples:
                chap_amb = np.pad(chap_amb, ((0, target_chap_samples - len(chap_amb)), (0, 0)), mode='reflect')
            chap_mix = bsd.mix_ambient_and_narration(chap_amb, chap_narr, sr=bsd.SR, target_ambient_rms=0.032, fade_sec=0.35)

            p = subprocess.Popen(
                ['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(bsd.SR), '-ac', '2', '-i', '-', chap_wav],
                stdin=subprocess.PIPE
            )
            p.communicate(input=chap_mix.astype(np.float32).tobytes())

            subprocess.run([
                'ffmpeg', '-y', '-v', 'error',
                '-i', existing_chap_mp4, '-i', chap_wav,
                '-map', '0:v:0', '-map', '1:a:0',
                '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                '-shortest', chap_mp4
            ], check=True)
            print(f'  [Audio-Only Remux Chapter {c_idx+1}] {chap_dict["title"]} ({chap_dur:.2f}s) -> {os.path.basename(chap_mp4)}')
            seg_files.append(chap_mp4)

        existing_seg_mp4 = os.path.join(work_dir, f'seg_{base_tag}_{idx:02d}.mp4')
        if not os.path.exists(existing_seg_mp4):
            raise FileNotFoundError(f'Missing existing shot video: {existing_seg_mp4}')

        dur = get_video_duration(existing_seg_mp4)
        narr_audio = fit_narration_to_window(narr_audios[idx], max_narr_sec=dur - 0.50, sr=bsd.SR)
        seg_out = os.path.join(work_dir, f'seg_{tag}_{idx:02d}.mp4')
        wav_path = os.path.join(work_dir, f'seg_{tag}_{idx:02d}.wav')

        clean_ambient = ambient_cache[idx]
        target_samples = int(round(dur * bsd.SR))
        if len(clean_ambient) < target_samples:
            clean_ambient = np.pad(clean_ambient, ((0, target_samples - len(clean_ambient)), (0, 0)), mode='reflect')
        else:
            clean_ambient = clean_ambient[:target_samples]

        final_audio = bsd.mix_ambient_and_narration(clean_ambient, narr_audio, sr=bsd.SR, target_ambient_rms=0.046, fade_sec=0.35)
        p = subprocess.Popen(
            ['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(bsd.SR), '-ac', '2', '-i', '-', wav_path],
            stdin=subprocess.PIPE
        )
        p.communicate(input=final_audio.astype(np.float32).tobytes())

        subprocess.run([
            'ffmpeg', '-y', '-v', 'error',
            '-i', existing_seg_mp4, '-i', wav_path,
            '-map', '0:v:0', '-map', '1:a:0',
            '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
            '-shortest', seg_out
        ], check=True)
        print(f'[{idx+1}/{total_shots}] Audio-Only Remux {fname} ({dur:.2f}s) | {loc_label}')
        seg_files.append(seg_out)

    list_file = os.path.join(work_dir, f'concat_{tag}.txt')
    with open(list_file, 'w') as f:
        for s in seg_files:
            f.write(f"file '{s}'\n")

    subprocess.run([
        'ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0',
        '-i', list_file, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
        '-movflags', '+faststart', out_mp4
    ], check=True)
    print(f'Successfully created (audio-only remux): {out_mp4}')


VOICE_TRACK_METADATA = {
    'primary': ('Primary Narrator', 'eng'),
    'tony': ('Classic Narrator Commentary', 'zaf'),
    'tony_alt': ('Classic Narrator Commentary (Alt)', 'zaf'),
    'narrator_uk': ('British Narrator', 'gbr'),
    'bumble': ('David Lloyd (Bumble) Commentary', 'gbr'),
    'en-US-AndrewMultilingualNeural': ('Discovery US Narrator (Andrew)', 'usa'),
    'en-GB-RyanNeural': ('BBC Earth UK Narrator (Ryan)', 'eng'),
}


def mux_multi_audio_mp4(track_specs, out_mp4):
    """
    Muxes 1 video stream (from track_specs[0]['mp4']) + N selectable stereo AAC audio streams
    into a single multi-audio MP4 without re-encoding video or audio (-c:v copy -c:a copy).
    track_specs: list of dicts [{'mp4': path, 'voice': voice_key, 'title': optional_title, 'lang': optional_lang}]
    """
    cmd = ['ffmpeg', '-y', '-v', 'error']
    for spec in track_specs:
        cmd.extend(['-i', spec['mp4']])

    cmd.extend(['-map', '0:v:0'])
    for i in range(len(track_specs)):
        cmd.extend(['-map', f'{i}:a:0'])

    cmd.extend(['-c:v', 'copy', '-c:a', 'copy'])
    for i, spec in enumerate(track_specs):
        v_key = spec.get('voice', f'track_{i}')
        default_title, default_lang = VOICE_TRACK_METADATA.get(v_key, (f'Narrator ({v_key})', 'eng'))
        title = spec.get('title') or default_title
        lang = spec.get('lang') or default_lang
        cmd.extend([
            f'-metadata:s:a:{i}', f'title={title}',
            f'-metadata:s:a:{i}', f'handler_name={title}',
            f'-metadata:s:a:{i}', f'language={lang}',
            f'-disposition:a:{i}', 'default' if i == 0 else '0',
        ])

    cmd.extend(['-movflags', '+faststart', out_mp4])
    subprocess.run(cmd, check=True)
    print(f'Successfully created multi-audio MP4 ({len(track_specs)} selectable audio tracks): {out_mp4}')


def load_or_synthesize_edge_tts_texts(texts, work_dir, voice_name, sr=48000):
    """Loads cached narr_<voice>_XX.mp3 files if available, otherwise synthesizes via Edge-TTS."""
    cached_mp3s = [os.path.join(work_dir, f'narr_{voice_name}_{i:02d}.mp3') for i in range(len(texts))]
    if all(os.path.exists(p) and os.path.getsize(p) > 1000 for p in cached_mp3s):
        print(f'[Edge-TTS Cache] Using all {len(texts)} cached MP3 segments for {voice_name}.')
        return [load_wav_48k_stereo(p, sr=sr) for p in cached_mp3s]
    return bsd.synthesize_edge_tts_texts(texts, work_dir, prefix=f'narr_{voice_name}', voice=voice_name, sr=sr)


def render_with_narration_arrays(tag, narr_audios, chap_audios, out_mp4, work_dir, breeze_clean, ambient_cache, hud_pngs, hud_corners):
    chap_by_shot = {c['before_shot']: (c_idx, c) for c_idx, c in enumerate(mth.CHAPTERS)}
    seg_files = []
    total_shots = len(bsd.SHOTS)

    for idx, (fname, start, base_dur, loc_label, _) in enumerate(bsd.SHOTS):
        if idx in chap_by_shot:
            c_idx, chap_dict = chap_by_shot[idx]
            chap_narr = chap_audios[c_idx]
            chap_dur = max(3.6, round(len(chap_narr) / bsd.SR + 0.85, 2))
            chap_wav = os.path.join(work_dir, f'chap_{tag}_{c_idx:02d}.wav')
            chap_mp4 = os.path.join(work_dir, f'chap_{tag}_{c_idx:02d}.mp4')

            chap_amb = breeze_clean[:int(chap_dur * bsd.SR)].copy()
            if len(chap_amb) < int(chap_dur * bsd.SR):
                chap_amb = np.pad(chap_amb, ((0, int(chap_dur * bsd.SR) - len(chap_amb)), (0, 0)), mode='reflect')
            chap_mix = bsd.mix_ambient_and_narration(chap_amb, chap_narr, sr=bsd.SR, target_ambient_rms=0.032, fade_sec=0.35)

            p = subprocess.Popen(
                ['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(bsd.SR), '-ac', '2', '-i', '-', chap_wav],
                stdin=subprocess.PIPE
            )
            p.communicate(input=chap_mix.astype(np.float32).tobytes())

            print(f'  [Chapter Map {c_idx+1}] {chap_dict["title"]} ({chap_dur:.2f}s)')
            mth.render_chapter_map_video(chap_dict, chap_mp4, chap_wav, duration=chap_dur, fps=25)
            seg_files.append(chap_mp4)

        in_path = os.path.join(bsd.GOPRO_DIR, fname)
        seg_out = os.path.join(work_dir, f'seg_{tag}_{idx:02d}.mp4')
        wav_path = os.path.join(work_dir, f'seg_{tag}_{idx:02d}.wav')

        narr_audio = narr_audios[idx]
        dur = max(base_dur, round(len(narr_audio) / bsd.SR + 0.85, 2))

        probe = subprocess.check_output([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', in_path
        ])
        src_total_dur = float(json.loads(probe)['format']['duration'])
        avail_src_dur = max(1.0, src_total_dur - start)

        hud_x, hud_y, corner_name = hud_corners[idx]
        hud_png = hud_pngs[idx]
        print(f'[{idx+1}/{total_shots}] {fname} (dur={dur:.2f}s, HUD={corner_name}) | {loc_label}')

        clean_ambient = ambient_cache[idx]
        target_samples = int(dur * bsd.SR)
        if len(clean_ambient) < target_samples:
            clean_ambient = np.pad(clean_ambient, ((0, target_samples - len(clean_ambient)), (0, 0)), mode='reflect')
        else:
            clean_ambient = clean_ambient[:target_samples]

        final_audio = bsd.mix_ambient_and_narration(clean_ambient, narr_audio, sr=bsd.SR, target_ambient_rms=0.046, fade_sec=0.35)
        p = subprocess.Popen(
            ['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(bsd.SR), '-ac', '2', '-i', '-', wav_path],
            stdin=subprocess.PIPE
        )
        p.communicate(input=final_audio.astype(np.float32).tobytes())

        v_chain = []
        if avail_src_dur < dur:
            stretch = (dur / avail_src_dur) * 1.02
            v_chain.append(f'setpts={stretch:.3f}*PTS,fps=25,settb=1/25')
        else:
            v_chain.append('fps=25,settb=1/25')
        v_chain.extend([
            'scale=1920:1080:force_original_aspect_ratio=decrease',
            'pad=1920:1080:(ow-iw)/2:(oh-ih)/2',
            'eq=contrast=1.04:saturation=1.08:brightness=-0.01',
        ])
        base_v = ','.join(v_chain)
        hud_out_t = max(3.5, min(dur - 1.1, 6.4))
        end_fade = f',fade=t=out:st={dur-1.0:.2f}:d=1.0' if idx == total_shots - 1 else ''
        filter_complex = (
            f'[0:v]{base_v}[bg];'
            f'[1:v]format=rgba,fade=t=in:st=0.45:d=0.45:alpha=1,fade=t=out:st={hud_out_t:.2f}:d=0.50:alpha=1[hud];'
            f'[bg][hud]overlay={hud_x}:{hud_y}:shortest=1{end_fade},format=yuv420p[vout]'
        )
        subprocess.run([
            'ffmpeg', '-y', '-v', 'error',
            '-ss', f'{start:.3f}', '-t', f'{min(dur, avail_src_dur):.3f}', '-i', in_path,
            '-loop', '1', '-t', f'{dur:.3f}', '-i', hud_png,
            '-i', wav_path,
            '-filter_complex', filter_complex,
            '-map', '[vout]', '-map', '2:a:0',
            '-t', f'{dur:.3f}',
            '-video_track_timescale', '25000',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
            '-c:a', 'aac', '-b:a', '192k',
            '-shortest', seg_out
        ], check=True)
        seg_files.append(seg_out)

    list_file = os.path.join(work_dir, f'concat_{tag}.txt')
    with open(list_file, 'w') as f:
        for s in seg_files:
            f.write(f"file '{s}'\n")

    subprocess.run([
        'ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0',
        '-i', list_file, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
        '-movflags', '+faststart', out_mp4
    ], check=True)
    print(f'Successfully created: {out_mp4}')


def main():
    parser = argparse.ArgumentParser(description='Expedition Documentary Creator')
    parser.add_argument('--video-dir', default='./raw_videos',
                        help='Folder containing raw GoPro/travel video clips')
    parser.add_argument('--voice', default='primary',
                        help='Voice preset in voices (primary, narrator_uk/narrator_uk_alt, tony/narrator classic, tony_alt, bumble) OR Edge-TTS voice (en-US-AndrewMultilingualNeural, en-GB-RyanNeural)')
    parser.add_argument('--ref-audio', default=None, help='Optional custom 24kHz mono WAV path for F5-TTS')
    parser.add_argument('--ref-text', default=None, help='Optional transcript for custom ref-audio')
    parser.add_argument('--steps', type=int, default=16, help='F5-TTS ODE steps (16=fast batch, 32=max quality)')
    parser.add_argument('-q', '--quantization-bits', type=int, default=8, choices=[0, 4, 8], help='F5-TTS quantization bits')
    parser.add_argument('--audio-only', action='store_true',
                        help='Do not re-encode video; only synthesize/mix new audio and remux (-c:v copy) against existing video segments')
    parser.add_argument('--base-tag', default='en-US-AndrewMultilingualNeural',
                        help='Base segment tag in work/segments_v4/ to copy video streams from when --audio-only is used')
    parser.add_argument('--multi-audio-output', default=None,
                        help='Optional output MP4 path that bundles 1 video stream + ALL requested voices as selectable audio tracks')
    parser.add_argument('--output', default='./expedition_documentary.mp4',
                        help='Output MP4 path (or comma-separated paths matching --voice)')
    args = parser.parse_args()

    bsd.GOPRO_DIR = args.video_dir
    first_out = args.output.split(',')[0].strip()
    work_dir = os.path.join(os.path.dirname(os.path.abspath(first_out)), 'work', 'segments_v4')
    os.makedirs(work_dir, exist_ok=True)
    bsd.WORK_DIR = work_dir

    # Cache cleaned ambient audio & HUD PNGs on disk so multi-voice runs reuse them instantly
    amb_cache_dir = os.path.join(work_dir, 'ambient_cache')
    os.makedirs(amb_cache_dir, exist_ok=True)

    breeze_npy = os.path.join(amb_cache_dir, 'breeze_clean.npy')
    if os.path.exists(breeze_npy):
        breeze_clean = np.load(breeze_npy)
    else:
        breeze_raw = extract_stereo_audio(os.path.join(args.video_dir, bsd.SHOTS[7][0]), sr=bsd.SR, start=2.0, duration=12.0)
        breeze_clean = suppress_voice_keep_ambient(breeze_raw, sr=bsd.SR)
        np.save(breeze_npy, breeze_clean)

    ambient_cache, hud_pngs, hud_corners = [], [], []
    for idx, (fname, start, base_dur, _, _) in enumerate(bsd.SHOTS):
        in_path = os.path.join(args.video_dir, fname)
        amb_npy = os.path.join(amb_cache_dir, f'amb_{fname}_{start:.1f}_{base_dur:.1f}.npy')
        clean_amb = None
        if os.path.exists(amb_npy):
            loaded = np.load(amb_npy, allow_pickle=True)
            if loaded.ndim == 2:
                clean_amb = loaded
        if clean_amb is None:
            raw_audio = extract_stereo_audio(in_path, sr=bsd.SR, start=start, duration=base_dur + 4.5)
            if raw_audio is not None and len(raw_audio) > bsd.SR:
                clean_amb = suppress_voice_keep_ambient(raw_audio, sr=bsd.SR)
            else:
                clean_amb = breeze_clean.copy()
            np.save(amb_npy, clean_amb)
        ambient_cache.append(clean_amb)

        if not args.audio_only:
            hud_png = os.path.join(work_dir, f'hud_card_{idx:02d}.png')
            if not os.path.exists(hud_png):
                mth.render_hud_overlay_png(idx, hud_png)
            hud_pngs.append(hud_png)
            hud_corners.append(mth.choose_best_hud_corner(in_path, start, base_dur))

    shot_texts = [s[4] for s in bsd.SHOTS]
    chap_texts = [c['narration'] for c in mth.CHAPTERS]
    all_texts = shot_texts + chap_texts

    voices = [v.strip() for v in args.voice.split(',') if v.strip()]
    outputs = [o.strip() for o in args.output.split(',') if o.strip()]
    if len(outputs) < len(voices):
        base_out_dir = os.path.dirname(os.path.abspath(outputs[0]))
        outputs = [os.path.join(base_out_dir, f'sample_documentary_{resolve_f5_preset(v) or v}.mp4') for v in voices]

    # Single-load multi-voice F5-TTS batch if multiple F5 voices are requested
    f5_pairs = [(resolve_f5_preset(v), out_mp4) for v, out_mp4 in zip(voices, outputs) if resolve_f5_preset(v) or args.ref_audio]
    pending_f5_pairs = [(p, m) for p, m in f5_pairs if not (args.audio_only and os.path.exists(m))]
    if pending_f5_pairs:
        cache_dir = os.path.join(work_dir, 'tts_cache')
        os.makedirs(cache_dir, exist_ok=True)
        combined_items = []
        voice_wav_map = {}
        for preset_tag, _ in pending_f5_pairs:
            tag = preset_tag or 'custom_f5'
            wavs = []
            for text in all_texts:
                h = hashlib.sha1(f"{tag}:{args.steps}:{args.quantization_bits}:{args.ref_audio}:{text.strip()}".encode('utf-8')).hexdigest()[:14]
                out_wav = os.path.join(cache_dir, f'f5_{tag}_{h}.wav')
                wavs.append(out_wav)
                combined_items.append({'text': text, 'output': out_wav, 'voice': tag})
            voice_wav_map[tag] = wavs

        batch_json_path = os.path.join(cache_dir, 'batch_multi.json')
        with open(batch_json_path, 'w') as f:
            json.dump(combined_items, f, indent=2)

        cmd = [
            DEVTOOLS_VOICE_PYTHON, F5_BATCH_SCRIPT,
            '--batch-json', batch_json_path,
            '--voice', pending_f5_pairs[0][0] or 'primary',
            '--steps', str(args.steps),
            '-q', str(args.quantization_bits),
        ]
        if args.ref_audio:
            cmd.extend(['--ref-audio', args.ref_audio])
        if args.ref_text:
            cmd.extend(['--ref-text', args.ref_text])
        subprocess.run(cmd, check=True)

        for preset_tag, out_mp4 in pending_f5_pairs:
            tag = preset_tag or 'custom_f5'
            all_audios = [load_wav_48k_stereo(p, sr=bsd.SR) for p in voice_wav_map[tag]]
            narr_audios = all_audios[:len(bsd.SHOTS)]
            chap_audios = all_audios[len(bsd.SHOTS):]
            if args.audio_only:
                remux_existing_video_with_narration(
                    tag, narr_audios, chap_audios, out_mp4, work_dir,
                    breeze_clean, ambient_cache, base_tag=args.base_tag
                )
            else:
                render_with_narration_arrays(
                    tag, narr_audios, chap_audios, out_mp4, work_dir,
                    breeze_clean, ambient_cache, hud_pngs, hud_corners
                )

    edge_pairs = [(v, out_mp4) for v, out_mp4 in zip(voices, outputs) if not (resolve_f5_preset(v) or args.ref_audio)]
    for v, out_mp4 in edge_pairs:
        if args.audio_only:
            if not os.path.exists(out_mp4):
                all_audios = load_or_synthesize_edge_tts_texts(all_texts, work_dir, v, sr=bsd.SR)
                narr_audios = all_audios[:len(bsd.SHOTS)]
                chap_audios = all_audios[len(bsd.SHOTS):]
                remux_existing_video_with_narration(
                    f'{v}_synced', narr_audios, chap_audios, out_mp4, work_dir,
                    breeze_clean, ambient_cache, base_tag=args.base_tag
                )
        else:
            bsd.render_documentary_for_voice(
                v, out_mp4, breeze_clean, ambient_cache, hud_pngs, hud_corners
            )

    if args.multi_audio_output:
        track_specs = [
            {'mp4': out_mp4, 'voice': resolve_f5_preset(v) or v}
            for v, out_mp4 in zip(voices, outputs)
        ]
        mux_multi_audio_mp4(track_specs, args.multi_audio_output)


if __name__ == '__main__':
    main()
