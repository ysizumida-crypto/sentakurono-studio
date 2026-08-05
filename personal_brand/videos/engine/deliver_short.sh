#!/bin/bash
# 生成したショートを「納品できる形」に仕上げる。
#
# 生成器の出力は音量が -25 LUFS 前後で、そのままでは YouTube で小さく聞こえる。
# また 1本 37MB あり、携帯へ送るには重い。ここで両方を片付ける。
#
#   bash deliver_short.sh ~/kuronon-work/kaiun_sep/out ~/kuronon-work/kaiun_sep/deliver
#
# 音量: loudnorm=I=-14:TP=-1.5:LRA=11(YouTube の標準ラウドネス)を**2回通しで**当てる。
#   1回通しだと -15.8 前後までしか寄らない。YouTube は大きい音は下げるが小さい音は
#   上げないので、その差はそのまま「他の動画より小さい」として残る。
# 画質: crf 23。窓の色が元素材からずれないことを verify_short.py で確認済み。
set -euo pipefail
SRC="${1:?入力ディレクトリ}"; DST="${2:-$SRC/../deliver}"
LN="I=-14:TP=-1.5:LRA=11"
mkdir -p "$DST"
for f in "$SRC"/kaiun_*.mp4; do
  out="$DST/$(basename "$f")"
  [ -f "$out" ] && continue
  # 1回目: 測るだけ
  m=$(ffmpeg -hide_banner -nostats -i "$f" -af "loudnorm=$LN:print_format=json" -f null - 2>&1 |
      sed -n '/^{/,/^}/p')
  get () { printf '%s' "$m" | grep "\"$1\"" | cut -d'"' -f4; }
  # 2回目: 測った値を渡して線形に合わせる
  ffmpeg -y -loglevel error -i "$f" \
    -c:v libx264 -preset slow -crf 23 -pix_fmt yuv420p -r 30 \
    -af "loudnorm=$LN:measured_I=$(get input_i):measured_TP=$(get input_tp):measured_LRA=$(get input_lra):measured_thresh=$(get input_thresh):offset=$(get target_offset):linear=true" \
    -c:a aac -b:a 160k -movflags +faststart "$out"
  printf '%s  %s\n' "$(basename "$out")" "$(du -h "$out" | cut -f1)"
done
