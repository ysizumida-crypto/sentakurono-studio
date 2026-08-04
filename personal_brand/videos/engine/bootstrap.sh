#!/bin/bash
# 素材ゼロの状態から、制作に必要なもの一式を組み立て直す。
#
# 作業場所(コンテナ)は使わないと片付けられるため、目覚めるたびに素材は失われている。
# リポジトリに残すのは「社長にしか撮れない元動画」と「設計図」だけで、
# 残りはすべてここで作り直す。だから素材の重複保存も、更新忘れも起きない。
#
#   bash bootstrap.sh [作業ディレクトリ]
#
# 所要 15〜25分。大半は音声合成エンジンの取得。
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
WORK="${1:-$HOME/kuronon-work}"
DESIGN="$REPO/personal_brand/videos/engine/design"
SK="$REPO/.claude/skills/stabilize-footage/scripts"
HS=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell

mkdir -p "$WORK"/{nachi,mystic,short01,longform}
cd "$WORK"
step () { echo; echo "=== $* ==="; }

step "0/6 依存の確認"
command -v ffmpeg >/dev/null || { echo "ffmpeg がありません"; exit 1; }
python3 -c "import cv2, numpy" 2>/dev/null || pip install --quiet numpy opencv-python-headless

step "1/6 神域の窓(那智の滝)を作る"
# 手順と数値の根拠は personal_brand/videos/NACHI_FOOTAGE.md にある。変えるときはそちらも直すこと。
if [ ! -f nachi/falls_loop.mp4 ]; then
  ffmpeg -y -loglevel error -ss 1.8 -t 4.0 -i "$REPO/personal_brand/videos/source/nachi_falls_gotaki.mov" \
    -an -c:v libx264 -preset slow -crf 12 -pix_fmt yuv420p nachi/seg.mp4
  python3 "$SK/lock_footage.py" nachi/seg.mp4 nachi/locked.mp4 --crop 60 100 950 1010 --order 3
  python3 "$SK/measure_shake.py" nachi/locked.mp4 | tee nachi/lock_report.txt
  grep -q "合格" nachi/lock_report.txt || { echo "固定が基準に達しませんでした"; exit 1; }
  ffmpeg -y -loglevel error -i nachi/locked.mp4 -vf scale=640:680 -an -r 30 \
    -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p nachi/src.mp4
  python3 "$SK/make_loop.py" nachi/src.mp4 nachi/falls_loop.mp4 0.4
fi
# 巻き戻しでコマがずれるのを避けるため、あらかじめ長く繋いだものを使う
[ -f nachi/falls_long.mp4 ] || {
  for _ in $(seq 40); do echo "file '$WORK/nachi/falls_loop.mp4'"; done > nachi/lg.txt
  ffmpeg -y -loglevel error -f concat -safe 0 -i nachi/lg.txt -c copy nachi/falls_long.mp4
}

step "2/6 滝の実音を49秒に伸ばす"
[ -f nachi/nachi_amb.wav ] || {
  ffmpeg -y -loglevel error -i "$REPO/personal_brand/videos/source/nachi_falls_gotaki.mov" \
    -vn -ac 1 -ar 44100 -c:a pcm_s16le nachi/a0.wav
  for i in 1 2 3; do
    ffmpeg -y -loglevel error -i nachi/a$((i-1)).wav -i nachi/a$((i-1)).wav \
      -filter_complex "[0][1]acrossfade=d=1:c1=tri:c2=tri" nachi/a$i.wav
  done
  mv nachi/a3.wav nachi/nachi_amb.wav
}

step "3/6 窓のマスクと背景(すべて30fps)"
# 背景を24fpsで作ると、30fpsの本体に載せる際に5コマに1コマ複製されて滝までカクつく。
$HS --no-sandbox --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
  --window-size=640,680 --screenshot=nachi/mask.png "file://$DESIGN/window_mask.html" 2>/dev/null
render_bg () {  # $1=設計図 $2=出力 $3=幅 $4=高さ
  [ -f "mystic/$2" ] && return
  local d="mystic/fr_${2%.mp4}"; rm -rf "$d"; mkdir -p "$d"
  for k in $(seq 0 239); do
    $HS --no-sandbox --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
      --window-size=$3,$4 --virtual-time-budget=$(( 1000 + k * 1000 / 30 )) \
      --screenshot="$d/f$(printf %04d $k).png" "file://$DESIGN/$1" 2>/dev/null
  done
  ffmpeg -y -loglevel error -framerate 30 -i "$d/f%04d.png" \
    -c:v libx264 -preset fast -crf 19 -pix_fmt yuv420p "mystic/$2"
  rm -rf "$d"
}
render_bg mystic_bg_v3.html mystic_bg_v3.mp4   1080 1920
render_bg mystic_bg.html    mystic_bg_loop.mp4 1920 1080
render_bg mystic_bg_b.html  mystic_bg_b.mp4    1920 1080
render_bg mystic_bg_c.html  mystic_bg_c.mp4    1920 1080

step "4/6 テロップを書き出す"
for f in "$DESIGN"/ov_*.html; do
  $HS --no-sandbox --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
    --default-background-color=00000000 --window-size=1080,1920 \
    --screenshot="short01/$(basename "${f%.html}").png" "file://$f" 2>/dev/null
done

step "5/6 BGM を取得"
# Kevin MacLeod "Ishikari Lore" (CC BY 4.0) — 概要欄のクレジット表記が必須
[ -f bgm.mp3 ] || curl -sL --retry 3 -o bgm.mp3 \
  "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Ishikari%20Lore.mp3" || \
  echo "BGM を取得できませんでした。手動で用意してください"

step "6/6 音声合成エンジン(VOICEVOX)"
if [ ! -x vv/linux-cpu-x64/run ]; then
  mkdir -p vv && cd vv
  curl -sL --retry 3 -o vv.7z.001 \
    "https://github.com/VOICEVOX/voicevox_engine/releases/download/0.24.1/voicevox_engine-linux-cpu-x64-0.24.1.7z.001"
  7z x -y vv.7z.001 >/dev/null && rm -f vv.7z.001
  chmod +x linux-cpu-x64/run; cd ..
fi

echo
echo "=== 組み立て完了: $WORK ==="
ls -la nachi/falls_loop.mp4 nachi/nachi_amb.wav mystic/mystic_bg_v3.mp4 2>/dev/null | awk '{print "  "$NF, $5"バイト"}'
echo "音声合成の起動: cd $WORK/vv/linux-cpu-x64 && NO_PROXY=127.0.0.1 ./run --host 127.0.0.1 --port 50021 &"
