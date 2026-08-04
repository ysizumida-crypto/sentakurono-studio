# 継ぎ目のない輪を作る — 等速のまま、尾と頭を正確に溶かす
#
# ffmpeg の xfade は透過率が最後のコマで 1.0 に届かず、尾の映像がわずかに残る。
# その残りが輪の境目で消えるため、一瞬だけ画が跳ねて「繋いである」と分かってしまう。
# ここでは透過率を 0 から 1 まで端点を含めて動かし、最後のコマを頭の映像そのものにする。
import cv2, numpy as np, subprocess, sys

SRC, OUT = sys.argv[1], sys.argv[2]
XF = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5   # 溶かす秒数

cap = cv2.VideoCapture(SRC)
fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
fr = []
while True:
    ok, f = cap.read()
    if not ok: break
    fr.append(f)
cap.release()
N = len(fr); K = int(round(XF * fps))
assert N > 3 * K, f'素材が短すぎます ({N}コマ、溶かしに{K}コマ必要)'
H, W = fr[0].shape[:2]

# 輪 = 中間部(頭K..尾K) + 溶かし部(尾K コマ ← 頭K コマ)
mid = fr[K:N - K]
blend = []
for i in range(K):
    t = i / (K - 1)                      # 端点を含めて 0→1
    a = t * t * (3 - 2 * t)              # なめらかに(端で速度ゼロ)
    tail = fr[N - K + i].astype(np.float32)
    head = fr[i].astype(np.float32)
    blend.append(np.clip(tail * (1 - a) + head * a, 0, 255).astype(np.uint8))
loop = mid + blend
# 輪の最後は頭の最終コマ = 中間部の1つ前。次の周の先頭に自然につながる。

p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24',
                      '-s', f'{W}x{H}', '-r', str(int(fps)), '-i', '-', '-c:v', 'libx264',
                      '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
for f in loop:
    p.stdin.write(np.ascontiguousarray(f).tobytes())
p.stdin.close(); p.wait()
print(f'{len(loop)}コマ / {len(loop)/fps:.2f}秒 の輪を書き出しました: {OUT}', flush=True)
