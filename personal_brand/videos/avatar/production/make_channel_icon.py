#!/usr/bin/env python3
"""チャンネルのプロフィール写真を作る。

YouTube はプロフィール写真を必ず「円」に切り抜き、コメント欄では 48px まで縮める。
だから (1) 顔だけを大きく (2) 明度差を最大に (3) 円からはみ出す位置に何も置かない。

配色は動画・サムネイルと同じ体系(thumbnails/a01_thumbnail_mystic.html)に揃えてある。
くろのんの頭を日食の影に見立て、金のコロナで夜から浮かせるのが標準(eclipse)。

  python3 make_channel_icon.py channel_icon_800.png            # 日食(納品したもの)
  python3 make_channel_icon.py channel_icon_800_sun.png sun    # 日輪(平らな別案)
"""
import cv2, numpy as np, sys, os

D = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(D, 'kuronon_happy.png')
N = 800                       # 出力サイズ(YouTube の推奨は 800x800)

# --- 元絵の実測値(alpha の走査で得た値。素材を差し替えたら測り直すこと) ---------------
HEAD = (620, 540, 230)        # 頭を包む円 cx, cy, r
#   r=230 の根拠: 右 871px から金貨が始まるので 250 未満。下端 770px は
#   赤いネクタイが現れる 775px の手前。どちらも顔の邪魔になるので入れない。
TUFT = (515, 262, 692, 430)   # 寝ぐせ。円からはみ出すので矩形で足す
FACE_CX, FACE_CY = 632, 517   # 目の中心は 658、頭の中心は 620。見た目の重心をとる

# 夜と金(BGR)。サムネイルの #241633 / #140E20 / #0B0710 / #F5C542 / #F7CE58 と同じ
NIGHT_IN, NIGHT_MID, NIGHT_OUT = (0x33, 0x16, 0x24), (0x20, 0x0E, 0x14), (0x10, 0x07, 0x0B)
GOLD, GOLD_HI, CREAM = (0x42, 0xC5, 0xF5), (0x58, 0xCE, 0xF7), (0xE4, 0xF3, 0xFB)


