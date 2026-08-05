#!/usr/bin/env python3
"""納品前の実測。WEEKLY_JOB.md の合格基準を、目視ではなく数値で判定する。

**目視で「直った」と判断してはいけない。** 2026-08-03、目視で合格にした30本の
残存ブレは実測 42.8px あった。以来、納品の可否は必ずこの数値で決めている。

  python3 verify_short.py ~/kuronon-work/kaiun_sep/out/*.mp4
  python3 verify_short.py --src ~/kuronon-work/nachi/falls_loop.mp4 out/*.mp4

終了コード 0 = 全項目合格。1 = どれかが基準外(納品しないこと)。
"""
import argparse, json, subprocess, sys, tempfile, os
import numpy as np, cv2

WIN = (220, 236, 640, 680)     # 神域の窓の位置(generator.py の overlay=220:236)
CORE = 0.62                    # 窓の中でマスクが完全不透明な中央部だけを見る
DUR = dict(hook=6.0, harai=16.0, charm=9.0, prayer=12.0, close=6.0)
CUTS = ['hook', 'harai', 'charm', 'prayer', 'close']
LIMITS = dict(dur=(48.8, 49.2), lufs=(-16.0, -13.0), dup=0, silence=0, color=5.0)


def probe(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                          'format=duration:stream=width,height,r_frame_rate,codec_type',
                          '-of', 'json', path], capture_output=True, text=True).stdout
    return json.loads(out)


def loudness(path):
    r = subprocess.run(['ffmpeg', '-nostats', '-i', path, '-filter_complex',
                        'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    return float(r.rsplit('I:', 1)[1].split('LUFS')[0].strip())


def window_frames(path, n=60):
    """窓の中央部だけを、等間隔に n コマ取り出す。"""
    cap = cv2.VideoCapture(path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    idx = np.linspace(0, max(total - 1, 0), min(n, total)).astype(int)
    x, y, w, h = WIN
    cx, cy = int(w * (1 - CORE) / 2), int(h * (1 - CORE) / 2)
    out = []
    for i in idx:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ok, f = cap.read()
        if not ok:
            break
        if f.shape[1] != 1080:                       # 素材(640x680)をそのまま渡した場合
            g = cv2.resize(f, (w, h))
        else:
            g = f[y:y + h, x:x + w]
        out.append(g[cy:h - cy, cx:w - cx])
    cap.release()
    return out


def duplicate_frames(path):
    """窓の中で、隣のコマとほぼ同じものを数える。0 でなければどこかでコマが複製されている。"""
    cap = cv2.VideoCapture(path)
    x, y, w, h = WIN
    prev, d = None, []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(f[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY).astype(np.float32)
        if prev is not None:
            d.append(float(np.abs(g - prev).mean()))
        prev = g
    cap.release()
    if not d:
        return -1, 0.0
    med = float(np.median(d))
    return int(sum(1 for v in d if v < med * 0.25)), med


def audio(path):
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as t:
        wav = t.name
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', path,
                    '-ac', '1', '-ar', '16000', '-f', 'wav', wav], check=True)
    import wave
    w = wave.open(wav); r = w.getframerate()
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)
    w.close(); os.unlink(wav)
    return a, r


def cut_dropouts(path):
    """カットの継ぎ目の直前が無音なら、そこで声が切れている(2026-08-03 の事故)。"""
    a, r = audio(path)
    bad, t = [], 0.0
    for name in CUTS[:-1]:
        t += DUR[name]
        seg = a[int((t - 0.4) * r):int(t * r)]
        if len(seg) and float(np.sqrt((seg ** 2).mean())) < 300:
            bad.append(name)
    return bad


def window_color(path, src):
    """窓の色が元素材とずれていないか。文字が乗るので中央値で見る(平均だと文字に引かれる)。"""
    a = np.concatenate([f.reshape(-1, 3) for f in window_frames(path)])
    b = np.concatenate([f.reshape(-1, 3) for f in window_frames(src)])
    return float(np.abs(np.median(a, 0) - np.median(b, 0)).max())


def check(path, src):
    p = probe(path)
    v = next(s for s in p['streams'] if s['codec_type'] == 'video')
    dur = float(p['format']['duration'])
    fps = eval(v['r_frame_rate'])
    lufs = loudness(path)
    dup, med = duplicate_frames(path)
    drops = cut_dropouts(path)
    color = window_color(path, src) if src else None

    rows = [
        ('尺', f'{dur:.2f}秒', LIMITS['dur'][0] <= dur <= LIMITS['dur'][1]),
        ('画面', f"{v['width']}x{v['height']} {fps:g}fps", (v['width'], v['height'], fps) == (1080, 1920, 30)),
        ('音量', f'{lufs:.1f} LUFS', LIMITS['lufs'][0] <= lufs <= LIMITS['lufs'][1]),
        ('コマの重複', f'{dup}コマ(中央値 {med:.2f})', dup == 0),
        ('音の途切れ', f'{len(drops)}箇所' + (f' {drops}' if drops else ''), not drops),
    ]
    if color is not None:
        rows.append(('窓の色', f'元素材との差 {color:.1f}', color < LIMITS['color']))
    ok = all(r[2] for r in rows)
    print(f'\n{os.path.basename(path)}  {"合格" if ok else "★不合格"}')
    for name, val, good in rows:
        print(f'  {"○" if good else "×"} {name:<10} {val}')
    return ok


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='+')
    ap.add_argument('--src', help='比較用の窓素材(falls_loop.mp4)。省略すると色の検査を飛ばす')
    a = ap.parse_args()
    results = [check(f, a.src) for f in a.files]
    n = sum(results)
    print(f'\n=== {n}/{len(results)} 本 合格 ===')
    print('※測っていない項目: 絵の好み、言葉の響き、縁起物の選び方')
    sys.exit(0 if n == len(results) else 1)
