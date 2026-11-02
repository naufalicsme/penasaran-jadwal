#!/usr/bin/env python3
"""Masukkan satu folder UPLOAD-* ke antrean IG (GitHub). Page FB distop sejak 1 Nov 2026 (19 reel cuma 13 tayangan).

Pakai: python3 antrikan.py <folder-upload> 2026-11-02T18:00:00+07:00 [--dengan-fb]
"""
import json, os, subprocess, sys, urllib.parse, urllib.request

REPO = 'naufalicsme/penasaran-jadwal'
HERE = os.path.dirname(os.path.abspath(__file__))
FB = os.path.expanduser('~/Downloads/Claude File 3/edukasi-shorts/uploader/fb_upload.py')
MAKS_CAPTION = 2200


def token_github():
    o = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n\n',
                       capture_output=True, text=True, check=True, timeout=30)
    return dict(l.split('=', 1) for l in o.stdout.splitlines() if '=' in l)['password']


def github(token, method, url, data=None, tipe='application/json'):
    req = urllib.request.Request(url, data=data, method=method, headers={
        'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json', 'Content-Type': tipe})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read() or b'{}')


def buat_release(tag, nama, at, berkas):
    token = token_github()
    rel = github(token, 'POST', f'https://api.github.com/repos/{REPO}/releases',
                 json.dumps(dict(tag_name=tag, name=nama, body=f'Jadwal {at}')).encode())
    for path, tipe in berkas:
        q = urllib.parse.urlencode(dict(name=os.path.basename(path)))
        github(token, 'POST', f'https://uploads.github.com/repos/{REPO}/releases/{rel["id"]}/assets?{q}',
               open(path, 'rb').read(), tipe)


def baca_caption(folder):
    p = os.path.join(folder, 'caption-instagram.txt')
    caption = open(p).read().strip() if os.path.exists(p) else ''
    if not caption:
        sys.exit(f'Caption kosong atau tidak ada: {p}')
    if len(caption) > MAKS_CAPTION:
        sys.exit(f'Caption terlalu panjang ({len(caption)} > {MAKS_CAPTION}): {p}')
    return caption


def main():
    folder, at = os.path.abspath(sys.argv[1]), sys.argv[2]
    files = os.listdir(folder)
    mp4 = next(f for f in sorted(files) if f.endswith('.mp4'))
    cover = next(f for f in sorted(files) if f.startswith('cover') and f.endswith('.jpg'))
    nama = os.path.basename(folder).replace('UPLOAD-', '')
    tag = f'v-{nama}'
    caption = baca_caption(folder)
    buat_release(tag, nama, at, [(os.path.join(folder, mp4), 'video/mp4'), (os.path.join(folder, cover), 'image/jpeg')])
    base = f'https://github.com/{REPO}/releases/download/{tag}'
    subprocess.run(['git', '-C', HERE, 'pull', '-q', '--rebase'], check=True)
    p = os.path.join(HERE, 'jadwal.json')
    q = json.load(open(p))
    q.append(dict(nama=nama, at=at, tag=tag, video=f'{base}/{mp4}', cover=f'{base}/{cover}', caption=caption))
    json.dump(q, open(p, 'w'), ensure_ascii=False, indent=1)
    subprocess.run(['git', '-C', HERE, 'add', 'jadwal.json'], check=True)
    subprocess.run(['git', '-C', HERE, 'commit', '-q', '-m', f'Antre IG: {nama} {at}\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>'], check=True)
    subprocess.run(['git', '-C', HERE, 'push', '-q'], check=True)
    print(f'IG antre: {nama} {at}')
    if '--dengan-fb' in sys.argv:
        subprocess.run([sys.executable, FB, folder, '--at', at], check=True)


if __name__ == '__main__':
    main()
