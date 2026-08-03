#!/usr/bin/env python3
"""完成した動画の中で画が飛ぶ瞬間を秒単位で特定する

隣り合うコマ同士のズレを位相相関で測る。ズレが突出した箇所が継ぎ目・カット・素材の抜け。
固定した素材を合成したあとでも、合成側の不具合(オーバーレイの取りこぼし等)で
画が動くことがあるため、素材の検証(measure_shake.py)とは別に完成品でも測る。

  python3 find_jumps.py 完成.mp4 X Y W H [しきい値px]

X Y W H は測る領域。文字の載る範囲を避けると、映像だけの動きを見られる。
相関値が 0 に近い箇所は「前後のコマが別物」= 素材が抜けているか切り替わっている。
"""
import cv2, numpy as np, sys
SRC = sys.argv[1]
X, Y, W, H = (int(v) for v in sys.argv[2:6])
THR = float(sys.argv[6]) if len(sys.argv) > 6 else 1.5

cap = cv2.VideoCapture(SRC)
fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
prev = None; i = 0; rows = []
win = None
while True:
    ok, f = cap.read()
    if not ok: break
    g = cv2.cvtColor(f[Y:Y+H, X:X+W], cv2.COLOR_BGR2GRAY).astype(np.float32)
    if win is None: win = cv2.createHanningWindow((g.shape[1], g.shape[0]), cv2.CV_32F)
    if prev is not None:
        (dx, dy), resp = cv2.phaseCorrelate(prev, g, win)
        rows.append((i/fps, float(np.hypot(dx, dy)), resp))
    prev = g; i += 1
cap.release()
d = np.array([r[1] for r in rows])
print(f'コマ数={i}  コマ間ズレ 中央値={np.median(d):.3f}px  平均={d.mean():.3f}px')
sp = [r for r in rows if r[1] > THR]
print(f'{THR}px を超える跳び = {len(sp)} 箇所')
for t, v, resp in sp[:40]:
    print(f'  {t:7.2f}s   {v:7.2f}px   相関={resp:.3f}')
