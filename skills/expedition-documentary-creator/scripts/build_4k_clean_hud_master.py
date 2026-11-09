#!/usr/bin/env python3
"""
4K ULTRA HD (3840x2160) MASTER VIDEO + CLEAN LARGE-FONT GEOGRAPHIC HUD BUILDER
Re-renders all 246 timeline segments directly from raw 4K GoPro & Google Photos sources:
  1. Preserves full native 3840x2160 4K resolution across the 136 4K GoPro clips and cleanly
     upscales the 110 1080p/720p clips to a unified 3840x2160 25fps canvas.
  2. Replaces the cluttered, micro-font 9pt HUD that appeared on every screen with a spacious,
     large-font (44pt-48pt) Geographic Card shown ONLY on the 58 Chapter Lead clips (leaving
     all 188 B-roll shots 100% unobstructed).
  3. Locks every segment's exact frame count to `segments_info.json` so total duration remains
     1566.850s, matching all 5 multi-language audio tracks (UK, US, Hindi, Bangla, Odia).
"""

import os
import sys
import json
import subprocess
import concurrent.futures

VIDEO_DIR    = '.'
WORK_OUT     = './work/equal_timeline_v2'
SEG_4K_DIR   = './work/segments_4k'
HUD_4K_DIR   = './work/segments_4k/huds'
AUDIO_TRACKS = './audio_tracks'
FINAL_MP4    = './expedition_all_videos_multiaudio.mp4'

sys.path.insert(0, VIDEO_DIR)
import map_telemetry_hud as mth

VOICE_SPECS = [
    ('uk',     'eng', '1. BBC Earth UK (Ryan)'),
    ('us',     'eng', '2. Discovery US (Andrew)'),
    ('hindi',  'hin', '3. Hindi (Madhur)'),
    ('bangla', 'ben', '4. Bangla (Bashkar)'),
    ('odia',   'ori', '5. Odia (IndicF5 Subhasini)'),
]

