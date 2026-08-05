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


def window_median(path):
    """窓の中身の「時間方向の中央値」。コマの対応づけを気にせず色だけを比べられる。"""
    x, y, w, h = WIN
    cap = cv2.VideoCapture(path)
    F = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        F.append(f[y:y + h, x:x + w] if f.shape[1] == 1080 else f)
    cap.release()
    return np.median(np.stack(F), 0)


def comparable_area(mask_png, ov_globs):
    """色を比べてよい画素だけを残す。

    ここを間違えると数字が意味を失う(2026-08-05、最初の実装で 13 と出て不合格にした。
    実際は「窓の外」と「文字の上」を数えていただけで、正しく測ると 2.0 だった)。

    - マスクが完全不透明な範囲 …… ここ以外は背景と混ざるので元素材と一致しない
    - どのテロップの文字も来ない範囲 …… 文字の上で測ると縁取りを色ずれと誤検出する
    """
    import glob
    x, y, w, h = WIN
    mk = cv2.imread(mask_png, cv2.IMREAD_GRAYSCALE)
    opaque = cv2.erode((mk >= 250).astype(np.uint8), np.ones((7, 7), np.uint8))
    cover = None
    for pat in ov_globs:
        for p in glob.glob(pat):
            a = cv2.imread(p, cv2.IMREAD_UNCHANGED)[y:y + h, x:x + w, 3]
            cover = a.copy() if cover is None else np.maximum(cover, a)
    if cover is None:
        return opaque.astype(bool)
    notext = cv2.erode((cover == 0).astype(np.uint8), np.ones((11, 11), np.uint8))
    return (opaque & notext).astype(bool)


def duplicate_frames(path):
    """コマが複製されていないか。複製されると滝が 10Hz でカクつく(24fps素材を30fpsに載せた事故)。

    判定は「隣のコマとの平均差」ではなく「**動いた画素の割合**」で見る。
    平均差だと、水がたまたま静かなコマを複製と誤検出する(2026-08-05、圧縮後に3コマ誤検出した)。

    しきい値 0.5% の根拠: 同じ動画をわざと 24fps 経由にして測ると 137コマ、
    正しい30fps通しなら 0コマ。間が大きく空いているので取り違えようがない。
    """
    cap = cv2.VideoCapture(path)
    x, y, w, h = WIN
    prev, moved = None, []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(f[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY).astype(np.float32)
        if prev is not None:
            moved.append(float((np.abs(g - prev) > 2).mean()))
        prev = g
    cap.release()
    if not moved:
        return -1, 0.0
    return int(sum(1 for v in moved if v < 0.005)), float(np.median(moved))


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


def window_color(path, src, area):
    """窓の色が元素材とずれていないか。比べてよい画素だけで見る。"""
    d = np.abs(window_median(path) - window_median(src)).max(2)[area]
    return float(np.median(d)), float(d.mean())


def check(path, src, area=None):
    p = probe(path)
    v = next(s for s in p['streams'] if s['codec_type'] == 'video')
    dur = float(p['format']['duration'])
    fps = eval(v['r_frame_rate'])
    lufs = loudness(path)
    dup, med = duplicate_frames(path)
    drops = cut_dropouts(path)
    color = window_color(path, src, area) if src is not None and area is not None else None

    rows = [
        ('尺', f'{dur:.2f}秒', LIMITS['dur'][0] <= dur <= LIMITS['dur'][1]),
        ('画面', f"{v['width']}x{v['height']} {fps:g}fps", (v['width'], v['height'], fps) == (1080, 1920, 30)),
        ('音量', f'{lufs:.1f} LUFS', LIMITS['lufs'][0] <= lufs <= LIMITS['lufs'][1]),
        ('コマの重複', f'{dup}コマ(動いた画素の中央値 {med*100:.1f}%)', dup == 0),
        ('音の途切れ', f'{len(drops)}箇所' + (f' {drops}' if drops else ''), not drops),
    ]
    if color is not None:
        med, avg = color
        rows.append(('窓の色', f'元素材との差 中央値{med:.1f} 平均{avg:.2f}', med < LIMITS['color']))
    ok = all(r[2] for r in rows)
    print(f'\n{os.path.basename(path)}  {"合格" if ok else "★不合格"}')
    for name, val, good in rows:
        print(f'  {"○" if good else "×"} {name:<10} {val}')
    return ok


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='+')
    ap.add_argument('--src', help='比較用の窓素材(falls_loop.mp4)。省略すると色の検査を飛ばす')
    ap.add_argument('--mask', help='窓のマスク(nachi/mask.png)')
    ap.add_argument('--overlays', nargs='*', default=[],
                    help='テロップPNGの場所(glob可)。日替わりのぶんも必ず含めること')
    a = ap.parse_args()
    area = comparable_area(a.mask, a.overlays) if (a.src and a.mask) else None
    if area is not None:
        print(f'色を比べる画素: {area.sum()}px(窓の {100 * area.mean():.1f}%)')
    results = [check(f, a.src, area) for f in a.files]
    n = sum(results)
    print(f'\n=== {n}/{len(results)} 本 合格 ===')
    print('※測っていない項目: 絵の好み、言葉の響き、縁起物の選び方')
    sys.exit(0 if n == len(results) else 1)
