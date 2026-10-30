#!/usr/bin/env python3
"""Masukkan satu folder UPLOAD-* ke antrean IG (GitHub) sekaligus jadwalkan Page FB lewat API.

Pakai: python3 antrikan.py <folder-upload> 2026-11-02T18:00:00+07:00 [--tanpa-fb]
"""
import json, os, subprocess, sys

REPO = 'naufalicsme/penasaran-jadwal'
HERE = os.path.dirname(os.path.abspath(__file__))
FB = os.path.expanduser('~/Downloads/Claude File 3/edukasi-shorts/uploader/fb_upload.py')


def main():
    folder, at = os.path.abspath(sys.argv[1]), sys.argv[2]
    files = os.listdir(folder)
    mp4 = next(f for f in sorted(files) if f.endswith('.mp4'))
    cover = next(f for f in sorted(files) if f.startswith('cover') and f.endswith('.jpg'))
    nama = os.path.basename(folder).replace('UPLOAD-', '')
    tag = f'v-{nama}'
    subprocess.run(['gh', 'release', 'create', tag, '-R', REPO, '--title', nama, '--notes', f'Jadwal {at}', os.path.join(folder, mp4), os.path.join(folder, cover)], check=True)
    base = f'https://github.com/{REPO}/releases/download/{tag}'
    subprocess.run(['git', '-C', HERE, 'pull', '-q', '--rebase'], check=True)
    p = os.path.join(HERE, 'jadwal.json')
    q = json.load(open(p))
    q.append(dict(nama=nama, at=at, tag=tag, video=f'{base}/{mp4}', cover=f'{base}/{cover}', caption=open(os.path.join(folder, 'caption-instagram.txt')).read().strip()))
    json.dump(q, open(p, 'w'), ensure_ascii=False, indent=1)
    subprocess.run(['git', '-C', HERE, 'add', 'jadwal.json'], check=True)
    subprocess.run(['git', '-C', HERE, 'commit', '-q', '-m', f'Antre IG: {nama} {at}\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>'], check=True)
    subprocess.run(['git', '-C', HERE, 'push', '-q'], check=True)
    print(f'IG antre: {nama} {at}')
    if '--tanpa-fb' not in sys.argv:
        subprocess.run([sys.executable, FB, folder, '--at', at], check=True)


if __name__ == '__main__':
    main()
