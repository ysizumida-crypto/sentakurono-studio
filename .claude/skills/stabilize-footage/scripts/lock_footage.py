#!/usr/bin/env python3
"""絶対固定(バーチャル三脚) — 視差吸収型スタビライザ

手持ち撮影ではカメラ位置そのものが動くため、手前と奥の被写体は違う量だけ動く(視差)。
平行移動+回転+拡大の相似変換は全画素に同じ動きを仮定するので、原理的に視差を消せない。
そこで画面内で滑らかに変化する動きを表せる2〜3次多項式を当てはめ、視差ごと打ち消す。

滝の水・炎・波など「動いていて当然のもの」は順逆追跡の往復誤差で自動的に除外され、
通行人など局所的に動くものは残差トリミングで除外される。マスクの手描きは不要。

  python3 lock_footage.py 入力.mp4 出力.mp4 [--crop CX CY CW CH] [--order 3]
"""
import argparse, subprocess, sys
import cv2
import numpy as np


def read_frames(path):
    cap = cv2.VideoCapture(path)
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    cap.release()
    if not frames:
        sys.exit(f'読み込めませんでした: {path}')
    return frames


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('out')
    ap.add_argument('--crop', nargs=4, type=int, metavar=('CX', 'CY', 'CW', 'CH'),
                    help='最終的に画面に映る矩形。この範囲の固定精度を最優先する')
    ap.add_argument('--order', type=int, default=3, choices=(1, 2, 3),
                    help='1=相似変換 2=2次 3=3次(既定・最も強力)')
    ap.add_argument('--ref', type=int, default=0, help='基準コマ番号')
    ap.add_argument('--crf', type=int, default=14)
    a = ap.parse_args()

    frames = read_frames(a.src)
    H, W = frames[0].shape[:2]
    grays = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]
    ref_g = grays[a.ref]
    CX, CY, CW, CH = a.crop if a.crop else (0, 0, W, H)
    print(f'frames={len(frames)} size={W}x{H} crop=({CX},{CY}) {CW}x{CH} order={a.order}', flush=True)

    # 追跡点は「映る範囲+15%の余白」から拾う。この範囲の精度を最大化するため。
    mx, my = int(CW * 0.15), int(CH * 0.15)
    mask = np.zeros((H, W), np.uint8)
    mask[max(0, CY - my):min(H, CY + CH + my), max(0, CX - mx):min(W, CX + CW + mx)] = 255
    ref_pts = cv2.goodFeaturesToTrack(ref_g, maxCorners=4000, qualityLevel=0.004,
                                      minDistance=6, blockSize=7, mask=mask)
    if ref_pts is None or len(ref_pts) < 100:
        sys.exit('追跡点が足りません。素材が暗すぎるかボケています')
    print(f'追跡点 = {len(ref_pts)}', flush=True)

    LK = dict(winSize=(31, 31), maxLevel=5,
              criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 60, 0.003))
    SX, SY = W / 2.0, H / 2.0   # 数値安定のための正規化

    def design(x, y):
        u, v = (x - SX) / SX, (y - SY) / SY
        cols = [np.ones_like(u), u, v]
        if a.order >= 2:
            cols += [u * u, u * v, v * v]
        if a.order >= 3:
            cols += [u * u * u, u * u * v, u * v * v, v * v * v]
        return np.column_stack(cols)

    def fit(src, dst):
        """src → dst の多項式を、残差の大きい点を捨てながら当てはめる"""
        keep = np.ones(len(src), bool)
        coef = None
        for _ in range(5):
            A = design(src[keep, 0], src[keep, 1])
            coef, *_ = np.linalg.lstsq(A, dst[keep], rcond=None)
            res = np.linalg.norm(design(src[:, 0], src[:, 1]) @ coef - dst, axis=1)
            thr = max(1.0, 2.5 * np.median(res[keep]))
            new = res < thr
            if new.sum() < 120 or (new == keep).all():
                break
            keep = new
        return coef, int(keep.sum())

    gx, gy = np.meshgrid(np.arange(CX, CX + CW, dtype=np.float32),
                         np.arange(CY, CY + CH, dtype=np.float32))
    Agrid = design(gx.ravel(), gy.ravel())

    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo',
                          '-pix_fmt', 'bgr24', '-s', f'{CW}x{CH}', '-r', '30', '-i', '-',
                          '-c:v', 'libx264', '-preset', 'slow', '-crf', str(a.crf),
                          '-pix_fmt', 'yuv420p', a.out], stdin=subprocess.PIPE)
    margin = 1e9
    for i, (f, g) in enumerate(zip(frames, grays)):
        if i == a.ref:
            p.stdin.write(np.ascontiguousarray(f[CY:CY + CH, CX:CX + CW]).tobytes())
            continue
        p1, s1, _ = cv2.calcOpticalFlowPyrLK(ref_g, g, ref_pts, None, **LK)
        p0, s0, _ = cv2.calcOpticalFlowPyrLK(g, ref_g, p1, None, **LK)
        fb = np.linalg.norm(ref_pts.reshape(-1, 2) - p0.reshape(-1, 2), axis=1)
        # 往復して戻ってこない点 = 水・炎など動くもの。ここで自動的に落ちる
        good = (s1.ravel() == 1) & (s0.ravel() == 1) & (fb < 0.3)
        dst, src = ref_pts.reshape(-1, 2)[good], p1.reshape(-1, 2)[good]
        if len(src) < 80:
            print(f'  !! frame {i}: 有効点 {len(src)} — 精度が落ちます', flush=True)
        # remap は「出力座標→入力座標」の逆写像を要求するので、基準→現コマ方向に当てはめる
        coef, nin = fit(dst, src)
        xy = Agrid @ coef
        mapx = xy[:, 0].reshape(CH, CW).astype(np.float32)
        mapy = xy[:, 1].reshape(CH, CW).astype(np.float32)
        margin = min(margin, mapx.min(), mapy.min(), W - 1 - mapx.max(), H - 1 - mapy.max())
        w = cv2.remap(f, mapx, mapy, interpolation=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        p.stdin.write(np.ascontiguousarray(w).tobytes())
        if i % 50 == 0:
            print(f'  frame {i} ok (採用点 {nin})', flush=True)
    p.stdin.close(); p.wait()

    print(f'切り出しの余裕 = {margin:.1f}px', flush=True)
    if margin < 0:
        print(f'  → 黒縁が入ります。--crop を各辺 {abs(margin):.0f}px 以上内側に詰めて再実行してください', flush=True)
    print(f'書き出し完了: {a.out}\n  次は measure_shake.py で検証してください', flush=True)


if __name__ == '__main__':
    main()
