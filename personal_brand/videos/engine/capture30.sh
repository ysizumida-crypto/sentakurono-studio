#!/bin/bash
# 背景を 30fps で書き出す。
# 24fps のままだと 30fps の本編に載せる際に5コマに1コマ複製され、
# 窓の実写まで一緒にカクついてしまう(2026-08-03 判明)。全工程を 30fps に揃える。
set -e
cd /tmp/claude-0/-home-user-sentakurono-studio/907dc579-de5f-57c5-893f-d6ea2ffa36f8/scratchpad/mystic
HS=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell

render () {  # $1=html $2=出力mp4 $3=幅 $4=高さ
  local html=$1 out=$2 W=$3 H=$4 dir="fr30_${2%.mp4}"
  rm -rf "$dir"; mkdir -p "$dir"
  for k in $(seq 0 239); do        # 8.0秒 × 30fps = 240コマ
    BUDGET=$(( 1000 + k * 1000 / 30 ))
    "$HS" --no-sandbox --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
      --window-size=$W,$H --virtual-time-budget=$BUDGET \
      --screenshot="$dir/f$(printf %04d $k).png" "file://$PWD/$html" 2>/dev/null
  done
  ffmpeg -y -loglevel error -framerate 30 -i "$dir/f%04d.png" \
    -c:v libx264 -preset fast -crf 19 -pix_fmt yuv420p "$out"
  rm -rf "$dir"
  echo "$out: $(ffprobe -v error -show_entries stream=r_frame_rate,nb_frames -of csv=p=0 "$out")"
}

render mystic_bg_v3.html  mystic_bg_v3.mp4   1080 1920
render mystic_bg.html     mystic_bg_loop.mp4 1920 1080
render mystic_bg_b.html   mystic_bg_b.mp4    1920 1080
render mystic_bg_c.html   mystic_bg_c.mp4    1920 1080
echo BG30-DONE
