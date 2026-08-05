#!/usr/bin/env python3
"""チャンネルのプロフィール写真を作る。

YouTube はプロフィール写真を必ず「円」に切り抜き、コメント欄では 48px まで縮める。
だから (1) 顔だけを大きく (2) 背景は明度差の大きい色 (3) 円からはみ出す位置に何も置かない。
くろのんは真っ黒なので、背景はブランドの金にして明暗差を最大にする。

  python3 make_channel_icon.py channel_icon_800.png 0.70 8   ← 納品した値
"""
import cv2, numpy as np, sys, os

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kuronon_happy.png')
N = 800                       # 出力サイズ(YouTube の推奨は 800x800)

# --- 元絵の実測値(alpha の走査で得た値。素材を差し替えたら測り直すこと) ---------------
HEAD = (620, 540, 230)        # 頭を包む円 cx, cy, r
#   r=230 の根拠: 右 871px から金貨が始まるので 250 未満。下端 770px は
#   赤いネクタイが現れる 775px の手前。どちらも入れてはいけない。
TUFT = (515, 262, 692, 430)   # 寝ぐせ。円からはみ出すので矩形で足す
FACE_CX = 632                 # 目の中心は 658、頭の中心は 620。見た目の重心をとる
FACE_CY = 517                 # 寝ぐせの天(262)と顎(770)の中間


def head_alpha(shape):
    """頭だけを残すマスク。金貨・翼・体を確実に落とす。"""
    m = np.zeros(shape[:2], np.uint8)
    cv2.circle(m, HEAD[:2], HEAD[2], 255, -1, cv2.LINE_AA)
    cv2.rectangle(m, TUFT[:2], TUFT[2:], 255, -1)
    return cv2.GaussianBlur(m, (0, 0), 2.0)   # 端を 2px ぼかして輪郭のギザギザを消す


def gold_bg(n):
    """中心が明るい金の円盤。BGR。"""
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    t = (np.clip(np.hypot(xx - n / 2, yy - n / 2) / (n / 2), 0, 1) ** 1.35)[..., None]
    c_in, c_out = np.float32([0x6B, 0xD8, 0xFF]), np.float32([0x24, 0x9C, 0xDE])
    return c_in * (1 - t) + c_out * t


def build(out, scale=0.74, dy=0):
    im = cv2.imread(SRC, cv2.IMREAD_UNCHANGED).astype(np.float32)
    im[:, :, 3] = np.minimum(im[:, :, 3], head_alpha(im.shape))

    side = int(round(2 * HEAD[2] / scale))          # 頭の直径が出力の scale 倍になる画角
    x, y = FACE_CX - side // 2, FACE_CY - side // 2 + dy
    pad = max(0, -x, -y, x + side - im.shape[1], y + side - im.shape[0])
    if pad:
        im = cv2.copyMakeBorder(im, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
        x, y = x + pad, y + pad
    crop = cv2.resize(im[y:y + side, x:x + side], (N, N), interpolation=cv2.INTER_AREA)
    a = crop[:, :, 3:4] / 255.0

    canvas = gold_bg(N)
    # 頭の落ち影。金の面に浮かず、小さくしても輪郭が締まる
    sh = cv2.GaussianBlur(np.roll(a[:, :, 0], 14, axis=0), (0, 0), 16)[..., None]
    canvas = canvas * (1 - sh * 0.34)
    # 円の内側に細い暗金の輪。白背景でも縁が溶けない
    rr = np.zeros((N, N), np.float32)
    cv2.circle(rr, (N // 2, N // 2), N // 2 - 9, 1.0, 10, cv2.LINE_AA)
    rr = cv2.GaussianBlur(rr, (0, 0), 1.2)[..., None]
    canvas = canvas * (1 - rr * .5) + np.float32([0x1C, 0x74, 0xB4]) * rr * .5

    img = np.clip(canvas * (1 - a) + crop[:, :, :3] * a, 0, 255).astype(np.uint8)

    # 四隅まで金で塗った不透明の正方形で出す。透過のまま渡すと、
    # 円に切り抜かない場所(アップロード画面の下書き表示など)で角が黒く落ちる。
    cv2.imwrite(out, img)

    # 検査: 円の外(=切り抜きで消える範囲)に絵が残っていないこと
    circ = np.zeros((N, N), np.uint8)
    cv2.circle(circ, (N // 2, N // 2), N // 2 - 6, 255, -1, cv2.LINE_AA)
    outside = (crop[:, :, 3] > 24) & (circ == 0)
    print(f'{out}: 円の外に出た絵 {int(outside.sum())}px(0であること)')
    return out


if __name__ == '__main__':
    args = sys.argv[1:]
    build(args[0] if args else 'icon.png',
          float(args[1]) if len(args) > 1 else 0.74,
          int(args[2]) if len(args) > 2 else 0)
