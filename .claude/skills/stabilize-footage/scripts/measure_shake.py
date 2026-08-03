#!/usr/bin/env python3
"""ブレ量の実測 — 補正の前後で必ず走らせる

基準コマに対して各コマの特徴点がどれだけ動いたか(中央値)を px で出す。
目視では「直ったように見える」素材が実際には無補正だったという事故を防ぐための計測。

  python3 measure_shake.py 動画.mp4            残存ブレを測る
  python3 measure_shake.py 動画.mp4 --scan 4   最も揺れの少ない4秒区間を探す

読み方: 平均1px未満=合格 / 3px以上=まだ揺れる / 10px以上=補正が効いていない
"""
import argparse, sys
import cv2
import numpy as np

LK = dict(winSize=(31, 31), maxLevel=5,
          criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 40, 0.01))


def load(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    g = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        g.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))
    cap.release()
    if not g:
        sys.exit(f'読み込めませんでした: {path}')
    return g, fps


def track(ref, cur, pts):
    """基準→現コマの対応を取り、往復誤差の小さい点だけ返す(水・炎はここで落ちる)"""
    p1, s1, _ = cv2.calcOpticalFlowPyrLK(ref, cur, pts, None, **LK)
    p0, s0, _ = cv2.calcOpticalFlowPyrLK(cur, ref, p1, None, **LK)
    fb = np.linalg.norm(pts.reshape(-1, 2) - p0.reshape(-1, 2), axis=1)
    good = (s1.ravel() == 1) & (s0.ravel() == 1) & (fb < 0.5)
    return p1.reshape(-1, 2)[good], pts.reshape(-1, 2)[good]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('--scan', type=float, metavar='SEC',
                    help='素材全体を走査し、最も揺れの少ない区間を探す')
    a = ap.parse_args()

    g, fps = load(a.src)
    pts = cv2.goodFeaturesToTrack(g[0], maxCorners=1500, qualityLevel=0.02,
                                  minDistance=12, blockSize=7)
    if pts is None or len(pts) < 30:
        sys.exit('追跡点が足りません。素材が暗すぎるかボケています')

    if a.scan:
        tr = [(0.0, 0.0, 0.0)]
        for i in range(1, len(g)):
            src, dst = track(g[0], g[i], pts)
            M = (cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC,
                                             ransacReprojThreshold=1.0)[0]
                 if len(src) >= 20 else None)
            tr.append(tr[-1] if M is None
                      else (M[0, 2], M[1, 2], np.degrees(np.arctan2(M[1, 0], M[0, 0]))))
        tr = np.array(tr)
        w = int(a.scan * fps)
        if w >= len(tr):
            sys.exit('走査窓が素材より長いです')
        rows = []
        for s in range(0, len(tr) - w + 1, 3):
            seg = tr[s:s + w]
            rng = float(np.hypot(np.ptp(seg[:, 0]), np.ptp(seg[:, 1])))
            rot = float(np.ptp(seg[:, 2]))
            rows.append((rng + rot * 30, s / fps, rng, rot))
        rows.sort()
        print(f'素材 {len(g)/fps:.1f}秒 / 走査窓 {a.scan}秒')
        print('  開始秒    移動幅px   回転幅deg')
        for _, t, rng, rot in rows[:8]:
            print(f'  {t:6.2f}s  {rng:8.1f}   {rot:.3f}')
        print(f'  最も荒い区間: {rows[-1][1]:.2f}s (移動幅 {rows[-1][2]:.1f}px)')
        return

    res = []
    failed = 0
    for i in range(1, len(g)):
        src, dst = track(g[0], g[i], pts)
        if len(src) < 20:
            failed += 1
            continue
        res.append(float(np.median(np.linalg.norm(src - dst, axis=1))))
    if not res:
        sys.exit('全コマで追跡に失敗しました')
    mean, worst = float(np.mean(res)), float(np.max(res))
    print(f'コマ数 = {len(g)}  追跡失敗 = {failed}')
    print(f'平均残存ブレ = {mean:.3f} px')
    print(f'最大残存ブレ = {worst:.2f} px (コマ {int(np.argmax(res)) + 1})')
    print(f'1px超のコマ = {sum(1 for r in res if r > 1.0)} / {len(res)}')
    verdict = ('合格 — 1080pに合成しても知覚できません' if mean < 1.0 else
               'まだ揺れます — --order 3 か切り出し矩形の見直しを' if mean < 10 else
               '補正が効いていません — 手法の選択から見直してください')
    print(f'判定: {verdict}')


if __name__ == '__main__':
    main()
