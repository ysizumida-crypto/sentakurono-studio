---
name: stabilize-footage
description: 手持ち撮影の動画のブレ・揺れを補正するスキル。「ブレを直して」「手ブレ補正」「揺れている」「固定して」「stabilize」等で発動。三脚で据えたように完全固定するバーチャル三脚モードと、動きを残して滑らかにする通常モードの2種を使い分ける。
---

# stabilize-footage — 手ブレ補正(バーチャル三脚)

ffmpeg の vid.stab フィルタによる2パス補正。くろのんチャンネルでは那智の滝の実写素材の固定に使用(2026-08-02 確立)。

## モード選択

- **バーチャル三脚(tripod)**: 背景を完全静止させたいとき(神域の窓など「据えた画」)。1コマ目を基準に全コマを釘付けにする
- **通常スムージング**: パン・歩き撮りなど、動き自体は残して滑らかにしたいとき

## 手順(バーチャル三脚)

```bash
# パス1: 基準コマに対する揺れを検出(shakiness=10 は最大感度)
ffmpeg -y -ss <開始> -t <秒数> -i input.mov \
  -vf "vidstabdetect=tripod=1:shakiness=10:accuracy=15:result=stab.trf" -f null -

# パス2: 揺れを打ち消して固定(zoom で補正縁の黒を隠す)
ffmpeg -y -ss <開始> -t <秒数> -i input.mov -an \
  -vf "vidstabtransform=tripod=1:input=stab.trf:zoom=10:optzoom=0:interpol=bicubic:crop=black" \
  -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p stabilized.mp4
```

通常モードはパス1の `tripod=1` を外し、パス2を `vidstabtransform=input=stab.trf:smoothing=30:zoom=5` にする。

## 注意点

- **-ss/-t は両パスで同一にする**(検出と変換でコマがずれると破綻する)
- zoom=10(10%拡大)でも端に補正縁が残ることがある。最終クロップは**左右とも50px以上内側**から取る
- 検証方法: 数秒離れた2コマを `blend=difference` で比較。静止物が黒く沈めば固定成功(動くべきもの=水・炎だけが浮かぶ)
  ```bash
  ffmpeg -y -ss 1 -i stabilized.mp4 -frames:v 1 a.png
  ffmpeg -y -ss 5 -i stabilized.mp4 -frames:v 1 b.png
  ffmpeg -y -i a.png -i b.png -filter_complex "blend=difference,eq=brightness=0.3" diff.png
  ```
- ループ素材にするときは順再生+逆再生のパリンドローム連結(`-vf reverse` → concat)で継ぎ目を消す
- 揺れが激しすぎる素材は tripod では歪む。その場合は通常モード+強スムージングに切り替える