def head_layer(scale, dy):
    """頭だけを切り出す。金貨・翼・体は必ず落とす。"""
    im = cv2.imread(SRC, cv2.IMREAD_UNCHANGED).astype(np.float32)
    m = np.zeros(im.shape[:2], np.uint8)
    cv2.circle(m, HEAD[:2], HEAD[2], 255, -1, cv2.LINE_AA)
    cv2.rectangle(m, TUFT[:2], TUFT[2:], 255, -1)
    im[:, :, 3] = np.minimum(im[:, :, 3], cv2.GaussianBlur(m, (0, 0), 2.0))

    side = int(round(2 * HEAD[2] / scale))          # 頭の直径が出力の scale 倍になる画角
    x, y = FACE_CX - side // 2, FACE_CY - side // 2 + dy
    pad = max(0, -x, -y, x + side - im.shape[1], y + side - im.shape[0])
    if pad:
        im = cv2.copyMakeBorder(im, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
        x, y = x + pad, y + pad
    c = cv2.resize(im[y:y + side, x:x + side], (N, N), interpolation=cv2.INTER_AREA)
    return c[:, :, :3], c[:, :, 3:4] / 255.0


def _r():
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    return np.hypot(xx - N / 2, yy - N / 2)


def _stars(canvas, n, seed):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        rad, th = N / 2 * np.sqrt(rng.random()) * .98, rng.random() * 2 * np.pi
        lay = np.zeros((N, N), np.float32)
        cv2.circle(lay, (int(N / 2 + rad * np.cos(th)), int(N / 2 + rad * np.sin(th))),
                   int(round(rng.random() * 1.6 + .9)), 1.0, -1, cv2.LINE_AA)
        lay = cv2.GaussianBlur(lay, (0, 0), .8)[..., None] * (.20 + .30 * rng.random())
        canvas[:] = canvas * (1 - lay) + np.float32(CREAM) * lay


def eclipse(scale=0.60, dy=4):
    """日食 — 頭を影に見立て、輪郭のすぐ外を金で光らせて夜から起こす。"""
    t = np.clip(_r() / (N / 2), 0, 1)[..., None]
    canvas = (np.float32(NIGHT_IN) * np.clip(1 - t / .52, 0, 1)
              + np.float32(NIGHT_MID) * np.clip(1 - abs(t - .52) / .48, 0, 1)
              + np.float32(NIGHT_OUT) * np.clip((t - .52) / .48, 0, 1))
    _stars(canvas, 16, 3)
    rgb, a = head_layer(scale, dy)
    # コロナは頭の輪郭からの距離で作る。円で描くと寝ぐせのところで途切れる
    dist = cv2.distanceTransform(1 - (a[:, :, 0] > .5).astype(np.uint8), cv2.DIST_L2, 5)
    glow = np.clip(np.exp(-dist / 15.) + np.exp(-dist / 58.) * .26, 0, 1)[..., None]
    canvas = np.clip(canvas + np.float32(GOLD_HI) * glow * .92, 0, 255)
    ring = np.zeros((N, N), np.float32)                       # 外周の細い金の輪
    cv2.circle(ring, (N // 2, N // 2), N // 2 - 26, 1.0, 2, cv2.LINE_AA)
    ring = cv2.GaussianBlur(ring, (0, 0), .7)[..., None] * .30
    canvas = canvas * (1 - ring) + np.float32(GOLD) * ring
    return canvas * (1 - a) + rgb * a, a


def sun(scale=0.50, dy=2):
    """日輪 — 光沢を使わず、夜の地に金の円を平らに置いて頭を収める。"""
    t = np.clip(_r() / (N / 2), 0, 1)[..., None]
    canvas = np.float32(NIGHT_MID) * (1 - t * .55) + np.float32(NIGHT_OUT) * (t * .55)
    _stars(canvas, 18, 11)
    disc = np.zeros((N, N), np.float32)
    cv2.circle(disc, (N // 2, N // 2 - 2), int(N * .36), 1.0, -1, cv2.LINE_AA)
    disc = cv2.GaussianBlur(disc, (0, 0), .8)[..., None]
    canvas = canvas * (1 - disc) + np.float32(GOLD) * disc
    rgb, a = head_layer(scale, dy)
    return canvas * (1 - a) + rgb * a, a


STYLES = {'eclipse': eclipse, 'sun': sun}


def build(out, style='eclipse'):
    img, a = STYLES[style]()
    img = np.clip(img, 0, 255).astype(np.uint8)
    # 四隅まで塗った不透過で出す。透過のまま渡すと、円に切り抜かない表示で角が黒く落ちる
    cv2.imwrite(out, img)

    # 検査1: 円の外(=切り抜きで消える範囲)に絵が残っていないこと
    circ = np.zeros((N, N), np.uint8)
    cv2.circle(circ, (N // 2, N // 2), N // 2 - 6, 255, -1, cv2.LINE_AA)
    outside = int(((a[:, :, 0] > .1) & (circ == 0)).sum())
    # 検査2: 48px に縮めても顔が潰れず、明暗が分かれていること
    L = cv2.cvtColor(cv2.resize(img, (48, 48), interpolation=cv2.INTER_AREA),
                     cv2.COLOR_BGR2LAB)[:, :, 0].astype(float) * 100 / 255
    print(f'{os.path.basename(out)} [{style}]  円外の絵 {outside}px(0であること) / '
          f'48px での明暗差 L* {L.max() - L.min():.1f}')
    return out


if __name__ == '__main__':
    args = sys.argv[1:]
    build(args[0] if args else os.path.join(D, 'channel_icon_800.png'),
          args[1] if len(args) > 1 else 'eclipse')