# 58-Chapter Geographic Telemetry progression (Starting City -> Metro Hub -> Valley City -> Forest Reserve -> Biosphere -> Mountain District -> Summit -> Starting City)
ROUTE_WAYPOINTS_58 = [
    ("STARTING CITY RING ROAD",    "PLATEAU STATE • NH-44 SOUTH",       17.2403, 78.4294, 536,  15),
    ("MAHBUBNAGAR PLAINS",     "PLATEAU STATE • DECCAN PLATEAU",    16.7488, 78.0035, 498,  95),
    ("KRISHNA RIVER CROSSING", "PLATEAU STATE / AP BORDER",         16.1850, 77.9450, 345, 165),
    ("KURNOOL BYPASS",         "ANDHRA PRADESH • NH-44",        15.8281, 78.0373, 285, 215),
    ("GOOTY & ANANTAPUR",      "ANDHRA PRADESH • RAYALASEEMA",  14.6819, 77.6006, 350, 360),
    ("PENUKONDA HIGHWAYS",     "ANDHRA PRADESH • SOUTH",        14.0810, 77.5940, 560, 440),
    ("CHICKBALLAPUR APPROACH", "HIGHLAND STATE • SUMMIT FOOTHILLS",   13.4355, 77.7315, 915, 515),
    ("METRO HUB EXPRESSWAY",   "HIGHLAND STATE • NH-275 CORRIDOR",   12.9010, 77.4850, 840, 580),
    ("RAMANAGARA GRANITE",     "HIGHLAND STATE • RAMANAGARA DIST.",  12.7209, 77.2799, 747, 620),
    ("MANDYA SUGAR BELT",      "HIGHLAND STATE • CAUVERY BASIN",     12.5218, 76.8951, 678, 665),
    ("CHAMUNDI HILLS SUMMIT",  "HIGHLAND STATE • VALLEY CITY (1,026m)",   12.2725, 76.6705, 1026, 715),
    ("GUNDLUPET FRONTIER",     "HIGHLAND STATE • CHAMARAJANAGAR",    11.8080, 76.6914, 795, 775),
    ("FOREST RESERVE TIGER RESERVE", "HIGHLAND STATE • CORE SANCTUARY",    11.6656, 76.6285, 910, 798),
    ("FOREST RESERVE FOREST TRACK",  "HIGHLAND STATE • MOUNTAIN BIOSPHERE", 11.6350, 76.6120, 925, 808),
    ("MOYAR GORGE FRONTIER",   "KA / TN BORDER • KAKKANALLA",   11.6085, 76.5975, 885, 816),
    ("BIOSPHERE TIGER RESERVE","SOUTHERN STATE • THE MOUNTAINS",     11.5819, 76.5858, 890, 825),
    ("MASINAGUDI FOOTHILLS",   "SOUTHERN STATE • MOYAR VALLEY",     11.5732, 76.6429, 950, 838),
    ("BOKKAPURAM ESCARPMENT",  "SOUTHERN STATE • MOUNTAIN SLOPES",   11.5540, 76.6510, 1015, 846),
    ("BIOSPHERE DAWN SAFARI",  "SOUTHERN STATE • THEPPAKADU",       11.5850, 76.5780, 895, 860),
    ("GUDALUR GHAT ASCENT",    "SOUTHERN STATE • WESTERN GHATS",    11.5030, 76.4917, 1070, 882),
    ("DEVALA RAINFOREST CORR", "SOUTHERN STATE • HIGH RAINFALL",    11.4780, 76.3850, 980, 902),
    ("MUTHANGA WILDLIFE POST", "HIGHLANDS • MOUNTAIN DISTRICT ENTRY",        11.6725, 76.3733, 865, 928),
    ("FRONTIER TOWN CORRIDOR","HIGHLANDS • MOUNTAIN DISTRICT HIGHLANDS",    11.6644, 76.2570, 905, 945),
    ("PLATEAU HQ PLATEAU",       "HIGHLANDS • MOUNTAIN DISTRICT DISTRICT",     11.6103, 76.0827, 780, 968),
    ("GHAT PASS MIST CANOPY",    "HIGHLANDS • SOUTHERN MOUNTAIN DISTRICT",     11.5515, 76.0402, 776, 982),
    ("CREST VIEW GHAT CREST",     "HIGHLANDS • ESCARPMENT PASS",    11.5194, 76.0191, 715, 990),
    ("RESERVOIR SAGAR DAM",     "HIGHLANDS • WESTERN MOUNTAIN DISTRICT",      11.6705, 75.9575, 815, 1018),
    ("RESERVOIR ISLAND PEAKS",  "HIGHLANDS • KARAMANATHODU BASIN",  11.6780, 75.9510, 845, 1025),
    ("KARAPUZHA RESERVOIR",    "HIGHLANDS • MOUNTAIN DISTRICT WATERSHED",    11.6180, 76.1720, 760, 1052),
    ("RIDGE TOWN TEA ESTATES",    "HIGHLANDS • HIGH RANGE SLOPES",    11.5546, 76.1353, 940, 1070),
    ("KALLADI FOREST ASCENT",  "HIGHLANDS • RIDGE TOWN VALLEY",       11.5152, 76.1225, 1120, 1078),
    ("HIGHLAND PEAK CLOUD RIDGE",  "HIGHLANDS • 1,458m SUMMIT CREST",  11.4948, 76.1060, 1458, 1086),
    ("WESTERN GHATS PRECIPICE","HIGHLANDS • MOUNTAIN DISTRICT / NILAMBUR",   11.4880, 76.1150, 1445, 1090),
    ("SOOCHIPARA WATERFALLS",  "HIGHLANDS • VELLARIMALA RANGE",    11.5110, 76.1635, 895, 1104),
    ("EASTERN RIDGE HIGHLANDS",  "HIGHLANDS • EASTERN MOUNTAIN DISTRICT",      11.5390, 76.2085, 880, 1118),
    ("RIVER VALLEY RIVER VALLEY", "HIGHLANDS • CENTRAL MOUNTAIN DISTRICT",      11.7380, 76.0740, 735, 1148),
    ("NORTHERN CORRIDOR CORRIDOR",  "HIGHLANDS • NORTHERN MOUNTAIN DISTRICT",     11.8014, 76.0044, 760, 1168),
    ("TEMPLE FOREST FOREST ROAD", "HIGHLANDS • HIGH SLOPES SLOPES",    11.9110, 75.9960, 890, 1192),
    ("WATERSHED RIVER WATERSHED", "HIGHLANDS / HIGHLAND STATE FRONTIER",   11.9320, 76.1450, 725, 1218),
    ("NAGARAHOLE BORDER ROAD", "HIGHLAND STATE • HD KOTE TALUK",     12.0750, 76.3250, 740, 1255),
    ("VALLEY CITY RING RETURN",     "HIGHLAND STATE • CAUVERY PLAINS",    12.3150, 76.6550, 765, 1305),
    ("SRIRANGAPATNA CROSSING", "HIGHLAND STATE • NH-275 NORTH",      12.4244, 76.6894, 680, 1325),
    ("CHANNAPATNA & BIDADI",   "HIGHLAND STATE • EXPRESSWAY",        12.6518, 77.2067, 730, 1385),
    ("METRO HUB OUTER RING",   "HIGHLAND STATE • NORTHBOUND",        13.0350, 77.5970, 910, 1445),
    ("DEVANAHALLI CORRIDOR",   "HIGHLAND STATE • NH-44 NORTH",       13.2460, 77.7120, 905, 1480),
    ("SUMMIT HILLS PLATEAU",    "HIGHLAND STATE • 1,478m MONOLITH",   13.3702, 77.6835, 1478, 1502),
    ("BAGEPALLI FRONTIER",     "HIGHLAND STATE / AP BORDER",         13.7850, 77.7950, 710, 1555),
    ("ANANTAPUR WIND PLAINS",  "ANDHRA PRADESH • NH-44 NORTH",  14.6819, 77.6006, 355, 1655),
    ("GOOTY FORT CORRIDOR",    "ANDHRA PRADESH • DECCAN",       15.1180, 77.6350, 375, 1710),
    ("DHONE LIMESTONE HILLS",  "ANDHRA PRADESH • KURNOOL DIST.",15.3950, 77.8720, 425, 1755),
    ("KURNOOL TUNGABHADRA",    "ANDHRA PRADESH • RIVER BASIN",  15.8281, 78.0373, 285, 1805),
    ("BEECHUPALLY & GADWAL",   "PLATEAU STATE • KRISHNA VALLEY",    16.2350, 77.9650, 350, 1855),
    ("JADCHERLA EXPRESSWAY",   "PLATEAU STATE • NH-44 CORRIDOR",    16.7620, 78.1380, 515, 1915),
    ("SHADNAGAR APPROACH",     "PLATEAU STATE • RANGA REDDY DIST.", 17.0680, 78.2050, 585, 1950),
    ("OUTER RING RING ROAD",   "PLATEAU STATE • STARTING CITY SOUTH",   17.2403, 78.4294, 540, 1978),
    ("ORR WEST EXPRESSWAY",    "PLATEAU STATE • GACHIBOWLI LINK",   17.3650, 78.3450, 565, 1992),
    ("STARTING CITY SKYLINE",      "PLATEAU STATE • EXPEDITION FINISH", 17.4250, 78.3950, 545, 2000),
    ("2,000 KM LOOP COMPLETE", "STARTING CITY • PLATEAU STATE",         17.4400, 78.3800, 545, 2000),
]


