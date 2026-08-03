# 神域の窓 — 那智の滝素材の正本仕様

社長撮影(IMG_0270.mov・iPhone縦位置13.0秒)を、全動画に共通で使う「神域の窓」素材に加工する手順の正本。
2026-08-03 に**全面やり直し**。それ以前の素材は手ブレが残っていたため使用禁止。

## 事故の記録(必読)

初回制作では ffmpeg の `vidstabdetect/transform` をバーチャル三脚モードで通し、目視で「固定できた」と判断して30本以上を納品した。
後日 px 単位で実測したところ、**残存ブレは平均42.8px・最大235px** で、ほぼ無補正だった。原因は補正幅の不足:

- 元素材の手ブレは最大 **220px・2.2度**
- `vidstabtransform` の `zoom=10` は元画角の10%(=108px)しか補正できない
- 補正しきれない分はそのまま残るが、処理自体はエラーなく完了するため気づけない

**教訓**: 補正後は必ず `stabilize-footage` スキルの `measure_shake.py` で実測し、数値で合否を判断する。

## 現行の加工手順

```bash
SK=.claude/skills/stabilize-footage/scripts

# 1. 回転メタデータを適用して正立させ、4.0〜11.0秒を切り出す(滝と鳥居が最もよく収まる区間)
ffmpeg -y -ss 4.0 -t 7.0 -i IMG_0270.mov -an -c:v libx264 -preset slow -crf 12 -pix_fmt yuv420p src_rot.mp4

# 2. 窓に映る矩形(640x680)を最優先で絶対固定する
python3 $SK/lock_footage.py src_rot.mp4 win.mp4 --crop 284 707 640 680 --order 3

# 3. 実測(平均1px未満で合格)
python3 $SK/measure_shake.py win.mp4

# 4. 末尾20コマは被写体が画角から外れ精度が落ちるため切り落とす
ffmpeg -y -i win.mp4 -frames:v 190 -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p win_trim.mp4

# 5. 1.3倍にゆっくりして神秘系の色に整え、順再生+逆再生で継ぎ目のないループにする
G="eq=saturation=0.62:contrast=1.06:brightness=-0.09,colorbalance=rm=.08:gm=.03:bm=-.08:rh=.05:bh=-.05"
ffmpeg -y -i win_trim.mp4 -filter:v "setpts=1.3*PTS,$G" -an -c:v libx264 -preset slow -crf 15 -pix_fmt yuv420p fwd.mp4
ffmpeg -y -i fwd.mp4 -vf reverse -an -c:v libx264 -preset slow -crf 15 -pix_fmt yuv420p rev.mp4
printf "file 'fwd.mp4'\nfile 'rev.mp4'\n" > cc.txt
ffmpeg -y -f concat -safe 0 -i cc.txt -c copy falls_loop.mp4
```

**成果物**: `falls_loop.mp4` — 640x680・**16.4667秒**・平均残存ブレ 0.60px

## 実測値

| 状態 | 平均残存ブレ | 最大 |
|---|---|---|
| 元素材 | 119.6px | 247.6px |
| 旧納品(vid.stab) | 42.8px | 235.2px |
| 現行 | **0.60px** | 1.21px |
| 合成後のショート実測 | **0.35px** | 0.49px |

## 生成器側の設定

ループ長を変えたら、参照している定数を必ず全部更新する(参照位置がずれて静止画のように見える事故が起きる)。

| ファイル | 定数 |
|---|---|
| `personal_brand/shorts/september_batch/generator.py` | `WINDUR = 16.4667` |
| `personal_brand/shorts/specials/build_sayonara.py` | `woff % 16.4667` |
| `personal_brand/videos/engine/lf_engine.py` | `% 16.4667`(2箇所+カット割り) |

## 音の扱い

同じ撮影の実音(`nachi_amb45.wav`・45秒ループ)を全動画の底に敷く。社長指示により**はっきり聞こえる音量**にすること。

- ショート・特別編: `volume=0.55`、ナレーションで浅くダック(`ratio=2.5`)
- 本編: `volume=0.36`(尺が長いので控えめ)
- 納品時に `loudnorm=I=-14:TP=-1.5:LRA=11` で YouTube 標準ラウドネスに正規化する

概要欄に「音 — 熊野・那智の滝(実録)」のクレジットを必ず入れる。
