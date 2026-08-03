# 神域の窓 — 那智の滝素材の正本仕様

社長撮影の実写を、全動画に共通で使う「神域の窓」素材に加工する手順の正本。

**採用素材: IMG_0271.mov(6.99秒・iPhone縦位置)— 那智の滝 御瀧拝所からの実写**
2026-08-03 に IMG_0270.mov から差し替え(社長判断)。滝の落差全体と、注連縄を巻いた磐座・金の御幣が写る、飛瀧神社の拝所そのものの画。

## 事故の記録(必読)

初回制作では ffmpeg の `vidstabdetect/transform` をバーチャル三脚モードで通し、目視で「固定できた」と判断して30本以上を納品した。
後日 px 単位で実測したところ、**残存ブレは平均42.8px** で、ほぼ無補正だった。原因は補正幅の不足:

- 手持ち撮影のブレは 220〜300px に達する
- `vidstabtransform` の `zoom=10` は元画角の10%(=108px)しか補正できない
- 補正しきれない分はそのまま残るが、処理自体はエラーなく完了するため気づけない

**教訓**: 補正後は必ず `stabilize-footage` スキルの `measure_shake.py` で実測し、数値で合否を判断する。

## 画角の設計(2026-08-03 決定)

窓は蝕の中心に開く楕円(640x680・ほぼ真円)。この形に何を映すかで印象が決まる。

- **採用**: 滝の落差全体を柱として通す画(元座標 x60,y100 の 950x1010)。楕円の天から地へ銀の水が貫き、蝕が滝への入口になる。小さく表示されても「滝」と一瞬で読める
- **不採用**: 御幣・注連縄を主役にした画。信仰の場としては雄弁だが、640x680 では金の御幣が数十pxにしかならず読めない。落差の迫力も失う
- **色調**: この素材は旧素材より明るいため、テロップ(白文字)と白い水が競合する。`brightness=-0.23` まで沈めて水を銀色に落ち着かせ、文字を確実に読ませる

## 現行の加工手順

```bash
SK=.claude/skills/stabilize-footage/scripts

# 1. 回転メタデータを適用して正立させ、最も揺れの少ない 1.8〜5.8秒を切り出す
#    (区間は measure_shake.py --scan 4.0 で特定した)
ffmpeg -y -ss 1.8 -t 4.0 -i IMG_0271.mov -an -c:v libx264 -preset slow -crf 12 -pix_fmt yuv420p seg.mp4

# 2. 窓に映る矩形を最優先で絶対固定する
python3 $SK/lock_footage.py seg.mp4 locked.mp4 --crop 60 100 950 1010 --order 3

# 3. 実測(平均1px未満で合格)
python3 $SK/measure_shake.py locked.mp4

# 4. 1.5倍にゆっくりして神秘系の色に沈め、順再生+逆再生で継ぎ目のないループにする
G="eq=saturation=0.50:contrast=1.16:brightness=-0.23,colorbalance=rm=.09:gm=.03:bm=-.10:rh=.04:bh=-.06"
ffmpeg -y -i locked.mp4 -filter:v "setpts=1.5*PTS,scale=640:680,$G" -an -c:v libx264 -preset slow -crf 15 -pix_fmt yuv420p fwd.mp4
ffmpeg -y -i fwd.mp4 -vf reverse -an -c:v libx264 -preset slow -crf 15 -pix_fmt yuv420p rev.mp4
printf "file 'fwd.mp4'\nfile 'rev.mp4'\n" > cc.txt
ffmpeg -y -f concat -safe 0 -i cc.txt -c copy falls_loop.mp4

# 5. 滝の実音を自己クロスフェードで継ぎ目なく49秒まで伸ばす
ffmpeg -y -i IMG_0271.mov -vn -ac 1 -ar 44100 -c:a pcm_s16le raw.wav
for i in 1 2 3; do ffmpeg -y -i in.wav -i in.wav -filter_complex "[0][1]acrossfade=d=1:c1=tri:c2=tri" out.wav; done
```

**成果物**: `falls_loop.mp4`(640x680・**12.0秒**)/ `nachi_amb.wav`(49.0秒)

## 実測値

| 状態 | 平均残存ブレ | 最大 |
|---|---|---|
| 元素材 IMG_0271 | 160.3px | 301.3px |
| 採用区間(1.8〜5.8秒)を絶対固定 | **0.31px** | 0.57px |
| (参考)旧素材 IMG_0270 を vid.stab | 42.8px | 235.2px |

## 生成器側の設定

ループ長を変えたら、参照している定数を必ず全部更新する(参照位置がずれて静止画のように見える事故が起きる)。

| ファイル | 定数 |
|---|---|
| `personal_brand/shorts/september_batch/generator.py` | `WINDUR = 12.0` |
| `personal_brand/shorts/specials/build_sayonara.py` | `woff % 12.0` |
| `personal_brand/videos/engine/lf_engine.py` | `% 12.0`(2箇所+カット割り) |

## 音の扱い

同じ撮影の実音を全動画の底に敷く。社長指示により**はっきり聞こえる音量**にすること。
IMG_0271 の音は拝所で録れているため旧素材より 3.4dB 大きく、人声・風切りのない広帯域の滝音。

- ショート・特別編: `volume=0.55`、ナレーションで浅くダック(`ratio=2.5`)
- 本編: `volume=0.36`(尺が長いので控えめ)
- 納品時に `loudnorm=I=-14:TP=-1.5:LRA=11` で YouTube 標準ラウドネスに正規化する

概要欄に「音 — 熊野・那智の滝(実録)」のクレジットを必ず入れる。