def setup_58_chapter_telemetry():
    telem = []
    for idx, (title, sd, lat, lon, alt, dist_km) in enumerate(ROUTE_WAYPOINTS_58):
        telem.append({
            'id': idx,
            'title': title,
            'subtitle': sd,
            'state_dist': sd,
            'lat': lat,
            'lon': lon,
            'alt_m': alt,
            'spd_kmh': 65,
            'dist_km': dist_km,
            'zoom': 10,
            'edge_arrows': [],
        })
    mth.SHOT_TELEMETRY = telem


def get_src_duration(src_path):
    try:
        out = subprocess.check_output([
            '/opt/homebrew/bin/ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', src_path
        ]).decode().strip()
        return float(out)
    except Exception:
        return 30.0


def render_4k_segment(task):
    seg_idx = task['seg_idx']
    group_idx = task['group_idx']
    role = task['role']
    src_path = task['src_path']
    start = task['start']
    dur = task['dur']
    hud_png = task['hud_png']
    out_mp4 = task['out_mp4']

    if os.path.exists(out_mp4) and os.path.getsize(out_mp4) > 500_000:
        try:
            probe_w = subprocess.check_output([
                '/opt/homebrew/bin/ffprobe', '-v', 'error', '-select_streams', 'v:0',
                '-show_entries', 'stream=width', '-of', 'default=noprint_wrappers=1:nokey=1', out_mp4
            ]).decode().strip()
            if probe_w == '3840':
                return seg_idx, out_mp4
        except Exception:
            pass

    src_total_dur = get_src_duration(src_path)
    avail_dur = max(0.5, src_total_dur - start)

    v_filters = []
    if avail_dur < dur:
        stretch = (dur / avail_dur) * 1.02
        v_filters.append(f'setpts={stretch:.4f}*PTS')

    v_filters.extend([
        'fps=25',
        'scale=3840:2160:force_original_aspect_ratio=decrease',
        'pad=3840:2160:(ow-iw)/2:(oh-ih)/2',
        'settb=1/25',
        'format=yuv420p',
    ])
    base_vf = ','.join(v_filters)

    if role == 'lead' and hud_png and os.path.exists(hud_png):
        # Overlay the clean, large-font 4K Geographic Card in top-right (3840 - 1160 - 52 = 2628, y = 52)
        # Fades in at 0.4s and fades out cleanly at min(dur - 0.6, 5.2)s
        hud_out = max(2.5, min(dur - 0.6, 5.2))
        fc = (
            f"[0:v]{base_vf}[bg];"
            f"[1:v]format=rgba,fade=t=in:st=0.35:d=0.4:alpha=1,fade=t=out:st={hud_out:.2f}:d=0.45:alpha=1[hud];"
            f"[bg][hud]overlay=2628:52:format=auto,format=yuv420p[vout]"
        )
        cmd = [
            '/opt/homebrew/bin/ffmpeg', '-y', '-v', 'error',
            '-ss', f'{start:.3f}', '-t', f'{min(avail_dur, dur + 0.5):.3f}', '-i', src_path,
            '-loop', '1', '-t', f'{dur:.3f}', '-i', hud_png,
            '-filter_complex', fc,
            '-map', '[vout]', '-an',
            '-t', f'{dur:.3f}',
            '-c:v', 'h264_videotoolbox', '-b:v', '22M', '-maxrate', '30M', '-bufsize', '40M',
            '-video_track_timescale', '25000',
            out_mp4
        ]
    else:
        # B-roll: 100% unobstructed 4K Ultra HD frame
        cmd = [
            '/opt/homebrew/bin/ffmpeg', '-y', '-v', 'error',
            '-ss', f'{start:.3f}', '-t', f'{min(avail_dur, dur + 0.5):.3f}', '-i', src_path,
            '-vf', base_vf, '-an',
            '-t', f'{dur:.3f}',
            '-c:v', 'h264_videotoolbox', '-b:v', '22M', '-maxrate', '30M', '-bufsize', '40M',
            '-video_track_timescale', '25000',
            out_mp4
        ]

    subprocess.run(cmd, check=True)
    return seg_idx, out_mp4


