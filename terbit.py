#!/usr/bin/env python3
"""Penerbit Reels IG Penasaran Deh (dijalankan GitHub Actions tiap 5 menit).

API IG tidak punya fitur jadwal, jadi antrean di jadwal.json dicek di sini: video yang jamnya sudah lewat
diterbitkan satu per run (container → tunggu proses → media_publish), lalu file di Releases dihapus.
Pakai: META_TOKEN=... python3 terbit.py [--dry <url-video> <url-cover>]
"""
import datetime as dt, json, os, subprocess, sys, time, urllib.error, urllib.parse, urllib.request

IG = '17841441408055618'
PAGE = '1359830100552007'
G = 'https://graph.facebook.com/v21.0'
Q = 'jadwal.json'
MAKS_COBA = 3


def http(method, url, data=None):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method), timeout=120) as r:
            return json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or b'{}')


def token_page():
    sys_tok = os.environ['META_TOKEN']
    return http('GET', f'{G}/{PAGE}?fields=access_token&access_token={urllib.parse.quote(sys_tok)}')['access_token']


def container(tok, video, cover, caption):
    p = dict(media_type='REELS', video_url=video, cover_url=cover, caption=caption, share_to_feed='true', is_ai_generated='false', access_token=tok)
    c = http('POST', f'{G}/{IG}/media', urllib.parse.urlencode(p).encode())
    if 'id' not in c:
        raise RuntimeError(f'container gagal: {c.get("error", c)}')
    for _ in range(60):
        s = http('GET', f"{G}/{c['id']}?fields=status_code,status&access_token={tok}")
        if s.get('status_code') == 'FINISHED':
            return c['id']
        if s.get('status_code') in ('ERROR', 'EXPIRED'):
            raise RuntimeError(f'proses gagal: {s.get("status")}')
        time.sleep(10)
    raise RuntimeError('proses belum selesai setelah 10 menit')


def simpan(q, pesan):
    json.dump(q, open(Q, 'w'), ensure_ascii=False, indent=1)
    for a in (['add', Q], ['commit', '-m', pesan], ['pull', '-q', '--rebase'], ['push', '-q']):
        subprocess.run(['git', *a], check=True)


def main():
    tok = token_page()
    if len(sys.argv) > 1 and sys.argv[1] == '--dry':
        print('Container siap (tidak diterbitkan):', container(tok, sys.argv[2], sys.argv[3], 'tes'))
        return
    q = json.load(open(Q))
    now = dt.datetime.now(dt.timezone.utc)
    it = next((i for i in q if not i.get('hasil') and i.get('gagal', 0) < MAKS_COBA and dt.datetime.fromisoformat(i['at']) <= now), None)
    if not it:
        print('Tidak ada video yang waktunya tayang')
        return
    try:
        cid = container(tok, it['video'], it['cover'], it['caption'])
        p = http('POST', f'{G}/{IG}/media_publish', urllib.parse.urlencode(dict(creation_id=cid, access_token=tok)).encode())
        if 'id' not in p:
            raise RuntimeError(f'publish gagal: {p.get("error", p)}')
        it['hasil'] = http('GET', f"{G}/{p['id']}?fields=permalink&access_token={tok}").get('permalink', p['id'])
    except Exception as e:
        it['gagal'] = it.get('gagal', 0) + 1
        it['error'] = str(e)[:300]
        simpan(q, f"Gagal coba {it['gagal']}: {it['nama']}")
        sys.exit(f"{it['nama']}: {e}")
    subprocess.run(['gh', 'release', 'delete', it['tag'], '--yes', '--cleanup-tag'], check=False)
    simpan(q, f"Tayang IG: {it['nama']}")
    print('Tayang:', it['hasil'])


if __name__ == '__main__':
    main()
