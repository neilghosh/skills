"""
Utility script to verify that each generated .m4a audio track is a valid MP4 container
and contains audio data. This helps catch errors like the missing moov atom for
track_shastri.m4a before the final mux step.

Usage:
    python3 verify_audio_tracks.py
"""
import subprocess
import pathlib

AUDIO_DIR = pathlib.Path('/Users/neilghosh/dev/video/audio_tracks')

def is_valid_m4a(file_path: pathlib.Path) -> bool:
    """Return True if ffprobe can read the file and reports an audio stream."""
    try:
        out = subprocess.check_output([
            '/opt/homebrew/bin/ffprobe', '-v', 'error', '-show_entries',
            'stream=codec_type', '-of', 'default=noprint_wrappers=1:nokey=1', str(file_path)
        ], stderr=subprocess.STDOUT)
        return b'audio' in out
    except subprocess.CalledProcessError:
        return False

def main():
    bad = []
    for m4a in AUDIO_DIR.glob('*.m4a'):
        if not is_valid_m4a(m4a):
            bad.append(m4a.name)
    if not bad:
        print('All audio tracks are valid.')
    else:
        print('Invalid or unreadable audio tracks:')
        for name in bad:
            print(' -', name)

if __name__ == '__main__':
    main()