def main():
    os.makedirs(SEG_4K_DIR, exist_ok=True)
    os.makedirs(HUD_4K_DIR, exist_ok=True)

    setup_58_chapter_telemetry()

    tl = json.load(open(os.path.join(WORK_OUT, 'equal_timeline_final.json')))
    segs_info = json.load(open(os.path.join(WORK_OUT, 'segments_info.json')))

    print("=" * 72)
    print("BUILDING 4K ULTRA HD (3840x2160) MASTER WITH CLEAN LARGE-FONT CHAPTER HUDS")
    print("=" * 72)

    # 1. Pre-render the 58 Clean 4K Geographic Cards (one per chapter lead)
    print(f"[Phase 1] Rendering 58 Clean Large-Font 4K Geographic Cards (1160x480)...")
    hud_paths = {}
    for g_idx in range(len(tl)):
        hp = os.path.join(HUD_4K_DIR, f'hud_4k_chap_{g_idx:03d}.png')
        mth.render_hud_overlay_png(g_idx, hp, is_4k=True)
        hud_paths[g_idx] = hp
    print("  All 58 4K Geographic Cards rendered.")

    # 2. Build flat segment task list matching segments_info.json 1:1
    flat_clips = []
    for g_idx, g in enumerate(tl):
        c_lead = dict(g['clip'])
        c_lead['group_idx'] = g_idx
        c_lead['role'] = 'lead'
        flat_clips.append(c_lead)
        for b in g['brolls']:
            c_b = dict(b)
            c_b['group_idx'] = g_idx
            c_b['role'] = 'broll'
            flat_clips.append(c_b)

    assert len(flat_clips) == len(segs_info), f"Mismatch {len(flat_clips)} vs {len(segs_info)}"

    tasks = []
    for seg_idx, (clip, s_info) in enumerate(zip(flat_clips, segs_info)):
        g_idx = s_info['group_idx']
        role = s_info['role']
        tasks.append({
            'seg_idx': seg_idx,
            'group_idx': g_idx,
            'role': role,
            'src_path': clip['path'],
            'start': float(clip.get('start', 0.0)),
            'dur': float(s_info['dur']),
            'hud_png': hud_paths[g_idx] if role == 'lead' else None,
            'out_mp4': os.path.join(SEG_4K_DIR, f'seg_4k_{seg_idx:03d}.mp4'),
        })

    print(f"[Phase 2] Encoding {len(tasks)} segments in 4K (3840x2160) via Apple Silicon VideoToolbox...")
    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(render_4k_segment, t) for t in tasks]
        for fut in concurrent.futures.as_completed(futs):
            s_idx, _ = fut.result()
            completed += 1
            if completed % 20 == 0 or completed == len(tasks):
                print(f"  Progress: {completed}/{len(tasks)} 4K segments encoded...", flush=True)

    # 3. Concatenate all 246 4K segments
    concat_4k_txt = os.path.join(SEG_4K_DIR, 'concat_4k_master.txt')
    with open(concat_4k_txt, 'w') as f:
        for t in tasks:
            f.write(f"file '{t['out_mp4']}'\n")

    master_4k_video = os.path.join(SEG_4K_DIR, 'temp_master_4k_video.mp4')
    print(f"[Phase 3] Concatenating 246 4K segments -> {master_4k_video}...")
    subprocess.run([
        '/opt/homebrew/bin/ffmpeg', '-y', '-v', 'error',
        '-f', 'concat', '-safe', '0', '-i', concat_4k_txt,
        '-c:v', 'copy', '-an', master_4k_video
    ], check=True)

    vid_dur = float(subprocess.check_output([
        '/opt/homebrew/bin/ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
        master_4k_video
    ]).decode().strip())

    # 4. Multiplex 4K Master Video + 5 Voice-Suppressed Multi-Language Audio Tracks
    print(f"[Phase 4] Multiplexing 4K video ({vid_dur:.3f}s) + 5 audio tracks -> {FINAL_MP4}...")
    temp_mux = os.path.join(VIDEO_DIR, 'work', 'temp_mux_4k_multiaudio.mp4')
    cmd = ['/opt/homebrew/bin/ffmpeg', '-y', '-v', 'error', '-i', master_4k_video]
    for v_tag, _, _ in VOICE_SPECS:
        cmd += ['-i', os.path.join(AUDIO_TRACKS, f'track_{v_tag}_scratch.m4a')]

    cmd += ['-map', '0:v:0']
    for i, (v_tag, lang, label) in enumerate(VOICE_SPECS):
        cmd += [
            '-map', f'{i+1}:a:0',
            f'-metadata:s:a:{i}', f'language={lang}',
            f'-metadata:s:a:{i}', f'title={label}',
            f'-metadata:s:a:{i}', f'handler_name={label}',
            f'-disposition:a:{i}', 'default' if i == 0 else '0'
        ]

    cmd += ['-t', f'{vid_dur:.3f}', '-shortest', '-c:v', 'copy', '-c:a', 'copy', temp_mux]
    subprocess.run(cmd, check=True)
    os.replace(temp_mux, FINAL_MP4)

    if os.path.exists(master_4k_video):
        os.remove(master_4k_video)

    print("=" * 72)
    print(f"4K ULTRA HD MASTER COMPLETE: {FINAL_MP4}")
    print(f"Size: {os.path.getsize(FINAL_MP4)/(1024**3):.2f} GB | Duration: {vid_dur:.3f}s")
    print("=" * 72)


if __name__ == '__main__':
    main()
