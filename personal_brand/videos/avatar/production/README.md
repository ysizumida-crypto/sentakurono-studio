# くろのん 制作用素材 v2.0(マスターアート派生)

全て 1254×1254 / 背景透過PNG。マスターアート `../kuronon_master_art_v2.png` から生成。
`.svg` は同名PNGの生成ソース(ベース画像+表情オーバーレイ)。修正時はSVGを編集して再レンダリングする。

## ファイル一覧

| ファイル | 内容 | 用途 |
|---|---|---|
| `kuronon_base_transparent.png` | 基本(通常表情・口閉じ) | 全カットのベース。**口パクの「閉」もこれ** |
| `kuronon_happy.png` | 笑顔(にこにこ目) | 良い報告・成功・締めの口上 |
| `kuronon_surprised.png` | 驚き(見開き目+口開き) | 想定外の数字・どんでん返し |
| `kuronon_troubled.png` | 困り(困り眉+汗) | 交渉難航・リスク説明 |
| `kuronon_serious.png` | 真剣(キリッと眉) | 撤退ライン・重要な判断の解説 |
| `kuronon_mouth_half.png` | 通常表情・口半開き | 口パク中間コマ |
| `kuronon_mouth_open.png` | 通常表情・口開き | 口パク開きコマ |

## 口パクの使い方(CapCut等)

音声に合わせて `base(閉) → mouth_half → mouth_open → mouth_half → …` を循環。
2コマ(閉/開)でも成立するが、3コマの方が滑らか。表情カット中の口パクが必要になったら、該当表情のSVGに口オーバーレイを足して追加生成する。

## 再生成手順(組織内・無料)

```bash
# SVG編集後:
chromium --headless --default-background-color=00000000 \
  --screenshot=<出力>.png --window-size=1254,1254 <対象>.svg
```

## 規律

- 新規パターン追加時も `kuronon_<expression>_<mouth>.png` の命名規則に従う
- マスターアートの改変は社長承認後のみ(ブランド正本)
